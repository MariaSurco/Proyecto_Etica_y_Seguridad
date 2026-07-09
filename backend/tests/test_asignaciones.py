import datetime
import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import (
    Asignacion,
    AuditLog,
    Campania,
    Cliente,
    Consentimiento,
    Permiso,
    ResultadoContacto,
    Rol,
    RolPermiso,
    Usuario,
)
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


def _make_user(db, prefix, suffix, permisos):
    rol = Rol(nombre=f"{prefix}_{suffix}_rol", descripcion="x")
    db.add(rol)
    db.flush()
    for nombre in permisos:
        db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=_make_permiso(db, nombre).permiso_id))
    user = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.{suffix}", nombre_completo=suffix,
        email_corporativo=f"{prefix}.{suffix}@bancoproyecto.pe",
        password_hash=hash_password(PASSWORD), rol_id=rol.rol_id,
    )
    db.add(user)
    db.commit()
    return user, rol


def _make_cliente(db, estado):
    cliente = Cliente(
        cliente_id=uuid.uuid4(), nombre_cifrado=encrypt_field("Cliente Asignacion"),
        dni_cifrado=encrypt_field("00000002"), email_cifrado=encrypt_field("asig@test.pe"),
        telefono_cifrado=encrypt_field("+51900000002"), direccion_cifrada=encrypt_field("Test 2"),
        age=32, job="admin.", marital="single", education="secondary", default_credit="no",
        balance=100, housing="no", loan="no", contact="cellular", day=1, month="jan",
        duration=60, campaign=1, pdays=-1, previous=0, poutcome="unknown", deposit="yes",
    )
    db.add(cliente)
    db.flush()
    db.add(Consentimiento(consentimiento_id=uuid.uuid4(), cliente_id=cliente.cliente_id, estado=estado))
    db.commit()
    return cliente


@pytest.fixture
def scenario():
    db = SessionLocal()
    prefix = f"asigtest_{uuid.uuid4().hex[:8]}"
    supervisor, rol_supervisor = _make_user(db, prefix, "supervisor", ["campanias:crear_editar", "campanias:consultar"])
    teleop, rol_teleop = _make_user(db, prefix, "teleop", ["clientes:ver_asignados", "resultados:registrar"])
    opt_in = _make_cliente(db, "opt-in")
    opt_out = _make_cliente(db, "opt-out")
    campania = Campania(
        campania_id=uuid.uuid4(), nombre=f"{prefix}_campania", producto="deposito",
        fecha_inicio=datetime.date.today(), estado="activa",
    )
    db.add(campania)
    db.commit()
    try:
        yield {
            "supervisor": supervisor,
            "teleop": teleop,
            "roles": [rol_supervisor, rol_teleop],
            "clientes": [opt_in, opt_out],
            "campania": campania,
        }
    finally:
        db.query(AuditLog).filter(AuditLog.usuario_id.in_([supervisor.usuario_id, teleop.usuario_id])).delete(synchronize_session=False)
        db.query(ResultadoContacto).filter(ResultadoContacto.asignacion_id.in_(db.query(Asignacion.asignacion_id).filter(Asignacion.campania_id == campania.campania_id))).delete(synchronize_session=False)
        db.query(Asignacion).filter(Asignacion.campania_id == campania.campania_id).delete()
        db.query(Campania).filter(Campania.campania_id == campania.campania_id).delete()
        db.query(Consentimiento).filter(Consentimiento.cliente_id.in_([c.cliente_id for c in [opt_in, opt_out]])).delete(synchronize_session=False)
        db.query(Cliente).filter(Cliente.cliente_id.in_([c.cliente_id for c in [opt_in, opt_out]])).delete(synchronize_session=False)
        db.query(Usuario).filter(Usuario.usuario_id.in_([supervisor.usuario_id, teleop.usuario_id])).delete(synchronize_session=False)
        for rol in [rol_supervisor, rol_teleop]:
            db.query(RolPermiso).filter(RolPermiso.rol_id == rol.rol_id).delete()
            db.query(Rol).filter(Rol.rol_id == rol.rol_id).delete()
        db.commit()
        db.close()


@pytest.fixture
def scoped_scenario():
    """Users with only ONE of the two permissions that gate campaign-scoped
    read endpoints, to verify require_any_permission actually accepts either."""
    db = SessionLocal()
    prefix = f"asigscope_{uuid.uuid4().hex[:8]}"
    editor, rol_editor = _make_user(db, prefix, "editor", ["campanias:crear_editar"])
    consultor, rol_consultor = _make_user(db, prefix, "consultor", ["campanias:consultar"])
    teleop, rol_teleop = _make_user(db, prefix, "teleop", ["clientes:ver_asignados", "resultados:registrar"])
    opt_in = _make_cliente(db, "opt-in")
    campania = Campania(
        campania_id=uuid.uuid4(), nombre=f"{prefix}_campania", producto="deposito",
        fecha_inicio=datetime.date.today(), estado="activa",
    )
    db.add(campania)
    db.commit()

    asignacion = Asignacion(
        asignacion_id=uuid.uuid4(),
        cliente_id=opt_in.cliente_id,
        campania_id=campania.campania_id,
        usuario_id=teleop.usuario_id,
        estado_contacto="pendiente",
    )
    db.add(asignacion)
    db.commit()

    usuarios = [editor, consultor, teleop]
    roles = [rol_editor, rol_consultor, rol_teleop]
    try:
        yield {
            "editor": editor,
            "consultor": consultor,
            "teleop": teleop,
            "campania": campania,
            "asignacion": asignacion,
            "cliente": opt_in,
        }
    finally:
        db.query(AuditLog).filter(AuditLog.usuario_id.in_([u.usuario_id for u in usuarios])).delete(synchronize_session=False)
        db.query(ResultadoContacto).filter(ResultadoContacto.asignacion_id == asignacion.asignacion_id).delete()
        db.query(Asignacion).filter(Asignacion.asignacion_id == asignacion.asignacion_id).delete()
        db.query(Campania).filter(Campania.campania_id == campania.campania_id).delete()
        db.query(Consentimiento).filter(Consentimiento.cliente_id == opt_in.cliente_id).delete()
        db.query(Cliente).filter(Cliente.cliente_id == opt_in.cliente_id).delete()
        db.query(Usuario).filter(Usuario.usuario_id.in_([u.usuario_id for u in usuarios])).delete(synchronize_session=False)
        for rol in roles:
            db.query(RolPermiso).filter(RolPermiso.rol_id == rol.rol_id).delete()
            db.query(Rol).filter(Rol.rol_id == rol.rol_id).delete()
        db.commit()
        db.close()


