import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import AuditLog, Cliente, Consentimiento, Permiso, Rol, RolPermiso, Usuario
from app.security.crypto import encrypt_field
from app.security.hashing import hash_password

client = TestClient(app)
PASSWORD = "Sup3rSecret!Pass"


def _make_permiso(db, nombre):
    permiso = db.query(Permiso).filter(Permiso.nombre == nombre).first()
    if permiso is None:
        recurso, accion = nombre.split(":")
        permiso = Permiso(nombre=nombre, recurso=recurso, accion=accion)
        db.add(permiso)
        db.flush()
    return permiso


def _make_user(db, prefix, permisos):
    rol = Rol(nombre=f"{prefix}_rol", descripcion="x")
    db.add(rol)
    db.flush()
    for nombre in permisos:
        db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=_make_permiso(db, nombre).permiso_id))
    user = Usuario(
        usuario_id=uuid.uuid4(),
        username=f"{prefix}.user",
        nombre_completo="Consentimiento Test",
        email_corporativo=f"{prefix}@bancoproyecto.pe",
        password_hash=hash_password(PASSWORD),
        rol_id=rol.rol_id,
    )
    db.add(user)
    db.commit()
    return user, rol


def _make_cliente(db):
    cliente = Cliente(
        cliente_id=uuid.uuid4(), nombre_cifrado=encrypt_field("Cliente Consentimiento"),
        dni_cifrado=encrypt_field("00000001"), email_cifrado=encrypt_field("cons@test.pe"),
        telefono_cifrado=encrypt_field("+51900000001"), direccion_cifrada=encrypt_field("Test 1"),
        age=31, job="admin.", marital="single", education="secondary", default_credit="no",
        balance=100, housing="no", loan="no", contact="cellular", day=1, month="jan",
        duration=60, campaign=1, pdays=-1, previous=0, poutcome="unknown", deposit="no",
    )
    db.add(cliente)
    db.flush()
    consentimiento = Consentimiento(
        consentimiento_id=uuid.uuid4(),
        cliente_id=cliente.cliente_id,
        estado="opt-in",
        canal="web",
    )
    db.add(consentimiento)
    db.commit()
    return cliente, consentimiento


@pytest.fixture
def scenario():
    db = SessionLocal()
    prefix = f"constest_{uuid.uuid4().hex[:8]}"
    user, rol = _make_user(db, prefix, ["clientes:ver_sensible"])
    cliente, consentimiento = _make_cliente(db)
    try:
        yield {"user": user, "rol": rol, "cliente": cliente, "consentimiento": consentimiento}
    finally:
        db.query(AuditLog).filter(AuditLog.usuario_id == user.usuario_id).delete()
        db.query(Consentimiento).filter(Consentimiento.cliente_id == cliente.cliente_id).delete()
        db.query(Cliente).filter(Cliente.cliente_id == cliente.cliente_id).delete()
        db.query(Usuario).filter(Usuario.usuario_id == user.usuario_id).delete()
        db.query(RolPermiso).filter(RolPermiso.rol_id == rol.rol_id).delete()
        db.query(Rol).filter(Rol.rol_id == rol.rol_id).delete()
        db.commit()
        db.close()


@pytest.fixture
def parcial_scenario():
    db = SessionLocal()
    prefix = f"consparcial_{uuid.uuid4().hex[:8]}"
    user, rol = _make_user(db, prefix, ["clientes:ver_parcial"])
    cliente, consentimiento = _make_cliente(db)
    try:
        yield {"user": user, "rol": rol, "cliente": cliente, "consentimiento": consentimiento}
    finally:
        db.query(AuditLog).filter(AuditLog.usuario_id == user.usuario_id).delete()
        db.query(Consentimiento).filter(Consentimiento.cliente_id == cliente.cliente_id).delete()
        db.query(Cliente).filter(Cliente.cliente_id == cliente.cliente_id).delete()
        db.query(Usuario).filter(Usuario.usuario_id == user.usuario_id).delete()
        db.query(RolPermiso).filter(RolPermiso.rol_id == rol.rol_id).delete()
        db.query(Rol).filter(Rol.rol_id == rol.rol_id).delete()
        db.commit()
        db.close()


def _login(username):
    resp = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_get_consentimiento_allows_ver_parcial(parcial_scenario):
    token = _login(parcial_scenario["user"].username)
    resp = client.get(
        f"/clientes/{parcial_scenario['cliente'].cliente_id}/consentimiento",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "opt-in"


def test_update_consentimiento_persists_and_audits(scenario):
    token = _login(scenario["user"].username)
    resp = client.patch(
        f"/clientes/{scenario['cliente'].cliente_id}/consentimiento",
        json={"estado": "opt-out", "canal": "telefono"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "opt-out"

    db = SessionLocal()
    try:
        log = (
            db.query(AuditLog)
            .filter(AuditLog.usuario_id == scenario["user"].usuario_id, AuditLog.accion == "actualiza_consentimiento")
            .first()
        )
        assert log is not None
    finally:
        db.close()
