from datetime import datetime
from typing import Literal

from pydantic import BaseModel


EstadoConsentimiento = Literal["opt-in", "opt-out", "no informado"]


class ConsentimientoOut(BaseModel):
    consentimiento_id: str
    cliente_id: str
    estado: EstadoConsentimiento
    canal: str | None = None
    fecha_registro: datetime | None = None
    fecha_actualizacion: datetime | None = None
    actualizado_por: str | None = None


class ConsentimientoUpdate(BaseModel):
    estado: EstadoConsentimiento
    canal: str | None = None
