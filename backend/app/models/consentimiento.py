import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Consentimiento(Base):
    __tablename__ = "consentimiento"
    consentimiento_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("cliente.cliente_id"), nullable=False)
    estado = Column(String(20), nullable=False)
    canal = Column(String(30))
    fecha_registro = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    actualizado_por = Column(UUID(as_uuid=True), ForeignKey("usuario.usuario_id"))

    __table_args__ = (
        CheckConstraint("estado IN ('opt-in','opt-out','no informado')", name="ck_consentimiento_estado"),
    )
