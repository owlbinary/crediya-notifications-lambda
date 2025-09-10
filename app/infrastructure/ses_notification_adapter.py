import os
import json
import boto3
from app.infrastructure.logger import get_logger
from app.application.ports import EmailNotificationPort

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = get_logger()

class SESNotificationAdapter(EmailNotificationPort):
    def __init__(self, aws_region: str = None):
        self.aws_region = aws_region or os.getenv("AWS_REGION", "us-east-1")
        self.ses = boto3.client("ses", region_name=self.aws_region)
        self.source_email = os.getenv("SES_SOURCE_EMAIL", "notifications@crediya.com")
        
    def send_email_notification(self, notification_data):
        try:
            if isinstance(notification_data, str):
                try:
                    message_data = json.loads(notification_data)
                except json.JSONDecodeError:
                    logger.warning("Mensaje no es JSON válido, se omite")
                    return
            else:
                message_data = notification_data
            
            recipient_email = message_data.get("email")
            if not recipient_email:
                logger.error("No se encontró email en el mensaje")
                return
            tipo = message_data.get("tipo", "estado_solicitud")
            
            subject = self._build_simple_subject(message_data, tipo)
            body = self._build_simple_body(message_data, tipo)
            
            self.ses.send_email(
                Source=self.source_email,
                Destination={
                    'ToAddresses': [recipient_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
        except json.JSONDecodeError as json_error:
            logger.error(f"Error al parsear el mensaje JSON: {json_error}")
        except Exception as e:
            logger.error(f"Error al enviar email: {str(e)}")
            raise
            
    def _build_simple_subject(self, data: dict, tipo: str) -> str:
        """Build simple subject based on notification type"""
        if tipo == "estado_solicitud":
            estado = data.get("estado", "").upper()
            solicitud_id = data.get("solicitudId", "")
            
            return f"Crediya - Solicitud #{solicitud_id} {estado}"
        elif tipo == "capacidad_endeudamiento":
            resultado = data.get("resultado", "").upper()
            return f"Crediya - Evaluación de Capacidad: {resultado}"
        else:
            return "Crediya - Notificación"
            
    def _build_simple_body(self, data: dict, tipo: str) -> str:
        """Build simple email body with essential information"""
        if tipo == "estado_solicitud":
            estado = data.get("estado", "")
            solicitud_id = data.get("solicitudId", "")
            tipo_prestamo = data.get("tipoPrestamo", data.get("tipo_prestamo", ""))
            monto = data.get("monto", "")
            plazo = data.get("plazo", "")
            
            body = "Crediya - Sistema de Créditos\n\n"
            body += f"Su solicitud #{solicitud_id} ha sido: {estado.upper()}\n\n"
            
            if tipo_prestamo:
                body += f"Tipo de préstamo: {tipo_prestamo}\n"
            if monto:
                body += f"Monto: ${monto:,}\n"
            if plazo:
                body += f"Plazo: {plazo} meses\n"
            
            body += "\nGracias por confiar en Crediya."
            
        elif tipo == "capacidad_endeudamiento":
            usuario = data.get("usuario", "")
            resultado = data.get("resultado", "")
            
            body = "Crediya - Evaluación de Capacidad\n\n"
            body += f"Estimado/a {usuario},\n\n"
            body += "Su capacidad de endeudamiento ha sido evaluada.\n"
            body += f"Resultado: {resultado}\n\n"
            body += "Gracias por confiar en Crediya."
        else:
            body = "Crediya - Notificación\n\nHa recibido una nueva notificación."
            
        return body
