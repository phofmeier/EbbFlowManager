# Example usage with Docker Compose

This example contains a docker compose configuration launching 4 container.

1. The Ebb Flow Manager
2. The MQTT2DB application
3. The Mosquitto MQTT broker
4. A MongoDB Database

There is no authentication used anywhere. So please do not use this example for production.

This example can be used in combination with the [Ebb Flow Controller](https://github.com/phofmeier/EbbFlowControl) running on an ESP32 embedded hardware.

## Instruction for testing

### Run Docker container with docker compose

```
cd ./example
docker compose build
docker compose up
```

### Open Ebb Flow Manager in Browser

Open [http://localhost:5006/](http://localhost:5006/)
