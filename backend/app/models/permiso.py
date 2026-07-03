from sqlalchemy import Column, Integer, String
from app.database import Base

class Permiso(Base):
    __tablename__ = "permiso"
    permiso_id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    recurso = Column(String(100), nullable=False)
    accion = Column(String(50), nullable=False)
