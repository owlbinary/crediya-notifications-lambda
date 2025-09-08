from app.application.notification_factory import NotificationFactory
from app.domain.notification_message import NotificationMessage

def test_build_message_estado_solicitud():
    notification = NotificationMessage(
        tipo="estado_solicitud",
        params={
            "solicitudId": "12345",
            "estado": "APROBADO",
            "justificacion": "Validación automática",
            "email": "test@correo.com"
        }
    )
    result = NotificationFactory.build_message(notification)
    assert result == "La solicitud de crédito número 12345 ha sido: APROBADO"

def test_build_message_default():
    notification = NotificationMessage(
        tipo="otro_tipo",
        params={"foo": "bar"}
    )
    result = NotificationFactory.build_message(notification)
    assert result == '{"foo": "bar"}'
