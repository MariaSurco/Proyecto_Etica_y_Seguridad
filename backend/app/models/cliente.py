import uuid
from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Cliente(Base):
    __tablename__ = "cliente"
    cliente_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_cifrado = Column(String)
    dni_cifrado = Column(String)
    email_cifrado = Column(String)
    telefono_cifrado = Column(String)
    direccion_cifrada = Column(String)
    age = Column(Integer)
    job = Column(String(50))
    marital = Column(String(30))
    education = Column(String(30))
    default_credit = Column(String(5))
    balance = Column(Numeric(12, 2))
    housing = Column(String(5))
    loan = Column(String(5))
    contact = Column(String(30))
    day = Column(Integer)
    month = Column(String(10))
    duration = Column(Integer)
    campaign = Column(Integer)
    pdays = Column(Integer)
    previous = Column(Integer)
    poutcome = Column(String(30))
    deposit = Column(String(5))
