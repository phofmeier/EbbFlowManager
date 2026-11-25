from fastapi.testclient import TestClient

from ebb_flow_manager_api.app import app
from ebb_flow_manager_api.controllers import DemoControllers


def test_list_controllers():
    response = TestClient(app).get("/controllers/")

    assert response.status_code == 200
    assert response.json() == [1, 2]


def test_list_controller_connection_states():
    response = TestClient(app).get("/api/controllers")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Controller 1", "connected": True},
        {"id": 2, "name": "Controller 2", "connected": False},
    ]


def test_selected_controller_dashboard():
    response = TestClient(app).get("/api/controllers/1/dashboard")

    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["id"] == 1
    assert dashboard["connection"]["rssi_dbm"] == -58
    assert dashboard["pump"] == {
        "duration_seconds": 120,
        "start_times": ["06:00", "13:28", "20:00"],
    }
    assert dashboard["light"]["changes"][0] == {
        "time": "06:00",
        "output_percent": 80,
        "transition_minutes": 45,
    }
    assert {"minute": 405, "output_percent": 80} in dashboard["light"]["points"]


def test_save_pump_schedule_for_the_selected_controller(monkeypatch):
    monkeypatch.setattr("ebb_flow_manager_api.app.controllers", DemoControllers())
    client = TestClient(app)
    response = client.put(
        "/api/controllers/1/pump",
        json={"duration_seconds": 75, "start_times": ["21:00", "13:28"]},
    )

    assert response.status_code == 200
    assert response.json() == {"state": "applied"}
    selected = client.get("/api/controllers/1/dashboard").json()
    assert selected["pump"] == {
        "duration_seconds": 75,
        "start_times": ["13:28", "21:00"],
    }
    assert selected["light"]["changes"][0]["output_percent"] == 80
    assert selected["latest_change"] == {"section": "pump_cycles", "state": "applied"}
    other = client.get("/api/controllers/2/dashboard").json()
    assert other["pump"]["duration_seconds"] == 90


def test_save_light_output_percentage_and_transition(monkeypatch):
    monkeypatch.setattr("ebb_flow_manager_api.app.controllers", DemoControllers())
    client = TestClient(app)
    response = client.put(
        "/api/controllers/1/light",
        json={
            "changes": [
                {"time": "06:00", "output_percent": 62.5, "transition_minutes": 15},
                {"time": "21:00", "output_percent": 0, "transition_minutes": 60},
            ]
        },
    )

    assert response.json() == {"state": "applied"}
    light = client.get("/api/controllers/1/dashboard").json()["light"]
    assert {"minute": 375, "output_percent": 62.5} in light["points"]
    assert {"minute": 1320, "output_percent": 0} in light["points"]


def test_reject_invalid_or_disconnected_pump_updates():
    client = TestClient(app)
    for time in ("9:07", "24:00", "13:60"):
        invalid = client.put(
            "/api/controllers/1/pump",
            json={"duration_seconds": 60, "start_times": [time]},
        )
        assert invalid.status_code == 422

    disconnected = client.put(
        "/api/controllers/2/pump",
        json={"duration_seconds": 60, "start_times": ["13:28"]},
    )
    assert disconnected.status_code == 409
