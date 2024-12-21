import panel as pn

class Configurator(pn.viewable.Viewer):

    def __panel__(self):

        return pn.template.MaterialTemplate(
            site="Ebb Flow Manager",
            title="Configurator",
            # sidebar=[variable_widget, window_widget, sigma_widget],
            # main=[bound_plot],
            )




configurator = Configurator()
configurator.servable()
