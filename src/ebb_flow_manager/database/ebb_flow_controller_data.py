import param
from dateutil import parser


class EbbFlowControllerData:
    """Data store for one controller."""

    def __init__(self):
        """initialize new empty datastore."""
        self.status = EbbFlowControllerStatus()
        self.config = EbbFlowControllerConfig()

    def update_status(self, data: dict):
        """Update the status of the controller.

        Args:
            data (dict): new status data.
        """
        self.status.update(data)

    def update_config(self, data: dict):
        """Update the config of the controller.

        Args:
            data (dict): new config data.
        """
        self.config.update(data)

    def __eq__(self, other):
        if isinstance(other, EbbFlowControllerData):
            return self.status == other.status and self.config == other.config
        return False


class EbbFlowControllerStatus(param.Parameterized):
    """Status of the Controller."""

    connection = param.String(
        default="",
        doc="The current connection status of the Controller",
    )
    wifi_rssi = param.Number(
        default=None,
        doc="The current wifi signal strength",
    )
    last_updated = param.Date(doc="Timepoint of last update")

    def __init__(self):
        """Initialize empty status."""
        super().__init__()

    def update(self, data: dict):
        """Update the status from new data.

        Args:
            data (dict): new data for update
        """
        self.connection = data["connection"]
        self.wifi_rssi = data.get("rssi_level", None)

        ts_received = data["ts_received"]
        if isinstance(ts_received, str):
            ts_received = parser.parse(ts_received)
        self.last_updated = ts_received

    def __eq__(self, other):
        if isinstance(other, EbbFlowControllerStatus):
            return (
                self.connection == other.connection
                and self.last_updated == other.last_updated
            )
        return False


class EbbFlowControllerConfig(param.Parameterized):
    """Configuration data of the controller."""

    pump_cycles = param.Dict()
    last_updated = param.Date(doc="Timepoint of last update")

    def __init__(self):
        """Initialize the empty configuration."""
        super().__init__()

    def update(self, data: dict):
        """Update the configuration from new data.

        Args:
            data (dict): new data for update.
        """
        self.pump_cycles = data["pump_cycles"]
        ts_received = data["ts_received"]
        if isinstance(ts_received, str):
            ts_received = parser.parse(ts_received)
        self.last_updated = ts_received

    def __eq__(self, other):
        if isinstance(other, EbbFlowControllerConfig):
            return (
                self.pump_cycles == other.pump_cycles
                and self.last_updated == other.last_updated
            )
        return False
