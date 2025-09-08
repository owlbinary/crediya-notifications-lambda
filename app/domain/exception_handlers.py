from fastapi import status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.requests import Request as StarletteRequest
from datetime import datetime, timezone
from app.domain.schemas import ErrorResponse
from app.domain.exceptions import NotificacionException, ErrorDeValidacion
import logging

def notificacion_exception_handler(request: StarletteRequest, exc: NotificacionException):
    error = ErrorResponse(
        codigo=exc.codigo,
        mensaje=exc.detalle,
        timestamp=datetime.now(timezone.utc).isoformat(),
        path=str(request.url),
        detalles=None
    )
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(error))

def validation_exception_handler(request: StarletteRequest, exc: ErrorDeValidacion):
    error = ErrorResponse(
        codigo=exc.codigo,
        mensaje=exc.detalle,
        timestamp=datetime.now(timezone.utc).isoformat(),
        path=str(request.url),
        detalles=None
    )
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(error))

def pydantic_validation_exception_handler(request: StarletteRequest, exc: RequestValidationError):
    error = ErrorResponse(
        codigo="VALIDATION_ERROR",
        mensaje="Error de validación en la solicitud",
        timestamp=datetime.now(timezone.utc).isoformat(),
        path=str(request.url),
        detalles=exc.errors()
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=jsonable_encoder(error))

def generic_exception_handler(request: StarletteRequest, exc: Exception):
    logging.getLogger("notificaciones").error(f"Error inesperado: {str(exc)}", exc_info=True)
    error = ErrorResponse(
        codigo="INTERNAL_ERROR",
        mensaje="Error interno. Intente más tarde.",
        timestamp=datetime.now(timezone.utc).isoformat(),
        path=str(request.url),
        detalles=None
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(error))
