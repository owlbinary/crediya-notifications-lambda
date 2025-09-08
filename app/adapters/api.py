from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
from app.infrastructure.logger import get_logger
from app.infrastructure.sns_notification_adapter import SNSNotificationAdapter
from app.domain.notification_message import NotificationMessage
from app.application.notification_factory import NotificationFactory
from app.domain.schemas import NotificarRequest, NotificarResponse, ErrorResponse
from app.domain.exceptions import NotificacionException, ErrorDeValidacion
from app.domain.exception_handlers import (
	notificacion_exception_handler,
	validation_exception_handler,
	pydantic_validation_exception_handler,
	generic_exception_handler
)
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
logger = get_logger()

app.add_exception_handler(NotificacionException, notificacion_exception_handler)
app.add_exception_handler(ErrorDeValidacion, validation_exception_handler)
app.add_exception_handler(RequestValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.post("/api/v1/notificar", response_model=NotificarResponse, responses={
	422: {"model": ErrorResponse},
	400: {"model": ErrorResponse},
	500: {"model": ErrorResponse},
})
async def notificar(request: NotificarRequest):
	tipo = request.tipo
	params = request.params
	if tipo == "estado_solicitud":
		required = ["solicitudId", "estado", "justificacion", "email"]
		missing = [k for k in required if not params.get(k)]
		if missing:
			raise ErrorDeValidacion(f"Faltan campos obligatorios: {', '.join(missing)}")
	# sns_topic_arn = os.getenv("SNS_TOPIC_ARN")
	# aws_region = os.getenv("AWS_REGION", "us-east-1")
	# adapter = SNSNotificationAdapter(sns_topic_arn, aws_region)
	# notification = NotificationMessage(tipo=tipo, params=params)
	# message = NotificationFactory.build_message(notification)
	# adapter.send_email_notification(message)
	# return NotificarResponse(message="Notificación enviada")
	# ---
	return NotificarResponse(message="Notificación simulada (no se envió correo)")
