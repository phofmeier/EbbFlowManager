import copy
import logging
import logging.config
from functools import partial

import panel as pn

from ebb_flow_manager.config import Config
from ebb_flow_manager.database.database import Database
from ebb_flow_manager.mqtt.mqtt import MQTTConnection
from ebb_flow_manager.views.controller_configurator.controller_configurator import (
    ControllerConfiguratorView,
)
from ebb_flow_manager.views.controller_status import ControllerStatusView

pn.extension(design="material")


def init_logger(logging_config: dict):
    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(__name__)
    return logger


def updateData(controller_data, logger, db):
    old_data = copy.deepcopy(controller_data.rx.value)
    new_data = db.getControllerData()
    if old_data == new_data:
        return
    controller_data.rx.value = new_data
    logger.info("Data changed")


def layout_flex_box(flex_box, controller_data, mqtt):
    flex_box.clear()
    for id, controller in controller_data.items():
        name = pn.panel(f"# Controller {id}")
        status = ControllerStatusView(controller.status)
        config = ControllerConfiguratorView(controller.config, id, mqtt)
        widget_box = pn.WidgetBox(name, status, config)
        flex_box.append(widget_box)

    return flex_box


def start_serve():
    config = Config("config.yml")
    logger = init_logger(config.get("logging"))
    db = Database(config.get("database"))
    mqtt = MQTTConnection(config.get("mqtt"))
    controller_data = pn.rx({})
    flex_box = pn.layout.FlexBox()
    updateData(controller_data, logger, db)
    pn.state.add_periodic_callback(
        callback=partial(updateData, controller_data, logger, db),
        period=5000,
    )
    flex_box_bind = pn.bind(
        layout_flex_box,
        flex_box=flex_box,
        controller_data=controller_data,
        mqtt=mqtt,
    )
    template = pn.template.MaterialTemplate(
        title="Ebb Flow Manager",
        main=flex_box_bind,
    )
    return template


def main():
    pn.serve(start_serve(), admin=True)


if __name__ == "__main__":
    start_serve().servable()
    # main()

start_serve().servable()
