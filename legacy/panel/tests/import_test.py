from importlib import import_module

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "ebb_flow_manager.ebb_flow_manager_app",
        "ebb_flow_manager.ebb_flow_manager_data_viewer",
        "ebb_flow_manager.ebb_flow_manager_templates",
    ],
)
def test_import(module):
    import_module(module)
