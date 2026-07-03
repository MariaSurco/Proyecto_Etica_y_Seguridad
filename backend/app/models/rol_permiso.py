from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class RolPermiso(Base):
    __tablename__ = "rol_permiso"
    rol_id = Column(Integer, ForeignKey("rol.rol_id"), primary_key=True)
    permiso_id = Column(Integer, ForeignKey("permiso.permiso_id"), primary_key=True)
    rol = relationship("Rol", back_populates="permisos")
    permiso = relationship("Permiso")
