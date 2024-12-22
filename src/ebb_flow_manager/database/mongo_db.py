import logging

from pymongo import MongoClient


class Database:
    """Implementation of connection to a MongoDB database."""

    def __init__(self, connection_string = "db:27017") -> None:
        """Initialize the connection to the database.

        Args:
            config (dict): Configuration for the database connection.
        """
        self.logger = logging.getLogger(__name__)
        self.client = MongoClient(connection_string)


    def getDatabasesNames(self) -> list[str]:
        return self.client.list_database_names()

    def getCollectionNames(self, database_name: str) -> list[str]:
        return self.client[database_name].list_collection_names()

    def getAllDataFrom(self, database: str, collection: str):
        return list(self.client[database][collection].find({}, {"_id": False}))

    def getAllTimedDataFrom(self, database: str, collection: str):
        return list(self.client[database][collection].find({}, {}))
