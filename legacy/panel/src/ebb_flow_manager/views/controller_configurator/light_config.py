import datetime

import panel as pn
import param
import logging

class LightConfig(pn.viewable.Viewer):
    """Configuration view for the light settings."""

    times_min_per_day = param.List(item_type=int, doc="List of times (in minutes) per day when the light is active.")
    intensity = param.List(item_type=int, doc="List of light intensities for each period.")
    rise_time_min = param.List(item_type=int, doc="List of rise times (in minutes) for each period.")

    def __init__(self, curr_light_conf: dict, **params):
        """Initialize the view for the light configuration.

        Args:
            curr_light_conf (dict): the current configuration.
        """
        super().__init__(**params)
        self.logger = logging.getLogger(__name__)
        self.curr_light_conf = curr_light_conf

        # Initialize with current values
        self.times_min_per_day = self.curr_light_conf.get("times_min_per_day", [])
        self.intensity = self.curr_light_conf.get("intensity", [])
        self.rise_time_min = self.curr_light_conf.get("rise_time_min", [])

        # Widgets for user input (example, can be expanded as needed)
        self.nr_periods_input_widget = pn.widgets.IntInput(
            name="Number of light periods",
            value=len(self.times_min_per_day),
            end=24,
            step=1,
        )

        self.new_period_inputs_column = pn.Column()

    def get_new_config(self) -> dict:
        """Get the new configuration as a dictionary."""
        return {
            "nr_light_changes": len(self.times_min_per_day),
            "times_min_per_day": self.times_min_per_day,
            "intensity": self.intensity,
            "rise_time_min": self.rise_time_min,
        }

    def update_new_periods_input(self, *param):
        """Update the input widgets for the pump time."""
        self.nr_periods_input_widget.value = len(self.times_min_per_day)
        self.new_period_inputs_column.clear()
        for i in range(len(self.times_min_per_day)):
            time = datetime.time(
                hour=int(self.times_min_per_day[i] / 60),
                minute=self.times_min_per_day[i] % 60,
            )
            time_widget = pn.widgets.TimePicker(
                value=time,
                format="H:i",
            )
            intensity_widget = pn.widgets.IntInput(
                name=f"Intensity for period {i+1}",
                value=self.intensity[i] if i < len(self.intensity) else 0,
                start=0,
                end=32767,
                step=1,
            )
            rise_time_widget = pn.widgets.IntInput(
                name=f"Rise time (min) for period {i+1}",
                value=self.rise_time_min[i] if i < len(self.rise_time_min) else 0,
                start=0,
                end=32767,
                step=1,
            )
            self.new_period_inputs_column.append(pn.Row(time_widget, intensity_widget, rise_time_widget))
            pn.bind(self.update_period_time, new_time=time_widget, i=i, watch=True)
            pn.bind(self.update_intensity, new_intensity=intensity_widget, i=i, watch=True)
            pn.bind(self.update_rise_time, new_rise_time=rise_time_widget, i=i, watch=True)

    def update_number_periods(self, new_nr_periods: int):
        """Update the number of light periods.

        Args:
            new_nr_periods (int): amount of new light periods
        """
        max_val = 24 * 60
        new_times = [
            int(i * (max_val / new_nr_periods) + (max_val / new_nr_periods / 2))
            for i in range(new_nr_periods)
        ]
        self.times_min_per_day = new_times
        self.intensity = [0] * new_nr_periods  # Default intensity
        self.rise_time_min = [60] * new_nr_periods  # Default rise time

    def update_period_time(self, i: int, new_time: int):
        """Update the time of a specific period (in minutes)."""
        new_period_times = self.times_min_per_day.copy()
        new_period_times[i] = int(new_time.hour * 60 + new_time.minute)
        self.times_min_per_day = new_period_times

    def update_intensity(self, i: int, new_intensity: float):
        """Update the intensity of a specific period."""
        if 0 <= i < len(self.intensity):
            self.intensity[i] = new_intensity

    def update_rise_time(self, i: int, new_rise_time: int):
        """Update the rise time of a specific period (in minutes)."""
        if 0 <= i < len(self.rise_time_min):
            self.rise_time_min[i] = new_rise_time

    def __panel__(self) -> pn.panel:
        """Get the panel for configuring the Light settings.

        Returns:
            pn.panel: light configuration panel
        """
        if self.times_min_per_day:
            curr_periods_string = ""
            for min_per_day, intensity, rise_time in zip(self.times_min_per_day, self.intensity, self.rise_time_min):
                curr_periods_string += (
                    f"- {int(min_per_day / 60):02}:{int(min_per_day % 60):02}, "
                    f"Intensity: {intensity}, Rise Time: {rise_time}\n"
                )
        else:
            curr_periods_string = "NA"

        self.nr_periods_input_widget = pn.widgets.IntInput(
            name="Number of light periods",
            value=len(self.times_min_per_day),
            end=24,
            step=1,
        )
        pn.bind(
            self.update_number_periods,
            self.nr_periods_input_widget,
            watch=True,
        )

        # Widgets for each period (time, intensity, rise time)
        # period_widgets = pn.Column()
        # for i in range(len(self.times_min_per_day)):
        #     time_widget = pn.widgets.IntInput(
        #         name=f"Time (min) for period {i+1}",
        #         value=self.times_min_per_day[i],
        #         start=0,
        #         end=24*60,
        #         step=1,
        #     )
        #     intensity_widget = pn.widgets.IntInput(
        #         name=f"Intensity for period {i+1}",
        #         value=self.intensity[i] if i < len(self.intensity) else 0,
        #         start=0,
        #         end=32767,
        #         step=1,
        #     )
        #     rise_time_widget = pn.widgets.IntInput(
        #         name=f"Rise time (min) for period {i+1}",
        #         value=self.rise_time_min[i] if i < len(self.rise_time_min) else 0,
        #         start=0,
        #         end=24*60,
        #         step=1,
        #     )
        #     pn.bind(self.update_period_time, i=i, new_time=time_widget, watch=True)
        #     pn.bind(self.update_intensity, i=i, new_intensity=intensity_widget, watch=True)
        #     pn.bind(self.update_rise_time, i=i, new_rise_time=rise_time_widget, watch=True)
        #     period_widgets.append(
        #         pn.Row(time_widget, intensity_widget, rise_time_widget)
        #     )
        self.update_new_periods_input()

        return pn.Column(
            "### Light Configuration",
            pn.layout.GridBox(
                "#### Light periods per day\n" + curr_periods_string,
                pn.Column(
                    self.nr_periods_input_widget,
                    self.new_period_inputs_column,
                ),
                pn.panel(""),
                ncols=2,
            ),
        )
