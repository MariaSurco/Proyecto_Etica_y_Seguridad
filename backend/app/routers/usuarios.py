import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.audit.logger import write_audit_log
from app.database import get_db
from app.models import Permiso, Rol, Usuario
from app.schemas.usuarios import (
    PermisoOut,
    RolOut,
    UsuarioActivoUpdate,
    UsuarioCreate,
    UsuarioOut,
)
from app.security.hashing import hash_password, validate_password_policy
from app.security.rbac import require_any_permission, require_permission

router = APIRouter(tags=["usuarios"])


def _usuario_out(usuario: Usuario) -> UsuarioOut:
    return UsuarioOut(
        usuario_id=str(usuario.usuario_id),
        username=usuario.username,
        nombre_completo=usuario.nombre_completo,
        email_corporativo=usuario.email_corporativo,
        rol_id=usuario.rol_id,
        rol_nombre=usuario.rol.nombre if usuario.rol else None,
        activo=usuario.activo,
        fecha_creacion=usuario.fecha_creacion,
    )


@router.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("usuarios:gestionar")),
):
    usuarios = db.query(Usuario).order_by(Usuario.username.asc()).all()
    return [_usuario_out(usuario) for usuario in usuarios]


@router.get("/usuarios/teleoperadores", response_model=list[UsuarioOut])
def listar_teleoperadores(
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("campanias:crear_editar", "usuarios:gestionar")),
):
    usuarios = (
        db.query(Usuario)
        .join(Rol, Rol.rol_id == Usuario.rol_id)
        .filter(Rol.nombre == "teleoperador", Usuario.activo.is_(True))
        .order_by(Usuario.username.asc())
        .all()
    )
    return [_usuario_out(usuario) for usuario in usuarios]


@router.post("/usuarios", response_model=UsuarioOut, status_code=201)
def crear_usuario(
    payload: UsuarioCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("usuarios:gestionar")),
):
    errors = validate_password_policy(payload.password)
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    if db.query(Rol).filter(Rol.rol_id == payload.rol_id).first() is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    existing = (
        db.query(Usuario)
        .filter(
            (Usuario.username == payload.username)
            | (Usuario.email_corporativo == payload.email_corporativo)
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Usuario o email ya existe")

    usuario = Usuario(
        usuario_id=uuid.uuid4(),
        username=payload.username,
        nombre_completo=payload.nombre_completo,
        email_corporativo=payload.email_corporativo,
        password_hash=hash_password(payload.password),
        rol_id=payload.rol_id,
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    write_audit_log(
        usuario_id=user["sub"], accion="crea_usuario", recurso="usuario",
        recurso_id=str(usuario.usuario_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=usuario.username,
    )
    return _usuario_out(usuario)


@router.patch("/usuarios/{usuario_id}/activo", response_model=UsuarioOut)
def actualizar_usuario_activo(
    usuario_id: uuid.UUID,
    payload: UsuarioActivoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("usuarios:gestionar")),
):
    usuario = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.activo = payload.activo
    db.commit()
    db.refresh(usuario)
    write_audit_log(
        usuario_id=user["sub"], accion="actualiza_usuario_activo", recurso="usuario",
        recurso_id=str(usuario.usuario_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"activo={payload.activo}",
    )
    return _usuario_out(usuario)


@router.get("/roles", response_model=list[RolOut])
def listar_roles(
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("usuarios:gestionar")),
):
    roles = db.query(Rol).order_by(Rol.nombre.asc()).all()
    return [RolOut(rol_id=rol.rol_id, nombre=rol.nombre, descripcion=rol.descripcion) for rol in roles]


@router.get("/permisos", response_model=list[PermisoOut])
def listar_permisos(
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("usuarios:gestionar")),
):
    permisos = db.query(Permiso).order_by(Permiso.nombre.asc()).all()
    return [
        PermisoOut(
            permiso_id=permiso.permiso_id,
            nombre=permiso.nombre,
            recurso=permiso.recurso,
            accion=permiso.accion,
        )
        for permiso in permisos
    ]
