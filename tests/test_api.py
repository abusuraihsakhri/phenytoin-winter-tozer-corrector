"""HTTP smoke and security checks for the optional API and static front end."""
import pytest
from fastapi.testclient import TestClient
from agents.api import app

client = TestClient(app)


def test_health_and_browser_assets():
    assert client.get("/health").json()["status"] == "ok"
    html = client.get("/")
    assert html.status_code == 200
    assert "Winter–Tozer calculator" in html.text
    js = client.get("/app.js")
    assert js.status_code == 200
    assert "calculateCorrection" in js.text


def test_correct_api():
    response = client.post("/api/correct", json={
        "measured_phenytoin_mg_l": 8,
        "albumin_g_dl": 2.0
    })
    assert response.status_code == 200
    assert response.json()["corrected_phenytoin_mg_l"] == 13.3
    response = client.post("/api/correct", json={
        "measured_phenytoin_mg_l": 8,
        "albumin_g_dl": 2.0,
        "crcl_ml_min": 5
    })
    assert response.json()["corrected_phenytoin_mg_l"] == 26.7


@pytest.mark.parametrize("payload", [
    {"measured_phenytoin_mg_l": 8, "albumin_g_dl": 0},
    {"measured_phenytoin_mg_l": -1, "albumin_g_dl": 2},
    {"measured_phenytoin_mg_l": 8, "albumin_g_dl": 2, "crcl_ml_min": -5},
])
def test_correct_api_validation(payload):
    assert client.post("/api/correct", json=payload).status_code == 422


def test_audit_routes_disabled_without_key(monkeypatch):
    monkeypatch.delenv("AUDIT_API_KEY", raising=False)
    assert client.get("/api/audit/logs").status_code == 503
    assert client.post("/api/chat", json={"query": "hello"}).status_code == 503


def test_audit_routes_require_key(monkeypatch):
    monkeypatch.setenv("AUDIT_API_KEY", "test-key-only")
    assert client.get("/api/audit/logs").status_code == 401
    assert client.get("/api/audit/logs", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/api/audit/logs", headers={"X-API-Key": "test-key-only"}).status_code == 200
