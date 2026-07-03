import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Asignacion(Base):
    __tablename__ = "asignacion"
    asignacion_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("cliente.cliente_id"), nullable=False)
    campania_id = Column(UUID(as_uuid=True), ForeignKey("campania.campania_id"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuario.usuario_id"), nullable=False)
    estado_contacto = Column(String(30), default="pendiente")
    fecha_asignacion = Column(DateTime, server_default=func.now())
