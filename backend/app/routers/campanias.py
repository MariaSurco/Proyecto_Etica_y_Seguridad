import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.audit.logger import write_audit_log
from app.database import get_db
from app.models import Campania, Cliente, Consentimiento
from app.schemas.campanias import CampaniaCreate, CampaniaOut, CampaniaUpdate
from app.security.masking import mask_cliente
from app.security.rbac import require_any_permission, require_permission

router = APIRouter(prefix="/campanias", tags=["campanias"])


def _campania_out(campania: Campania) -> CampaniaOut:
    return CampaniaOut(
        campania_id=str(campania.campania_id),
        nombre=campania.nombre,
        producto=campania.producto,
        fecha_inicio=campania.fecha_inicio,
        fecha_fin=campania.fecha_fin,
        estado=campania.estado,
    )


@router.get("", response_model=list[CampaniaOut])
def listar_campanias(
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("campanias:consultar", "campanias:consultar_asignadas")),
):
    campanias = db.query(Campania).order_by(Campania.fecha_inicio.desc()).all()
    return [_campania_out(c) for c in campanias]


@router.post("", response_model=CampaniaOut, status_code=201)
def crear_campania(
    payload: CampaniaCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("campanias:crear_editar")),
):
    campania = Campania(
        campania_id=uuid.uuid4(),
        nombre=payload.nombre,
        producto=payload.producto,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
        estado=payload.estado,
    )
    db.add(campania)
    db.commit()
    db.refresh(campania)
    write_audit_log(
        usuario_id=user["sub"], accion="crea_campania", recurso="campania",
        recurso_id=str(campania.campania_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=campania.nombre,
    )
    return _campania_out(campania)


@router.patch("/{campania_id}", response_model=CampaniaOut)
def actualizar_campania(
    campania_id: uuid.UUID,
    payload: CampaniaUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("campanias:crear_editar")),
):
    campania = db.query(Campania).filter(Campania.campania_id == campania_id).first()
    if campania is None:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(campania, field, value)
    db.commit()
    db.refresh(campania)
    write_audit_log(
        usuario_id=user["sub"], accion="actualiza_campania", recurso="campania",
        recurso_id=str(campania.campania_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=",".join(updates.keys()),
    )
    return _campania_out(campania)


@router.get("/{campania_id}/clientes-elegibles")
def listar_clientes_elegibles_campania(
    campania_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_sensible", "clientes:ver_parcial")),
):
    campania = db.query(Campania).filter(Campania.campania_id == campania_id).first()
    if campania is None:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    rows = (
        db.query(Cliente)
        .join(Consentimiento, Consentimiento.cliente_id == Cliente.cliente_id)
        .filter(Consentimiento.estado == "opt-in")
        .all()
    )
    return [mask_cliente(cliente, user["rol"]) for cliente in rows]
