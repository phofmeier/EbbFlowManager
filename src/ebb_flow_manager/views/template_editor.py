import panel as pn

from ebb_flow_manager.database.database import Database
from ebb_flow_manager.views.controller_configurator.nutrition_pump_config import (
    NutritionPumpConfig,
)

# pn.extension("modal")


class TemplateEditorView(pn.viewable.Viewer):
    """View to edit a template."""

    def __init__(self, template: dict, database: Database, **params):
        """Initialize the View

        Args:
            template (dict): Current template.
            database (Database): database connection.
        """
        super().__init__(**params)
        self.template = template
        self.database = database
        self.nutrition_pump_config = NutritionPumpConfig(
            self.template.get("pump_cycles", {})
        )

    def save_new_config(self, _):
        """Save the new chosen config"""
        self.template["pump_cycles"] = self.nutrition_pump_config.get_new_config()
        changed_template = {
            "name": self.template["name"],
            "pump_cycles": self.nutrition_pump_config.get_valid_config(),
        }
        self.database.set_new_template(changed_template)

    def remove_this_template(self, event):
        """Remove this config from the database."""
        self.database.delete_template(self.template["name"])
        pn.state.location.reload = False
        pn.state.location.reload = True

    def __panel__(self) -> pn.panel:
        """build the view

        Returns:
            pn.panel: view showing the template editor.
        """
        save_template_button = pn.widgets.Button(
            name="Save new template", button_type="primary"
        )
        pn.bind(self.save_new_config, save_template_button, watch=True)

        # TODO: Confirmation seams to not work correctly.
        # Maybe try later
        # confirm_delete_button = pn.widgets.Button(
        #     name="Delete template now.", button_type="primary"
        # )

        # delete_modal = pn.layout.Modal(
        #     f"Do you really want to delete the template: {self.template['name']}",
        #     confirm_delete_button,
        #     background_close=True,
        #     name=f"delete_modal_{self.template['name']}",
        # )

        # remove_template_button = delete_modal.create_button(action="show",
        # icon="trash")
        remove_template_button = pn.widgets.Button(icon="trash", button_type="primary")

        pn.bind(
            self.remove_this_template,
            remove_template_button,  # confirm_delete_button,
            # delete_modal=delete_modal,
            watch=True,
        )

        return pn.Column(
            # delete_modal,
            f"## {self.template['name']}",
            remove_template_button,
            self.nutrition_pump_config,
            save_template_button,
        )
