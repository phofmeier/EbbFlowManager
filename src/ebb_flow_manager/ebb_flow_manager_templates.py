import logging
import logging.config
import re

import panel as pn

from ebb_flow_manager.config import Config
from ebb_flow_manager.database.database import Database
from ebb_flow_manager.views.template_editor import TemplateEditorView

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


def filter_template_names(search_field, all_names):
    filtered_names = [
        name for name in all_names if re.search(search_field, name) is not None
    ]
    return filtered_names


def layout_flex_box_cb(white_list, all_templates, database):
    return pn.layout.FlexBox(
        *[
            pn.WidgetBox(TemplateEditorView(config, database))
            for config in all_templates
            if config["name"] in white_list
        ]
    )


def start_serve() -> pn.panel:
    """Start serving the app.

    Returns:
        pn.panel: the app
    """
    config = Config("config.yml")
    logger = init_logger(config.get("logging"))
    logger.debug("start app")
    db = Database(config.get("database"))
    search_field = pn.widgets.TextInput(placeholder="Search templates ...")

    config_white_list = pn.bind(
        filter_template_names,
        search_field=search_field,
        all_names=db.get_all_config_template_names(),
        watch=True,
    )
    layout_flex_box = pn.bind(
        layout_flex_box_cb,
        white_list=config_white_list,
        all_templates=db.get_all_config_templates(),
        database=db,
        watch=True,
    )
    # config_white_list = db.get_all_config_template_names()
    template = pn.template.MaterialTemplate(
        title="Ebb Flow Manager - Template Configuration",
        main=pn.Column(
            search_field,
            layout_flex_box,
        ),
    )
    return template


def main():
    pn.serve(start_serve(), admin=True)


if __name__ == "__main__":
    # start_serve().servable()
    main()
elif __name__.startswith("bokeh_app"):
    start_serve().servable()
