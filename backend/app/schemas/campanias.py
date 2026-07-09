from datetime import date
from typing import Literal

from pydantic import BaseModel


EstadoCampania = Literal["planificada", "activa", "cerrada", "cancelada"]


class CampaniaOut(BaseModel):
    campania_id: str
    nombre: str
    producto: str
    fecha_inicio: date
    fecha_fin: date | None = None
    estado: EstadoCampania


class CampaniaCreate(BaseModel):
    nombre: str
    producto: str
    fecha_inicio: date
    fecha_fin: date | None = None
    estado: EstadoCampania = "planificada"


class CampaniaUpdate(BaseModel):
    nombre: str | None = None
    producto: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    estado: EstadoCampania | None = None
