import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, Permiso, RolPermiso, AuditLog
from app.security.hashing import hash_password

client = TestClient(app)

ROL_NOMBRE = "auditor_test"
USERNAME = "ana.auditora.test"
PERMISO_NOMBRE = "auditoria:consultar"


def _cleanup(db):
    user = db.query(Usuario).filter(Usuario.username == USERNAME).first()
    if user:
        db.query(AuditLog).filter(AuditLog.usuario_id == user.usuario_id).delete()
    db.query(Usuario).filter(Usuario.username == USERNAME).delete()
    rol = db.query(Rol).filter(Rol.nombre == ROL_NOMBRE).first()
    if rol:
        db.query(RolPermiso).filter(RolPermiso.rol_id == rol.rol_id).delete()
        db.query(Rol).filter(Rol.rol_id == rol.rol_id).delete()
    db.commit()


@pytest.fixture
def auditor_user():
    db = SessionLocal()
    _cleanup(db)
    permiso = db.query(Permiso).filter(Permiso.nombre == PERMISO_NOMBRE).first()
    if permiso is None:
        permiso = Permiso(nombre=PERMISO_NOMBRE, recurso="auditoria", accion="consultar")
        db.add(permiso)
        db.flush()
    rol = Rol(nombre=ROL_NOMBRE, descripcion="x")
    db.add(rol)
    db.flush()
    db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=permiso.permiso_id))
    user = Usuario(
        usuario_id=uuid.uuid4(), username=USERNAME, nombre_completo="Ana Auditora",
        email_corporativo="ana.auditora.test@bancoproyecto.pe",
        password_hash=hash_password("Sup3rSecret!Pass"), rol_id=rol.rol_id,
    )
    db.add(user)
    db.commit()
    try:
        yield user
    finally:
        _cleanup(db)
        db.close()


def _login(username: str) -> str:
    resp = client.post("/auth/login", data={"username": username, "password": "Sup3rSecret!Pass"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_auditoria_logs_contains_login_event_and_filters_by_accion(auditor_user):
    token = _login(USERNAME)
    resp = client.get(
        "/auditoria/logs",
        params={"accion": "login_exitoso", "usuario_id": str(auditor_user.usuario_id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert all(entry["accion"] == "login_exitoso" for entry in body)
    assert all(entry["usuario_id"] == str(auditor_user.usuario_id) for entry in body)
