import socket

from fastapi.testclient import TestClient

from agro_rag.bootstrap.app import create_app


def test_liveness_works_without_credentials_or_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("health must not connect to a provider")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with TestClient(create_app()) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_liveness_does_not_claim_readiness():
    with TestClient(create_app()) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").status_code == 401
