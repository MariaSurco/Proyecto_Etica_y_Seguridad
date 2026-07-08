import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, AuditLog
from app.security.hashing import hash_password

client = TestClient(app)

ROL_NOMBRE = "teleoperador_test"
USERNAME = "carlos.test"


def _cleanup(db):
    """Delete the test usuario's audit_log rows first (FK to usuario), then
    the usuario itself (FK to rol), then the test rol."""
    user = db.query(Usuario).filter(Usuario.username == USERNAME).first()
    if user:
        db.query(AuditLog).filter(AuditLog.usuario_id == user.usuario_id).delete()
    db.query(Usuario).filter(Usuario.username == USERNAME).delete()
    db.query(Rol).filter(Rol.nombre == ROL_NOMBRE).delete()
    db.commit()


def _make_role_and_user(db):
    rol = Rol(nombre=ROL_NOMBRE, descripcion="x")
    db.add(rol); db.flush()
    user = Usuario(
        usuario_id=uuid.uuid4(), username=USERNAME, nombre_completo="Carlos Test",
        email_corporativo="carlos.test@bancoproyecto.pe",
        password_hash=hash_password("Sup3rSecret!Pass"), rol_id=rol.rol_id,
    )
    db.add(user); db.commit()
    return user


@pytest.fixture
def test_user():
    """Creates the teleoperador_test role + carlos.test user for the duration
    of a test, then tears both rows down regardless of pass/fail. This keeps
    the suite repeatable against the persistent Railway dev database, which
    has no separate test instance and no per-test transaction rollback."""
    db = SessionLocal()
    # Defensive cleanup in case a previous run (e.g. before this fixture
    # existed, or an interrupted run) left stale rows behind.
    _cleanup(db)
    user = _make_role_and_user(db)
    try:
        yield user
    finally:
        _cleanup(db)
        db.close()


def test_login_success_returns_jwt(test_user):
    resp = client.post("/auth/login", data={"username": "carlos.test", "password": "Sup3rSecret!Pass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login_wrong_password_returns_401(test_user):
    resp = client.post("/auth/login", data={"username": "carlos.test", "password": "wrong"})
    assert resp.status_code == 401

def test_protected_endpoint_requires_token(test_user):
    resp = client.get("/auditoria/logs")
    assert resp.status_code == 401
