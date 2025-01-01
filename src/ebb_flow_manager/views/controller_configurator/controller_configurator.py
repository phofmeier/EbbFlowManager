import panel as pn
import param

from ebb_flow_manager.database.database import Database
from ebb_flow_manager.database.ebb_flow_controller_data import EbbFlowControllerConfig
from ebb_flow_manager.mqtt.mqtt import MQTTConnection
from ebb_flow_manager.views.controller_configurator.nutrition_pump_config import (
    NutritionPumpConfig,
)


class ControllerConfiguratorView(pn.viewable.Viewer):
    """View for configure a controller."""

    current_template_selection = param.String(default="None")

    def __init__(
        self,
        config_data: EbbFlowControllerConfig,
        id: int,
        mqtt: MQTTConnection,
        db: Database,
        **params,
    ):
        """Initialize the view to configure a controller.

        Args:
            config_data (EbbFlowControllerConfig): Current configuration
                                                data of the controller.
            id (int): Controller id.
            mqtt (MQTTConnection): MQTT connection to set a new config.
        """
        super().__init__(**params)
        self.config_data = config_data
        self.mqtt = mqtt
        self.id = id
        self.db = db

        # Configuration for the nutrition pump
        self.current_template_selection = self.db.get_used_template_of(self.id)
        self.nutrition_pump_config = NutritionPumpConfig(self.config_data.pump_cycles)
        self.selected_template = "None"

    def set_new_config(self, _):
        """Set the new configuration."""
        self.mqtt.publish_new_config(
            {
                "id": self.id,
                "pump_cycles": self.nutrition_pump_config.get_new_config(),
            }
        )

        self.db.set_used_template_of(self.id, self.selected_template)
        self.current_template_selection = self.selected_template

    def selected_new_template(self, selected_template_name: str):
        """_Callback if anew Config Template was selected

        Args:
            selected_template_name (str): name of the newly selected template.
        """
        self.nutrition_pump_config.update_selection_from_config(
            self.db.get_config_template(selected_template_name).get("pump_cycles", {})
        )
        self.selected_template = selected_template_name

    def __panel__(self) -> pn.panel:
        """Build the panel for the configuration.

        Returns:
            pn.panel: Panel for the configuration.
        """
        new_conf_button = pn.widgets.Button(
            name="Send new config", button_type="primary"
        )
        pn.bind(self.set_new_config, new_conf_button, watch=True)

        template_options = self.db.get_all_config_template_names()

        selected_template_value = (
            self.current_template_selection
            if self.current_template_selection in template_options
            else "None"
        )
        template_options.append("None")

        template_selector = pn.widgets.Select(
            name="Configuration Template",
            options=template_options,
            value=selected_template_value,
        )
        pn.bind(self.selected_new_template, template_selector, watch=True)
        self.selected_new_template(selected_template_value)

        return pn.Column(
            "## Configuration",
            pn.panel(f"- Last updated: {self.config_data.last_updated}"),
            pn.GridBox(
                pn.panel(f"- Used Template: {self.current_template_selection}"),
                template_selector,
                ncols=2,
            ),
            self.nutrition_pump_config,
            new_conf_button,
        )
