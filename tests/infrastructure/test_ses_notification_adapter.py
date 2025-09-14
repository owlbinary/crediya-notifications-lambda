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


def test_send_email_with_plan_pago_aprobado(monkeypatch):
    """Test email with plan de pago when estado is APROBADO"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "APROBADO",
        "email": "test@correo.com",
        "planPago": [
            {"numero_cuota": 1, "cuota": 1000.0},
            {"numero_cuota": 2, "cuota": 1000.0}
        ]
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert "--- PLAN DE PAGO ---" in sent_email["Body"]
    assert "Cuota 1: $1,000.00" in sent_email["Body"]
    assert "Cuota 2: $1,000.00" in sent_email["Body"]


def test_send_email_with_justificacion(monkeypatch):
    """Test email with justificacion field"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "RECHAZADO",
        "email": "test@correo.com",
        "justificacion": "Ingresos insuficientes"
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert "Motivo: Ingresos insuficientes" in sent_email["Body"]


def test_send_email_monto_formatting_error(monkeypatch):
    """Test monto formatting when conversion to float fails"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "APROBADO",
        "email": "test@correo.com",
        "monto": "invalid_amount"
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert "Monto: $invalid_amount" in sent_email["Body"]


def test_send_email_plan_pago_valor_formatting_error(monkeypatch):
    """Test plan pago valor formatting when conversion fails"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "APROBADO",
        "email": "test@correo.com",
        "planPago": [
            {"numero_cuota": 1, "cuota": "invalid_value"}
        ]
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert "Cuota 1: $invalid_value" in sent_email["Body"]


def test_constructor_default_values(monkeypatch):
    """Test constructor with default environment values"""
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "default@test.com")
    
    with patch('boto3.client') as mock_boto_client:
        mock_ses_client = MagicMock()
        mock_boto_client.return_value = mock_ses_client
        
        adapter = SESNotificationAdapter()
        
        assert adapter.aws_region == "us-west-2"
        assert adapter.source_email == "default@test.com"
        mock_boto_client.assert_called_once_with("ses", region_name="us-west-2")


def test_constructor_no_env_vars(monkeypatch):
    """Test constructor with no environment variables set"""
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("SES_SOURCE_EMAIL", raising=False)
    
    with patch('boto3.client') as mock_boto_client:
        mock_ses_client = MagicMock()
        mock_boto_client.return_value = mock_ses_client
        
        adapter = SESNotificationAdapter()
        
        assert adapter.aws_region == "us-east-1"
        assert adapter.source_email == "notifications@crediya.com"
        mock_boto_client.assert_called_once_with("ses", region_name="us-east-1")


def test_send_email_with_tipo_prestamo_alternative_field(monkeypatch):
    """Test email with tipo_prestamo field (alternative name)"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "APROBADO",
        "email": "test@correo.com",
        "tipo_prestamo": "Hipotecario"
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert "Tipo de préstamo: Hipotecario" in sent_email["Body"]


def test_send_email_empty_plan_pago(monkeypatch):
    """Test email with empty plan de pago"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "APROBADO",
        "email": "test@correo.com",
        "planPago": []
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert "--- PLAN DE PAGO ---" not in sent_email["Body"]


def test_send_email_estado_not_aprobado_with_plan_pago(monkeypatch):
    """Test that plan de pago is not included when estado is not APROBADO"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "RECHAZADO",
        "email": "test@correo.com",
        "planPago": [
            {"numero_cuota": 1, "cuota": 1000.0}
        ]
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert "--- PLAN DE PAGO ---" not in sent_email["Body"]


def test_build_simple_subject_with_empty_fields(monkeypatch):
    """Test subject building with empty fields"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    
    data = {"solicitudId": "", "estado": ""}
    result = adapter._build_simple_subject(data, "estado_solicitud")
    assert result.__contains__("Crediya - Solicitud")


def test_build_simple_body_with_minimal_data(monkeypatch):
    """Test body building with minimal data"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    
    data = {"solicitudId": "456", "estado": "pendiente"}
    result = adapter._build_simple_body(data, "estado_solicitud")
    
    expected_parts = [
        "Crediya - Sistema de Créditos",
        "Su solicitud #456 ha sido: PENDIENTE",
        "Gracias por confiar en Crediya"
    ]
    
    for part in expected_parts:
        assert part in result


def test_send_email_with_none_values(monkeypatch):
    """Test email with None values for optional fields"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SES_SOURCE_EMAIL", "test@crediya.com")
    
    adapter = SESNotificationAdapter("us-east-1")
    monkeypatch.setattr(adapter, "ses", DummySESClient())
    
    params = {
        "tipo": "estado_solicitud",
        "solicitudId": "123",
        "estado": "APROBADO",
        "email": "test@correo.com",
        "monto": None,
        "plazo": None,
        "justificacion": None,
        "tipoPrestamo": None
    }
    
    adapter.send_email_notification(params)
    
    assert len(adapter.ses.sent_emails) == 1
    sent_email = adapter.ses.sent_emails[0]
    assert "Monto:" not in sent_email["Body"]
    assert "Plazo:" not in sent_email["Body"]  
    assert "Motivo:" not in sent_email["Body"]
    assert "Tipo de préstamo:" not in sent_email["Body"]
