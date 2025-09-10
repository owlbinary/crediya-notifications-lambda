import os
import pytest
import json
from unittest.mock import patch, MagicMock
from app.infrastructure.ses_notification_adapter import SESNotificationAdapter

class DummySESClient:
    def __init__(self):
        self.sent_emails = []
    
    def send_email(self, Source, Destination, Message):
        self.sent_emails.append({
            "Source": Source,
            "Destination": Destination,
            "Subject": Message["Subject"]["Data"],
            "Body": Message["Body"]["Text"]["Data"]
        })
        return {"MessageId": "dummy-message-id"}

class ErrorSESClient:
    def send_email(self, Source, Destination, Message):
        raise Exception("SES Error")

def test_send_email_estado_solicitud(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "APROBADA",
        "tipoPrestamo": "Personal",
        "monto": 50000,
        "plazo": 24,
        "email": "test@correo.com"
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert sent_email["Source"] == "test@crediya.com"
    assert sent_email["Destination"]["ToAddresses"] == ["test@correo.com"]
    assert "Crediya - Solicitud #123 APROBADA" in sent_email["Subject"]
    assert "Su solicitud #123 ha sido: APROBADA" in sent_email["Body"]
    assert "Tipo de préstamo: Personal" in sent_email["Body"]
    assert "Monto: $50,000" in sent_email["Body"]
    assert "Plazo: 24 meses" in sent_email["Body"]

def test_send_email_capacidad_endeudamiento(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "capacidad_endeudamiento",
        "usuario": "Juan Pérez",
        "resultado": "ALTA",
        "email": "juan@correo.com"
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert sent_email["Source"] == "test@crediya.com"
    assert sent_email["Destination"]["ToAddresses"] == ["juan@correo.com"]
    assert "Crediya - Evaluación de Capacidad: ALTA" in sent_email["Subject"]
    assert "Estimado/a Juan Pérez" in sent_email["Body"]
    assert "Resultado: ALTA" in sent_email["Body"]

def test_send_email_missing_recipient(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "APROBADA"
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 0


@patch('boto3.client')
def test_ses_adapter_with_dotenv_import_error(mock_boto_client, monkeypatch):
    """Test SES adapter when dotenv is not available"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    mock_ses_client = MagicMock()
    mock_boto_client.return_value = mock_ses_client
    
    adapter = SESNotificationAdapter()
    
    assert adapter.aws_region == "us-east-1"
    assert adapter.source_email == "test@crediya.com"


def test_send_email_with_string_message(monkeypatch):
    """Test handling of string message input"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    message_json = json.dumps({
        "tipo": "estado_solicitud",
        "solicitudId": "456",
        "estado": "RECHAZADA",
        "email": "test@correo.com"
    })
    
    adapter.send_email_notification(message_json)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert "Solicitud #456 RECHAZADA" in sent_email["Subject"]


def test_send_email_invalid_json_string(monkeypatch):
    """Test handling of invalid JSON string"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    adapter.send_email_notification("invalid json string")
    
    assert len(adapter.ses.sent_emails) == 0


def test_send_email_ses_error(monkeypatch):
    """Test SES error handling"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", ErrorSESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "APROBADA",
        "email": "test@correo.com"
    }
    
    with pytest.raises(Exception, match="SES Error"):
        adapter.send_email_notification(params)


def test_build_simple_subject_unknown_type(monkeypatch):
    """Test subject building for unknown notification type"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    
    result = adapter._build_simple_subject({}, "unknown_type")
    assert result == "Crediya - Notificación"


def test_build_simple_body_unknown_type(monkeypatch):
    """Test body building for unknown notification type"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    
    result = adapter._build_simple_body({}, "unknown_type")
    assert result == "Crediya - Notificación\n\nHa recibido una nueva notificación."


def test_send_email_json_decode_error(monkeypatch):
    """Test handling of JSON decode error in string processing"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    with patch('app.infrastructure.ses_notification_adapter.json.loads') as mock_json_loads:
        mock_json_loads.side_effect = json.JSONDecodeError("Test error", "doc", 0)
        
        adapter.send_email_notification("some string")
        
        assert len(adapter.ses.sent_emails) == 0
