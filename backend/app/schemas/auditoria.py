from datetime import datetime
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    log_id: str
    usuario_id: str | None
    accion: str
    recurso: str
    recurso_id: str | None
    ip_origen: str | None
    resultado: str
    detalle: str | None
    timestamp_evento: datetime | None
