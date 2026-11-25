#!/usr/bin/env bash
set -euo pipefail

# Fresh Docker volumes are owned by root. Match the effective devcontainer user.
for directory in .venv frontend/node_modules; do
    if [[ ! -O "$directory" ]]; then
        sudo chown -R "$(id -u):$(id -g)" "$directory"
    fi
done

uv sync --locked --extra dev
npm --prefix frontend ci
npm --prefix frontend run build

export EBBFLOW_CONFIG="$PWD/example/manager/config/config.yml"
uv run --no-sync python -m ebb_flow_manager_api.import_crop_profiles
uv run --no-sync python -m ebb_flow_manager_api.import_grow_lights
uv run --no-sync tools/seed_demo_controllers.py

uv run --no-sync pre-commit install --install-hooks
