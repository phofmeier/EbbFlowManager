import json
import subprocess
import sys


def test_import_rejects_invalid_ppfd_grid_before_connecting(tmp_path):
    source = tmp_path / "grow_lights"
    source.mkdir()
    (source / "invalid-fixture.json").write_text(
        json.dumps(
            {
                "name": "Invalid fixture",
                "ppfd": {
                    "reference_area_cm": {"width": 40, "length": 40},
                    "statistic": "area_average",
                    "source_url": "https://example.invalid/datasheet.pdf",
                    "source_revision": "1",
                    "output_percent": [50, 100],
                    "canopy_distance_cm": [20, 30],
                    "values_umol_m2_s": [[386, 746]],
                },
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ebb_flow_manager_api.import_grow_lights",
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
    assert "invalid-fixture.json" in result.stderr
    assert "PPFD table dimensions must match the axes." in result.stderr
