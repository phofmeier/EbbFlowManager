import json
from collections import Counter
from datetime import datetime
from os import getenv
from pathlib import Path

import yaml
from pymongo import MongoClient

TOOLS_DIR = Path(__file__).resolve().parent


def read_documents(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def insert_missing(collection, documents, key):
    for document in documents:
        collection.update_one(
            {key: document[key]}, {"$setOnInsert": document}, upsert=True
        )


def insert_measurements(database, name, documents):
    if name not in database.list_collection_names():
        database.create_collection(
            name, timeseries={"timeField": "ts", "metaField": "id"}, check_exists=False
        )
    collection = database[name]
    occurrences: Counter[str] = Counter()
    for document in documents:
        key = json.dumps(document, sort_keys=True)
        occurrences[key] += 1
        document["ts"] = datetime.fromisoformat(document["ts"])
        if collection.count_documents(document) < occurrences[key]:
            collection.insert_one(document)


def main():
    config_path = getenv("EBBFLOW_CONFIG")
    database_config = {}
    if config_path:
        config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        database_config = config["database"]
    uri = database_config.get("connection_string", "db:27017")
    with MongoClient(uri, serverSelectionTimeoutMS=5000) as client:
        for path in sorted((TOOLS_DIR / "test_data").glob("*.json")):
            database_name, collection_name = path.stem.split("-", maxsplit=1)
            database = client[database_config.get("database_name", database_name)]
            documents = read_documents(path)
            if collection_name.endswith("_timed"):
                insert_measurements(database, collection_name, documents)
            else:
                key = "id" if collection_name.endswith("_static") else "name"
                insert_missing(database[collection_name], documents, key)

        templates = read_documents(TOOLS_DIR.parent / "templates" / "templates.json")
        database = client[database_config.get("database_name", "efc")]
        insert_missing(database.config_template, templates, "name")


if __name__ == "__main__":
    main()
