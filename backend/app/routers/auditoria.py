from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditLog
from app.security.rbac import require_permission
from app.schemas.auditoria import AuditLogOut

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("/logs", response_model=list[AuditLogOut])
def list_logs(
    usuario_id: str | None = None,
    accion: str | None = None,
    recurso: str | None = None,
    resultado: str | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("auditoria:consultar")),
):
    query = db.query(AuditLog)
    if usuario_id:
        query = query.filter(AuditLog.usuario_id == usuario_id)
    if accion:
        query = query.filter(AuditLog.accion == accion)
    if recurso:
        query = query.filter(AuditLog.recurso == recurso)
    if resultado:
        query = query.filter(AuditLog.resultado == resultado)
    logs = query.order_by(AuditLog.timestamp_evento.desc()).limit(200).all()
    return [
        AuditLogOut(
            log_id=str(l.log_id),
            usuario_id=str(l.usuario_id) if l.usuario_id else None,
            accion=l.accion, recurso=l.recurso, recurso_id=l.recurso_id,
            ip_origen=l.ip_origen, resultado=l.resultado, detalle=l.detalle,
            timestamp_evento=l.timestamp_evento,
        )
        for l in logs
    ]
