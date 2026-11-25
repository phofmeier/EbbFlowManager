import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "release_changelog.py"
TAGGED_CHANGELOG = """\
# Changelog

## [UNRELEASED]

### Added

- Show controller history.

## [1.1.0] - 2026-10-01

### Added

- Show controller status.
"""
VERSION = "1.2.0"
DATE = "2026-11-25"
RELEASE_ENTRY = f"## [{VERSION}] - {DATE}\n\n### Added\n\n- Show controller history."


def run_changelog(mode, tagged, destination, *options, version=VERSION):
    return subprocess.run(
        [sys.executable, SCRIPT, mode, version, DATE, tagged, destination, *options],
        capture_output=True,
        text=True,
    )


def test_prepare_uses_unreleased_notes_from_tag(tmp_path):
    tagged = tmp_path / "tagged.md"
    tagged.write_text(TAGGED_CHANGELOG)
    prepared = tmp_path / "prepared.md"

    result = run_changelog("prepare", tagged, prepared)

    assert result.returncode == 0, result.stderr
    assert prepared.read_text() == TAGGED_CHANGELOG.replace(
        "## [UNRELEASED]\n\n### Added\n\n- Show controller history.",
        f"## [UNRELEASED]\n\n{RELEASE_ENTRY}",
    )
    assert tagged.read_text() == TAGGED_CHANGELOG


def test_rollover_retains_new_notes_and_records_the_release(tmp_path):
    tagged = tmp_path / "tagged.md"
    tagged.write_text(TAGGED_CHANGELOG)
    latest = tmp_path / "CHANGELOG.md"
    latest.write_text(
        TAGGED_CHANGELOG.replace(
            "- Show controller history.",
            "- Add an updated dashboard.\n\n- Add a controller filter.\n"
            "- Show controller history.\n\n"
            "### Fixed\n\n- Restore controller polling.",
        )
    )

    result = run_changelog("rollover", tagged, latest)

    assert result.returncode == 0, result.stderr
    assert latest.read_text() == TAGGED_CHANGELOG.replace(
        "- Show controller history.",
        "- Add an updated dashboard.\n\n- Add a controller filter.\n\n"
        "### Fixed\n\n- Restore controller polling.\n\n" + RELEASE_ENTRY,
    )


def test_prepare_waits_until_previous_release_notes_are_recorded(tmp_path):
    tagged = tmp_path / "tagged.md"
    tagged.write_text(TAGGED_CHANGELOG)
    prepared = tmp_path / "prepared.md"

    result = run_changelog("prepare", tagged, prepared, "--previous-stable", "v1.1.1")

    assert result.returncode != 0
    assert "Merge the changelog PR for 1.1.1" in result.stderr
    assert not prepared.exists()


def test_rollover_is_safe_to_retry(tmp_path):
    tagged = tmp_path / "tagged.md"
    tagged.write_text(TAGGED_CHANGELOG)
    latest = tmp_path / "CHANGELOG.md"
    latest.write_text(TAGGED_CHANGELOG)

    first = run_changelog("rollover", tagged, latest)
    assert first.returncode == 0, first.stderr
    rolled_over = latest.read_text()
    assert "## [UNRELEASED]\n\n" + RELEASE_ENTRY in rolled_over

    second = run_changelog("rollover", tagged, latest)
    assert second.returncode == 0, second.stderr
    assert latest.read_text() == rolled_over


def test_rollover_leaves_edited_release_notes_for_manual_resolution(tmp_path):
    tagged = tmp_path / "tagged.md"
    tagged.write_text(TAGGED_CHANGELOG)
    latest = tmp_path / "CHANGELOG.md"
    edited = TAGGED_CHANGELOG.replace(
        "- Show controller history.", "- Show pump history."
    )
    latest.write_text(edited)

    result = run_changelog("rollover", tagged, latest)

    assert result.returncode != 0
    assert "A tagged changelog entry changed on main" in result.stderr
    assert latest.read_text() == edited


def test_prepare_supports_a_prerelease_tag(tmp_path):
    tagged = tmp_path / "tagged.md"
    tagged.write_text(TAGGED_CHANGELOG)
    prepared = tmp_path / "prepared.md"

    result = run_changelog("prepare", tagged, prepared, version="1.2.0-rc.1")

    assert result.returncode == 0, result.stderr
    assert prepared.read_text() == TAGGED_CHANGELOG.replace(
        "## [UNRELEASED]\n\n### Added\n\n- Show controller history.",
        f"## [UNRELEASED]\n\n{RELEASE_ENTRY.replace(VERSION, '1.2.0-rc.1')}",
    )
    assert tagged.read_text() == TAGGED_CHANGELOG


def test_prepare_reuses_an_existing_version_section(tmp_path):
    tagged = tmp_path / "tagged.md"
    manual = TAGGED_CHANGELOG.replace(
        "### Added\n\n- Show controller history.", RELEASE_ENTRY
    )
    tagged.write_text(manual)
    prepared = tmp_path / "prepared.md"

    result = run_changelog("prepare", tagged, prepared)

    assert result.returncode == 0, result.stderr
    assert prepared.read_text() == manual
