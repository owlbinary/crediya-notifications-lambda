import os
import pytest
from app.infrastructure.sns_notification_adapter import SNSNotificationAdapter

class DummySNSClient:
    def __init__(self):
        self.published = []
    def publish(self, TopicArn, Message):
        self.published.append((TopicArn, Message))
        return {"MessageId": "dummy-id"}

def test_send_email_notification(monkeypatch):
    from app.domain.notification_message import NotificationMessage
    from app.application.notification_factory import NotificationFactory
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    adapter = SNSNotificationAdapter("arn:aws:sns:us-east-1:123456789012:test-topic", "us-east-1")
    monkeypatch.setattr(adapter, "sns", DummySNSClient())
    notification = NotificationMessage(
        tipo="estado_solicitud",
        params={
            "solicitudId": "123",
            "estado": "APROBADO",
            "justificacion": "Validación automática",
            "email": "test@correo.com"
        }
    )
    message = NotificationFactory.build_message(notification)
    adapter.send_email_notification(message)
    assert adapter.sns.published
    assert adapter.sns.published[0][0] == "arn:aws:sns:us-east-1:123456789012:test-topic"
    assert adapter.sns.published[0][1] == "La solicitud de crédito número 123 ha sido: APROBADO"
