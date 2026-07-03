import uuid
from sqlalchemy import Column, String, Date, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Campania(Base):
    __tablename__ = "campania"
    campania_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(120), nullable=False)
    producto = Column(String(80), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date)
    estado = Column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint("estado IN ('planificada','activa','cerrada','cancelada')", name="ck_campania_estado"),
    )
