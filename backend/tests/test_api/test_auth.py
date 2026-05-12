"""Tests for API-key auth and per-user identity dependencies."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.core.config as cfg


@pytest.fixture
def auth_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Build a fresh TestClient with APP_API_KEY enforced."""
    monkeypatch.setenv("APP_API_KEY", "test-secret")
    cfg.get_settings.cache_clear()
    from app.main import app

    return TestClient(app)


def test_missing_api_key_returns_401_problem_json(auth_client: TestClient) -> None:
    res = auth_client.get("/api/paper/refs")
    assert res.status_code == 401
    assert res.headers["content-type"].startswith("application/problem+json")
    body = res.json()
    assert body["status"] == 401
    assert body["title"] == "Unauthorized"


def test_wrong_api_key_returns_401(auth_client: TestClient) -> None:
    res = auth_client.get("/api/paper/refs", headers={"X-API-Key": "wrong"})
    assert res.status_code == 401


def test_correct_api_key_allows_access(auth_client: TestClient) -> None:
    res = auth_client.get(
        "/api/paper/refs", headers={"X-API-Key": "test-secret"}
    )
    assert res.status_code == 200
    assert "set_ids" in res.json()


def test_health_is_public(auth_client: TestClient) -> None:
    res = auth_client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_validation_error_returns_problem_json(auth_client: TestClient) -> None:
    res = auth_client.post(
        "/api/research/explore",
        json={"topic": "ab"},  # too short — min_length=3
        headers={"X-API-Key": "test-secret"},
    )
    assert res.status_code == 422
    assert res.headers["content-type"].startswith("application/problem+json")
    body = res.json()
    assert body["title"] == "Validation Error"
    assert isinstance(body["errors"], list)


def test_request_id_echoed(auth_client: TestClient) -> None:
    res = auth_client.get(
        "/health", headers={"X-Request-ID": "test-trace-xyz"}
    )
    assert res.headers["x-request-id"] == "test-trace-xyz"
