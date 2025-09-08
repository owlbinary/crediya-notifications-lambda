
import os
from mangum import Mangum
from app.adapters.api import app
from dotenv import load_dotenv
load_dotenv()

handler = Mangum(app)

def lambda_handler(event, context):
	"""
	Handler para AWS Lambda con trigger SQS. Reutiliza la lógica de validación y notificación del endpoint FastAPI.
	"""
	from app.infrastructure.sns_notification_adapter import SNSNotificationAdapter
	from app.domain.notification_message import NotificationMessage
	from app.application.notification_factory import NotificationFactory
	from app.domain.exceptions import ErrorDeValidacion
	import json

	sns_topic_arn = os.getenv("SNS_TOPIC_ARN")
	aws_region = os.getenv("AWS_REGION", "us-east-1")
	adapter = SNSNotificationAdapter(sns_topic_arn, aws_region)

	for record in event.get("Records", []):
		try:
			body = record["body"]
			params = json.loads(body) if isinstance(body, str) else body
			tipo = params.get("tipo", "estado_solicitud")
			# --- Lógica de validación igual que en el endpoint API ---
			if tipo == "estado_solicitud":
				required = ["solicitudId", "estado", "justificacion", "email"]
				missing = [k for k in required if not params.get(k)]
				if missing:
					raise ErrorDeValidacion(f"Faltan campos obligatorios: {', '.join(missing)}")
			notification = NotificationMessage(tipo=tipo, params=params)
			message = NotificationFactory.build_message(notification)
			# ---
			# adapter.send_email_notification(message)  # Descomentar en AWS
			# ---
			print(f"Notificación simulada (no se envió correo): {message}")
		except Exception as e:
			import logging
			logging.error(f"Error procesando mensaje SQS: {e}")
