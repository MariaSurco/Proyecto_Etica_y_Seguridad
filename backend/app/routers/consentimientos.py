import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.audit.logger import write_audit_log
from app.database import get_db
from app.models import Cliente, Consentimiento
from app.schemas.consentimientos import ConsentimientoOut, ConsentimientoUpdate
from app.security.rbac import require_any_permission, require_permission

router = APIRouter(prefix="/clientes", tags=["consentimientos"])


def _consentimiento_out(consentimiento: Consentimiento) -> ConsentimientoOut:
    return ConsentimientoOut(
        consentimiento_id=str(consentimiento.consentimiento_id),
        cliente_id=str(consentimiento.cliente_id),
        estado=consentimiento.estado,
        canal=consentimiento.canal,
        fecha_registro=consentimiento.fecha_registro,
        fecha_actualizacion=consentimiento.fecha_actualizacion,
        actualizado_por=str(consentimiento.actualizado_por) if consentimiento.actualizado_por else None,
    )


@router.get("/{cliente_id}/consentimiento", response_model=ConsentimientoOut)
def obtener_consentimiento(
    cliente_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_sensible", "clientes:ver_parcial")),
):
    consentimiento = (
        db.query(Consentimiento)
        .filter(Consentimiento.cliente_id == cliente_id)
        .order_by(Consentimiento.fecha_actualizacion.desc())
        .first()
    )
    if consentimiento is None:
        raise HTTPException(status_code=404, detail="Consentimiento no encontrado")
    return _consentimiento_out(consentimiento)


@router.patch("/{cliente_id}/consentimiento", response_model=ConsentimientoOut)
def actualizar_consentimiento(
    cliente_id: uuid.UUID,
    payload: ConsentimientoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("clientes:ver_sensible")),
):
    cliente = db.query(Cliente).filter(Cliente.cliente_id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    consentimiento = (
        db.query(Consentimiento)
        .filter(Consentimiento.cliente_id == cliente_id)
        .order_by(Consentimiento.fecha_actualizacion.desc())
        .first()
    )
    if consentimiento is None:
        consentimiento = Consentimiento(consentimiento_id=uuid.uuid4(), cliente_id=cliente_id)
        db.add(consentimiento)

    consentimiento.estado = payload.estado
    consentimiento.canal = payload.canal
    consentimiento.actualizado_por = uuid.UUID(str(user["sub"]))
    db.commit()
    db.refresh(consentimiento)

    write_audit_log(
        usuario_id=user["sub"],
        accion="actualiza_consentimiento",
        recurso="consentimiento",
        recurso_id=str(cliente_id),
        ip_origen=request.client.host if request.client else None,
        resultado="exito",
        detalle=f"estado={payload.estado}",
    )
    return _consentimiento_out(consentimiento)
