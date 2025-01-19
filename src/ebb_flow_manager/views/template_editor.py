import panel as pn

from ebb_flow_manager.database.database import Database
from ebb_flow_manager.views.controller_configurator.nutrition_pump_config import (
    NutritionPumpConfig,
)


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

    def __panel__(self) -> pn.panel:
        """build the view

        Returns:
            pn.panel: view showing the template editor.
        """
        save_template_button = pn.widgets.Button(
            name="Save new template", button_type="primary"
        )
        pn.bind(self.save_new_config, save_template_button, watch=True)

        return pn.Column(
            f"## {self.template['name']}",
            self.nutrition_pump_config,
            save_template_button,
        )
