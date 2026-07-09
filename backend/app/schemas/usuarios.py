from datetime import datetime

from pydantic import BaseModel


class RolOut(BaseModel):
    rol_id: int
    nombre: str
    descripcion: str | None = None


class PermisoOut(BaseModel):
    permiso_id: int
    nombre: str
    recurso: str
    accion: str


class UsuarioOut(BaseModel):
    usuario_id: str
    username: str
    nombre_completo: str
    email_corporativo: str
    rol_id: int
    rol_nombre: str | None = None
    activo: bool
    fecha_creacion: datetime | None = None


class UsuarioCreate(BaseModel):
    username: str
    nombre_completo: str
    email_corporativo: str
    password: str
    rol_id: int


class UsuarioActivoUpdate(BaseModel):
    activo: bool
