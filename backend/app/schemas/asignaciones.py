from datetime import datetime

from pydantic import BaseModel


class AsignacionOut(BaseModel):
    asignacion_id: str
    cliente_id: str
    campania_id: str
    usuario_id: str
    estado_contacto: str | None = None
    fecha_asignacion: datetime | None = None


class AsignacionCreate(BaseModel):
    cliente_id: str
    campania_id: str
    usuario_id: str


class ResultadoContactoOut(BaseModel):
    resultado_id: str
    asignacion_id: str
    resultado: str
    observacion: str | None = None
    fecha_contacto: datetime | None = None


class ResultadoContactoCreate(BaseModel):
    resultado: str
    observacion: str | None = None
