import datetime
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, Permiso, RolPermiso, Cliente, Consentimiento, Asignacion, Campania, AuditLog
from app.security.hashing import hash_password
from app.security.crypto import encrypt_field

client = TestClient(app)

PASSWORD = "Sup3rSecret!Pass"

# mask_cliente (app/security/masking.py) branches on the literal role name
# ("administrador"/"supervisor"/"analista"/"teleoperador"), so these fixture
# roles must use those exact names for masking assertions to be meaningful.
# Usernames stay prefixed/unique per test run; the roles are cleaned up by
# name in `finally`, following the defensive-cleanup pattern in
# tests/test_auth.py.
ROL_ANALISTA = "analista"
ROL_TELEOP = "teleoperador"


def _make_permiso(db, nombre, recurso, accion):
    p = db.query(Permiso).filter(Permiso.nombre == nombre).first()
    if p is None:
        p = Permiso(nombre=nombre, recurso=recurso, accion=accion)
        db.add(p)
        db.flush()
    return p


def _make_user(db, rol_nombre, username, permiso_nombres):
    rol = db.query(Rol).filter(Rol.nombre == rol_nombre).first()
    if rol is None:
        rol = Rol(nombre=rol_nombre, descripcion="x")
        db.add(rol)
        db.flush()
    for nombre in permiso_nombres:
        permiso = _make_permiso(db, nombre, nombre.split(":")[0], nombre.split(":")[1])
        existing = (
            db.query(RolPermiso)
            .filter(RolPermiso.rol_id == rol.rol_id, RolPermiso.permiso_id == permiso.permiso_id)
            .first()
        )
        if existing is None:
            db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=permiso.permiso_id))
    user = Usuario(
        usuario_id=uuid.uuid4(), username=username, nombre_completo=username,
        email_corporativo=f"{username}@bancoproyecto.pe",
        password_hash=hash_password(PASSWORD), rol_id=rol.rol_id,
    )
    db.add(user)
    db.commit()
    return user, rol


def _make_cliente(db, estado_consentimiento):
    cliente = Cliente(
        cliente_id=uuid.uuid4(), nombre_cifrado=encrypt_field("Cliente Test"),
        dni_cifrado=encrypt_field("00000000"), email_cifrado=encrypt_field("c@test.pe"),
        telefono_cifrado=encrypt_field("+51900000000"), direccion_cifrada=encrypt_field("Test 123"),
        age=30, job="admin.", marital="single", education="secondary", default_credit="no",
        balance=100.0, housing="no", loan="no", contact="cellular", day=1, month="jan",
        duration=60, campaign=1, pdays=-1, previous=0, poutcome="unknown", deposit="no",
    )
    db.add(cliente)
    db.flush()
    db.add(Consentimiento(consentimiento_id=uuid.uuid4(), cliente_id=cliente.cliente_id, estado=estado_consentimiento))
    db.commit()
    return cliente


@pytest.fixture
def scenario():
    db = SessionLocal()
    prefix = f"clitest_{uuid.uuid4().hex[:8]}"
    analista, rol_analista = _make_user(db, ROL_ANALISTA, f"{prefix}.analista", ["clientes:ver_parcial"])
    teleop, rol_teleop = _make_user(db, ROL_TELEOP, f"{prefix}.teleop", ["clientes:ver_asignados"])
    opt_in = _make_cliente(db, "opt-in")
    opt_out = _make_cliente(db, "opt-out")
    campania = Campania(campania_id=uuid.uuid4(), nombre="Campania Test", producto="deposito",
                         fecha_inicio=datetime.date.today(), estado="activa")
    db.add(campania)
    db.flush()
    asignacion = Asignacion(asignacion_id=uuid.uuid4(), cliente_id=opt_in.cliente_id, campania_id=campania.campania_id, usuario_id=teleop.usuario_id)
    db.add(asignacion)
    db.commit()
    try:
        yield {"analista": analista, "teleop": teleop, "opt_in": opt_in, "opt_out": opt_out}
    finally:
        db.query(AuditLog).filter(AuditLog.usuario_id.in_([analista.usuario_id, teleop.usuario_id])).delete(synchronize_session=False)
        db.query(Asignacion).filter(Asignacion.usuario_id == teleop.usuario_id).delete()
        db.query(Campania).filter(Campania.campania_id == campania.campania_id).delete()
        db.query(Consentimiento).filter(Consentimiento.cliente_id.in_([opt_in.cliente_id, opt_out.cliente_id])).delete(synchronize_session=False)
        db.query(Cliente).filter(Cliente.cliente_id.in_([opt_in.cliente_id, opt_out.cliente_id])).delete(synchronize_session=False)
        db.query(Usuario).filter(Usuario.usuario_id.in_([analista.usuario_id, teleop.usuario_id])).delete(synchronize_session=False)
        for rol in (rol_analista, rol_teleop):
            db.query(RolPermiso).filter(RolPermiso.rol_id == rol.rol_id).delete()
            db.query(Rol).filter(Rol.rol_id == rol.rol_id).delete()
        db.commit()
        db.close()


def _login(username):
    resp = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_elegibles_excludes_opt_out_and_masks_pii_for_analista(scenario):
    token = _login(scenario["analista"].username)
    resp = client.get("/clientes/elegibles", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    ids = [c["cliente_id"] for c in resp.json()]
    assert str(scenario["opt_in"].cliente_id) in ids
    assert str(scenario["opt_out"].cliente_id) not in ids
    assert all("nombre" not in c for c in resp.json())


def test_teleoperador_only_sees_assigned_clients(scenario):
    token = _login(scenario["teleop"].username)
    resp_ok = client.get(f"/clientes/{scenario['opt_in'].cliente_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp_ok.status_code == 200
    assert resp_ok.json()["nombre"] == "Cliente Test"

    resp_forbidden = client.get(f"/clientes/{scenario['opt_out'].cliente_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp_forbidden.status_code == 403


def test_asignados_returns_only_teleoperador_own_clients(scenario):
    token = _login(scenario["teleop"].username)
    resp = client.get("/clientes/asignados", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    ids = [c["cliente_id"] for c in resp.json()]
    assert str(scenario["opt_in"].cliente_id) in ids
    assert str(scenario["opt_out"].cliente_id) not in ids


def test_cliente_detalle_404_for_unknown_id(scenario):
    token = _login(scenario["analista"].username)
    resp = client.get(f"/clientes/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_elegibles_requires_authentication():
    resp = client.get("/clientes/elegibles")
    assert resp.status_code == 401
