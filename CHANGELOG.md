# Changelog

All notable changes to this project will be documented in this file.

Use the following labels:

- `Added` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for soon-to-be removed features.
- `Removed` for now removed features.
- `Fixed` for any bug fixes.
- `Security` in case of vulnerabilities.

## [UNRELEASED]

### Added

- [Minor] Added a Vue dashboard and FastAPI backend for monitoring controllers and editing pump and light schedules.
- [Minor] Added per-controller crop and grow-phase targets, grow-light fixture settings, PPFD and DLI estimates, and a light schedule calculator.
- [Patch] Added new Data Viewer page.
- [Patch] Support for configuration templates.
- [Patch] New page to show and change templates.
- [Patch] Create and delete templates.
- [Patch] Export templates as json file.

### Changed

- [Minor] Require MongoDB configuration for FastAPI and initialize starter catalogs through the import commands before serving requests.
- [Patch] Completed the bundled Basil and Lettuce grow targets, including a Basil seedling phase.
- [Minor] Updated the Docker Compose example to run the Vue dashboard and FastAPI and import the starter catalogs on startup.
- [Major] Docker releases publish FastAPI and Vue images. Panel is archived for manual use.
- [Patch] Moved the Panel application to its own Python project under `legacy/panel/`.
- [Patch] Changed example to write logs to files.
- [Patch] Changed example config to correctly save timed messages.

### Fixed

- [Patch] Reject overlapping runs and transitions, zero-duration pump runs with scheduled starts, and light ramps that reach midnight.
- [Patch] Detect stale schedule edits and preserve the controller's exact dimmer values when saving unedited light levels.
- [Patch] Keep MQTT2DB startup changes and Mosquitto persistence files out of version control.
- [Patch] Require a fresh controller report to confirm schedule changes and show when a schedule already matched the last report.
- [Patch] Apply the lettuce reservoir temperature migration once so later catalog edits survive restarts.
- [Patch] Show empty charts in the archived Panel data viewer when telemetry is missing.
- [Patch] GitHub releases use the pushed Git tag and publish after both Docker images are available. Only stable releases update the `latest` image tags.

## [0.0.2] - 2024-12-29

### Fixed

- [Patch] Fixed Example.

## [0.0.1] - 2024-12-27

### Added

- [Patch] First Version.
