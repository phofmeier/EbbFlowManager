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


def init_logger(logging_config: dict) -> logging.Logger:
    """Initialize the logger.

    Args:
        logging_config (dict): configuration for the logger.

    Returns:
        logging.Logger: logger object.
    """
    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(__name__)
    return logger


def update_data(controller_data: pn.rx, logger: logging.Logger, db: Database):
    """Update the data of the Controller.

    needs to be called periodically.
    Only updates the data if it changes.

    Args:
        controller_data (dict): controller data to update
        logger (logging.Logger): logger
        db (Database): connection to database for new data.
    """
    old_data = copy.deepcopy(controller_data.rx.value)
    new_data = db.getControllerData()
    if old_data == new_data:
        return
    controller_data.rx.value = new_data
    logger.info("Data changed")


def layout_flex_box(
    flex_box: pn.layout.FlexBox,
    controller_data: dict,
    mqtt: MQTTConnection,
) -> pn.layout.FlexBox:
    """Layout the flex box with all controller data.

    Args:
        flex_box (pn.layout.FlexBox): flex box to add the new data
        controller_data (dict): data of all controller.
        mqtt (MQTTConnection): connection to mqtt

    Returns:
        pn.layout.FlexBox: new flex box with data.
    """
    flex_box.clear()
    for id, controller in controller_data.items():
        name = pn.panel(f"# Controller {id}")
        status = ControllerStatusView(controller.status)
        config = ControllerConfiguratorView(controller.config, id, mqtt)
        widget_box = pn.WidgetBox(name, status, config)
        flex_box.append(widget_box)

    return flex_box


def start_serve() -> pn.panel:
    """Start serving the app.

    Returns:
        pn.panel: the app
    """
    config = Config("config.yml")
    logger = init_logger(config.get("logging"))
    db = Database(config.get("database"))
    mqtt = MQTTConnection(config.get("mqtt"))
    controller_data = pn.rx({})
    flex_box = pn.layout.FlexBox()
    update_data(controller_data, logger, db)
    pn.state.add_periodic_callback(
        callback=partial(update_data, controller_data, logger, db),
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
    # start_serve().servable()
    main()
elif __name__.startswith("bokeh_app"):
    start_serve().servable()
