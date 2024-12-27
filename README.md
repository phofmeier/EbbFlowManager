# EbbFlowManager

Web application to show the status and manage tho configuration of multiple EbbFlowController.

## Deployment

### Local installation

Install and run the application locally using pip.

```sh
python3.11 -m venv ./venv/
source venv/bin/activate
pip install . # or use pip install -e .[dev] for development
ebb_flow_manager
```

For development run

```sh
panel serve src/ebb_flow_manager/ebb_flow_manager_app.py --dev
```

### Docker

Checkout the example for using this app with docker compose [here](example/README.md).

Or only run the app in a container with the following command.

```sh
docker run -d -v ./config.yml:/home/app/config.yml ghcr.io/phofmeier/ebbflowmanager:latest
```
