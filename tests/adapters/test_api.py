import os
import pytest
from fastapi.testclient import TestClient
from app.adapters.api import app

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:test-topic")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

class DummySNSAdapter:
    def __init__(self, *args, **kwargs):
        self.sent = []
    def send_email_notification(self, message_body: str):
        self.sent.append(message_body)
        return True

def test_notificar_success(monkeypatch):
    from app.adapters import api
    monkeypatch.setattr(api, "SNSNotificationAdapter", DummySNSAdapter)
    client = TestClient(app)
    payload = {
        "tipo": "estado_solicitud",
        "params": {
            "solicitudId": "123",
            "estado": "APROBADO",
            "justificacion": "Validación automática",
            "email": "test@correo.com"
        }
    }
    response = client.post("/api/v1/notificar", json=payload)
    assert response.status_code == 200
    assert response.json()["message"].startswith("Notificación simulada")


def test_notificar_missing_fields():
    client = TestClient(app)
    payload = {
        "tipo": "estado_solicitud",
        "params": {
            "email": "test@correo.com"
        }
    }
    response = client.post("/api/v1/notificar", json=payload)
    assert response.status_code == 422
    assert "Faltan campos obligatorios" in response.text
