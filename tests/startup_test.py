from collections import defaultdict
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from ebb_flow_manager_api.app import app


def test_api_requires_manager_configuration(monkeypatch):
    monkeypatch.delenv("EBBFLOW_CONFIG", raising=False)

    with pytest.raises(RuntimeError, match="EBBFLOW_CONFIG"), TestClient(app):
        pass


def test_empty_database_stays_empty_when_api_reads_catalogs(
    monkeypatch, manager_config
):
    monkeypatch.setenv("EBBFLOW_CONFIG", str(manager_config))
    collections = defaultdict(MagicMock)
    mongo = MagicMock()
    mongo.__getitem__.return_value.__getitem__.side_effect = collections.__getitem__
    monkeypatch.setattr("ebb_flow_manager_api.live.MongoClient", lambda *a, **kw: mongo)

    with TestClient(app) as client:
        for path in ("/api/controllers", "/api/crops", "/api/grow-lights"):
            response = client.get(path)
            assert response.status_code == 200
            assert response.json() == []

    collections["crop_profiles"].update_one.assert_not_called()
    collections["grow_lights"].update_one.assert_not_called()
