import pytest


def test_list_controllers(client):
    response = client.get("/controllers/")

    assert response.status_code == 200
    assert response.json() == [1, 2]


def test_list_controller_connection_states(client):
    response = client.get("/api/controllers")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Controller 1", "connected": True},
        {"id": 2, "name": "Controller 2", "connected": False},
    ]


def test_selected_controller_dashboard(client):
    response = client.get("/api/controllers/1/dashboard")

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
        "output_percent_exact": 26214 * 100 / 32767,
        "transition_minutes": 45,
    }
    assert {"minute": 405, "output_percent": 80} in dashboard["light"]["points"]


def test_save_pump_schedule_for_the_selected_controller(client):
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


def test_save_light_output_percentage_and_transition(client):
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


def test_stale_editor_cannot_overwrite_a_newer_schedule(client):
    controller = "/api/controllers/1"
    original = client.get(f"{controller}/dashboard").json()
    headers = {"X-Schedule-Revision": original["schedule_revisions"]["pump"]}
    updated = {**original["pump"], "duration_seconds": 75}
    stale = {**original["pump"], "start_times": ["06:00", "20:00"]}

    saved = client.put(f"{controller}/pump", json=updated, headers=headers)
    conflict = client.put(f"{controller}/pump", json=stale, headers=headers)
    dashboard = client.get(f"{controller}/dashboard").json()

    assert saved.json() == {"state": "applied"}
    assert conflict.status_code == 409
    assert "changed since you opened" in conflict.json()["detail"]
    assert dashboard["pump"] == updated
    assert dashboard["schedule_revisions"]["light"] == (
        original["schedule_revisions"]["light"]
    )


def test_reported_light_output_round_trips_without_a_write(client, demo_controllers):
    demo_controllers.apply(
        1,
        "light",
        {
            "nr_light_changes": 1,
            "times_min_per_day": [360],
            "intensity": [3276],
            "rise_time_min": [0],
        },
    )
    controller = "/api/controllers/1"
    dashboard = client.get(f"{controller}/dashboard").json()
    [change] = dashboard["light"]["changes"]
    assert change["output_percent"] == 10
    response = client.put(
        f"{controller}/light",
        json={
            "changes": [{**change, "output_percent": change["output_percent_exact"]}]
        },
        headers={"X-Schedule-Revision": dashboard["schedule_revisions"]["light"]},
    )

    assert response.json() == {"state": "unchanged"}


@pytest.mark.parametrize(("transition", "status"), [(29, 200), (30, 422), (60, 422)])
def test_light_transition_must_finish_before_midnight(client, transition, status):
    response = client.put(
        "/api/controllers/1/light",
        json={
            "changes": [
                {"time": "01:00", "output_percent": 100, "transition_minutes": 0},
                {
                    "time": "23:30",
                    "output_percent": 0,
                    "transition_minutes": transition,
                },
            ]
        },
    )

    assert response.status_code == status
    if status == 422:
        assert "finish before midnight" in response.json()["detail"][0]["msg"]


def test_reject_invalid_or_disconnected_pump_updates(client):
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


def test_zero_duration_pump_schedule_requires_no_starts(client):
    endpoint = "/api/controllers/1/pump"

    scheduled = client.put(
        endpoint, json={"duration_seconds": 0, "start_times": ["06:00"]}
    )
    disabled = client.put(endpoint, json={"duration_seconds": 0, "start_times": []})

    assert scheduled.status_code == 422
    assert disabled.json() == {"state": "applied"}
