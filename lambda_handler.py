
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
	from app.infrastructure.ses_notification_adapter import SESNotificationAdapter
	from app.domain.notification_message import NotificationMessage
	from app.application.notification_factory import NotificationFactory
	from app.domain.exceptions import ErrorDeValidacion
	import json

	aws_region = os.getenv("AWS_REGION", "us-east-1")
	adapter = SESNotificationAdapter(aws_region)

	for record in event.get("Records", []):
		try:
			body = record["body"]
			try:
				params = json.loads(body) if isinstance(body, str) else body
			except json.JSONDecodeError as json_error:
				print(f"ERROR: Error al parsear el mensaje JSON: {json_error}")
				continue
			
			tipo = params.get("tipo", "estado_solicitud")
			if tipo == "estado_solicitud":
				required = ["solicitudId", "estado", "email"]
				missing = [k for k in required if not params.get(k)]
				if missing:
					raise ErrorDeValidacion(f"Faltan campos obligatorios: {', '.join(missing)}")
			elif tipo == "capacidad_endeudamiento":
				required = ["usuario", "resultado", "email"]
				missing = [k for k in required if not params.get(k)]
				if missing:
					raise ErrorDeValidacion(f"Faltan campos obligatorios para capacidad_endeudamiento: {', '.join(missing)}")

			adapter.send_email_notification(params)
			
		except ErrorDeValidacion as validation_error:
			print(f"ERROR {tipo}: {validation_error}")
		except Exception as e:
			import logging
			logging.error(f"ERROR {tipo}: Error inesperado procesando mensaje SQS: {e}")