def _login(username):
    resp = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_listar_asignaciones_campania_allows_crear_editar_only(scoped_scenario):
    token = _login(scoped_scenario["editor"].username)
    resp = client.get(
        f"/campanias/{scoped_scenario['campania'].campania_id}/asignaciones",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_listar_asignaciones_campania_allows_consultar_only(scoped_scenario):
    token = _login(scoped_scenario["consultor"].username)
    resp = client.get(
        f"/campanias/{scoped_scenario['campania'].campania_id}/asignaciones",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_supervisor_with_only_consultar_can_view_others_resultado(scoped_scenario):
    teleop_token = _login(scoped_scenario["teleop"].username)
    asignacion_id = scoped_scenario["asignacion"].asignacion_id
    posted = client.post(
        f"/asignaciones/{asignacion_id}/resultado",
        json={"resultado": "contactado", "observacion": "ok"},
        headers={"Authorization": f"Bearer {teleop_token}"},
    )
    assert posted.status_code == 201

    consultor_token = _login(scoped_scenario["consultor"].username)
    resp = client.get(
        f"/asignaciones/{asignacion_id}/resultado",
        headers={"Authorization": f"Bearer {consultor_token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["resultado"] == "contactado"


def test_teleop_with_only_registrar_cannot_view_others_resultado(scoped_scenario):
    """A user holding only resultados:registrar (no campaign-level view
    permission) must still be blocked from viewing a resultado that belongs
    to another user's asignacion."""
    teleop_token = _login(scoped_scenario["teleop"].username)
    asignacion_id = scoped_scenario["asignacion"].asignacion_id
    posted = client.post(
        f"/asignaciones/{asignacion_id}/resultado",
        json={"resultado": "contactado", "observacion": "ok"},
        headers={"Authorization": f"Bearer {teleop_token}"},
    )
    assert posted.status_code == 201

    db = SessionLocal()
    prefix = f"asigother_{uuid.uuid4().hex[:8]}"
    other_teleop, other_rol = _make_user(db, prefix, "other", ["resultados:registrar"])
    try:
        other_token = _login(other_teleop.username)
        resp = client.get(
            f"/asignaciones/{asignacion_id}/resultado",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403
    finally:
        db.query(AuditLog).filter(AuditLog.usuario_id == other_teleop.usuario_id).delete()
        db.query(Usuario).filter(Usuario.usuario_id == other_teleop.usuario_id).delete()
        db.query(RolPermiso).filter(RolPermiso.rol_id == other_rol.rol_id).delete()
        db.query(Rol).filter(Rol.rol_id == other_rol.rol_id).delete()
        db.commit()
        db.close()


def test_supervisor_assigns_only_opt_in_and_teleop_registers_result(scenario):
    supervisor_token = _login(scenario["supervisor"].username)
    teleop_token = _login(scenario["teleop"].username)
    opt_in, opt_out = scenario["clientes"]

    forbidden = client.post(
        "/asignaciones",
        json={
            "cliente_id": str(opt_out.cliente_id),
            "campania_id": str(scenario["campania"].campania_id),
            "usuario_id": str(scenario["teleop"].usuario_id),
        },
        headers={"Authorization": f"Bearer {supervisor_token}"},
    )
    assert forbidden.status_code == 409

    created = client.post(
        "/asignaciones",
        json={
            "cliente_id": str(opt_in.cliente_id),
            "campania_id": str(scenario["campania"].campania_id),
            "usuario_id": str(scenario["teleop"].usuario_id),
        },
        headers={"Authorization": f"Bearer {supervisor_token}"},
    )
    assert created.status_code == 201
    asignacion_id = created.json()["asignacion_id"]

    mine = client.get("/asignaciones/mias", headers={"Authorization": f"Bearer {teleop_token}"})
    assert mine.status_code == 200
    assert asignacion_id in [row["asignacion_id"] for row in mine.json()]

    result = client.post(
        f"/asignaciones/{asignacion_id}/resultado",
        json={"resultado": "contactado", "observacion": "Acepta recibir informacion"},
        headers={"Authorization": f"Bearer {teleop_token}"},
    )
    assert result.status_code == 201
    assert result.json()["resultado"] == "contactado"
