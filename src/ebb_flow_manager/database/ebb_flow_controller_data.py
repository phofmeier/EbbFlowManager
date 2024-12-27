import param
from dateutil import parser


class EbbFlowControllerConfig(param.Parameterized):
    pump_cycles = param.Dict()
    last_updated = param.Date(doc="Timepoint of last update")

    def __init__(self):
        super().__init__()

    def update(self, data):
        self.pump_cycles = data["pump_cycles"]
        ts_received = data["ts_received"]
        if isinstance(ts_received, str):
            ts_received = parser.parse(ts_received)
        self.last_updated = ts_received

    def __eq__(self, value):
        return (
            self.pump_cycles == value.pump_cycles
            and self.last_updated == value.last_updated
        )


class EbbFlowControllerStatus(param.Parameterized):
    connection = param.String(
        default="", doc="The current connection status of the Controller"
    )
    last_updated = param.Date(doc="Timepoint of last update")

    def __init__(self):

        super().__init__()

    def update(self, data):
        self.connection = data["connection"]

        ts_received = data["ts_received"]
        if isinstance(ts_received, str):
            ts_received = parser.parse(ts_received)
        self.last_updated = ts_received

    def __eq__(self, value):
        return (
            self.connection == value.connection
            and self.last_updated == value.last_updated
        )


class EbbFlowControllerData:
    def __init__(self, id: int):
        self.status = EbbFlowControllerStatus()
        self.config = EbbFlowControllerConfig()
        pass

    def update_status(self, data: dict):
        self.status.update(data)

    def update_config(self, data: dict):
        self.config.update(data)
        pass

    def __eq__(self, other):
        if isinstance(other, EbbFlowControllerData):
            return self.status == other.status and self.config == other.config
        return False
