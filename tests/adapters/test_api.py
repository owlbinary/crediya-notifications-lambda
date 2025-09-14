import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.adapters.api import app

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")

class DummySESAdapter:
    def __init__(self, *args, **kwargs):
        self.sent = []
    def send_email_notification(self, message_body: str):
        self.sent.append(message_body)
        return True

class ErrorSESAdapter:
    def __init__(self, *args, **kwargs):
        pass
    def send_email_notification(self, message_body: str):
        raise Exception("SES Error")

def test_notificar_success(monkeypatch):
    from app.adapters import api
    monkeypatch.setattr(api, "SESNotificationAdapter", DummySESAdapter)
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
    assert "Notificación enviada por correo electrónico" in response.json()["message"]


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

@patch('app.adapters.api.os.getenv')
def test_notificar_with_env_region(mock_getenv, monkeypatch):
    """Test notification with environment region configuration"""
    from app.adapters import api
    monkeypatch.setattr(api, "SESNotificationAdapter", DummySESAdapter)
    
    mock_getenv.return_value = "us-west-2"
    
    client = TestClient(app)
    payload = {
        "tipo": "estado_solicitud",
        "params": {
            "solicitudId": "789",
            "estado": "APROBADO",
            "email": "test@correo.com"
        }
    }
    response = client.post("/api/v1/notificar", json=payload)
    assert response.status_code == 200
