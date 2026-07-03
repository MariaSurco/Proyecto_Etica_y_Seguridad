import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuario.usuario_id"))
    accion = Column(String(100), nullable=False)
    recurso = Column(String(100), nullable=False)
    recurso_id = Column(String(100))
    ip_origen = Column(String(45))
    resultado = Column(String(30), nullable=False)
    detalle = Column(Text)
    timestamp_evento = Column(DateTime, server_default=func.now())
