import datetime
import logging

import panel as pn
import param


class NutritionPumpConfig(pn.viewable.Viewer):
    """Configuration view for the nutrition pump."""

    new_pump_time_s = param.Integer(
        bounds=(0, 24 * 60 * 60), label="New pump time in seconds"
    )
    new_times_minutes_per_day = param.List(item_type=int)

    def __init__(self, curr_pump_cycle_conf: dict, **params):
        """Initialize the view for the nutrition pump configuration.

        Args:
            curr_pump_cycle_conf (dict): the current configuration.
        """
        super().__init__(**params)
        self.logger = logging.getLogger(__name__)
        self.curr_pump_cycle_conf = curr_pump_cycle_conf

        # Column holding the Input widgets for the pump times
        self.new_nr_pump_times_inputs = pn.Column()

        # Initialize with current values
        self.new_pump_time_s = self.curr_pump_cycle_conf["pump_time_s"]
        self.new_times_minutes_per_day = self.curr_pump_cycle_conf[
            "times_minutes_per_day"
        ]

    def update_number_pumping_times(self, new_nr_pump_times: int):
        """Update the number of the new pumping times.

        Args:
            new_nr_pump_times (int): amount of new pumping times
        """
        max_val = 24 * 60
        new_pump_times = [
            int(i * (max_val / new_nr_pump_times) + (max_val / new_nr_pump_times / 2))
            for i in range(new_nr_pump_times)
        ]
        self.new_times_minutes_per_day = new_pump_times

    def update_pump_time(self, i: int, new_time: datetime.time):
        """Update the pump time of a specific index.

        Args:
            i (int): index of the pump time to update
            new_time (datetime.time): new pump time
        """
        new_pump_times = self.new_times_minutes_per_day.copy()
        new_pump_times[i] = int(new_time.hour * 60 + new_time.minute)
        self.new_times_minutes_per_day = new_pump_times

    def update_time_input_widgets(self, *param):
        """Update the input widgets for the pump time."""
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
            pn.bind(self.update_pump_time, new_time=new_widget, i=i, watch=True)

    def get_new_config(self) -> dict:
        """Get the new configuration for the nutrition pump.

        Returns:
            dict: new configuration.
        """
        return {
            "pump_time_s": self.new_pump_time_s,
            "nr_pump_cycles": len(self.new_times_minutes_per_day),
            "times_minutes_per_day": self.new_times_minutes_per_day,
        }

    def __panel__(self) -> pn.panel:
        """Get the panel for configure the Nutrition pump.

        Returns:
            pn.panel: nutrition pump configuration panel
        """
        curr_pumping_times_string = ""
        for min_per_day in self.curr_pump_cycle_conf["times_minutes_per_day"]:
            curr_pumping_times_string += (
                f"- {int(min_per_day / 60):02}:{int(min_per_day % 60):02}\n"
            )

        new_nr_pump_times = pn.widgets.IntInput(
            name="New number of pumping times",
            value=len(self.curr_pump_cycle_conf["times_minutes_per_day"]),
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
            "### Nutrition Pump",
            pn.layout.GridBox(
                f"#### Pumping time \n"
                f"- {self.curr_pump_cycle_conf["pump_time_s"]} s",
                pn.widgets.IntInput.from_param(self.param.new_pump_time_s),
                "#### Pumping timepoints per day\n" + curr_pumping_times_string,
                pn.Column(
                    new_nr_pump_times,
                    self.new_nr_pump_times_inputs,
                ),
                pn.panel(""),
                ncols=2,
            ),
        )
