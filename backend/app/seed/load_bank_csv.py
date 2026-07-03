import sys
import os
import uuid
import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Rol, Permiso, RolPermiso, Usuario, Cliente, Consentimiento
from app.security.hashing import hash_password
from app.security.crypto import encrypt_field
from app.seed.generate_synthetic import (
    generate_clientes, generate_consentimientos,
    generate_roles_and_permisos, generate_usuarios_internos,
)

BANK_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "bank.csv")


def seed_roles_permisos(db: Session) -> dict[str, int]:
    roles, permisos, rol_permiso = generate_roles_and_permisos()
    rol_by_name = {}
    for r in roles:
        obj = Rol(nombre=r["nombre"], descripcion=r["descripcion"])
        db.add(obj)
        db.flush()
        rol_by_name[r["nombre"]] = obj.rol_id
    permiso_by_name = {}
    for p in permisos:
        obj = Permiso(nombre=p["nombre"], recurso=p["recurso"], accion=p["accion"])
        db.add(obj)
        db.flush()
        permiso_by_name[p["nombre"]] = obj.permiso_id
    for rp in rol_permiso:
        db.add(RolPermiso(rol_id=rol_by_name[rp["rol_nombre"]], permiso_id=permiso_by_name[rp["permiso_nombre"]]))
    db.commit()
    return rol_by_name


def seed_usuarios(db: Session, rol_by_name: dict[str, int]) -> None:
    usuarios = generate_usuarios_internos({"administrador": 1, "supervisor": 2, "analista": 3, "teleoperador": 8})
    default_password = "CambiarEnPrimerAcceso!123"
    for u in usuarios:
        db.add(Usuario(
            usuario_id=uuid.UUID(u["usuario_id"]), username=u["username"],
            nombre_completo=u["nombre_completo"], email_corporativo=u["email_corporativo"],
            password_hash=hash_password(default_password),
            rol_id=rol_by_name[u["rol_nombre"]],
        ))
    db.commit()


def seed_clientes_y_consentimientos(db: Session) -> None:
    df_base = pd.read_csv(BANK_CSV_PATH)
    clientes = generate_clientes(df_base)
    for c in clientes:
        db.add(Cliente(
            cliente_id=uuid.UUID(c["cliente_id"]),
            nombre_cifrado=encrypt_field(c["nombre"]),
            dni_cifrado=encrypt_field(c["dni"]),
            email_cifrado=encrypt_field(c["email"]),
            telefono_cifrado=encrypt_field(c["telefono"]),
            direccion_cifrada=encrypt_field(c["direccion"]),
            age=c["age"], job=c["job"], marital=c["marital"], education=c["education"],
            default_credit=c["default"], balance=c["balance"], housing=c["housing"],
            loan=c["loan"], contact=c["contact"], day=c["day"], month=c["month"],
            duration=c["duration"], campaign=c["campaign"], pdays=c["pdays"],
            previous=c["previous"], poutcome=c["poutcome"], deposit=c["deposit"],
        ))
    db.commit()
    cliente_ids = [c["cliente_id"] for c in clientes]
    for cons in generate_consentimientos(cliente_ids):
        db.add(Consentimiento(
            consentimiento_id=uuid.UUID(cons["consentimiento_id"]), cliente_id=uuid.UUID(cons["cliente_id"]),
            estado=cons["estado"], canal=cons["canal"],
        ))
    db.commit()


def main():
    db = SessionLocal()
    try:
        rol_by_name = seed_roles_permisos(db)
        seed_usuarios(db, rol_by_name)
        seed_clientes_y_consentimientos(db)
        print("Seed completed.")
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
