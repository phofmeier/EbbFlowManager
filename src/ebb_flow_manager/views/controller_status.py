import panel as pn

from ebb_flow_manager.database.ebb_flow_controller_data import EbbFlowControllerStatus


class ControllerStatusView(pn.viewable.Viewer):
    """View to show the current controller status."""

    def __init__(self, status_data: EbbFlowControllerStatus, **params):
        """Initialize the view for the current controller status."""
        super().__init__(**params)
        self.status_data = status_data

    def __panel__(self) -> pn.panel:
        """Panel showing the status of the controller.

        Returns:
            pn.panel: panel to show the status.
        """
        return pn.Column(
            "## Status",
            pn.panel(
                f"- Connection: {self.status_data.connection} \n"
                f"- Last updated: {self.status_data.last_updated}"
            ),
        )
