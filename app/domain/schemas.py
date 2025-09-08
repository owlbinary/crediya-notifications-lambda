from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class NotificarRequest(BaseModel):
    tipo: str = Field(default="estado_solicitud")
    params: Dict[str, Any]

class NotificarResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    codigo: str
    mensaje: str
    timestamp: str
    path: str
    detalles: Optional[Any] = None
