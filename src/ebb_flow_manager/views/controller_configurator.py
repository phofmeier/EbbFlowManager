import datetime
import logging

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
        self.logger = logging.getLogger(__name__)
        self.config_data = config_data
        self.new_pump_time_s = self.config_data.pump_cycles["pump_time_s"]
        self.new_times_minutes_per_day = self.config_data.pump_cycles[
            "times_minutes_per_day"
        ]
        self.mqtt = mqtt
        self.id = id
        self.new_nr_pump_times_inputs = pn.Column()

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

    def update_number_pumping_times(self, new_nr_pump_times):
        self.logger.info("Update number")
        max_val = 24 * 60
        new_pump_times = [
            int(i * (max_val / new_nr_pump_times) + (max_val / new_nr_pump_times / 2))
            for i in range(new_nr_pump_times)
        ]
        self.new_times_minutes_per_day = new_pump_times

    def update_number_pump_time(self, i, new_time):
        self.logger.info(
            f"update number pump time {new_time.hour * 60 + new_time.minute}"
        )
        new_pump_times = self.new_times_minutes_per_day.copy()
        new_pump_times[i] = int(new_time.hour * 60 + new_time.minute)
        self.new_times_minutes_per_day = new_pump_times

    def update_time_input_widgets(self, new_nr_pump_times, new_times_minutes_per_day):
        self.new_nr_pump_times_inputs.clear()
        for i, new_pump_times_min_per_day in enumerate(self.new_times_minutes_per_day):
            time = datetime.time(
                hour=int(new_pump_times_min_per_day / 60),
                minute=new_pump_times_min_per_day % 60,
            )
            new_widget = pn.widgets.TimePicker(
                value=time,
                format="H:i",
            )
            self.new_nr_pump_times_inputs.append(new_widget)
            pn.bind(self.update_number_pump_time, new_time=new_widget, i=i, watch=True)

    def __panel__(self):
        new_conf_button = pn.widgets.Button(
            name="Send new config", button_type="primary"
        )
        pn.bind(self.setNewConfig, new_conf_button, watch=True)

        curr_pumping_times_string = ""
        for min_per_day in self.config_data.pump_cycles["times_minutes_per_day"]:
            curr_pumping_times_string += (
                f"- {int(min_per_day / 60):02}:{int(min_per_day % 60):02}\n"
            )
        new_nr_pump_times = pn.widgets.IntInput(
            name="New number pumping times",
            value=len(self.config_data.pump_cycles["times_minutes_per_day"]),
            end=24,
            step=1,
        )

        pn.bind(self.update_number_pumping_times, new_nr_pump_times, watch=True)
        pn.bind(
            self.update_time_input_widgets,
            new_nr_pump_times,
            self.new_times_minutes_per_day,
            watch=True,
        )

        self.update_time_input_widgets(
            new_nr_pump_times, self.new_times_minutes_per_day
        )

        return pn.Column(
            "## Configuration",
            pn.panel(f"- Last updated: {self.config_data.last_updated}"),
            "### Nutrition Pump",
            pn.layout.GridBox(
                f"#### Pumping time \n"
                f"- {self.config_data.pump_cycles["pump_time_s"]} s",
                pn.widgets.IntInput.from_param(self.param.new_pump_time_s),
                "#### Pumping timepoints per day\n" + curr_pumping_times_string,
                pn.Column(
                    new_nr_pump_times,
                    self.new_nr_pump_times_inputs,
                ),
                pn.panel(""),
                new_conf_button,
                ncols=2,
            ),
        )
