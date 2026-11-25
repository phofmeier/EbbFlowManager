from os import environ
from pathlib import Path

import uvicorn
import yaml

if __name__ == "__main__":
    config_path = Path(environ["EBBFLOW_CONFIG"])
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    uvicorn.run(
        "ebb_flow_manager_api.app:app",
        host="0.0.0.0",
        port=8001,
        log_config=config["logging"],
    )
