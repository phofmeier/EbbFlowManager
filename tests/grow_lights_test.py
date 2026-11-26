import pytest

HABIBI_ID = "bloomstar-fluxshield-habibi-150"


@pytest.mark.parametrize("saved_distance", [None, 30])
def test_schedule_suggestion_uses_entered_distance_without_saving_it(
    client, saved_distance
):
    controller = "/api/controllers/1"
    installation = {"grow_light_id": HABIBI_ID, "canopy_distance_cm": saved_distance}
    saved = client.patch(f"{controller}/grow-light-installation", json=installation)
    assert saved.status_code == 200

    response = client.post(
        f"{controller}/light/suggestion",
        json={
            "canopy_distance_cm": 20,
            "max_ppfd_umol_m2_s": 322,
            "dli_mol_m2_day": 17,
            "rise_time_minutes": 30,
        },
    )

    assert response.status_code == 200
    suggestion = response.json()
    assert suggestion["canopy_distance_cm"] == 20
    assert suggestion["schedule"]["changes"][0]["output_percent"] == 41.46
    dashboard = client.get(f"{controller}/dashboard").json()
    assert dashboard["grow_light_installation"] == installation


@pytest.mark.parametrize(
    ("target_dli", "start", "ramp_down", "estimated_dli"),
    [
        (13.33584, "06:00", "17:30", 13.33584),
        (17, "04:25", "19:05", 17.00664),
    ],
)
def test_suggest_light_schedule_reaches_targets_without_saving(
    client, target_dli, start, ramp_down, estimated_dli
):
    controller = "/api/controllers/1"
    assert (
        client.put(
            f"{controller}/grow-light-installation",
            json={"grow_light_id": HABIBI_ID, "canopy_distance_cm": 30},
        ).status_code
        == 200
    )
    original = client.get(f"{controller}/dashboard").json()["light"]
    response = client.post(
        f"{controller}/light/suggestion",
        json={
            "max_ppfd_umol_m2_s": 322,
            "dli_mol_m2_day": target_dli,
            "rise_time_minutes": 30,
        },
    )

    assert response.status_code == 200
    suggestion = response.json()
    assert suggestion["schedule"]["changes"] == [
        {"time": start, "output_percent": 50, "transition_minutes": 30},
        {"time": ramp_down, "output_percent": 0, "transition_minutes": 30},
    ]
    assert suggestion["peak_ppfd_umol_m2_s"] == 322
    assert suggestion["dli_mol_m2_day"] == pytest.approx(estimated_dli)
    assert suggestion["dli_status"] == "extrapolated"
    assert client.get(f"{controller}/dashboard").json()["light"] == original

    assert (
        client.put(f"{controller}/light", json=suggestion["schedule"]).status_code
        == 200
    )
    saved = client.get(f"{controller}/dashboard").json()["light"]
    assert saved["dli_mol_m2_day"] == pytest.approx(suggestion["dli_mol_m2_day"])


@pytest.mark.parametrize(
    ("ppfd", "dli", "rise", "feedback"),
    [
        (700, 17, 30, "This fixture can reach 624"),
        (322, 0.1, 120, "Minimum DLI"),
        (322, 30, 0, "Maximum DLI"),
        (322, 27.24, 30, "Maximum DLI"),
    ],
)
def test_schedule_suggestion_explains_unreachable_targets(
    client, ppfd, dli, rise, feedback
):
    controller = "/api/controllers/1"
    assert (
        client.put(
            f"{controller}/grow-light-installation",
            json={"grow_light_id": HABIBI_ID, "canopy_distance_cm": 30},
        ).status_code
        == 200
    )
    response = client.post(
        f"{controller}/light/suggestion",
        json={
            "max_ppfd_umol_m2_s": ppfd,
            "dli_mol_m2_day": dli,
            "rise_time_minutes": rise,
        },
    )
    assert response.status_code == 422
    assert feedback in response.json()["detail"]


