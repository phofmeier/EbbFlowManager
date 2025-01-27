import logging

from pymongo import MongoClient


class MongoDbImpl:
    """Implementation of connection to a MongoDB database."""

    def __init__(self, config: dict) -> None:
        """Initialize the connection to the database.

        Args:
            config (dict): Configuration for the database connection.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = MongoClient(self.config["connection_string"])

    def get_config_data(self) -> list[dict]:
        """Get all configurations from the database.

        Returns:
            list[dict]: List with all configuration dicts.
        """
        return self.get_all_data_from(
            self.config["database_name"], self.config["collection_config_name"]
        )

    def get_status_data(self) -> list[dict]:
        """Get all the status data from the database.

        Returns:
            list[dict]: List with all status data from the database.
        """
        return self.get_all_data_from(
            self.config["database_name"], self.config["collection_status_name"]
        )

    def get_config_template_names(self) -> list[str]:
        """Get a List containing all names of available config templates

        Returns:
            list[str]: List containing names of the available configs
        """
        return [
            entry["name"]
            for entry in list(
                self.client[self.config["database_name"]][
                    self.config["collection_config_template_name"]
                ].find({}, {"name": True, "_id": False})
            )
        ]

    def get_config_templates(self) -> list[dict]:
        """Get all the configuration templates.

        Returns:
            list[dict]: list containing all configuration template dicts.
        """
        return list(
            self.client[self.config["database_name"]][
                self.config["collection_config_template_name"]
            ].find({}, {"_id": False})
        )

    def get_config_template(self, template_name: str) -> dict:
        """Get a specific config template.

        Returns an empty dict if the name is not in the database.

        Args:
            template_name (str): Name of the template to load from database.

        Returns:
            dict: Config template.
        """
        founded_template = list(
            self.client[self.config["database_name"]][
                self.config["collection_config_template_name"]
            ].find({"name": template_name}, {"_id": False})
        )
        if len(founded_template) > 0:
            return founded_template[0]
        return {}

    def set_new_template(self, new_template: dict):
        """Save a new template to database.

        Args:
            new_template (dict): the new template.
        """
        self.client[self.config["database_name"]][
            self.config["collection_config_template_name"]
        ].replace_one(
            {"name": new_template["name"]},
            new_template,
            upsert=True,
        )

    def delete_template(self, template_name: str):
        """Delete a template from the database.

        Args:
            template_name (str): Name of the template to delete
        """
        self.client[self.config["database_name"]][
            self.config["collection_config_template_name"]
        ].delete_many({"name": template_name})

    def get_used_template_of(self, id: int) -> str:
        """Get the currently used template of a specific controller.

        Args:
            id (int): Id of the controller

        Returns:
            str: Config Template name of the specific controller.
        """
        template_names = list(
            self.client[self.config["database_name"]][
                self.config["collection_used_template_name"]
            ].find({"id": id}, {"name": True, "_id": False})
        )
        if len(template_names) == 0:
            return "N/A"
        return template_names[0].get("name", "N/A")

    def set_used_template_of(self, id: int, template_name: str):
        """Set the current used template name of a specific controller.

        Args:
            id (int): id of the controller
            template_name (str): name of the template used by this controller.
        """
        self.client[self.config["database_name"]][
            self.config["collection_used_template_name"]
        ].replace_one(
            {"id": id},
            {"id": id, "name": template_name},
            upsert=True,
        )

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
