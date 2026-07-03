import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuario"
    usuario_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), nullable=False, unique=True)
    nombre_completo = Column(String(120), nullable=False)
    email_corporativo = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    rol_id = Column(Integer, ForeignKey("rol.rol_id"), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
