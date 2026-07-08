import pytest
from unittest.mock import patch
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.security.jwt import create_access_token
from app.security.rbac import require_any_permission

app = FastAPI()


@app.get("/protegido")
def protegido(user: dict = Depends(require_any_permission("a:leer", "b:leer"))):
    return {"ok": True}


client = TestClient(app)


def test_allows_when_user_has_one_of_the_permissions():
    token = create_access_token("00000000-0000-0000-0000-000000000000", "rol_x", ["b:leer"])
    resp = client.get("/protegido", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_denies_when_user_has_none_of_the_permissions():
    with patch("app.security.rbac.write_audit_log"):
        token = create_access_token("00000000-0000-0000-0000-000000000000", "rol_x", ["c:leer"])
        resp = client.get("/protegido", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
