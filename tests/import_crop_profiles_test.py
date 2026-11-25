import json
import subprocess
import sys


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
