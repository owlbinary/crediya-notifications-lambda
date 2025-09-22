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
            
            if "," in recipient_email:
                email_list = [email.strip() for email in recipient_email.split(",")]
            else:
                email_list = [recipient_email.strip()]
            
            subject = self._build_simple_subject(message_data, tipo)
            body = self._build_simple_body(message_data, tipo)
            
            self.ses.send_email(
                Source=self.source_email,
                Destination={
                    'ToAddresses': email_list
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
        elif tipo == "reporte_rendimiento":
            asunto_custom = data.get("asunto", "")
            if asunto_custom:
                return asunto_custom
            else:
                return "Crediya - Reporte Diario de Rendimiento"
        else:
            return "Crediya - Notificación"
            
    def _build_simple_body(self, data: dict, tipo: str) -> str:
        """Build simple email body with essential information"""
        if tipo == "estado_solicitud":
            return self._build_loan_status_body(data)
        elif tipo == "reporte_rendimiento":
            return self._build_performance_report_body(data)
        else:
            return "Crediya - Notificación\n\nHa recibido una nueva notificación."
    
    def _build_loan_status_body(self, data: dict) -> str:
        """Build body for loan status notifications"""
        estado = data.get("estado", "")
        solicitud_id = data.get("solicitudId", "")
        tipo_prestamo = data.get("tipoPrestamo", data.get("tipo_prestamo", ""))
        monto = data.get("monto", "")
        plazo = data.get("plazo", "")
        justificacion = data.get("justificacion", "")
        plan_pago = data.get("planPago", [])
        
        body = "Crediya - Sistema de Créditos\n\n"
        body += f"Su solicitud #{solicitud_id} ha sido: {estado.upper()}\n\n"
        
        if justificacion:
            body += f"Motivo: {justificacion}\n\n"
        
        if tipo_prestamo:
            body += f"Tipo de préstamo: {tipo_prestamo}\n"
        if monto:
            try:
                monto_formatted = f"${float(monto):,.2f}"
            except (ValueError, TypeError):
                monto_formatted = f"${monto}"
            body += f"Monto: {monto_formatted}\n"
        if plazo:
            body += f"Plazo: {plazo} meses\n"
        
        if estado.upper() == "APROBADO" and plan_pago:
            body += "\n--- PLAN DE PAGO ---\n"
            for cuota in plan_pago:
                numero = cuota.get("numero_cuota", "")
                valor_cuota = cuota.get("cuota", "")
                try:
                    valor_formatted = f"${float(valor_cuota):,.2f}"
                except (ValueError, TypeError):
                    valor_formatted = f"${valor_cuota}"
                body += f"Cuota {numero}: {valor_formatted}\n"
        return body
    
    def _build_performance_report_body(self, data: dict) -> str:
        contenido = data.get("contenido", "")
        fecha_generacion = data.get("fechaGeneracion", "")
        
        if contenido:
            return contenido
        else:
            body = "Crediya - Reporte de Rendimiento\n\n"
            body += "Se ha generado un nuevo reporte de rendimiento.\n"
            if fecha_generacion:
                body += f"Fecha de generación: {fecha_generacion}\n"
            return body
