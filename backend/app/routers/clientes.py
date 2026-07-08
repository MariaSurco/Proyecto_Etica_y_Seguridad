from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Consentimiento, Asignacion
from app.security.rbac import require_any_permission, get_current_user
from app.security.masking import mask_cliente
from app.audit.logger import write_audit_log

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("/elegibles")
def listar_elegibles(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_sensible", "clientes:ver_parcial")),
):
    rows = (
        db.query(Cliente)
        .join(Consentimiento, Consentimiento.cliente_id == Cliente.cliente_id)
        .filter(Consentimiento.estado == "opt-in")
        .all()
    )
    resultado = [mask_cliente(c, user["rol"]) for c in rows]
    write_audit_log(
        usuario_id=user["sub"], accion="consulta_clientes_elegibles", recurso="clientes",
        recurso_id=None, ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"{len(resultado)} resultados",
    )
    return resultado


@router.get("/asignados")
def listar_asignados(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_asignados")),
):
    rows = (
        db.query(Cliente)
        .join(Asignacion, Asignacion.cliente_id == Cliente.cliente_id)
        .filter(Asignacion.usuario_id == user["sub"])
        .all()
    )
    resultado = [mask_cliente(c, user["rol"]) for c in rows]
    write_audit_log(
        usuario_id=user["sub"], accion="consulta_clientes_asignados", recurso="clientes",
        recurso_id=None, ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"{len(resultado)} resultados",
    )
    return resultado


@router.get("/{cliente_id}")
def obtener_cliente(
    cliente_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    permisos = user.get("permisos", [])
    permisos_validos = {"clientes:ver_sensible", "clientes:ver_parcial", "clientes:ver_asignados"}
    if not permisos_validos & set(permisos):
        raise HTTPException(status_code=403, detail="No autorizado para este recurso")

    cliente = db.query(Cliente).filter(Cliente.cliente_id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    solo_asignados = "clientes:ver_sensible" not in permisos and "clientes:ver_parcial" not in permisos
    if solo_asignados:
        asignado = (
            db.query(Asignacion)
            .filter(Asignacion.cliente_id == cliente_id, Asignacion.usuario_id == user["sub"])
            .first()
        )
        if asignado is None:
            write_audit_log(
                usuario_id=user["sub"], accion="acceso_denegado", recurso="clientes",
                recurso_id=str(cliente_id), ip_origen=request.client.host if request.client else None,
                resultado="denegado", detalle="Cliente no asignado al usuario",
            )
            raise HTTPException(status_code=403, detail="Cliente no asignado")

    write_audit_log(
        usuario_id=user["sub"], accion="consulta_cliente_detalle", recurso="clientes",
        recurso_id=str(cliente_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=None,
    )
    return mask_cliente(cliente, user["rol"])
