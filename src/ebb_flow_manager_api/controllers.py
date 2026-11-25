from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from math import sin
from typing import Any

from ebb_flow_manager_api.grow import DemoGrowProfiles
from ebb_flow_manager_api.grow_lights import DemoGrowLights
from ebb_flow_manager_api.schedules import present_light, present_pump

Document = dict[str, Any]


@dataclass
class ControllerSnapshot:
    status: Document
    config: Document = field(default_factory=dict)
    reservoir: list[Document] = field(default_factory=list)
    diagnostics: list[Document] = field(default_factory=list)
    latest_reservoir: Document | None = None
    latest_diagnostics: Document | None = None

    def dashboard(self, controller_id: int, demo: bool, now: datetime) -> dict:
        return {
            "id": controller_id,
            "demo": demo,
            "history_end": now,
            "connection": {
                "connected": self.status.get("connection") == "connected",
                "rssi_dbm": self.status.get("rssi_level"),
                "firmware_version": self.status.get("version"),
                "status_received_at": self.status.get("ts_received"),
                "config_received_at": self.config.get("ts_received"),
            },
            "pump": present_pump(self.config.get("pump_cycles")),
            "light": present_light(self.config.get("light")),
            "reservoir": {
                "latest": self.latest_reservoir,
                "history": self.reservoir,
            },
            "diagnostics": {
                "latest": self.latest_diagnostics,
                "history": self.diagnostics,
            },
        }


def controller_summary(controller_id: int, status: Document) -> dict:
    return {
        "id": controller_id,
        "name": f"Controller {controller_id}",
        "connected": status.get("connection") == "connected",
    }


class DemoControllers:
    demo = True

    def __init__(self) -> None:
        self.grow = DemoGrowProfiles()
        self.grow_lights = DemoGrowLights()
        now = datetime.now(UTC).replace(second=0, microsecond=0)
        self.controllers = {
            1: self.sample(now, connected=True),
            2: self.sample(now - timedelta(hours=2), connected=False),
        }

    @staticmethod
    def sample(now: datetime, connected: bool) -> ControllerSnapshot:
        status = {
            "connection": "connected" if connected else "disconnected",
            "rssi_level": -58 if connected else None,
            "version": "1.8.0",
            "ts_received": now - timedelta(minutes=20) if connected else now,
        }
        config = {
            "ts_received": now - timedelta(hours=5),
            "pump_cycles": {
                "pump_time_s": 120 if connected else 90,
                "nr_pump_cycles": 3 if connected else 2,
                "times_minutes_per_day": [360, 808, 1200] if connected else [480, 960],
            },
            "light": {
                "nr_light_changes": 3,
                "times_min_per_day": [360, 720, 1260],
                "intensity": [26214, 32767, 0] if connected else [19660, 22937, 0],
                "rise_time_min": [45, 30, 60],
            },
        }
        reservoir = [
            {
                "ts": now - timedelta(minutes=30 * (48 - index)),
                "distance_mm": round(139 + 3 * sin(index / 6) + 22 * (index % 14 == 9)),
            }
            for index in range(49)
        ]
        diagnostics = [
            {
                "ts": now - timedelta(hours=24 - index),
                "free_heap_size": 93440 + round(3100 * sin(index / 3)),
                "min_free_heap_size": 80128 - 128 * (index // 6),
                "store_total_bytes": 1048576,
                "store_used_bytes": 239616 + 4096 * (index // 4),
            }
            for index in range(25)
        ]
        return ControllerSnapshot(
            status, config, reservoir, diagnostics, reservoir[-1], diagnostics[-1]
        )

    def summaries(self) -> list[dict]:
        return [
            controller_summary(controller_id, snapshot.status)
            for controller_id, snapshot in self.controllers.items()
        ]

    def status(self, controller_id: int) -> Document | None:
        controller = self.controllers.get(controller_id)
        return controller.status if controller else None

    def apply(self, controller_id: int, section: str, config: Document) -> str:
        self.controllers[controller_id].config.update(
            {section: config, "ts_received": datetime.now(UTC)}
        )
        return "applied"

    def snapshot(self, controller_id: int, now: datetime) -> ControllerSnapshot | None:
        controller = self.controllers.get(controller_id)
        if controller is None:
            return None
        earliest = now - timedelta(hours=24)
        return ControllerSnapshot(
            controller.status,
            controller.config.copy(),
            [sample for sample in controller.reservoir if sample["ts"] >= earliest],
            [sample for sample in controller.diagnostics if sample["ts"] >= earliest],
            controller.latest_reservoir,
            controller.latest_diagnostics,
        )
