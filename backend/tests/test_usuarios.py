import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import AuditLog, Permiso, Rol, RolPermiso, Usuario
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


@pytest.fixture
def admin_scenario():
    db = SessionLocal()
    prefix = f"usertest_{uuid.uuid4().hex[:8]}"
    admin_rol = Rol(nombre=f"{prefix}_admin_rol", descripcion="x")
    managed_rol = Rol(nombre=f"{prefix}_managed_rol", descripcion="x")
    db.add(admin_rol)
    db.add(managed_rol)
    db.flush()
    db.add(RolPermiso(rol_id=admin_rol.rol_id, permiso_id=_make_permiso(db, "usuarios:gestionar").permiso_id))
    admin = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.admin", nombre_completo="Admin Test",
        email_corporativo=f"{prefix}.admin@bancoproyecto.pe", password_hash=hash_password(PASSWORD),
        rol_id=admin_rol.rol_id,
    )
    db.add(admin)
    db.commit()
    created_username = f"{prefix}.created"
    try:
        yield {"admin": admin, "admin_rol": admin_rol, "managed_rol": managed_rol, "created_username": created_username}
    finally:
        created = db.query(Usuario).filter(Usuario.username == created_username).first()
        if created:
            db.query(AuditLog).filter(AuditLog.usuario_id == created.usuario_id).delete()
            db.query(Usuario).filter(Usuario.usuario_id == created.usuario_id).delete()
        db.query(AuditLog).filter(AuditLog.usuario_id == admin.usuario_id).delete()
        db.query(Usuario).filter(Usuario.usuario_id == admin.usuario_id).delete()
        for rol in (admin_rol, managed_rol):
            db.query(RolPermiso).filter(RolPermiso.rol_id == rol.rol_id).delete()
            db.query(Rol).filter(Rol.rol_id == rol.rol_id).delete()
        db.commit()
        db.close()


@pytest.fixture
def teleoperadores_scenario():
    db = SessionLocal()
    prefix = f"telelist_{uuid.uuid4().hex[:8]}"
    supervisor_rol = Rol(nombre=f"{prefix}_supervisor_rol", descripcion="x")
    teleoperador_rol = Rol(nombre="teleoperador", descripcion="x")
    otro_rol = Rol(nombre=f"{prefix}_otro_rol", descripcion="x")
    existing_teleoperador_rol = db.query(Rol).filter(Rol.nombre == "teleoperador").first()
    if existing_teleoperador_rol is not None:
        teleoperador_rol = existing_teleoperador_rol
    else:
        db.add(teleoperador_rol)
    db.add(supervisor_rol)
    db.add(otro_rol)
    db.flush()
    db.add(RolPermiso(rol_id=supervisor_rol.rol_id, permiso_id=_make_permiso(db, "campanias:crear_editar").permiso_id))
    supervisor = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.supervisor", nombre_completo="Supervisor Test",
        email_corporativo=f"{prefix}.supervisor@bancoproyecto.pe", password_hash=hash_password(PASSWORD),
        rol_id=supervisor_rol.rol_id,
    )
    teleoperador = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.teleop", nombre_completo="Teleoperador Test",
        email_corporativo=f"{prefix}.teleop@bancoproyecto.pe", password_hash=hash_password(PASSWORD),
        rol_id=teleoperador_rol.rol_id,
    )
    otro = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.otro", nombre_completo="Otro Test",
        email_corporativo=f"{prefix}.otro@bancoproyecto.pe", password_hash=hash_password(PASSWORD),
        rol_id=otro_rol.rol_id,
    )
    db.add_all([supervisor, teleoperador, otro])
    db.commit()
    try:
        yield {
            "supervisor": supervisor,
            "teleoperador": teleoperador,
            "otro": otro,
            "supervisor_rol": supervisor_rol,
            "otro_rol": otro_rol,
            "teleoperador_rol_preexisted": existing_teleoperador_rol is not None,
            "teleoperador_rol": teleoperador_rol,
        }
    finally:
        db.query(AuditLog).filter(
            AuditLog.usuario_id.in_([supervisor.usuario_id, teleoperador.usuario_id, otro.usuario_id])
        ).delete(synchronize_session=False)
        db.query(Usuario).filter(
            Usuario.usuario_id.in_([supervisor.usuario_id, teleoperador.usuario_id, otro.usuario_id])
        ).delete(synchronize_session=False)
        db.query(RolPermiso).filter(RolPermiso.rol_id == supervisor_rol.rol_id).delete()
        db.query(Rol).filter(Rol.rol_id == supervisor_rol.rol_id).delete()
        db.query(Rol).filter(Rol.rol_id == otro_rol.rol_id).delete()
        if existing_teleoperador_rol is None:
            db.query(Rol).filter(Rol.rol_id == teleoperador_rol.rol_id).delete()
        db.commit()
        db.close()


def _login(username):
    resp = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_admin_creates_and_deactivates_user(admin_scenario):
    token = _login(admin_scenario["admin"].username)
    resp = client.post(
        "/usuarios",
        json={
            "username": admin_scenario["created_username"],
            "nombre_completo": "Usuario Creado",
            "email_corporativo": f"{admin_scenario['created_username']}@bancoproyecto.pe",
            "password": "NuevaClaveSegura123",
            "rol_id": admin_scenario["managed_rol"].rol_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    usuario_id = resp.json()["usuario_id"]

    weak = client.post(
        "/usuarios",
        json={
            "username": f"{admin_scenario['created_username']}.weak",
            "nombre_completo": "Usuario Debil",
            "email_corporativo": f"{admin_scenario['created_username']}.weak@bancoproyecto.pe",
            "password": "123",
            "rol_id": admin_scenario["managed_rol"].rol_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert weak.status_code == 422

    updated = client.patch(
        f"/usuarios/{usuario_id}/activo",
        json={"activo": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert updated.status_code == 200
    assert updated.json()["activo"] is False


def test_listar_teleoperadores_returns_only_teleoperador_role(teleoperadores_scenario):
    token = _login(teleoperadores_scenario["supervisor"].username)
    resp = client.get(
        "/usuarios/teleoperadores",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    usernames = [row["username"] for row in resp.json()]
    assert teleoperadores_scenario["teleoperador"].username in usernames
    assert teleoperadores_scenario["supervisor"].username not in usernames
    assert teleoperadores_scenario["otro"].username not in usernames
    for row in resp.json():
        assert row["rol_nombre"] == "teleoperador"
