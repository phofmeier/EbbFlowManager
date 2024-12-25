import panel as pn

from ebb_flow_manager.database.ebb_flow_controller_data import EbbFlowControllerStatus


class ControllerStatusView(pn.viewable.Viewer):
    def __init__(self, status_data: EbbFlowControllerStatus, **params):
        self.status_data = status_data
        super().__init__(**params)

    def __panel__(self):

        return pn.Column(
            "## Status",
            pn.panel(
                f"- Connection: {self.status_data.connection} \n"
                f"- Last updated: {self.status_data.last_updated}"
            ),
        )
