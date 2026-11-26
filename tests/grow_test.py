def test_crop_phases_and_active_selection_are_controller_scoped(client):
    crop = client.put(
        "/api/crops/basil/phases/production",
        json={
            "crop_name": "Basil",
            "phase_name": "Production",
            "targets": {
                "ph": {"min": 5.5, "max": 6},
                "reservoir_temperature_c": {"min": 22, "max": 24},
            },
        },
    )
    assert crop.status_code == 200
    catalog = client.get("/api/crops").json()
    basil = next(crop for crop in catalog if crop["id"] == "basil")
    assert basil["phases"]["production"]["targets"] == {
        "ph": {"min": 5.5, "max": 6},
        "reservoir_temperature_c": {"min": 22, "max": 24},
    }

    selection = {"crop_id": "basil", "phase_id": "production"}
    response = client.put("/api/controllers/2/grow-selection", json=selection)
    assert response.status_code == 200
    assert client.get("/api/controllers/2/dashboard").json()["grow_selection"] == (
        selection
    )
    assert client.get("/api/controllers/1/dashboard").json()["grow_selection"] is None
    invalid = client.put(
        "/api/controllers/2/grow-selection",
        json={"crop_id": "basil", "phase_id": "missing"},
    )
    assert invalid.status_code == 404
    assert client.get("/api/controllers/2/dashboard").json()["grow_selection"] == (
        selection
    )


def test_default_profiles_contain_distinct_targets_for_each_lettuce_phase(client):
    catalog = client.get("/api/crops").json()

    lettuce = next(crop for crop in catalog if crop["id"] == "lettuce")
    phases = lettuce["phases"]
    assert phases["seedling"]["targets"]["ppfd_umol_m2_s"] == {
        "min": 250,
        "max": 250,
    }
    production = phases["production"]["targets"]
    assert set(production) == {
        "ph",
        "ec_ms_cm",
        "reservoir_temperature_c",
        "air_temperature_c",
        "relative_humidity_pct",
        "ppfd_umol_m2_s",
        "dli_mol_m2_day",
    }
    assert production["reservoir_temperature_c"] == {"min": 24, "max": 25}
    assert production["dli_mol_m2_day"] == {"min": 17, "max": 17}


def test_kohlrabi_has_complete_seedling_and_production_targets(client):
    catalog = client.get("/api/crops").json()
    kohlrabi = next(crop for crop in catalog if crop["id"] == "kohlrabi")
    phases = kohlrabi["phases"]
    assert set(phases) == {"seedling", "production"}

    for phase_id, expected_ec in (("seedling", 0.75), ("production", 1.3)):
        targets = phases[phase_id]["targets"]
        assert set(targets) == {
            "ph",
            "ec_ms_cm",
            "reservoir_temperature_c",
            "air_temperature_c",
            "relative_humidity_pct",
            "ppfd_umol_m2_s",
            "dli_mol_m2_day",
        }
        assert targets["ec_ms_cm"] == {"min": expected_ec, "max": expected_ec}
        assert targets["dli_mol_m2_day"] == {
            bound: round(ppfd * 16 * 3600 / 1_000_000, 1)
            for bound, ppfd in targets["ppfd_umol_m2_s"].items()
        }
        selection = {"crop_id": "kohlrabi", "phase_id": phase_id}
        response = client.put("/api/controllers/1/grow-selection", json=selection)
        assert response.status_code == 200
        assert client.get("/api/controllers/1/dashboard").json()["grow_selection"] == (
            selection
        )
