# Legacy Panel application

Panel is archived for manual use. The app, templates, and data viewer are
served as separate pages. The project has its own Python dependencies and
lockfile.

Run from the repository root with MongoDB and MQTT available. Panel reads and
rewrites `config.yml` in its working directory. Provide a writable copy based
on the [example manager configuration](../../example/manager/config/config.yml)
and adjust the MongoDB and MQTT addresses for your environment. Create a
`logs/` directory if you use the example's file logging handler.

```sh
uv run --project legacy/panel --locked panel serve legacy/panel/src/ebb_flow_manager/ebb_flow_manager_*.py --dev
```

Open [http://localhost:5006/](http://localhost:5006/) after starting.

Run the legacy import tests manually from the repository root.

```sh
uv run --directory legacy/panel --locked --extra dev pytest
```
