from fastapi import status

class NotificacionException(Exception):
    def __init__(self, detalle: str, codigo: str = None, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.detalle = detalle
        self.codigo = codigo or "NOTIFICACION_ERROR"
        self.status_code = status_code

class ErrorDeValidacion(Exception):
    def __init__(self, detalle: str, codigo: str = None):
        self.detalle = detalle
        self.codigo = codigo or "VALIDATION_ERROR"
        self.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
