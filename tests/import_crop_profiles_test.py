import json
import subprocess
import sys
from unittest.mock import MagicMock

from ebb_flow_manager_api.catalog_import import run_import
from ebb_flow_manager_api.grow import load_crop_profiles


def test_import_rejects_invalid_targets_before_connecting(tmp_path):
    source = tmp_path / "crops"
    source.mkdir()
    (source / "kohlrabi.json").write_text(
        json.dumps(
            {
                "name": "Kohlrabi",
                "phases": {
                    "seedling": {
                        "name": "Seedling",
                        "targets": {"ec_ms_cm": {"min": 1, "max": 0.75}},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ebb_flow_manager_api.import_crop_profiles",
            "--config",
            str(tmp_path / "unused.yml"),
            "--source",
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "kohlrabi.json" in result.stderr
    assert "The minimum target must not exceed the maximum." in result.stderr


def test_bundled_crop_import_migrates_unmodified_legacy_lettuce(
    monkeypatch, manager_config
):
    mongo = MagicMock()
    crops = mongo.__getitem__.return_value.__getitem__.return_value
    monkeypatch.setattr("ebb_flow_manager_api.live.MongoClient", lambda *a, **kw: mongo)
    monkeypatch.setattr(
        sys, "argv", ["import_crop_profiles", "--config", str(manager_config)]
    )
    targets = load_crop_profiles()["lettuce"]["phases"]["production"]["targets"]
    temperature = targets.pop("reservoir_temperature_c")

    run_import("crops")

    crops.update_one.assert_any_call(
        {
            "_id": "lettuce",
            "_lettuce_temperature_migrated": {"$exists": False},
            "phases.production.targets": targets,
        },
        {
            "$set": {
                "phases.production.targets.reservoir_temperature_c": temperature,
                "_lettuce_temperature_migrated": True,
            }
        },
    )
