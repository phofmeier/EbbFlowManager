import json
from os import environ
from pathlib import Path

import yaml
from pymongo import MongoClient

FIXTURES = Path(__file__).with_name("test_data")


def main() -> None:
    config_path = Path(environ["EBBFLOW_CONFIG"])
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    database_config = config["database"]
    id_field = database_config.get("id_field_name", "id")
    with MongoClient(
        database_config["connection_string"], serverSelectionTimeoutMS=5000
    ) as client:
        database = client[database_config.get("database_name", "efc")]
        for config_key, fixture in (
            ("collection_config_name", "config_static"),
            ("collection_status_name", "status_static"),
        ):
            collection = database[database_config.get(config_key, fixture)]
            with (FIXTURES / f"{fixture}.json").open(encoding="utf-8") as file:
                documents = json.load(file)
            for document in documents:
                controller_id = document.pop("id")
                document[id_field] = controller_id
                collection.update_one(
                    {id_field: controller_id},
                    {"$setOnInsert": document},
                    upsert=True,
                )


if __name__ == "__main__":
    main()
