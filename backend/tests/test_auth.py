import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol
from app.security.hashing import hash_password

client = TestClient(app)

def _make_role_and_user(db):
    rol = Rol(nombre="teleoperador_test", descripcion="x")
    db.add(rol); db.flush()
    user = Usuario(
        usuario_id=uuid.uuid4(), username="carlos.test", nombre_completo="Carlos Test",
        email_corporativo="carlos.test@bancoproyecto.pe",
        password_hash=hash_password("Sup3rSecret!Pass"), rol_id=rol.rol_id,
    )
    db.add(user); db.commit()
    return user

def test_login_success_returns_jwt():
    db = SessionLocal()
    _make_role_and_user(db)
    db.close()
    resp = client.post("/auth/login", data={"username": "carlos.test", "password": "Sup3rSecret!Pass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login_wrong_password_returns_401():
    resp = client.post("/auth/login", data={"username": "carlos.test", "password": "wrong"})
    assert resp.status_code == 401

def test_protected_endpoint_requires_token():
    resp = client.get("/auditoria/logs")
    assert resp.status_code == 401
