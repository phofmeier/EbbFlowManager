import panel as pn

class EbbFlowController(pn.viewable.Viewer):

    def __init__(self, id, **params):
        self._id = id
        super().__init__(**params)

    def __panel__(self):
        return pn.WidgetBox(f'# Controller {self._id}', pn.panel("Status"))



