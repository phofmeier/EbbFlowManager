import panel as pn
import param

from ebb_flow_manager.database.ebb_flow_controller_data import EbbFlowControllerConfig
from ebb_flow_manager.mqtt.mqtt import MQTTConnection


class ControllerConfiguratorView(pn.viewable.Viewer):
    new_pump_time_s = param.Integer(bounds=(0, 10 * 60))
    new_times_minutes_per_day = param.List(item_type=int)

    def __init__(
        self,
        config_data: EbbFlowControllerConfig,
        id: int,
        mqtt: MQTTConnection,
        **params,
    ):
        super().__init__(**params)
        self.config_data = config_data
        self.new_pump_time_s = self.config_data.pump_cycles["pump_time_s"]
        self.new_times_minutes_per_day = self.config_data.pump_cycles[
            "times_minutes_per_day"
        ]
        self.mqtt = mqtt
        self.id = id

    def setNewConfig(self, event):
        self.mqtt.publish_new_config(
            {
                "id": self.id,
                "pump_cycles": {
                    "pump_time_s": self.new_pump_time_s,
                    "nr_pump_cycles": len(self.new_times_minutes_per_day),
                    "times_minutes_per_day": self.new_times_minutes_per_day,
                },
            }
        )
        print("new_config_set")

    def __panel__(self):
        new_conf_button = pn.widgets.Button(name="New Config", button_type="primary")
        pn.bind(self.setNewConfig, new_conf_button, watch=True)

        # return pn.Column(curr_data, new_params, new_conf_button)
        return pn.Column(
            "## Configuration",
            pn.panel(f"- Last updated: {self.config_data.last_updated}"),
            "### Nutrition Pump",
            pn.layout.GridBox(
                "Pumping time in seconds",
                pn.panel(self.config_data.pump_cycles["pump_time_s"]),
                pn.widgets.IntInput.from_param(self.param.new_pump_time_s),
                "Pumping times in minutes per day",
                pn.panel(self.config_data.pump_cycles["times_minutes_per_day"]),
                pn.panel(self.param.new_times_minutes_per_day),
                ncols=3,
            ),
            new_conf_button,
        )
