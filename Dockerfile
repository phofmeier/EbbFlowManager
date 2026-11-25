FROM node:24-bookworm-slim AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/public/ public/
COPY frontend/src/ src/
RUN npm run build

FROM nginx:stable-alpine AS frontend

COPY example/manager/config/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /build/frontend/dist/ /usr/share/nginx/html/

FROM python:3.13-slim-bookworm AS api

COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /usr/local/bin/uv
WORKDIR /home/app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src/ src/
RUN SETUPTOOLS_SCM_PRETEND_VERSION_FOR_EBB_FLOW_MANAGER_API=0.0.0 \
    uv sync --locked --no-dev --no-editable
COPY example/manager/start_api.py ./
RUN mkdir -p logs
ENV PATH="/home/app/.venv/bin:${PATH}" PYTHONUNBUFFERED=1 EBBFLOW_CONFIG=/home/app/config.yml

CMD ["/bin/sh", "-ec", "python -m ebb_flow_manager_api.import_crop_profiles && python -m ebb_flow_manager_api.import_grow_lights && exec python start_api.py"]
