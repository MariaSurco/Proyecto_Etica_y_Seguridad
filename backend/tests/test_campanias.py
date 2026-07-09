import datetime
import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import AuditLog, Campania, Permiso, Rol, RolPermiso, Usuario
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
def supervisor():
    db = SessionLocal()
    prefix = f"camptest_{uuid.uuid4().hex[:8]}"
    rol = Rol(nombre=f"{prefix}_rol", descripcion="x")
    db.add(rol)
    db.flush()
    for nombre in ("campanias:crear_editar", "campanias:consultar"):
        db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=_make_permiso(db, nombre).permiso_id))
    user = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.supervisor", nombre_completo="Supervisor Test",
        email_corporativo=f"{prefix}@bancoproyecto.pe", password_hash=hash_password(PASSWORD),
        rol_id=rol.rol_id,
    )
    db.add(user)
    db.commit()
    try:
        yield {"user": user, "rol": rol}
    finally:
        db.query(AuditLog).filter(AuditLog.usuario_id == user.usuario_id).delete()
        db.query(Campania).filter(Campania.nombre.like(f"{prefix}%")).delete(synchronize_session=False)
        db.query(Usuario).filter(Usuario.usuario_id == user.usuario_id).delete()
        db.query(RolPermiso).filter(RolPermiso.rol_id == rol.rol_id).delete()
        db.query(Rol).filter(Rol.rol_id == rol.rol_id).delete()
        db.commit()
        db.close()


def _login(username):
    resp = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_create_and_update_campania(supervisor):
    token = _login(supervisor["user"].username)
    nombre = f"camptest_{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/campanias",
        json={
            "nombre": nombre,
            "producto": "deposito",
            "fecha_inicio": datetime.date.today().isoformat(),
            "estado": "planificada",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    campania_id = resp.json()["campania_id"]

    resp = client.patch(
        f"/campanias/{campania_id}",
        json={"estado": "activa"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "activa"
