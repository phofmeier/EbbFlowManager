import panel as pn
from ebb_flow_manager.database.ebb_flow_controller_data import EbbFlowControllerData
from ebb_flow_manager.database.mongo_db import Database
from ebb_flow_manager.mqtt.mqtt import MQTTConnection
from ebb_flow_manager.views.controller_configurator import ControllerConfiguratorView
from ebb_flow_manager.views.controller_status import ControllerStatusView

pn.extension()
db = Database()
mqtt = MQTTConnection()

controller_data_stream = pn.rx({})
flex_box = pn.layout.FlexBox()


def updateData():
    all_status_data = db.getAllDataFrom("efc", "status_static")
    controller_data = controller_data_stream.rx.value
    for status_data in all_status_data:
        id = status_data["id"]
        if id not in controller_data:
            # add new data store
            controller_data.update({id: EbbFlowControllerData(id)})
        controller_data[id].update_status(status_data)

    all_config_data = db.getAllDataFrom("efc", "config_static")

    for config_data in all_config_data:
        id = config_data["id"]
        if id not in controller_data:
            continue

        controller_data[id].update_config(config_data)

    flex_box.clear()
    for id, controller in controller_data.items():
        name = pn.panel(f"# Controller {id}")
        status = ControllerStatusView(controller.status)
        config = ControllerConfiguratorView(controller.config, id, mqtt)
        widget_box = pn.WidgetBox(name, status, config)
        flex_box.append(widget_box)


def main():
    cb = pn.state.add_periodic_callback(updateData, 5000, timeout=5000)
    pn.serve(flex_box, admin=True)


if __name__ == "__main__":
    main()
