# EbbFlowManager Agent Instructions

## Development

### Setup and Installation

- Install dependencies using a Python virtual environment:
  ```sh
  python3.13 -m venv ./venv/
  source venv/bin/activate
  pip install .
  ```
  Use `pip install -e .[dev]` for development dependencies.

### Running the Application

- Start the application using `uv` and `panel`:
  ```sh
  uv run panel serve src/ebb_flow_manager/ebb_flow_manager_* --dev
  ```
  Access the app at `http://localhost:5006/` after starting.

### Docker

- Run the application with Docker:
  ```sh
  docker run -d -v ./config.yml:/home/app/config.yml ghcr.io/phofmeier/ebbflowmanager:latest
  ```

## Configuration

- The `config.yml` file is the primary configuration file. Key sections include:
  - **Database**: Connection string, database name, and collection configurations.
  - **Logging**: Handlers, formatters, and root logger settings.
  - **MQTT**: Broker, port, and publish topics.

- Example configuration provided in `config.yml`. Ensure all required fields are set.

## Key Files

- **Main Application**: `src/ebb_flow_manager/ebb_flow_manager_app.py`
- **Database Interface**: `src/ebb_flow_manager/database/database.py`
- **MQTT Connection**: `src/ebb_flow_manager/mqtt/mqtt.py`
- **Views**:
  - `src/ebb_flow_manager/views/controller_status.py` (status view)
  - `src/ebb_flow_manager/views/controller_configurator/controller_configurator.py` (configurator view)

## Testing

- Run tests using `pytest`:

  ```sh
  coverage run -m pytest -v -s
  ```

- Generate a coverage report:
  ```sh
  coverage report -m
  ```

## CI/CD

- Pre-commit checks and unit tests are automated via GitHub Actions.
- Ensure all pre-commit hooks pass before committing.

## Docker Compose

- Use the provided `example/README.md` for a Docker Compose setup with:
  - Ebb Flow Manager
  - MQTT2DB application
  - Mosquitto MQTT broker
  - MongoDB Database

- Build and run:
  ```sh
  cd ./example
  docker compose build
  docker compose up
  ```

## Quirks and Gotchas

- **Panel**: The application uses `panel` for serving, which may require additional setup or familiarity.
- **MQTT and MongoDB**: External services are required. Ensure they are running and properly configured.
- **Dependencies**: Some dependencies (e.g., `paho-mqtt`, `pymongo`) may require specific versions.

## References

- For detailed architecture, refer to:
  - `src/ebb_flow_manager/database/database.py` (database interactions)
  - `src/ebb_flow_manager/mqtt/mqtt.py` (MQTT interactions)
  - `config.yml` (configuration structure)

- Use `opencode.json` to reference this file for agent guidance.
