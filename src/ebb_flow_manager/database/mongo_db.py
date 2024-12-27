import logging

from pymongo import MongoClient


class MongoDbImplementation:
    """Implementation of connection to a MongoDB database."""

    def __init__(self, config: dict) -> None:
        """Initialize the connection to the database.

        Args:
            config (dict): Configuration for the database connection.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = MongoClient(self.config["connection_string"])

    def get_databases_names(self) -> list[str]:
        """get the names of the databases.

        Returns:
            list[str]: List with names of the databases.
        """
        return self.client.list_database_names()

    def get_collection_names(self, database_name: str) -> list[str]:
        """Get all names of the collections.

        Args:
            database_name (str): name of database to use.

        Returns:
            list[str]: all names of the collections.
        """
        return self.client[database_name].list_collection_names()

    def get_all_data_from(self, database: str, collection: str) -> list[dict]:
        """get all data from a specific database and collection.

        Args:
            database (str): name of the database
            collection (str): name of the collection

        Returns:
            list[dict]: list with all entries in the collection.
        """
        return list(self.client[database][collection].find({}, {"_id": False}))

    def get_all_timed_data_from(self, database: str, collection: str):
        return list(self.client[database][collection].find({}, {}))
