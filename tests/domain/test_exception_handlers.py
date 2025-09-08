import pytest
import json
from fastapi import status
from fastapi.requests import Request
from fastapi.exceptions import RequestValidationError
from starlette.datastructures import URL
from app.domain.schemas import ErrorResponse
from app.domain.exceptions import NotificacionException, ErrorDeValidacion
from app.domain import exception_handlers

class DummyRequest:
    def __init__(self, url="http://testserver/test"):
        self.url = URL(url)

def test_notificacion_exception_handler():
    req = DummyRequest()
    exc = NotificacionException("detalle", codigo="CODIGO_X")
    exc.status_code = 418
    response = exception_handlers.notificacion_exception_handler(req, exc)
    assert response.status_code == 418
    data = json.loads(response.body)
    assert data["codigo"] == "CODIGO_X"
    assert data["mensaje"] == "detalle"
    assert data["path"] == str(req.url)


def test_validation_exception_handler():
    req = DummyRequest()
    exc = ErrorDeValidacion("faltan campos")
    exc.status_code = 422
    response = exception_handlers.validation_exception_handler(req, exc)
    assert response.status_code == 422
    data = json.loads(response.body)
    assert data["codigo"] == "VALIDATION_ERROR"
    assert data["mensaje"] == "faltan campos"
    assert data["path"] == str(req.url)


def test_pydantic_validation_exception_handler():
    req = DummyRequest()
    errors = [{"loc": ["body", "campo"], "msg": "falta", "type": "value_error.missing"}]
    exc = RequestValidationError(errors)
    response = exception_handlers.pydantic_validation_exception_handler(req, exc)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = json.loads(response.body)
    assert data["codigo"] == "VALIDATION_ERROR"
    assert data["mensaje"] == "Error de validación en la solicitud"
    assert data["detalles"] == errors
    assert data["path"] == str(req.url)


def test_generic_exception_handler():
    req = DummyRequest()
    exc = Exception("algo malo")
    response = exception_handlers.generic_exception_handler(req, exc)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = json.loads(response.body)
    assert data["codigo"] == "INTERNAL_ERROR"
    assert data["mensaje"] == "Error interno. Intente más tarde."
    assert data["path"] == str(req.url)
