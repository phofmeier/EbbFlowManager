import logging
import logging.config

import panel as pn

from ebb_flow_manager.config import Config
from ebb_flow_manager.database.database import Database
from ebb_flow_manager.mqtt.mqtt import MQTTConnection
from ebb_flow_manager.views.controller_configurator import ControllerConfiguratorView
from ebb_flow_manager.views.controller_status import ControllerStatusView

pn.extension()


def init_logger(logging_config: dict):
    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(__name__)
    return logger


config = Config("config.yml")
logger = init_logger(config.get("logging"))
db = Database(config.get("database"))
mqtt = MQTTConnection(config.get("mqtt"))

flex_box = pn.layout.FlexBox()


def updateData():
    controller_data = db.getControllerData()
    flex_box.clear()
    for id, controller in controller_data.items():
        name = pn.panel(f"# Controller {id}")
        status = ControllerStatusView(controller.status)
        config = ControllerConfiguratorView(controller.config, id, mqtt)
        widget_box = pn.WidgetBox(name, status, config)
        flex_box.append(widget_box)


cb = pn.state.add_periodic_callback(updateData, 5000, timeout=5000)


def main():
    logger.info("Serve site")
    pn.serve(flex_box, admin=True)


if __name__ == "__main__":
    flex_box.servable()
    # main()
