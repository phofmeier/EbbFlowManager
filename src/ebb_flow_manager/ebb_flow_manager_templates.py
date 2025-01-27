import logging
import logging.config
import re

import panel as pn

from ebb_flow_manager.config import Config
from ebb_flow_manager.database.database import Database
from ebb_flow_manager.views.template_editor import TemplateEditorView

pn.extension("modal", notifications=True, design="material")


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


def filter_template_names(search_field: str, all_names: list[str]) -> list[str]:
    """Filter list of templates by a search string

    Args:
        search_field (str): string used for search
        all_names (list[str]): full list of names

    Returns:
        list[str]: filtered lists
    """
    filtered_names = [
        name for name in all_names if re.search(search_field, name) is not None
    ]
    return filtered_names


def layout_flex_box_cb(
    white_list: list[str], all_templates: list[dict], database: Database
) -> pn.FlexBox:
    """Layout the Flexbox with all templates.

    Args:
        white_list (list[str]): list of showed template names
        all_templates (list[dict]): lis containing all templates
        database (Database): reference to the database

    Returns:
        pn.FlexBox: the generated flexbox.
    """
    return pn.layout.FlexBox(
        *[
            pn.WidgetBox(TemplateEditorView(config, database))
            for config in all_templates
            if config["name"] in white_list
        ]
    )


def create_new_template(
    event, new_template_name: str, db: Database, create_template_modal: pn.widget
):
    """Create a new empty template and save to database.

    Args:
        event (_type_): unused
        new_template_name (str): unique name for the template.
        db (Database): reference to the database
        create_template_modal (pn.widget): modal to close after creation.
    """
    new_name = new_template_name.strip()

    if len(new_name) < 1:
        pn.state.notifications.error(f"Template name `{new_name}` is to short.").s
        return
    if new_name in db.get_all_config_template_names():
        pn.state.notifications.error(f"Template name `{new_name}` already exists.")
        return

    try:
        db.set_new_template({"name": new_name})
    except Exception as ex:
        pn.state.notifications.error(f"Error during creation. {ex}")
        return

    create_template_modal.hide()
    pn.state.location.reload = False
    pn.state.location.reload = True


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

    new_template_name = pn.widgets.TextInput(placeholder="Enter name here ...")
    save_new_template_button = pn.widgets.Button(
        name="Create new template", button_type="primary"
    )
    create_template_modal = pn.layout.Modal(
        "Create New Template",
        new_template_name,
        save_new_template_button,
        name="Create New Template",
    )
    new_template_button = create_template_modal.create_button(
        "show", name="Create New Template"
    )

    pn.bind(
        create_new_template,
        save_new_template_button,
        new_template_name=new_template_name,
        db=db,
        create_template_modal=create_template_modal,
        watch=True,
    )

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
    template = pn.template.BootstrapTemplate(
        title="Ebb Flow Manager - Template Configuration",
        main=[
            create_template_modal,
            pn.Column(
                pn.Row(
                    search_field,
                    new_template_button,
                ),
                layout_flex_box,
            ),
        ],
    )
    return template


def main():
    pn.serve(start_serve(), admin=True)


if __name__ == "__main__":
    # start_serve().servable()
    main()
elif __name__.startswith("bokeh_app"):
    start_serve().servable()
