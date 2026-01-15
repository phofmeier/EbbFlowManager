import datetime
import json
import os

from pymongo import MongoClient

connection_string = "db:27017"
client = MongoClient(connection_string)

id_filed_name = "id"


def get_all_files(path="."):
    for dirpath, dirnames, filenames in os.walk(path):
        if "tools" in dirnames:
            return get_all_files(dirpath + "/tools")
        if "test_data" in dirnames:
            return get_all_files(dirpath + "/test_data")
        json_file_names = [name for name in filenames if name.endswith(".json")]
        json_file_paths = [dirpath + "/" + name for name in json_file_names]
        return json_file_paths


for json_file in get_all_files():
    filename = json_file.split("/")[-1]
    database = filename.split("-")[0]
    collection = filename.split("-")[1].split(".")[0]
    type_name = collection.split("_")[-1]

    with open(json_file) as file:
        all_data = json.load(file)

    if type_name == "static":
        for data in all_data:
            client[database][collection].replace_one(
                {id_filed_name: data[id_filed_name]},
                data,
                upsert=True,
            )
    elif type_name == "timed":
        if collection not in client[database].list_collection_names():
            # Insert new collection
            client[database].create_collection(
                collection,
                timeseries={
                    "timeField": "ts",
                    "metaField": "id",
                },
            )
        for data in all_data:
            datetime_ts = datetime.datetime.fromisoformat(data["ts"])
            data["ts"] = datetime_ts
            client[database][collection].insert_one(
                data,
            )
    else:
        for data in all_data:
            client[database][collection].replace_one(
                {"name": data["name"]},
                data,
                upsert=True,
            )
