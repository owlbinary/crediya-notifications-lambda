from app.domain.notification_message import NotificationMessage
import json

class NotificationFactory:
    @staticmethod
    def build_message(notification: NotificationMessage) -> str:
        if notification.tipo == "estado_solicitud":
            solicitud_id = notification.params.get("solicitudId")
            estado = notification.params.get("estado")
            return f"La solicitud de crédito número {solicitud_id} ha sido: {estado}"
        elif notification.tipo == "capacidad_endeudamiento":
            usuario = notification.params.get("usuario")
            resultado = notification.params.get("resultado")
            return f"Estimado/a {usuario}, su capacidad de endeudamiento ha sido evaluada. Resultado: {resultado}"
        else:
            return json.dumps(notification.params)
