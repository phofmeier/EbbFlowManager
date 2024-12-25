from ebb_flow_manager.database.ebb_flow_controller_data import EbbFlowControllerData
from ebb_flow_manager.database.mongo_db import MongoDbImplementation


class Database:
    def __init__(self, config: dict):
        self.config = config
        self.db_connection = MongoDbImplementation(config)
        self.controller_data: dict[int, EbbFlowControllerData] = {}
        self.updateControllerData()

    def updateControllerData(self):
        all_status_data = self.db_connection.getAllDataFrom(
            self.config["database_name"], self.config["collection_status_name"]
        )
        for status_data in all_status_data:
            id = status_data[self.config["id_field_name"]]
            if id not in self.controller_data:
                # add new data store
                self.controller_data.update({id: EbbFlowControllerData(id)})
            self.controller_data[id].update_status(status_data)

        all_config_data = self.db_connection.getAllDataFrom(
            self.config["database_name"], self.config["collection_config_name"]
        )

        for config_data in all_config_data:
            id = config_data[self.config["id_field_name"]]
            if id not in self.controller_data:
                continue

            self.controller_data[id].update_config(config_data)

    def getControllerData(self) -> dict[int, EbbFlowControllerData]:
        self.updateControllerData()
        return self.controller_data
