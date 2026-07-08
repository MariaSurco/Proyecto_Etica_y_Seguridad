import uuid
from app.database import SessionLocal
from app.models import AuditLog
from app.audit.logger import write_audit_log


def test_write_audit_log_persists_row_with_null_user():
    marker = f"test-marker-{uuid.uuid4()}"
    write_audit_log(
        usuario_id=None, accion="evento_test", recurso="test",
        recurso_id=marker, ip_origen="127.0.0.1", resultado="exito", detalle=None,
    )
    db = SessionLocal()
    try:
        row = db.query(AuditLog).filter(AuditLog.recurso_id == marker).first()
        assert row is not None
        assert row.accion == "evento_test"
        assert row.usuario_id is None
        assert row.resultado == "exito"
    finally:
        db.query(AuditLog).filter(AuditLog.recurso_id == marker).delete()
        db.commit()
        db.close()
