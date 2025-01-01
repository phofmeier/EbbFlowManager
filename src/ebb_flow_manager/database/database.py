from ebb_flow_manager.database.ebb_flow_controller_data import EbbFlowControllerData
from ebb_flow_manager.database.mongo_db import MongoDbImpl


class Database:
    def __init__(self, config: dict):
        self.config = config
        self.db_impl = MongoDbImpl(config)
        self.controller_data: dict[int, EbbFlowControllerData] = {}
        self.updateControllerData()

    def updateControllerData(self):
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

    def getControllerData(self) -> dict[int, EbbFlowControllerData]:
        self.updateControllerData()
        return self.controller_data

    def get_all_config_template_names(self):
        return self.db_impl.get_config_template_names()

    def get_all_config_templates(self):
        return self.db_impl.get_config_templates()

    def get_config_template(self, template_name: str) -> dict:
        return self.db_impl.get_config_template(template_name)

    def get_used_template_of(self, id: int) -> str:
        return self.db_impl.get_used_template_of(id)

    def set_used_template_of(self, id: int, template_name: str):
        self.db_impl.set_used_template_of(id, template_name)