def test_long_schedule_extends_daylight_at_both_ends(
    client,
):
    controller = "/api/controllers/1"
    targets = {
        "max_ppfd_umol_m2_s": 322.05,
        "dli_mol_m2_day": 25,
        "rise_time_minutes": 30,
    }
    response = client.post(f"{controller}/light/suggestion", json=targets)
    assert response.status_code == 409

    assert (
        client.put(
            f"{controller}/grow-light-installation",
            json={"grow_light_id": HABIBI_ID, "canopy_distance_cm": 30},
        ).status_code
        == 200
    )
    response = client.post(f"{controller}/light/suggestion", json=targets)
    assert response.status_code == 200
    suggestion = response.json()
    assert suggestion["schedule"]["changes"] == [
        {"time": "00:58", "output_percent": 50, "transition_minutes": 30},
        {"time": "22:32", "output_percent": 0, "transition_minutes": 30},
    ]
    assert suggestion["peak_ppfd_umol_m2_s"] <= targets["max_ppfd_umol_m2_s"]
    assert suggestion["dli_mol_m2_day"] == pytest.approx(25, abs=0.01)


def test_light_catalog_contains_the_manufacturer_calibration(client):
    response = client.get("/api/grow-lights")

    assert response.status_code == 200
    light = next(light for light in response.json() if light["id"] == HABIBI_ID)
    assert light["name"] == "BloomStar FLUXshield Habibi 150"
    assert light["ppfd"]["reference_area_cm"] == {"width": 40, "length": 40}
    assert light["ppfd"]["statistic"] == "area_average"
    assert light["ppfd"]["output_percent"] == list(range(10, 101, 10))
    assert light["ppfd"]["canopy_distance_cm"] == [20, 30, 40]
    assert light["ppfd"]["values_umol_m2_s"] == [
        [71, 156, 234, 311, 386, 460, 533, 605, 676, 746],
        [65, 131, 195, 260, 322, 384, 446, 506, 565, 624],
        [55, 109, 163, 217, 269, 321, 372, 423, 472, 520],
    ]


@pytest.mark.parametrize(
    ("output_percent", "distance_cm", "ppfd", "status"),
    [
        (50, 30, 322, "reference"),
        (35, 25, 250, "interpolated"),
        (35.5, 25, 253.55, "interpolated"),
        (100, 10, 907.62, "extrapolated"),
        (100, 50, 439.99, "extrapolated"),
        (5, 30, 32.5, "extrapolated"),
        (5, 50, 23.57, "extrapolated"),
        (0, 60, 0, "off"),
    ],
)
def test_estimate_light_ppfd(client, output_percent, distance_cm, ppfd, status):
    response = client.get(
        f"/api/grow-lights/{HABIBI_ID}/ppfd",
        params={"output_percent": output_percent, "canopy_distance_cm": distance_cm},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ppfd_umol_m2_s": pytest.approx(ppfd, abs=0.01),
        "status": status,
    }


def test_controller_uses_its_installed_fixture_for_scheduled_ppfd(client):
    response = client.put(
        "/api/controllers/1/grow-light-installation",
        json={"grow_light_id": HABIBI_ID, "canopy_distance_cm": 25},
    )
    assert response.status_code == 200
    assert (
        client.put(
            "/api/controllers/1/light",
            json={
                "changes": [
                    {"time": "06:00", "output_percent": 35, "transition_minutes": 30},
                    {"time": "21:00", "output_percent": 0, "transition_minutes": 0},
                ]
            },
        ).status_code
        == 200
    )

    dashboard = client.get("/api/controllers/1/dashboard").json()
    assert dashboard["grow_light_installation"] == response.json()
    assert dashboard["light"]["changes"][0]["ppfd"] == {
        "ppfd_umol_m2_s": 250,
        "status": "interpolated",
    }
    assert dashboard["light"]["changes"][1]["ppfd"] == {
        "ppfd_umol_m2_s": 0,
        "status": "off",
    }
    assert {
        "minute": 390,
        "output_percent": 35,
        "ppfd": {"ppfd_umol_m2_s": 250, "status": "interpolated"},
    } in dashboard["light"]["points"]
    [at_twenty_percent] = [
        point for point in dashboard["light"]["points"] if point["output_percent"] == 20
    ]
    assert at_twenty_percent["minute"] == pytest.approx(360 + 30 * 20 / 35)
    assert at_twenty_percent["ppfd"]["ppfd_umol_m2_s"] == 143.5
    assert dashboard["light"]["dli_mol_m2_day"] == pytest.approx(13.27365)
    assert dashboard["light"]["dli_status"] == "extrapolated"

    other = client.get("/api/controllers/2/dashboard").json()
    assert other["grow_light_installation"] is None
    assert "ppfd" not in other["light"]["changes"][0]

    updated = client.put(
        "/api/controllers/1/grow-light-installation",
        json={"grow_light_id": HABIBI_ID, "canopy_distance_cm": 30},
    )
    assert updated.status_code == 200
    dashboard = client.get("/api/controllers/1/dashboard").json()
    assert dashboard["light"]["changes"][0]["ppfd"]["ppfd_umol_m2_s"] == 227.5

    invalid = client.put(
        "/api/controllers/1/grow-light-installation",
        json={"grow_light_id": "unknown-light", "canopy_distance_cm": 40},
    )
    assert invalid.status_code == 404
    dashboard = client.get("/api/controllers/1/dashboard").json()
    assert dashboard["grow_light_installation"] == updated.json()


