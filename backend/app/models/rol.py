from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Rol(Base):
    __tablename__ = "rol"
    rol_id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text)
    permisos = relationship("RolPermiso", back_populates="rol")
