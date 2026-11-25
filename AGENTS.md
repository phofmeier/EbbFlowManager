# EbbFlowManager Agent Instructions

## Project layout

- The Python 3.13 FastAPI project is at the repository root. API routes are in [`src/ebb_flow_manager_api/app.py`](src/ebb_flow_manager_api/app.py), and MongoDB reads and MQTT writes are in [`live.py`](src/ebb_flow_manager_api/live.py). API tests are in [`tests/`](tests/).
- The Vue 3 frontend is in [`frontend/`](frontend/). [`App.vue`](frontend/src/App.vue) handles controller selection, [`ControllerDashboard.vue`](frontend/src/ControllerDashboard.vue) renders the dashboard, and [`ScheduleSettings.vue`](frontend/src/ScheduleSettings.vue) handles schedule editing.
- [`legacy/panel/`](legacy/panel/README.md) contains the archived Panel app and instructions for manual use.
- Bundled crop and light catalogs live under [`src/ebb_flow_manager_api/data/`](src/ebb_flow_manager_api/data/). Dev container controller fixtures live in [`tools/test_data/`](tools/test_data/).

## Development

Run these commands from the repository root to install the locked dependencies. The dev container uses Node.js 24.

```sh
uv sync --locked --extra dev
npm --prefix frontend ci
```

Start FastAPI and Vite in separate terminals.

```sh
uv run --locked uvicorn ebb_flow_manager_api.app:app --reload --host 0.0.0.0 --port 8001
npm --prefix frontend run dev
```

Open `http://localhost:5173/`. FastAPI uses in-memory sample data by default. Set `EBBFLOW_CONFIG` to a manager YAML file for MongoDB and MQTT integration. The [example config](example/manager/config/config.yml) uses Compose service names. Adjust `database.connection_string` and `mqtt.broker` for processes running on the host.

The [dev container setup](.devcontainer/setup.sh) installs FastAPI and the frontend, loads the catalogs and controller fixtures, and installs pre-commit hooks. The [Compose example](example/README.md) serves Vue and FastAPI on port 5006. The [Dockerfile](Dockerfile) builds the Vue and FastAPI images for Compose and releases.

## Verification

Run the FastAPI tests and build Vue from the repository root.

```sh
uv run --locked --extra dev pytest
npm --prefix frontend run build
```

GitHub Actions runs the FastAPI suite with coverage. Run `uv run --locked --extra dev coverage run -m pytest` and `uv run --locked --extra dev coverage report -m` from the repository root for the local coverage report.

Run pre-commit before committing. To run the repository-wide checks, use `uv run --locked --extra dev pre-commit run --all-files`.

When changing startup, configuration, or deployment, update the relevant instructions in the [root README](README.md) and [Compose guide](example/README.md). Record user-facing changes under `[UNRELEASED]` in the [changelog](CHANGELOG.md).

Follow the [release guide](RELEASING.md) when preparing and publishing a version.
