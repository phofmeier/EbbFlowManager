from copy import deepcopy
from datetime import UTC, datetime, timedelta
from math import sin
from threading import Lock

import pytest
from fastapi.testclient import TestClient

from ebb_flow_manager_api.app import app, controller_store
from ebb_flow_manager_api.controllers import (
    ControllerSnapshot,
    Document,
    controller_summary,
)
from ebb_flow_manager_api.grow import GrowPhaseUpdate, GrowSelection, load_crop_profiles
from ebb_flow_manager_api.grow_lights import (
    GrowLight,
    GrowLightSettings,
    load_grow_lights,
)


class DemoGrowProfiles:
    def __init__(self) -> None:
        self.crops: dict[str, Document] = {
            crop_id: {"id": crop_id, **crop}
            for crop_id, crop in load_crop_profiles().items()
        }
        self.selections: dict[int, Document] = {}
        self.lock = Lock()

    def catalog(self) -> list[Document]:
        with self.lock:
            return deepcopy(sorted(self.crops.values(), key=lambda crop: crop["name"]))

    def save_phase(self, crop_id: str, phase_id: str, update: GrowPhaseUpdate) -> None:
        with self.lock:
            crop = self.crops.setdefault(crop_id, {"id": crop_id, "phases": {}})
            crop["name"] = update.crop_name
            crop["phases"][phase_id] = update.phase()

    def has_phase(self, selection: GrowSelection) -> bool:
        with self.lock:
            return selection.phase_id in self.crops.get(selection.crop_id, {}).get(
                "phases", {}
            )

    def selection(self, controller_id: int) -> Document | None:
        with self.lock:
            return self.selections.get(controller_id)

    def save_selection(self, controller_id: int, selection: GrowSelection) -> None:
        with self.lock:
            self.selections[controller_id] = selection.model_dump()


class DemoGrowLights:
    def __init__(self) -> None:
        self.lights = {
            light_id: GrowLight(id=light_id, **light)
            for light_id, light in load_grow_lights().items()
        }
        self.installations: dict[int, GrowLightSettings] = {}
        self.installation_lock = Lock()

    def catalog(self) -> list[GrowLight]:
        return sorted(self.lights.values(), key=lambda light: light.name)

    def light(self, light_id: str) -> GrowLight | None:
        return self.lights.get(light_id)

    def installation(self, controller_id: int) -> GrowLightSettings | None:
        with self.installation_lock:
            return self.installations.get(controller_id)

    def save_installation(
        self, controller_id: int, update: GrowLightSettings
    ) -> GrowLightSettings:
        with self.installation_lock:
            current = self.installations.get(controller_id, GrowLightSettings())
            settings = current.model_copy(update=update.model_dump(exclude_unset=True))
            self.installations[controller_id] = settings
            return settings


class DemoControllers:
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

    def configuration(self, controller_id: int) -> Document:
        controller = self.controllers.get(controller_id)
        return controller.config.copy() if controller else {}

    def apply(self, controller_id: int, section: str, config: Document) -> str:
        current = self.controllers[controller_id].config
        if current.get(section) == config:
            return "unchanged"
        current.update({section: config, "ts_received": datetime.now(UTC)})
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


@pytest.fixture
def manager_config(tmp_path):
    config = tmp_path / "config.yml"
    config.write_text(
        "database:\n  connection_string: mongodb://localhost\n"
        "mqtt:\n  broker: localhost\n",
        encoding="utf-8",
    )
    return config


@pytest.fixture
def demo_controllers() -> DemoControllers:
    return DemoControllers()


@pytest.fixture
def client(monkeypatch, demo_controllers) -> TestClient:
    monkeypatch.setitem(
        app.dependency_overrides, controller_store, lambda: demo_controllers
    )
    return TestClient(app)
