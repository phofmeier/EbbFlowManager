import panel as pn

from ebb_flow_manager.database.ebb_flow_controller_data import EbbFlowControllerConfig
from ebb_flow_manager.mqtt.mqtt import MQTTConnection
from ebb_flow_manager.views.controller_configurator.nutrition_pump_config import (
    NutritionPumpConfig,
)


class ControllerConfiguratorView(pn.viewable.Viewer):
    """View for configure a controller."""

    def __init__(
        self,
        config_data: EbbFlowControllerConfig,
        id: int,
        mqtt: MQTTConnection,
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

        # Configuration for the nutrition pump
        self.nutrition_pump_config = NutritionPumpConfig(self.config_data.pump_cycles)

    def setNewConfig(self, _):
        """Set the new configuration."""
        self.mqtt.publish_new_config(
            {
                "id": self.id,
                "pump_cycles": self.nutrition_pump_config.get_new_config(),
            }
        )

    def __panel__(self) -> pn.panel:
        """Build the panel for the configuration.

        Returns:
            pn.panel: Panel for the configuration.
        """
        new_conf_button = pn.widgets.Button(
            name="Send new config", button_type="primary"
        )
        pn.bind(self.setNewConfig, new_conf_button, watch=True)

        return pn.Column(
            "## Configuration",
            pn.panel(f"- Last updated: {self.config_data.last_updated}"),
            self.nutrition_pump_config,
            new_conf_button,
        )
