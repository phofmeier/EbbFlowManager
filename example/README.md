# Run EbbFlowManager with Docker Compose

This example runs the Vue dashboard in Nginx, the FastAPI backend, MongoDB,
Mosquitto, and MQTT2DB. Use this configuration only on a trusted development
network. The dashboard, broker, and database are published without authentication.
Production deployments require a separate, authenticated configuration. The
MQTT2DB image uses `linux/amd64`, which requires emulation on ARM hosts.

## Start the stack

Run from the repository root.

```sh
docker compose -f example/compose.yaml up --build --wait
```

Open [http://localhost:5006/](http://localhost:5006/). Nginx serves the
dashboard and forwards `/api/` requests to FastAPI. The API imports missing
crop profiles and grow-light fixtures into MongoDB before startup. Existing
catalog records are kept. The controller list starts empty on a fresh database
until MQTT2DB records a controller's status.

Configure your [Ebb Flow Controller](https://github.com/phofmeier/EbbFlowControl)
to use the Docker host's reachable IP address or hostname on MQTT port `1883`.
MQTT2DB reads messages under the `ef` prefix and stores them in MongoDB. The
API publishes pump and light configuration changes to `ef/efc/config/set`.

## Use published images

To run a release in the development stack, replace the `build` blocks in
`example/compose.yaml` with the matching `image` entries.

| Service          | Stable image                                       | Versioned tag        |
| ---------------- | -------------------------------------------------- | -------------------- |
| `api`            | `ghcr.io/phofmeier/ebbflowmanager:latest`          | `<version>`          |
| `ebbflowmanager` | `ghcr.io/phofmeier/ebbflowmanager:latest-frontend` | `<version>-frontend` |

Use the same version for both images, omitting the leading `v` from the Git tag.
Keep the service names and configuration from the example. Nginx forwards API
requests to `api:8001` on the container network.

```sh
docker compose -f example/compose.yaml up --no-build --pull always --wait
```

## Configuration and logs

| Service          | Configuration                                                      | Log file                      |
| ---------------- | ------------------------------------------------------------------ | ----------------------------- |
| `ebbflowmanager` | [manager/config/nginx.conf](manager/config/nginx.conf)             | Container output              |
| `api`            | [manager/config/config.yml](manager/config/config.yml)             | `manager/logs/manager.log`    |
| `mqtt2db`        | [mqtt2db/config/config.yml](mqtt2db/config/config.yml)             | `mqtt2db/logs/mqtt2db.log`    |
| `mosquitto`      | [mosquitto/config/mosquitto.conf](mosquitto/config/mosquitto.conf) | `mosquitto/log/mosquitto.log` |

Log file paths are relative to this directory. From the repository root, check
service status and recent logs with these commands.

```sh
docker compose -f example/compose.yaml ps
docker compose -f example/compose.yaml logs --tail=100 api mqtt2db mosquitto
curl -fsS http://localhost:5006/api/controllers
```

The host ports are `5006` for the dashboard and its API, `1883` for MQTT, and
`27017` for MongoDB. Within Compose, the manager uses `db:27017` and
`mosquitto:1883`. If the controller list stays empty, check that the device can
reach the broker and that MQTT2DB is writing to the same database the API uses
(`efc` by default). To confirm a schedule change, MQTT2DB must record a matching
configuration with a `ts_received` from the current save attempt and newer than
any previous report.

## Stop the stack

```sh
docker compose -f example/compose.yaml down
```

The `mongodb-data` named volume keeps controller data, catalog edits, crop
selections, and fixture settings across restarts. Mosquitto stores its data
under `mosquitto/data/`.
