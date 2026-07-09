import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.audit.logger import write_audit_log
from app.database import get_db
from app.models import Asignacion, Campania, Cliente, Consentimiento, ResultadoContacto, Usuario
from app.schemas.asignaciones import (
    AsignacionCreate,
    AsignacionOut,
    ResultadoContactoCreate,
    ResultadoContactoOut,
)
from app.security.rbac import require_any_permission, require_permission

router = APIRouter(tags=["asignaciones"])


def _asignacion_out(asignacion: Asignacion) -> AsignacionOut:
    return AsignacionOut(
        asignacion_id=str(asignacion.asignacion_id),
        cliente_id=str(asignacion.cliente_id),
        campania_id=str(asignacion.campania_id),
        usuario_id=str(asignacion.usuario_id),
        estado_contacto=asignacion.estado_contacto,
        fecha_asignacion=asignacion.fecha_asignacion,
    )


def _resultado_out(resultado: ResultadoContacto) -> ResultadoContactoOut:
    return ResultadoContactoOut(
        resultado_id=str(resultado.resultado_id),
        asignacion_id=str(resultado.asignacion_id),
        resultado=resultado.resultado,
        observacion=resultado.observacion,
        fecha_contacto=resultado.fecha_contacto,
    )


@router.post("/asignaciones", response_model=AsignacionOut, status_code=201)
def crear_asignacion(
    payload: AsignacionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("campanias:crear_editar")),
):
    cliente_id = uuid.UUID(payload.cliente_id)
    campania_id = uuid.UUID(payload.campania_id)
    usuario_id = uuid.UUID(payload.usuario_id)

    if db.query(Cliente).filter(Cliente.cliente_id == cliente_id).first() is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if db.query(Campania).filter(Campania.campania_id == campania_id).first() is None:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    if db.query(Usuario).filter(Usuario.usuario_id == usuario_id, Usuario.activo.is_(True)).first() is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")

    consentimiento = (
        db.query(Consentimiento)
        .filter(Consentimiento.cliente_id == cliente_id, Consentimiento.estado == "opt-in")
        .first()
    )
    if consentimiento is None:
        raise HTTPException(status_code=409, detail="Cliente sin consentimiento opt-in")

    existing = (
        db.query(Asignacion)
        .filter(Asignacion.cliente_id == cliente_id, Asignacion.campania_id == campania_id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Cliente ya asignado a esta campaña")

    asignacion = Asignacion(
        asignacion_id=uuid.uuid4(),
        cliente_id=cliente_id,
        campania_id=campania_id,
        usuario_id=usuario_id,
        estado_contacto="pendiente",
    )
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    write_audit_log(
        usuario_id=user["sub"], accion="crea_asignacion", recurso="asignacion",
        recurso_id=str(asignacion.asignacion_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"cliente={cliente_id};usuario={usuario_id}",
    )
    return _asignacion_out(asignacion)


@router.get("/asignaciones/mias", response_model=list[AsignacionOut])
def listar_mis_asignaciones(
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("clientes:ver_asignados")),
):
    rows = (
        db.query(Asignacion)
        .filter(Asignacion.usuario_id == uuid.UUID(str(user["sub"])))
        .order_by(Asignacion.fecha_asignacion.desc())
        .all()
    )
    return [_asignacion_out(row) for row in rows]


@router.get("/campanias/{campania_id}/asignaciones", response_model=list[AsignacionOut])
def listar_asignaciones_campania(
    campania_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("campanias:crear_editar", "campanias:consultar")),
):
    rows = (
        db.query(Asignacion)
        .filter(Asignacion.campania_id == campania_id)
        .order_by(Asignacion.fecha_asignacion.desc())
        .all()
    )
    return [_asignacion_out(row) for row in rows]


@router.post("/asignaciones/{asignacion_id}/resultado", response_model=ResultadoContactoOut, status_code=201)
def registrar_resultado(
    asignacion_id: uuid.UUID,
    payload: ResultadoContactoCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("resultados:registrar")),
):
    asignacion = db.query(Asignacion).filter(Asignacion.asignacion_id == asignacion_id).first()
    if asignacion is None:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    if str(asignacion.usuario_id) != str(user["sub"]):
        write_audit_log(
            usuario_id=user["sub"], accion="acceso_denegado", recurso="resultado_contacto",
            recurso_id=str(asignacion_id), ip_origen=request.client.host if request.client else None,
            resultado="denegado", detalle="Asignación pertenece a otro usuario",
        )
        raise HTTPException(status_code=403, detail="Asignación no pertenece al usuario")

    resultado = ResultadoContacto(
        resultado_id=uuid.uuid4(),
        asignacion_id=asignacion_id,
        resultado=payload.resultado,
        observacion=payload.observacion,
    )
    asignacion.estado_contacto = payload.resultado
    db.add(resultado)
    db.commit()
    db.refresh(resultado)
    write_audit_log(
        usuario_id=user["sub"], accion="registra_resultado_contacto", recurso="resultado_contacto",
        recurso_id=str(resultado.resultado_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=payload.resultado,
    )
    return _resultado_out(resultado)


@router.get("/asignaciones/{asignacion_id}/resultado", response_model=list[ResultadoContactoOut])
def obtener_resultados_asignacion(
    asignacion_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(
        require_any_permission("resultados:registrar", "campanias:crear_editar", "campanias:consultar")
    ),
):
    asignacion = db.query(Asignacion).filter(Asignacion.asignacion_id == asignacion_id).first()
    if asignacion is None:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    user_permisos = user.get("permisos", [])
    tiene_vista_campania = "campanias:crear_editar" in user_permisos or "campanias:consultar" in user_permisos
    if not tiene_vista_campania and str(asignacion.usuario_id) != str(user["sub"]):
        raise HTTPException(status_code=403, detail="Asignación no pertenece al usuario")
    rows = (
        db.query(ResultadoContacto)
        .filter(ResultadoContacto.asignacion_id == asignacion_id)
        .order_by(ResultadoContacto.fecha_contacto.desc())
        .all()
    )
    return [_resultado_out(row) for row in rows]
