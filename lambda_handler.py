
import os
from dotenv import load_dotenv
load_dotenv()

def lambda_handler(event, context):
	"""
	Handler para AWS Lambda con trigger SQS. Reutiliza la lógica de validación y notificación del endpoint FastAPI.
	"""
	from app.infrastructure.ses_notification_adapter import SESNotificationAdapter
	from app.domain.exceptions import ErrorDeValidacion
	import json

	aws_region = os.getenv("AWS_REGION", "us-east-1")
	adapter = SESNotificationAdapter(aws_region)

	for i, record in enumerate(event.get("Records", [])):
		try:
			body = record["body"]
			message_id = record.get("messageId", "unknown")
			print(f"Procesando mensaje {i+1}/{len(event.get('Records', []))}, MessageID: {message_id}")
			print(f"Body del mensaje: {body}")
			
			try:
				params = json.loads(body) if isinstance(body, str) else body
			except json.JSONDecodeError as json_error:
				print(f"ERROR: Error al parsear el mensaje JSON: {json_error}")
				continue
			
			tipo = params.get("tipo", "estado_solicitud")
			print(f"Tipo de notificación: {tipo}")
			
			if tipo != "estado_solicitud":
				print(f"Tipo {tipo} no es manejado por esta Lambda. Saltando mensaje.")
				continue
			
			if "params" in params:
				message_params = params["params"]
				message_params["tipo"] = tipo
			else:
				message_params = params
			
			required = ["solicitudId", "estado", "email"]
			missing = [k for k in required if not message_params.get(k)]
			if missing:
				raise ErrorDeValidacion(f"Faltan campos obligatorios: {', '.join(missing)}")

			adapter.send_email_notification(message_params)
			
		except ErrorDeValidacion as validation_error:
			print(f"ERROR {tipo}: {validation_error}")
		except Exception as e:
			import logging
			logging.error(f"ERROR {tipo}: Error inesperado procesando mensaje SQS: {e}")
