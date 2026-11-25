"""Prepare release notes from a tag and roll them forward on the main branch."""

import re
from argparse import ArgumentParser
from datetime import date
from pathlib import Path

UNRELEASED = re.compile(r"^## \[unreleased\][ \t]*\n", re.IGNORECASE | re.MULTILINE)
NEXT_VERSION = re.compile(r"^## ", re.MULTILINE)
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*)?")


def split_unreleased(changelog: str) -> tuple[str, str, str]:
    heading = UNRELEASED.search(changelog)
    if heading is None:
        raise ValueError("CHANGELOG.md needs a [UNRELEASED] heading.")
    next_heading = NEXT_VERSION.search(changelog, heading.end())
    end = next_heading.start() if next_heading else len(changelog)
    return (
        changelog[: heading.end()],
        changelog[heading.end() : end].strip(),
        changelog[end:],
    )


def has_version(changelog: str, version: str) -> bool:
    return (
        re.search(rf"^## \[{re.escape(version)}\](?:[ \t]|$)", changelog, re.M)
        is not None
    )


def release_entry(notes: str, version: str, release_date: date) -> str:
    return f"## [{version}] - {release_date}\n\n{notes}"


def join_changelog(prefix: str, notes: str, entry: str, history: str) -> str:
    sections = [section for section in (notes, entry, history.rstrip("\n")) if section]
    return prefix + "\n" + "\n\n".join(sections) + "\n"


def unpublished_notes(tagged: str) -> tuple[str, str, str]:
    prefix, notes, history = split_unreleased(tagged)
    if not notes:
        raise ValueError("The tagged [UNRELEASED] section has no release notes.")
    return prefix, notes, history


def prepare(tagged: str, version: str, release_date: date) -> str:
    if has_version(tagged, version):
        return tagged
    prefix, notes, history = unpublished_notes(tagged)
    return join_changelog(
        prefix, "", release_entry(notes, version, release_date), history
    )


def split_notes(notes: str) -> dict[str, list[str]]:
    sections = {}
    for section in re.split(r"(?m)(?=^### )", notes):
        if not section.strip():
            continue
        heading, _, body = (
            section.partition("\n") if section.startswith("### ") else ("", "", section)
        )
        if heading in sections:
            raise ValueError(f"Duplicate heading in [UNRELEASED]: {heading}")
        sections[heading] = [
            item
            for item in re.split(r"(?m)(?=^[-*+] )", body.strip("\n") + "\n")
            if item.strip()
        ]
    return sections


def rollover(tagged: str, latest: str, version: str, release_date: date) -> str:
    if has_version(latest, version):
        return latest
    if has_version(tagged, version):
        raise ValueError(
            f"Release {version} was prepared in the tag but is missing on main."
        )

    _, released_notes, _ = unpublished_notes(tagged)
    prefix, current_notes, history = split_unreleased(latest)
    remaining = split_notes(current_notes)
    for heading, released_items in split_notes(released_notes).items():
        current_items = remaining.get(heading, [])
        for item in released_items:
            matching_item = next(
                (
                    candidate
                    for candidate in current_items
                    if candidate.rstrip("\n") == item.rstrip("\n")
                ),
                None,
            )
            if matching_item is None:
                raise ValueError(
                    "A tagged changelog entry changed on main: "
                    f"{item.splitlines()[0]}\n"
                    "Reconcile the release notes and [UNRELEASED] manually."
                )
            current_items.remove(matching_item)

    new_notes = "\n\n".join(
        (heading + "\n\n" if heading else "") + "".join(items).rstrip("\n")
        for heading, items in remaining.items()
        if items
    )
    return join_changelog(
        prefix, new_notes, release_entry(released_notes, version, release_date), history
    )


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "rollover"])
    parser.add_argument("version")
    parser.add_argument("date", type=date.fromisoformat)
    parser.add_argument("tagged", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--previous-stable", default="")
    args = parser.parse_args()
    if not VERSION.fullmatch(args.version):
        parser.error("Use a release tag like v1.2.3 or v1.2.3-rc.1.")

    try:
        tagged = args.tagged.read_text(encoding="utf-8")
        if args.mode == "prepare":
            previous = args.previous_stable.removeprefix("v")
            if (
                previous
                and previous != args.version
                and not has_version(tagged, previous)
            ):
                raise ValueError(
                    f"Merge the changelog PR for {previous} "
                    "before tagging a new release."
                )
            updated = prepare(tagged, args.version, args.date)
        else:
            latest = args.destination.read_text(encoding="utf-8")
            updated = rollover(tagged, latest, args.version, args.date)
            if updated == latest:
                return
        args.destination.write_text(updated, encoding="utf-8")
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
