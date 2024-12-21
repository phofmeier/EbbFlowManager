# Example usage with Docker Compose

This example contains a docker compose configuration launching 3 container.

- 1. The MQTT2DB application
- 2. The Example Dashboard
- 3. The Mosquitto MQTT broker
- 4. A MongoDB Database

There is no authentication used anywhere. So please do not use this example for production.

## Instruction for testing

### Run Docker container with docker compose

```
cd ./example
docker compose build
docker compose up
```

### Install application locally

```
python3.11 -m venv ./venv
source venv/bin/activate
pip install .
```

### Publish data to database

```
python3.11 tools/publish_mqtt.py
```

### Show data in a dash app

Open [http://localhost:8050/](http://localhost:8050/)
