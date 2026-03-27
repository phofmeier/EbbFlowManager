import logging
import panel as pn
import plotly.express as px

from ebb_flow_manager.config import Config
from ebb_flow_manager.database.database import Database
from ebb_flow_manager.ebb_flow_manager_app import init_logger

pn.extension(design="material")

pn.extension("plotly")

def plot_free_store_data(db: Database) -> px.line:
    data = db.get_heap_size_data()
    
    data.sort_values("ts", inplace=True)

    figure = px.line(
        data_frame=data,
        x="ts",
        y="store_used_bytes",
        color="id",
        markers=True,
        line_shape="hv",
    )


    figure.update_layout(
        title="Used bytes of store over Time",
        xaxis_title="Timestamp",
        yaxis_title="Free size store (bytes)",
        xaxis_tickformat="%Y-%m-%d %H:%M:%S",
        xaxis_tickangle=-45,
    )
    figure.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        width=600,
    )
    return figure

def plot_min_heap_size_data(db: Database) -> px.line:
    data = db.get_heap_size_data()
    logger = logging.getLogger(__name__)
    logger.warning(f"Heap size data: {data}")
    data.sort_values("ts", inplace=True)

    figure = px.line(
        data_frame=data,
        x="ts",
        y="min_free_heap_size",
        color="id",
        markers=True,
        line_shape="hv",
    )


    figure.update_layout(
        title="Min Free Heap Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Min Heap Size (bytes)",
        xaxis_tickformat="%Y-%m-%d %H:%M:%S",
        xaxis_tickangle=-45,
    )
    figure.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        width=600,
    )
    return figure

def plot_heap_size_data(db: Database) -> px.line:
    data = db.get_heap_size_data()
    logger = logging.getLogger(__name__)
    logger.warning(f"Heap size data: {data}")
    data.sort_values("ts", inplace=True)

    figure = px.line(
        data_frame=data,
        x="ts",
        y="free_heap_size",
        color="id",
        markers=True,
        line_shape="hv",
    )


    figure.update_layout(
        title="Free Heap Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Heap Size (bytes)",
        xaxis_tickformat="%Y-%m-%d %H:%M:%S",
        xaxis_tickangle=-45,
    )
    figure.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        width=600,
    )
    return figure

def plot_pump_time_data(db: Database) -> px.line:
    data = db.get_pump_time_data()
    data.sort_values("ts", inplace=True)

    figure = px.line(
        data_frame=data,
        x="ts",
        y="status",
        color="id",
        markers=True,
        line_shape="hv",
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
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        width=600,
    )
    return figure


# New plot for light intensity over time
def plot_light_intensity_data(db: Database) -> px.line:
    data = db.get_light_intensity_data()
    data.sort_values("ts", inplace=True)

    figure = px.line(
        data_frame=data,
        x="ts",
        y="intensity",
        color="id",
        markers=True,
        line_shape="hv",
    )

    figure.update_layout(
        title="Light Intensity Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Light Intensity (lux)",
        xaxis_tickformat="%Y-%m-%d %H:%M:%S",
        xaxis_tickangle=-45,
    )
    figure.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        width=600,
    )
    return figure


def start_serve() -> pn.panel:
    """Start the panel server and display the data viewer.

    Returns:
        pn.panel: panel object containing the data viewer.
    """
    config = Config("config.yml")
    logger = init_logger(config.get("logging"))
    logger.debug("start app")
    db = Database(config.get("database"))

    
    plotly_pump_time_pane = pn.pane.Plotly(plot_pump_time_data(db))
    plotly_heap_size_pane = pn.pane.Plotly(plot_heap_size_data(db))
    plotly_min_heap_size_pane = pn.pane.Plotly(plot_min_heap_size_data(db))
    plotly_free_store_pane = pn.pane.Plotly(plot_free_store_data(db))
    plotly_light_intensity_pane = pn.pane.Plotly(plot_light_intensity_data(db))
    template = pn.template.BootstrapTemplate(
        title="Ebb Flow Manager - Data Viewer",
        main=[
            plotly_pump_time_pane,
            plotly_heap_size_pane,
            plotly_min_heap_size_pane,
            plotly_free_store_pane,
            plotly_light_intensity_pane,
        ],
    )
    return template


def main():
    pn.serve(start_serve(), admin=True)


if __name__ == "__main__":
    # start_serve().servable()
    main()
elif __name__.startswith("bokeh_app"):
    start_serve().servable()
