import panel as pn
import plotly.graph_objs as go

from ebb_flow_manager.config import Config
from ebb_flow_manager.database.database import Database
from ebb_flow_manager.ebb_flow_manager_app import init_logger

pn.extension(design="material")

pn.extension("plotly")


def start_serve() -> pn.panel:
    """Start the panel server and display the data viewer.

    Returns:
        pn.panel: panel object containing the data viewer.
    """
    config = Config("config.yml")
    logger = init_logger(config.get("logging"))
    logger.debug("start app")
    db = Database(config.get("database"))

    print(db.get_pump_time_data())
    data = db.get_pump_time_data()
    sorted_data = sorted(data, key=lambda x: x["ts"])
    timestamps = [data["ts"] for data in sorted_data]
    values = [data["status"] for data in sorted_data]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode="lines+markers",
            line={"shape": "hv"},
            name="Pump Status",
        )
    )
    figure.update_layout(
        title="Pump Status Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Status",
        xaxis_tickformat="%Y-%m-%d %H:%M:%S",
        xaxis_tickangle=-45,
    )
    figure.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=20, b=20),
        height=400,
        width=600,
    )
    plotly_pane = pn.pane.Plotly(figure)
    template = pn.template.BootstrapTemplate(
        title="Ebb Flow Manager - Data Viewer",
        main=[plotly_pane],
    )
    return template


def main():
    pn.serve(start_serve(), admin=True)


if __name__ == "__main__":
    # start_serve().servable()
    main()
elif __name__.startswith("bokeh_app"):
    start_serve().servable()
