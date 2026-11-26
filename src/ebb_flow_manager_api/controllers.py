from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

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

    def dashboard(self, controller_id: int, now: datetime) -> dict:
        return {
            "id": controller_id,
            "demo": False,
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
