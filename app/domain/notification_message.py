from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class NotificationMessage:
    tipo: str
    params: Dict[str, Any]
