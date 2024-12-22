import panel as pn


from database.mongo_db import Database
from database.ebb_flow_controller_data import EbbFlowControllerData
from configurator import Configurator
from mqtt.mqtt import MQTTConnection
pn.extension()
db = Database()
mqtt = MQTTConnection()

all_status_data = db.getAllDataFrom("efc", "status_static")


controller_data = {}
for status_data in all_status_data:
    id = status_data["id"]
    if id not in controller_data:
        # add new data store
        controller_data.update({id:EbbFlowControllerData(id)})
    controller_data[id].update_status(status_data)

all_config_data = db.getAllDataFrom("efc", "config_static") 

for config_data in all_config_data:
    id = config_data["id"]
    if id not in controller_data:
        continue
   
    controller_data[id].update_config(config_data)


for id, controller in controller_data.items():
    pn.panel(id).servable()
    pn.panel(controller.status).servable()
    Configurator(controller.config, id, mqtt).servable()

# print(controller_data)



