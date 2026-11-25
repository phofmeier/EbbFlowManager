import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event
from time import monotonic, sleep

import paho.mqtt.client as mqtt
import yaml
from pymongo import DESCENDING, MongoClient

from ebb_flow_manager_api.controllers import (
    ControllerSnapshot,
    Document,
    controller_summary,
)
from ebb_flow_manager_api.grow import MongoGrowProfiles
from ebb_flow_manager_api.grow_lights import MongoGrowLights

logger = logging.getLogger(__name__)


def report_timestamp(value: object) -> datetime | None:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return None
    if isinstance(value, datetime) and value.utcoffset() is not None:
        return value
    return None


class LiveControllers:
    demo = False

    def __init__(self, config_path: str) -> None:
        config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        database = config["database"]
        self.mqtt = config["mqtt"]
        self.id_field = database.get("id_field_name", "id")
        self.mongo: MongoClient[Document] = MongoClient(
            database["connection_string"],
            tz_aware=True,
            serverSelectionTimeoutMS=2500,
            timeoutMS=3000,
            connect=False,
        )
        db = self.mongo[database.get("database_name", "efc")]
        self.status_collection = db[
            database.get("collection_status_name", "status_static")
        ]
        self.config_collection = db[
            database.get("collection_config_name", "config_static")
        ]
        self.level_collection = db[database.get("collection_level_name", "level_timed")]
        self.heap_collection = db[
            database.get("collection_heap_size_name", "heap_timed")
        ]
        self.grow = MongoGrowProfiles(
            db[database.get("collection_crop_profiles_name", "crop_profiles")],
            db[database.get("collection_grow_selections_name", "grow_selections")],
        )
        self.grow_lights = MongoGrowLights(
            db[database.get("collection_grow_lights_name", "grow_lights")],
            db[
                database.get(
                    "collection_grow_light_installations_name",
                    "grow_light_installations",
                )
            ],
        )

    def summaries(self) -> list[dict]:
        statuses = self.status_collection.find(
            {}, {"_id": 0, self.id_field: 1, "connection": 1}
        ).sort(self.id_field)
        return [
            controller_summary(status[self.id_field], status) for status in statuses
        ]

    def status(self, controller_id: int) -> Document | None:
        return self.status_collection.find_one(
            {self.id_field: controller_id}, {"_id": 0}
        )

    def configuration(self, controller_id: int) -> Document:
        return (
            self.config_collection.find_one({self.id_field: controller_id}, {"_id": 0})
            or {}
        )

    def snapshot(self, controller_id: int, now: datetime) -> ControllerSnapshot | None:
        status = self.status(controller_id)
        if status is None:
            return None
        device = {self.id_field: controller_id}
        window = {**device, "ts": {"$gte": now - timedelta(hours=24), "$lte": now}}
        level_fields = {"_id": 0, "ts": 1, "distance_mm": 1}
        heap_fields = {
            "_id": 0,
            "ts": 1,
            "free_heap_size": 1,
            "min_free_heap_size": 1,
            "store_used_bytes": 1,
            "store_total_bytes": 1,
        }
        reservoir = list(self.level_collection.find(window, level_fields).sort("ts"))
        diagnostics = list(self.heap_collection.find(window, heap_fields).sort("ts"))
        return ControllerSnapshot(
            status=status,
            config=self.configuration(controller_id),
            reservoir=reservoir,
            diagnostics=diagnostics,
            latest_reservoir=(
                reservoir[-1]
                if reservoir
                else self.level_collection.find_one(
                    device, level_fields, sort=[("ts", DESCENDING)]
                )
            ),
            latest_diagnostics=(
                diagnostics[-1]
                if diagnostics
                else self.heap_collection.find_one(
                    device, heap_fields, sort=[("ts", DESCENDING)]
                )
            ),
        )

    def apply(self, controller_id: int, section: str, config: Document) -> str:
        previous = self.configuration(controller_id)
        if previous.get(section) == config:
            return "unchanged"

        previous_at = report_timestamp(previous.get("ts_received"))
        started_at = datetime.now(UTC)
        # MongoDB dates are stored with millisecond precision.
        started_at -= timedelta(microseconds=started_at.microsecond % 1000)
        if not self.publish({"id": controller_id, section: config}):
            return "unconfirmed"

        deadline = monotonic() + 5
        while monotonic() < deadline:
            reported = self.configuration(controller_id)
            received_at = report_timestamp(reported.get("ts_received"))
            if (
                received_at is not None
                and received_at >= started_at
                and (previous_at is None or received_at > previous_at)
                and reported.get(section) == config
            ):
                return "applied"
            sleep(0.25)
        return "unconfirmed"

    def publish(self, payload: Document) -> bool:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
        client.connect_timeout = 3
        if username := self.mqtt.get("username"):
            client.username_pw_set(username, self.mqtt.get("password"))

        connected = Event()

        def on_connect(client, userdata, flags, reason_code, properties):
            if not reason_code.is_failure:
                connected.set()

        client.on_connect = on_connect
        try:
            client.connect(self.mqtt["broker"], self.mqtt.get("port", 1883))
            client.loop_start()
            if not connected.wait(timeout=3):
                return False
            message = client.publish(
                self.mqtt.get("new_config_publish_topic", "ef/efc/config/set"),
                json.dumps(payload),
                qos=1,
                retain=False,
            )
            message.wait_for_publish(timeout=3)
            return message.is_published()
        except (OSError, RuntimeError, ValueError):
            logger.exception(
                "Could not publish settings for controller %s", payload["id"]
            )
            return False
        finally:
            client.disconnect()
            client.loop_stop()
