import uuid
from app.database import SessionLocal
from app.models import AuditLog


def write_audit_log(
    *, usuario_id, accion: str, recurso: str, recurso_id,
    ip_origen, resultado: str, detalle,
) -> None:
    db = SessionLocal()
    try:
        log = AuditLog(
            log_id=uuid.uuid4(),
            usuario_id=uuid.UUID(str(usuario_id)) if usuario_id else None,
            accion=accion,
            recurso=recurso,
            recurso_id=str(recurso_id) if recurso_id is not None else None,
            ip_origen=ip_origen,
            resultado=resultado,
            detalle=detalle,
        )
        db.add(log)
        db.commit()
    finally:
        db.close()
