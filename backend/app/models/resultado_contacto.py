import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class ResultadoContacto(Base):
    __tablename__ = "resultado_contacto"
    resultado_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asignacion_id = Column(UUID(as_uuid=True), ForeignKey("asignacion.asignacion_id"), nullable=False)
    resultado = Column(String(40), nullable=False)
    observacion = Column(Text)
    fecha_contacto = Column(DateTime, server_default=func.now())
