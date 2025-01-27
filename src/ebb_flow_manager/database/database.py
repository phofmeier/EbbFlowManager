from ebb_flow_manager.database.ebb_flow_controller_data import EbbFlowControllerData
from ebb_flow_manager.database.mongo_db import MongoDbImpl


class Database:
    """Interface to the database implementation."""

    def __init__(self, config: dict):
        """Initialize and connect to the database.

        Args:
            config (dict): Database specific configuration.
        """
        self.config = config
        self.db_impl = MongoDbImpl(config)
        self.controller_data: dict[int, EbbFlowControllerData] = {}
        self.update_controller_data()

    def update_controller_data(self):
        """Update the controller dict."""
        all_status_data = self.db_impl.get_status_data()
        for status_data in all_status_data:
            id = status_data[self.config["id_field_name"]]
            if id not in self.controller_data:
                # add new data store
                self.controller_data.update({id: EbbFlowControllerData()})
            self.controller_data[id].update_status(status_data)

        all_config_data = self.db_impl.get_config_data()

        for config_data in all_config_data:
            id = config_data[self.config["id_field_name"]]
            if id not in self.controller_data:
                continue

            self.controller_data[id].update_config(config_data)

    def get_controller_data(self) -> dict[int, EbbFlowControllerData]:
        """Get all data of the controller.

        Returns:
            dict[int, EbbFlowControllerData]: Mapping of Controller id
                                              to the actual data.
        """
        self.update_controller_data()
        return self.controller_data

    def get_all_config_template_names(self) -> list[str]:
        """Get a List containing all names of available config templates

        Returns:
            list[str]: List containing names of the available configs
        """
        return self.db_impl.get_config_template_names()

    def get_all_config_templates(self) -> list[dict]:
        """Get all the configuration templates.

        Returns:
            list[dict]: list containing all configuration template dicts.
        """
        return self.db_impl.get_config_templates()

    def get_config_template(self, template_name: str) -> dict:
        """Get a specific config template.

        Returns an empty dict if the name is not in the database.

        Args:
            template_name (str): Name of the template to load from database.

        Returns:
            dict: Config template.
        """
        return self.db_impl.get_config_template(template_name.strip())

    def set_new_template(self, new_template: dict):
        """Save a new template to the database.

        Args:
            new_template (dict): dict containing the new template.

        Raises:
            KeyError: Template needs at least a 'name' key
        """
        if "name" not in new_template:
            raise KeyError("The key 'name' needs to be in the template.")
        new_template.update({"name": new_template["name"].strip()})
        self.db_impl.set_new_template(new_template)

    def delete_template(self, template_name: str):
        """Delete a template from the database.

        Args:
            template_name (str): Name of the template to delete.

        Raises:
            KeyError: If template does not exist
        """
        name = template_name.strip()
        if name not in self.get_all_config_template_names():
            raise KeyError(
                f"The template with the name {name} is not inside the database."
            )
        self.db_impl.delete_template(name)

    def get_used_template_of(self, id: int) -> str:
        """Get the currently used template of a specific controller.

        Args:
            id (int): Id of the controller

        Returns:
            str: Config Template name of the specific controller.
        """
        return self.db_impl.get_used_template_of(id)

    def set_used_template_of(self, id: int, template_name: str):
        """Set the current used template name of a specific controller.

        Args:
            id (int): id of the controller
            template_name (str): name of the template used by this controller.
        """
        self.db_impl.set_used_template_of(id, template_name.strip())
