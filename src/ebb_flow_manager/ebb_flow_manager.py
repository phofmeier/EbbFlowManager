import panel as pn

from ebb_flow_controller import EbbFlowController

class EbbFlowManager(pn.viewable.Viewer):

    def __panel__(self):

        return pn.template.MaterialTemplate(
            site="Ebb Flow Manager",
            title="Overview",
            sidebar=[variable_widget, window_widget, sigma_widget],
            main=[pn.layout.GridBox(EbbFlowController(0), EbbFlowController(1), EbbFlowController(2), ncols=2)],
            )




main_app = EbbFlowManager()
main_app.servable()