def test_dashboard_keeps_unsupported_firmware_schedule_editable(
    client, demo_controllers
):
    demo_controllers.apply(
        1,
        "light",
        {
            "nr_light_changes": 2,
            "times_min_per_day": [60, 1410],
            "intensity": [32767, 0],
            "rise_time_min": [0, 60],
        },
    )
    client.put(
        "/api/controllers/1/grow-light-installation",
        json={"grow_light_id": HABIBI_ID, "canopy_distance_cm": 30},
    ).raise_for_status()

    light = client.get("/api/controllers/1/dashboard").json()["light"]

    assert light["transition_reaches_midnight"]
    assert light["points"] == []
    assert "dli_mol_m2_day" not in light
    assert light["changes"][-1]["time"] == "23:30"


@pytest.mark.parametrize(
    ("output_percent", "distance_cm"), [(-1, 30), (101, 30), (35, 0), (35, "inf")]
)
def test_estimate_requires_a_valid_output_percentage_and_distance(
    client, output_percent, distance_cm
):
    response = client.get(
        f"/api/grow-lights/{HABIBI_ID}/ppfd",
        params={"output_percent": output_percent, "canopy_distance_cm": distance_cm},
    )
    assert response.status_code == 422


def test_fixture_and_distance_can_be_saved_independently_for_each_controller(
    client,
):
    first = "/api/controllers/1"
    second = "/api/controllers/2"

    for controller, settings in (
        (first, {"canopy_distance_cm": 30}),
        (second, {"grow_light_id": HABIBI_ID}),
    ):
        response = client.patch(f"{controller}/grow-light-installation", json=settings)
        assert response.status_code == 200
        dashboard = client.get(f"{controller}/dashboard").json()
        assert dashboard["grow_light_installation"] == response.json()
        assert "dli_mol_m2_day" not in dashboard["light"]

    response = client.patch(
        f"{first}/grow-light-installation", json={"grow_light_id": HABIBI_ID}
    )
    assert response.json() == {"grow_light_id": HABIBI_ID, "canopy_distance_cm": 30}
    assert (
        client.put(
            f"{first}/light",
            json={
                "changes": [
                    {"time": "06:00", "output_percent": 50, "transition_minutes": 0},
                    {"time": "22:00", "output_percent": 0, "transition_minutes": 0},
                ]
            },
        ).status_code
        == 200
    )
    light = client.get(f"{first}/dashboard").json()["light"]
    assert light["dli_mol_m2_day"] == pytest.approx(18.5472)
    assert light["dli_status"] == "estimated"

    response = client.patch(
        f"{second}/grow-light-installation", json={"canopy_distance_cm": 42.5}
    )
    assert response.json() == {"grow_light_id": HABIBI_ID, "canopy_distance_cm": 42.5}
    for controller, distance in ((first, 30), (second, 42.5)):
        dashboard = client.get(f"{controller}/dashboard").json()
        assert dashboard["grow_light_installation"]["canopy_distance_cm"] == distance
