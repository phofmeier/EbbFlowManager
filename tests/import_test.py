import pytest


def test_import():
    try:
        import ebb_flow_manager.ebb_flow_manager_app  # noqa: F401
    except ImportError:
        pytest.fail("Import Error occurred. Check dependencies.")
