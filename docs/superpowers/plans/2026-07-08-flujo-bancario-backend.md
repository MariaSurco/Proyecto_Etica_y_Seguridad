# Flujo Bancario Backend (Auditoría, Clientes, Campañas, Asignaciones, Usuarios) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar la brecha entre el modelo de datos ya migrado (cliente, consentimiento, campania, asignacion, resultado_contacto, usuario, rol, permiso, audit_log) y el flujo funcional descrito en el PDF parcial (sección 9.1.2 "Flujos funcionales principales" y Tabla 9 "Casos de uso"): auditoría real, consulta de clientes elegibles filtrada por consentimiento, gestión de consentimiento, campañas, asignación de clientes a teleoperadores, registro de resultado de contacto y gestión de usuarios/roles.

**Architecture:** FastAPI routers nuevos montados en `app/main.py`, reutilizando `get_db` (SQLAlchemy Session), `require_permission`/`get_current_user` (RBAC vía JWT) y `write_audit_log` (que este plan implementa de verdad). El enmascaramiento de PII por rol vive en un helper nuevo `app/security/masking.py` que descifra vía `decrypt_field` solo cuando el rol lo permite. Cada escritura de negocio relevante (login ya lo hace; consentimiento, asignación, resultado, gestión de usuarios) llama a `write_audit_log`.

**Tech Stack:** FastAPI, SQLAlchemy ORM, Pydantic, pytest + `fastapi.testclient.TestClient`, PostgreSQL (Railway dev DB, sin instancia de test separada — los tests limpian sus propias filas, siguiendo el patrón de `tests/test_auth.py`).

## Estado de implementación al 2026-07-08

- Implementado: auditoría real, endpoint `/auditoria/logs`, `require_any_permission`, enmascaramiento por rol, router de clientes, consentimiento, campañas, asignaciones, resultados de contacto y administración básica de usuarios/roles/permisos.
- Tests agregados/validados: `test_consentimientos.py`, `test_campanias.py`, `test_asignaciones.py`, `test_usuarios.py`, además de auditoría/clientes existentes.
- Verificación parcial backend: `./.venv/bin/python -m pytest tests/test_audit_logger.py tests/test_auditoria_router.py tests/test_clientes.py tests/test_consentimientos.py tests/test_campanias.py tests/test_asignaciones.py tests/test_usuarios.py -q` pasa con 11 tests.
- Verificación completa backend: `./.venv/bin/python -m pytest -q` queda en 36 passed / 1 failed. El fallo está en `tests/test_dp.py::test_dp_model_returns_metrics_and_baseline` por incompatibilidad externa `diffprivlib`/SciPy (`fmin_l_bfgs_b()` ya no acepta `iprint`), no por el flujo bancario.
- Frontend mínimo implementado en `frontend/src/App.tsx`: login JWT, navegación por permisos, clientes/consentimiento, campañas, asignaciones, resultados, usuarios y auditoría.
- Infraestructura demo agregada: Dockerfiles, `infra/docker-compose.yml`, `infra/nginx.conf`, certificados autofirmados, scripts de backup/restore y `docs/GUIA_OPERATIVA.md`.
- Verificación frontend: `npm run build` pasa.
- Servidores locales levantados: backend `http://127.0.0.1:8000`, frontend `http://127.0.0.1:5173`.
- No se hicieron commits.

## Global Constraints

- No modificar el esquema de columnas de los modelos existentes (`app/models/*.py`) — ya migrados con Alembic.
- Todo endpoint que exponga o modifique datos de `cliente` debe filtrar/enmascarar por rol (principio de mínimo privilegio, PDF §9.1.1 y Tabla 8).
- Toda acción de negocio relevante (crear/editar consentimiento, campaña, asignación, resultado, usuario) debe generar una fila en `audit_log` vía `write_audit_log` (PDF §9.1.2 punto 5, RF-13).
- Los clientes con `consentimiento.estado != 'opt-in'` nunca deben aparecer como elegibles ni ser asignables a una campaña (PDF §10.4, RF-06, RF-11).
- Los nuevos routers deben registrarse en `app/main.py` con `app.include_router(...)`.
- Los tests nuevos siguen el patrón de `backend/tests/test_auth.py`: crean sus propias filas (rol/usuario/permiso de prueba) y las eliminan en un `finally`, porque corren contra la base Railway persistente compartida.
- No usar `git commit` salvo que el usuario lo pida explícitamente durante la ejecución.

---

## File Structure

- `backend/app/audit/logger.py` — implementación real de `write_audit_log` (Modify).
- `backend/app/routers/auditoria.py` — endpoint `/auditoria/logs` con filtros reales (Modify).
- `backend/app/security/rbac.py` — agrega `require_any_permission` (Modify).
- `backend/app/security/masking.py` — enmascaramiento de `Cliente` por rol (Create).
- `backend/app/schemas/clientes.py`, `campanias.py`, `asignaciones.py`, `usuarios.py`, `auditoria.py` — Pydantic request/response models (Create).
- `backend/app/routers/clientes.py`, `consentimientos.py`, `campanias.py`, `asignaciones.py`, `usuarios.py` — nuevos routers (Create).
- `backend/app/main.py` — registra los routers nuevos (Modify, una vez por tarea).
- `backend/tests/test_audit_logger.py`, `test_auditoria_router.py`, `test_clientes.py`, `test_consentimientos.py`, `test_campanias.py`, `test_asignaciones.py`, `test_usuarios.py` — nuevos tests (Create).

---

### Task 1: Auditoría real (logger + endpoint con filtros)

**Files:**
- Modify: `backend/app/audit/logger.py`
- Modify: `backend/app/routers/auditoria.py`
- Create: `backend/app/schemas/auditoria.py`
- Create: `backend/tests/test_audit_logger.py`
- Create: `backend/tests/test_auditoria_router.py`

**Interfaces:**
- Consumes: `app.database.SessionLocal`, `app.models.AuditLog`, `app.security.rbac.require_permission`.
- Produces: `write_audit_log(*, usuario_id: str | None, accion: str, recurso: str, recurso_id: str | None, ip_origen: str | None, resultado: str, detalle: str | None) -> None` (misma firma que ya consumen `auth.py` y `rbac.py`, ahora persiste de verdad). `GET /auditoria/logs` acepta query params opcionales `usuario_id`, `accion`, `recurso`, `resultado` y devuelve una lista de dicts con las claves `log_id, usuario_id, accion, recurso, recurso_id, ip_origen, resultado, detalle, timestamp_evento`.

- [ ] **Step 1: Escribir el test que falla para el logger**

```python
# backend/tests/test_audit_logger.py
import uuid
from app.database import SessionLocal
from app.models import AuditLog
from app.audit.logger import write_audit_log


def test_write_audit_log_persists_row_with_null_user():
    marker = f"test-marker-{uuid.uuid4()}"
    write_audit_log(
        usuario_id=None, accion="evento_test", recurso="test",
        recurso_id=marker, ip_origen="127.0.0.1", resultado="exito", detalle=None,
    )
    db = SessionLocal()
    try:
        row = db.query(AuditLog).filter(AuditLog.recurso_id == marker).first()
        assert row is not None
        assert row.accion == "evento_test"
        assert row.usuario_id is None
        assert row.resultado == "exito"
    finally:
        db.query(AuditLog).filter(AuditLog.recurso_id == marker).delete()
        db.commit()
        db.close()
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_audit_logger.py -v`
Expected: FAIL — el stub actual de `write_audit_log` no escribe nada, así que `row is None` y el `assert row is not None` falla.

- [ ] **Step 3: Implementar el logger real**

```python
# backend/app/audit/logger.py
import uuid
from app.database import SessionLocal
from app.models import AuditLog


def write_audit_log(
    *, usuario_id, accion: str, recurso: str, recurso_id,
    ip_origen, resultado: str, detalle,
) -> None:
    db = SessionLocal()
    try:
        log = AuditLog(
            log_id=uuid.uuid4(),
            usuario_id=uuid.UUID(str(usuario_id)) if usuario_id else None,
            accion=accion,
            recurso=recurso,
            recurso_id=str(recurso_id) if recurso_id is not None else None,
            ip_origen=ip_origen,
            resultado=resultado,
            detalle=detalle,
        )
        db.add(log)
        db.commit()
    finally:
        db.close()
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_audit_logger.py -v`
Expected: PASS

- [ ] **Step 5: Escribir el test que falla para el endpoint `/auditoria/logs`**

```python
# backend/tests/test_auditoria_router.py
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, Permiso, RolPermiso
from app.security.hashing import hash_password

client = TestClient(app)

ROL_NOMBRE = "auditor_test"
USERNAME = "ana.auditora.test"
PERMISO_NOMBRE = "auditoria:consultar"


def _cleanup(db):
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
```

- [ ] **Step 6: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_auditoria_router.py -v`
Expected: FAIL — `/auditoria/logs` siempre devuelve `[]`, así que `len(body) >= 1` falla.

- [ ] **Step 7: Implementar el endpoint con filtros reales**

```python
# backend/app/schemas/auditoria.py
from datetime import datetime
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    log_id: str
    usuario_id: str | None
    accion: str
    recurso: str
    recurso_id: str | None
    ip_origen: str | None
    resultado: str
    detalle: str | None
    timestamp_evento: datetime | None
```

```python
# backend/app/routers/auditoria.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditLog
from app.security.rbac import require_permission
from app.schemas.auditoria import AuditLogOut

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("/logs", response_model=list[AuditLogOut])
def list_logs(
    usuario_id: str | None = None,
    accion: str | None = None,
    recurso: str | None = None,
    resultado: str | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("auditoria:consultar")),
):
    query = db.query(AuditLog)
    if usuario_id:
        query = query.filter(AuditLog.usuario_id == usuario_id)
    if accion:
        query = query.filter(AuditLog.accion == accion)
    if recurso:
        query = query.filter(AuditLog.recurso == recurso)
    if resultado:
        query = query.filter(AuditLog.resultado == resultado)
    logs = query.order_by(AuditLog.timestamp_evento.desc()).limit(200).all()
    return [
        AuditLogOut(
            log_id=str(l.log_id),
            usuario_id=str(l.usuario_id) if l.usuario_id else None,
            accion=l.accion, recurso=l.recurso, recurso_id=l.recurso_id,
            ip_origen=l.ip_origen, resultado=l.resultado, detalle=l.detalle,
            timestamp_evento=l.timestamp_evento,
        )
        for l in logs
    ]
```

- [ ] **Step 8: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_auditoria_router.py tests/test_audit_logger.py tests/test_auth.py -v`
Expected: PASS en los tres archivos (incluye `test_auth.py`, que ahora ejercita el logger real en vez del stub).

- [ ] **Step 9: Commit**

```bash
git add backend/app/audit/logger.py backend/app/routers/auditoria.py backend/app/schemas/auditoria.py backend/tests/test_audit_logger.py backend/tests/test_auditoria_router.py
git commit -m "feat: implement real audit logging and /auditoria/logs filtering"
```

---

### Task 2: `require_any_permission` en RBAC

**Files:**
- Modify: `backend/app/security/rbac.py`
- Create: `backend/tests/test_rbac.py`

**Interfaces:**
- Consumes: `get_current_user` (ya existente en el mismo archivo).
- Produces: `require_any_permission(*permiso_nombres: str)` — dependencia FastAPI que autoriza si el usuario tiene **al menos uno** de los permisos dados; si no tiene ninguno, responde 403 y registra `acceso_denegado` en auditoría (mismo comportamiento que `require_permission`). La usarán los routers de clientes y campañas en las Tasks 3 y 5.

- [ ] **Step 1: Escribir el test que falla**

```python
# backend/tests/test_rbac.py
import pytest
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
    token = create_access_token("00000000-0000-0000-0000-000000000000", "rol_x", ["c:leer"])
    resp = client.get("/protegido", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_rbac.py -v`
Expected: FAIL con `ImportError: cannot import name 'require_any_permission'`.

- [ ] **Step 3: Implementar**

```python
# backend/app/security/rbac.py (agregar al final del archivo, después de require_permission)
def require_any_permission(*permiso_nombres: str):
    def dependency(request: Request, user: dict = Depends(get_current_user)) -> dict:
        user_permisos = user.get("permisos", [])
        if not any(p in user_permisos for p in permiso_nombres):
            write_audit_log(
                usuario_id=user.get("sub"), accion="acceso_denegado",
                recurso=",".join(permiso_nombres), recurso_id=None,
                ip_origen=request.client.host if request.client else None,
                resultado="denegado", detalle=f"Falta uno de: {permiso_nombres}",
            )
            raise HTTPException(status_code=403, detail="No autorizado para este recurso")
        return user
    return dependency
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_rbac.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/security/rbac.py backend/tests/test_rbac.py
git commit -m "feat: add require_any_permission RBAC dependency"
```

---

### Task 3: Enmascaramiento de `Cliente` por rol

**Files:**
- Create: `backend/app/security/masking.py`
- Create: `backend/tests/test_masking.py`

**Interfaces:**
- Consumes: `app.models.Cliente`, `app.security.crypto.decrypt_field`.
- Produces: `mask_cliente(cliente: Cliente, rol_nombre: str) -> dict`. Reglas:
  - `administrador` / `supervisor`: incluye PII descifrada (`nombre`, `dni`, `email`, `telefono`, `direccion`) + todos los campos demográficos/financieros/operacionales del dataset.
  - `analista`: sin PII (no incluye `nombre`, `dni`, `email`, `telefono`, `direccion`), sí incluye campos demográficos/financieros/operacionales.
  - `teleoperador`: solo `nombre` y `telefono` descifrados (los necesarios para contactar) + `cliente_id`; sin `dni`, `email`, `direccion`, `balance`, ni el resto de columnas financieras.
  - cualquier otro rol: solo `cliente_id` (defensivo; en la práctica los routers ya bloquean el acceso antes de llegar aquí).
  - En todos los casos se incluye `cliente_id` (str) y `deposit`.

- [ ] **Step 1: Escribir el test que falla**

```python
# backend/tests/test_masking.py
import uuid
from app.models import Cliente
from app.security.crypto import encrypt_field
from app.security.masking import mask_cliente


def _cliente():
    return Cliente(
        cliente_id=uuid.uuid4(),
        nombre_cifrado=encrypt_field("Juan Perez"),
        dni_cifrado=encrypt_field("12345678"),
        email_cifrado=encrypt_field("juan@example.com"),
        telefono_cifrado=encrypt_field("+51999999999"),
        direccion_cifrada=encrypt_field("Av. Siempre Viva 123"),
        age=41, job="management", marital="married", education="tertiary",
        default_credit="no", balance=1200.50, housing="yes", loan="no",
        contact="cellular", day=5, month="may", duration=120, campaign=1,
        pdays=-1, previous=0, poutcome="unknown", deposit="yes",
    )


def test_admin_sees_full_pii():
    out = mask_cliente(_cliente(), "administrador")
    assert out["nombre"] == "Juan Perez"
    assert out["dni"] == "12345678"
    assert out["balance"] == 1200.50


def test_analista_sees_no_pii():
    out = mask_cliente(_cliente(), "analista")
    assert "nombre" not in out
    assert "dni" not in out
    assert "email" not in out
    assert out["job"] == "management"
    assert out["balance"] == 1200.50


def test_teleoperador_sees_only_contact_fields():
    out = mask_cliente(_cliente(), "teleoperador")
    assert out["nombre"] == "Juan Perez"
    assert out["telefono"] == "+51999999999"
    assert "dni" not in out
    assert "balance" not in out
    assert "email" not in out
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_masking.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.security.masking'`.

- [ ] **Step 3: Implementar**

```python
# backend/app/security/masking.py
from app.models import Cliente
from app.security.crypto import decrypt_field

_DEMOGRAPHIC_FIELDS = [
    "age", "job", "marital", "education", "default_credit", "balance",
    "housing", "loan", "contact", "day", "month", "duration", "campaign",
    "pdays", "previous", "poutcome", "deposit",
]


def _demographic_dict(cliente: Cliente) -> dict:
    return {field: getattr(cliente, field) for field in _DEMOGRAPHIC_FIELDS}


def mask_cliente(cliente: Cliente, rol_nombre: str) -> dict:
    base = {"cliente_id": str(cliente.cliente_id), "deposit": cliente.deposit}

    if rol_nombre in ("administrador", "supervisor"):
        return {
            **base,
            "nombre": decrypt_field(cliente.nombre_cifrado),
            "dni": decrypt_field(cliente.dni_cifrado),
            "email": decrypt_field(cliente.email_cifrado),
            "telefono": decrypt_field(cliente.telefono_cifrado),
            "direccion": decrypt_field(cliente.direccion_cifrada),
            **_demographic_dict(cliente),
        }

    if rol_nombre == "analista":
        return {**base, **_demographic_dict(cliente)}

    if rol_nombre == "teleoperador":
        return {
            **base,
            "nombre": decrypt_field(cliente.nombre_cifrado),
            "telefono": decrypt_field(cliente.telefono_cifrado),
        }

    return base
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_masking.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/security/masking.py backend/tests/test_masking.py
git commit -m "feat: add role-based cliente masking helper"
```

---

### Task 4: Router de clientes (`/clientes/elegibles`, `/clientes/{id}`, `/clientes/asignados`)

**Files:**
- Create: `backend/app/routers/clientes.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_clientes.py`

**Interfaces:**
- Consumes: `mask_cliente` (Task 3), `require_any_permission`/`get_current_user` (Task 2 y `rbac.py`), `write_audit_log`, modelos `Cliente`, `Consentimiento`, `Asignacion`.
- Produces:
  - `GET /clientes/elegibles` → requiere `clientes:ver_sensible` o `clientes:ver_parcial`; devuelve solo clientes con `consentimiento.estado == 'opt-in'`, enmascarados según el rol del token.
  - `GET /clientes/asignados` → requiere `clientes:ver_asignados`; devuelve los clientes asignados (tabla `asignacion`) al `usuario_id` del token, enmascarados.
  - `GET /clientes/{cliente_id}` → cualquier usuario con `clientes:ver_sensible`, `clientes:ver_parcial` o `clientes:ver_asignados`; si el rol es `teleoperador`, exige que exista una fila en `asignacion` para ese cliente y ese usuario, si no → 403. 404 si el cliente no existe.
  - Todas las consultas registran auditoría vía `write_audit_log(accion="consulta_clientes...", recurso="clientes", ...)`.

- [ ] **Step 1: Escribir el test que falla**

```python
# backend/tests/test_clientes.py
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, Permiso, RolPermiso, Cliente, Consentimiento, Asignacion
from app.security.hashing import hash_password
from app.security.crypto import encrypt_field

client = TestClient(app)

PASSWORD = "Sup3rSecret!Pass"


def _make_permiso(db, nombre, recurso, accion):
    p = db.query(Permiso).filter(Permiso.nombre == nombre).first()
    if p is None:
        p = Permiso(nombre=nombre, recurso=recurso, accion=accion)
        db.add(p)
        db.flush()
    return p


def _make_user(db, rol_nombre, username, permiso_nombres):
    rol = Rol(nombre=rol_nombre, descripcion="x")
    db.add(rol)
    db.flush()
    for nombre in permiso_nombres:
        permiso = _make_permiso(db, nombre, nombre.split(":")[0], nombre.split(":")[1])
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
    analista, rol_analista = _make_user(db, f"{prefix}_analista", f"{prefix}.analista", ["clientes:ver_parcial"])
    teleop, rol_teleop = _make_user(db, f"{prefix}_teleop", f"{prefix}.teleop", ["clientes:ver_asignados"])
    opt_in = _make_cliente(db, "opt-in")
    opt_out = _make_cliente(db, "opt-out")
    asignacion = Asignacion(asignacion_id=uuid.uuid4(), cliente_id=opt_in.cliente_id, campania_id=uuid.uuid4(), usuario_id=teleop.usuario_id)
    # campania_id no tiene FK NOT NULL a una campania existente en este modelo simplificado de test;
    # se crea una campaña mínima para respetar la FK.
    from app.models import Campania
    import datetime
    campania = Campania(campania_id=asignacion.campania_id, nombre="Campania Test", producto="deposito",
                         fecha_inicio=datetime.date.today(), estado="activa")
    db.add(campania)
    db.add(asignacion)
    db.commit()
    try:
        yield {"analista": analista, "teleop": teleop, "opt_in": opt_in, "opt_out": opt_out}
    finally:
        db.query(Asignacion).filter(Asignacion.usuario_id == teleop.usuario_id).delete()
        db.query(Campania).filter(Campania.campania_id == campania.campania_id).delete()
        db.query(Consentimiento).filter(Consentimiento.cliente_id.in_([opt_in.cliente_id, opt_out.cliente_id])).delete(synchronize_session=False)
        db.query(Cliente).filter(Cliente.cliente_id.in_([opt_in.cliente_id, opt_out.cliente_id])).delete(synchronize_session=False)
        for rol in (rol_analista, rol_teleop):
            db.query(Usuario).filter(Usuario.rol_id == rol.rol_id).delete()
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
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_clientes.py -v`
Expected: FAIL — `404 Not Found` en `/clientes/elegibles` porque el router aún no existe.

- [ ] **Step 3: Implementar el router**

```python
# backend/app/schemas/clientes.py
from pydantic import BaseModel


class ClienteOut(BaseModel):
    cliente_id: str
    deposit: str | None = None

    class Config:
        extra = "allow"
```

```python
# backend/app/routers/clientes.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Consentimiento, Asignacion
from app.security.rbac import require_any_permission, get_current_user
from app.security.masking import mask_cliente
from app.audit.logger import write_audit_log

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("/elegibles")
def listar_elegibles(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_sensible", "clientes:ver_parcial")),
):
    rows = (
        db.query(Cliente)
        .join(Consentimiento, Consentimiento.cliente_id == Cliente.cliente_id)
        .filter(Consentimiento.estado == "opt-in")
        .all()
    )
    resultado = [mask_cliente(c, user["rol"]) for c in rows]
    write_audit_log(
        usuario_id=user["sub"], accion="consulta_clientes_elegibles", recurso="clientes",
        recurso_id=None, ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"{len(resultado)} resultados",
    )
    return resultado


@router.get("/asignados")
def listar_asignados(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_asignados")),
):
    rows = (
        db.query(Cliente)
        .join(Asignacion, Asignacion.cliente_id == Cliente.cliente_id)
        .filter(Asignacion.usuario_id == user["sub"])
        .all()
    )
    resultado = [mask_cliente(c, user["rol"]) for c in rows]
    write_audit_log(
        usuario_id=user["sub"], accion="consulta_clientes_asignados", recurso="clientes",
        recurso_id=None, ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"{len(resultado)} resultados",
    )
    return resultado


@router.get("/{cliente_id}")
def obtener_cliente(
    cliente_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    permisos = user.get("permisos", [])
    permisos_validos = {"clientes:ver_sensible", "clientes:ver_parcial", "clientes:ver_asignados"}
    if not permisos_validos & set(permisos):
        raise HTTPException(status_code=403, detail="No autorizado para este recurso")

    cliente = db.query(Cliente).filter(Cliente.cliente_id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    solo_asignados = "clientes:ver_sensible" not in permisos and "clientes:ver_parcial" not in permisos
    if solo_asignados:
        asignado = (
            db.query(Asignacion)
            .filter(Asignacion.cliente_id == cliente_id, Asignacion.usuario_id == user["sub"])
            .first()
        )
        if asignado is None:
            write_audit_log(
                usuario_id=user["sub"], accion="acceso_denegado", recurso="clientes",
                recurso_id=str(cliente_id), ip_origen=request.client.host if request.client else None,
                resultado="denegado", detalle="Cliente no asignado al usuario",
            )
            raise HTTPException(status_code=403, detail="Cliente no asignado")

    write_audit_log(
        usuario_id=user["sub"], accion="consulta_cliente_detalle", recurso="clientes",
        recurso_id=str(cliente_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=None,
    )
    return mask_cliente(cliente, user["rol"])
```

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, auditoria, dp, clientes

app = FastAPI(title="Sistema Seguro de Apoyo a Campañas Bancarias")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(auditoria.router)
app.include_router(dp.router)
app.include_router(clientes.router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_clientes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/clientes.py backend/app/schemas/clientes.py backend/app/main.py backend/tests/test_clientes.py
git commit -m "feat: add clientes router with consent filtering and role masking"
```

---

### Task 5: Router de consentimiento

**Files:**
- Create: `backend/app/schemas/consentimientos.py`
- Create: `backend/app/routers/consentimientos.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_consentimientos.py`

**Interfaces:**
- Consumes: `require_any_permission` (Task 2), `write_audit_log`, modelos `Cliente`, `Consentimiento`.
- Produces:
  - `GET /clientes/{cliente_id}/consentimiento` → requiere `clientes:ver_sensible` o `clientes:ver_parcial`; devuelve `{cliente_id, estado, canal, fecha_actualizacion}`. 404 si no existe consentimiento para ese cliente.
  - `PATCH /clientes/{cliente_id}/consentimiento` → requiere `clientes:ver_sensible` (solo admin/supervisor); body `{"estado": "opt-in"|"opt-out"|"no informado", "canal": str | None}`; actualiza `estado`, `canal`, `fecha_actualizacion` (server-side `func.now()` vía `onupdate`), `actualizado_por = user["sub"]`; registra auditoría `accion="actualizar_consentimiento"`.

- [ ] **Step 1: Escribir el test que falla**

```python
# backend/tests/test_consentimientos.py
import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, Permiso, RolPermiso, Cliente, Consentimiento
from app.security.hashing import hash_password
from app.security.crypto import encrypt_field

client = TestClient(app)
PASSWORD = "Sup3rSecret!Pass"


def _make_permiso(db, nombre):
    p = db.query(Permiso).filter(Permiso.nombre == nombre).first()
    if p is None:
        p = Permiso(nombre=nombre, recurso=nombre.split(":")[0], accion=nombre.split(":")[1])
        db.add(p)
        db.flush()
    return p


@pytest.fixture
def scenario():
    db = SessionLocal()
    prefix = f"constest_{uuid.uuid4().hex[:8]}"
    rol = Rol(nombre=f"{prefix}_supervisor", descripcion="x")
    db.add(rol)
    db.flush()
    permiso = _make_permiso(db, "clientes:ver_sensible")
    db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=permiso.permiso_id))
    user = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.supervisor", nombre_completo="Supervisor Test",
        email_corporativo=f"{prefix}.supervisor@bancoproyecto.pe",
        password_hash=hash_password(PASSWORD), rol_id=rol.rol_id,
    )
    db.add(user)
    cliente = Cliente(
        cliente_id=uuid.uuid4(), nombre_cifrado=encrypt_field("X"), dni_cifrado=encrypt_field("1"),
        email_cifrado=encrypt_field("x@x.pe"), telefono_cifrado=encrypt_field("+51900000001"),
        direccion_cifrada=encrypt_field("dir"), age=25, job="student", marital="single",
        education="secondary", default_credit="no", balance=0.0, housing="no", loan="no",
        contact="cellular", day=1, month="jan", duration=10, campaign=1, pdays=-1, previous=0,
        poutcome="unknown", deposit="no",
    )
    db.add(cliente)
    db.flush()
    consentimiento = Consentimiento(consentimiento_id=uuid.uuid4(), cliente_id=cliente.cliente_id, estado="no informado")
    db.add(consentimiento)
    db.commit()
    try:
        yield {"user": user, "cliente": cliente}
    finally:
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


def test_patch_consentimiento_updates_estado_and_excludes_from_elegibles(scenario):
    token = _login(scenario["user"].username)
    headers = {"Authorization": f"Bearer {token}"}
    cliente_id = scenario["cliente"].cliente_id

    resp = client.patch(
        f"/clientes/{cliente_id}/consentimiento",
        json={"estado": "opt-in", "canal": "email"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "opt-in"

    resp_get = client.get(f"/clientes/{cliente_id}/consentimiento", headers=headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["estado"] == "opt-in"

    resp_out = client.patch(
        f"/clientes/{cliente_id}/consentimiento",
        json={"estado": "opt-out", "canal": "email"},
        headers=headers,
    )
    assert resp_out.status_code == 200

    resp_elegibles = client.get("/clientes/elegibles", headers=headers)
    ids = [c["cliente_id"] for c in resp_elegibles.json()]
    assert str(cliente_id) not in ids
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_consentimientos.py -v`
Expected: FAIL con `404 Not Found` en el `PATCH` porque la ruta no existe.

- [ ] **Step 3: Implementar**

```python
# backend/app/schemas/consentimientos.py
from datetime import datetime
from pydantic import BaseModel


class ConsentimientoUpdate(BaseModel):
    estado: str
    canal: str | None = None


class ConsentimientoOut(BaseModel):
    cliente_id: str
    estado: str
    canal: str | None
    fecha_actualizacion: datetime | None
```

```python
# backend/app/routers/consentimientos.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Consentimiento
from app.security.rbac import require_any_permission
from app.audit.logger import write_audit_log
from app.schemas.consentimientos import ConsentimientoUpdate, ConsentimientoOut

router = APIRouter(prefix="/clientes", tags=["consentimiento"])

ESTADOS_VALIDOS = {"opt-in", "opt-out", "no informado"}


@router.get("/{cliente_id}/consentimiento", response_model=ConsentimientoOut)
def obtener_consentimiento(
    cliente_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_sensible", "clientes:ver_parcial")),
):
    cons = db.query(Consentimiento).filter(Consentimiento.cliente_id == cliente_id).first()
    if cons is None:
        raise HTTPException(status_code=404, detail="Consentimiento no encontrado")
    return ConsentimientoOut(
        cliente_id=str(cons.cliente_id), estado=cons.estado, canal=cons.canal,
        fecha_actualizacion=cons.fecha_actualizacion,
    )


@router.patch("/{cliente_id}/consentimiento", response_model=ConsentimientoOut)
def actualizar_consentimiento(
    cliente_id: str,
    body: ConsentimientoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_sensible")),
):
    if body.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=422, detail=f"estado debe ser uno de {ESTADOS_VALIDOS}")
    cons = db.query(Consentimiento).filter(Consentimiento.cliente_id == cliente_id).first()
    if cons is None:
        raise HTTPException(status_code=404, detail="Consentimiento no encontrado")

    estado_anterior = cons.estado
    cons.estado = body.estado
    cons.canal = body.canal
    cons.actualizado_por = user["sub"]
    db.add(cons)
    db.commit()
    db.refresh(cons)

    write_audit_log(
        usuario_id=user["sub"], accion="actualizar_consentimiento", recurso="consentimiento",
        recurso_id=str(cliente_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"{estado_anterior} -> {body.estado}",
    )
    return ConsentimientoOut(
        cliente_id=str(cons.cliente_id), estado=cons.estado, canal=cons.canal,
        fecha_actualizacion=cons.fecha_actualizacion,
    )
```

```python
# backend/app/main.py
from app.routers import auth, auditoria, dp, clientes, consentimientos
...
app.include_router(clientes.router)
app.include_router(consentimientos.router)
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_consentimientos.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/consentimientos.py backend/app/schemas/consentimientos.py backend/app/main.py backend/tests/test_consentimientos.py
git commit -m "feat: add consentimiento get/patch endpoints with audit trail"
```

---

### Task 6: Router de campañas

**Files:**
- Create: `backend/app/schemas/campanias.py`
- Create: `backend/app/routers/campanias.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_campanias.py`

**Interfaces:**
- Consumes: `require_any_permission`, `mask_cliente`, `write_audit_log`, modelos `Campania`, `Cliente`, `Consentimiento`.
- Produces:
  - `POST /campanias` → requiere `campanias:crear_editar`; body `{"nombre": str, "producto": str, "fecha_inicio": date, "fecha_fin": date|None, "estado": str}`; `estado` debe estar en `{"planificada","activa","cerrada","cancelada"}`.
  - `GET /campanias` → requiere `campanias:consultar`.
  - `PATCH /campanias/{campania_id}` → requiere `campanias:crear_editar`; actualiza `estado`/`fecha_fin`.
  - `GET /campanias/{campania_id}/clientes-elegibles` → requiere `clientes:ver_sensible` o `clientes:ver_parcial`; reutiliza la misma regla de `estado == 'opt-in'` que `/clientes/elegibles`.

- [ ] **Step 1: Escribir el test que falla**

```python
# backend/tests/test_campanias.py
import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, Permiso, RolPermiso, Campania
from app.security.hashing import hash_password

client = TestClient(app)
PASSWORD = "Sup3rSecret!Pass"


def _make_permiso(db, nombre):
    p = db.query(Permiso).filter(Permiso.nombre == nombre).first()
    if p is None:
        p = Permiso(nombre=nombre, recurso=nombre.split(":")[0], accion=nombre.split(":")[1])
        db.add(p)
        db.flush()
    return p


@pytest.fixture
def supervisor():
    db = SessionLocal()
    prefix = f"camptest_{uuid.uuid4().hex[:8]}"
    rol = Rol(nombre=f"{prefix}_supervisor", descripcion="x")
    db.add(rol)
    db.flush()
    permiso = _make_permiso(db, "campanias:crear_editar")
    permiso2 = _make_permiso(db, "campanias:consultar")
    db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=permiso.permiso_id))
    db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=permiso2.permiso_id))
    user = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.supervisor", nombre_completo="Supervisor",
        email_corporativo=f"{prefix}.supervisor@bancoproyecto.pe",
        password_hash=hash_password(PASSWORD), rol_id=rol.rol_id,
    )
    db.add(user)
    db.commit()
    try:
        yield user
    finally:
        creadas = db.query(Campania).filter(Campania.nombre.like(f"{prefix}%")).all()
        for c in creadas:
            db.delete(c)
        db.query(Usuario).filter(Usuario.usuario_id == user.usuario_id).delete()
        db.query(RolPermiso).filter(RolPermiso.rol_id == rol.rol_id).delete()
        db.query(Rol).filter(Rol.rol_id == rol.rol_id).delete()
        db.commit()
        db.close()


def _login(username):
    resp = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_create_and_list_and_update_campania(supervisor):
    headers = {"Authorization": f"Bearer {_login(supervisor.username)}"}
    prefix = supervisor.username.split(".")[0]

    resp = client.post(
        "/campanias",
        json={
            "nombre": f"{prefix} Campania Depositos", "producto": "deposito_plazo",
            "fecha_inicio": str(datetime.date.today()), "fecha_fin": None, "estado": "planificada",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    campania_id = resp.json()["campania_id"]

    resp_list = client.get("/campanias", headers=headers)
    assert resp_list.status_code == 200
    assert any(c["campania_id"] == campania_id for c in resp_list.json())

    resp_patch = client.patch(f"/campanias/{campania_id}", json={"estado": "activa"}, headers=headers)
    assert resp_patch.status_code == 200
    assert resp_patch.json()["estado"] == "activa"
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_campanias.py -v`
Expected: FAIL con `404 Not Found` en el `POST /campanias`.

- [ ] **Step 3: Implementar**

```python
# backend/app/schemas/campanias.py
from datetime import date
from pydantic import BaseModel


class CampaniaCreate(BaseModel):
    nombre: str
    producto: str
    fecha_inicio: date
    fecha_fin: date | None = None
    estado: str


class CampaniaUpdate(BaseModel):
    estado: str | None = None
    fecha_fin: date | None = None


class CampaniaOut(BaseModel):
    campania_id: str
    nombre: str
    producto: str
    fecha_inicio: date
    fecha_fin: date | None
    estado: str
```

```python
# backend/app/routers/campanias.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Campania, Cliente, Consentimiento
from app.security.rbac import require_any_permission
from app.security.masking import mask_cliente
from app.audit.logger import write_audit_log
from app.schemas.campanias import CampaniaCreate, CampaniaUpdate, CampaniaOut

router = APIRouter(prefix="/campanias", tags=["campanias"])

ESTADOS_VALIDOS = {"planificada", "activa", "cerrada", "cancelada"}


def _to_out(c: Campania) -> CampaniaOut:
    return CampaniaOut(
        campania_id=str(c.campania_id), nombre=c.nombre, producto=c.producto,
        fecha_inicio=c.fecha_inicio, fecha_fin=c.fecha_fin, estado=c.estado,
    )


@router.post("", response_model=CampaniaOut, status_code=status.HTTP_201_CREATED)
def crear_campania(
    body: CampaniaCreate, request: Request, db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("campanias:crear_editar")),
):
    if body.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=422, detail=f"estado debe ser uno de {ESTADOS_VALIDOS}")
    campania = Campania(campania_id=uuid.uuid4(), **body.model_dump())
    db.add(campania)
    db.commit()
    db.refresh(campania)
    write_audit_log(
        usuario_id=user["sub"], accion="crear_campania", recurso="campania",
        recurso_id=str(campania.campania_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=body.nombre,
    )
    return _to_out(campania)


@router.get("", response_model=list[CampaniaOut])
def listar_campanias(
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("campanias:consultar", "campanias:consultar_asignadas")),
):
    return [_to_out(c) for c in db.query(Campania).all()]


@router.patch("/{campania_id}", response_model=CampaniaOut)
def actualizar_campania(
    campania_id: str, body: CampaniaUpdate, request: Request, db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("campanias:crear_editar")),
):
    campania = db.query(Campania).filter(Campania.campania_id == campania_id).first()
    if campania is None:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    if body.estado is not None:
        if body.estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=422, detail=f"estado debe ser uno de {ESTADOS_VALIDOS}")
        campania.estado = body.estado
    if body.fecha_fin is not None:
        campania.fecha_fin = body.fecha_fin
    db.add(campania)
    db.commit()
    db.refresh(campania)
    write_audit_log(
        usuario_id=user["sub"], accion="actualizar_campania", recurso="campania",
        recurso_id=str(campania_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=str(body.model_dump(exclude_none=True)),
    )
    return _to_out(campania)


@router.get("/{campania_id}/clientes-elegibles")
def clientes_elegibles_de_campania(
    campania_id: str, request: Request, db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_sensible", "clientes:ver_parcial")),
):
    campania = db.query(Campania).filter(Campania.campania_id == campania_id).first()
    if campania is None:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    rows = (
        db.query(Cliente)
        .join(Consentimiento, Consentimiento.cliente_id == Cliente.cliente_id)
        .filter(Consentimiento.estado == "opt-in")
        .all()
    )
    resultado = [mask_cliente(c, user["rol"]) for c in rows]
    write_audit_log(
        usuario_id=user["sub"], accion="consulta_clientes_elegibles_campania", recurso="campania",
        recurso_id=str(campania_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"{len(resultado)} resultados",
    )
    return resultado
```

```python
# backend/app/main.py
from app.routers import auth, auditoria, dp, clientes, consentimientos, campanias
...
app.include_router(campanias.router)
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_campanias.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/campanias.py backend/app/schemas/campanias.py backend/app/main.py backend/tests/test_campanias.py
git commit -m "feat: add campanias CRUD and eligible-clients-per-campaign endpoint"
```

---

### Task 7: Router de asignaciones

**Files:**
- Create: `backend/app/schemas/asignaciones.py`
- Create: `backend/app/routers/asignaciones.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_asignaciones.py`

**Interfaces:**
- Consumes: `require_any_permission`, `write_audit_log`, modelos `Asignacion`, `Cliente`, `Consentimiento`, `Campania`, `Usuario`.
- Produces:
  - `POST /asignaciones` → requiere `campanias:crear_editar` (rol supervisor/admin); body `{"cliente_id": str, "campania_id": str, "usuario_id": str}`. Valida: cliente existe, campaña existe, `usuario_id` referencia un `Usuario` existente; el cliente debe tener `consentimiento.estado == 'opt-in'` (si no, 400 "Cliente sin consentimiento opt-in"). Crea la fila y audita.
  - `GET /asignaciones/mias` → requiere `clientes:ver_asignados`; devuelve las asignaciones del usuario autenticado.
  - `GET /campanias/{campania_id}/asignaciones` → requiere `campanias:crear_editar` o `campanias:consultar`; lista todas las asignaciones de esa campaña.

- [ ] **Step 1: Escribir el test que falla**

```python
# backend/tests/test_asignaciones.py
import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, Permiso, RolPermiso, Cliente, Consentimiento, Campania, Asignacion
from app.security.hashing import hash_password
from app.security.crypto import encrypt_field

client = TestClient(app)
PASSWORD = "Sup3rSecret!Pass"


def _make_permiso(db, nombre):
    p = db.query(Permiso).filter(Permiso.nombre == nombre).first()
    if p is None:
        p = Permiso(nombre=nombre, recurso=nombre.split(":")[0], accion=nombre.split(":")[1])
        db.add(p)
        db.flush()
    return p


def _make_user(db, prefix, suffix, permisos):
    rol = Rol(nombre=f"{prefix}_{suffix}", descripcion="x")
    db.add(rol)
    db.flush()
    for nombre in permisos:
        permiso = _make_permiso(db, nombre)
        db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=permiso.permiso_id))
    user = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.{suffix}", nombre_completo=suffix,
        email_corporativo=f"{prefix}.{suffix}@bancoproyecto.pe",
        password_hash=hash_password(PASSWORD), rol_id=rol.rol_id,
    )
    db.add(user)
    return user, rol


@pytest.fixture
def scenario():
    db = SessionLocal()
    prefix = f"asigtest_{uuid.uuid4().hex[:8]}"
    supervisor, rol_sup = _make_user(db, prefix, "supervisor", ["campanias:crear_editar", "campanias:consultar"])
    teleop, rol_teleop = _make_user(db, prefix, "teleop", ["clientes:ver_asignados"])
    campania = Campania(campania_id=uuid.uuid4(), nombre=f"{prefix} camp", producto="deposito",
                         fecha_inicio=datetime.date.today(), estado="activa")
    db.add(campania)
    cliente_opt_in = Cliente(
        cliente_id=uuid.uuid4(), nombre_cifrado=encrypt_field("A"), dni_cifrado=encrypt_field("1"),
        email_cifrado=encrypt_field("a@a.pe"), telefono_cifrado=encrypt_field("+51900000002"),
        direccion_cifrada=encrypt_field("d"), age=30, job="admin.", marital="single", education="secondary",
        default_credit="no", balance=0.0, housing="no", loan="no", contact="cellular", day=1, month="jan",
        duration=1, campaign=1, pdays=-1, previous=0, poutcome="unknown", deposit="no",
    )
    cliente_opt_out = Cliente(
        cliente_id=uuid.uuid4(), nombre_cifrado=encrypt_field("B"), dni_cifrado=encrypt_field("2"),
        email_cifrado=encrypt_field("b@b.pe"), telefono_cifrado=encrypt_field("+51900000003"),
        direccion_cifrada=encrypt_field("d"), age=30, job="admin.", marital="single", education="secondary",
        default_credit="no", balance=0.0, housing="no", loan="no", contact="cellular", day=1, month="jan",
        duration=1, campaign=1, pdays=-1, previous=0, poutcome="unknown", deposit="no",
    )
    db.add_all([cliente_opt_in, cliente_opt_out])
    db.flush()
    db.add(Consentimiento(consentimiento_id=uuid.uuid4(), cliente_id=cliente_opt_in.cliente_id, estado="opt-in"))
    db.add(Consentimiento(consentimiento_id=uuid.uuid4(), cliente_id=cliente_opt_out.cliente_id, estado="opt-out"))
    db.commit()
    try:
        yield {
            "supervisor": supervisor, "teleop": teleop, "campania": campania,
            "cliente_opt_in": cliente_opt_in, "cliente_opt_out": cliente_opt_out,
        }
    finally:
        db.query(Asignacion).filter(Asignacion.campania_id == campania.campania_id).delete()
        db.query(Consentimiento).filter(
            Consentimiento.cliente_id.in_([cliente_opt_in.cliente_id, cliente_opt_out.cliente_id])
        ).delete(synchronize_session=False)
        db.query(Cliente).filter(
            Cliente.cliente_id.in_([cliente_opt_in.cliente_id, cliente_opt_out.cliente_id])
        ).delete(synchronize_session=False)
        db.query(Campania).filter(Campania.campania_id == campania.campania_id).delete()
        for u, r in ((supervisor, rol_sup), (teleop, rol_teleop)):
            db.query(Usuario).filter(Usuario.usuario_id == u.usuario_id).delete()
            db.query(RolPermiso).filter(RolPermiso.rol_id == r.rol_id).delete()
            db.query(Rol).filter(Rol.rol_id == r.rol_id).delete()
        db.commit()
        db.close()


def _login(username):
    resp = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_asignar_cliente_opt_in_succeeds_and_teleop_sees_it(scenario):
    sup_headers = {"Authorization": f"Bearer {_login(scenario['supervisor'].username)}"}
    resp = client.post(
        "/asignaciones",
        json={
            "cliente_id": str(scenario["cliente_opt_in"].cliente_id),
            "campania_id": str(scenario["campania"].campania_id),
            "usuario_id": str(scenario["teleop"].usuario_id),
        },
        headers=sup_headers,
    )
    assert resp.status_code == 201

    teleop_headers = {"Authorization": f"Bearer {_login(scenario['teleop'].username)}"}
    resp_mias = client.get("/asignaciones/mias", headers=teleop_headers)
    assert resp_mias.status_code == 200
    assert len(resp_mias.json()) == 1


def test_asignar_cliente_opt_out_is_rejected(scenario):
    sup_headers = {"Authorization": f"Bearer {_login(scenario['supervisor'].username)}"}
    resp = client.post(
        "/asignaciones",
        json={
            "cliente_id": str(scenario["cliente_opt_out"].cliente_id),
            "campania_id": str(scenario["campania"].campania_id),
            "usuario_id": str(scenario["teleop"].usuario_id),
        },
        headers=sup_headers,
    )
    assert resp.status_code == 400
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_asignaciones.py -v`
Expected: FAIL con `404 Not Found` en `POST /asignaciones`.

- [ ] **Step 3: Implementar**

```python
# backend/app/schemas/asignaciones.py
from datetime import datetime
from pydantic import BaseModel


class AsignacionCreate(BaseModel):
    cliente_id: str
    campania_id: str
    usuario_id: str


class AsignacionOut(BaseModel):
    asignacion_id: str
    cliente_id: str
    campania_id: str
    usuario_id: str
    estado_contacto: str
    fecha_asignacion: datetime | None
```

```python
# backend/app/routers/asignaciones.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asignacion, Cliente, Consentimiento, Campania, Usuario
from app.security.rbac import require_any_permission
from app.audit.logger import write_audit_log
from app.schemas.asignaciones import AsignacionCreate, AsignacionOut

router = APIRouter(tags=["asignaciones"])


def _to_out(a: Asignacion) -> AsignacionOut:
    return AsignacionOut(
        asignacion_id=str(a.asignacion_id), cliente_id=str(a.cliente_id),
        campania_id=str(a.campania_id), usuario_id=str(a.usuario_id),
        estado_contacto=a.estado_contacto, fecha_asignacion=a.fecha_asignacion,
    )


@router.post("/asignaciones", response_model=AsignacionOut, status_code=status.HTTP_201_CREATED)
def crear_asignacion(
    body: AsignacionCreate, request: Request, db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("campanias:crear_editar")),
):
    if db.query(Cliente).filter(Cliente.cliente_id == body.cliente_id).first() is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if db.query(Campania).filter(Campania.campania_id == body.campania_id).first() is None:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    if db.query(Usuario).filter(Usuario.usuario_id == body.usuario_id).first() is None:
        raise HTTPException(status_code=404, detail="Usuario (teleoperador) no encontrado")

    consentimiento = db.query(Consentimiento).filter(Consentimiento.cliente_id == body.cliente_id).first()
    if consentimiento is None or consentimiento.estado != "opt-in":
        raise HTTPException(status_code=400, detail="El cliente no tiene consentimiento opt-in")

    asignacion = Asignacion(asignacion_id=uuid.uuid4(), **body.model_dump())
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    write_audit_log(
        usuario_id=user["sub"], accion="crear_asignacion", recurso="asignacion",
        recurso_id=str(asignacion.asignacion_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"cliente={body.cliente_id} teleoperador={body.usuario_id}",
    )
    return _to_out(asignacion)


@router.get("/asignaciones/mias", response_model=list[AsignacionOut])
def mis_asignaciones(
    db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("clientes:ver_asignados")),
):
    rows = db.query(Asignacion).filter(Asignacion.usuario_id == user["sub"]).all()
    return [_to_out(a) for a in rows]


@router.get("/campanias/{campania_id}/asignaciones", response_model=list[AsignacionOut])
def asignaciones_de_campania(
    campania_id: str, db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("campanias:crear_editar", "campanias:consultar")),
):
    rows = db.query(Asignacion).filter(Asignacion.campania_id == campania_id).all()
    return [_to_out(a) for a in rows]
```

```python
# backend/app/main.py
from app.routers import auth, auditoria, dp, clientes, consentimientos, campanias, asignaciones
...
app.include_router(asignaciones.router)
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_asignaciones.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/asignaciones.py backend/app/schemas/asignaciones.py backend/app/main.py backend/tests/test_asignaciones.py
git commit -m "feat: add asignaciones endpoints enforcing opt-in consent"
```

---

### Task 8: Router de resultados de contacto

**Files:**
- Create: `backend/app/schemas/resultados.py`
- Create: `backend/app/routers/resultados.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_resultados.py`

**Interfaces:**
- Consumes: `require_any_permission`, `write_audit_log`, modelos `Asignacion`, `ResultadoContacto`.
- Produces:
  - `POST /asignaciones/{asignacion_id}/resultado` → requiere `resultados:registrar`; solo permitido si `Asignacion.usuario_id == user["sub"]` (si no, 403); body `{"resultado": str, "observacion": str | None}`; crea la fila y además actualiza `Asignacion.estado_contacto = body.resultado`.
  - `GET /asignaciones/{asignacion_id}/resultado` → requiere `resultados:registrar` o `campanias:crear_editar`/`campanias:consultar`; 404 si no hay resultado registrado aún.

- [ ] **Step 1: Escribir el test que falla**

```python
# backend/tests/test_resultados.py
import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, Permiso, RolPermiso, Cliente, Consentimiento, Campania, Asignacion, ResultadoContacto
from app.security.hashing import hash_password
from app.security.crypto import encrypt_field

client = TestClient(app)
PASSWORD = "Sup3rSecret!Pass"


def _make_permiso(db, nombre):
    p = db.query(Permiso).filter(Permiso.nombre == nombre).first()
    if p is None:
        p = Permiso(nombre=nombre, recurso=nombre.split(":")[0], accion=nombre.split(":")[1])
        db.add(p)
        db.flush()
    return p


@pytest.fixture
def scenario():
    db = SessionLocal()
    prefix = f"restest_{uuid.uuid4().hex[:8]}"
    rol = Rol(nombre=f"{prefix}_teleop", descripcion="x")
    db.add(rol)
    db.flush()
    permiso = _make_permiso(db, "resultados:registrar")
    db.add(RolPermiso(rol_id=rol.rol_id, permiso_id=permiso.permiso_id))
    teleop = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.teleop", nombre_completo="Teleop",
        email_corporativo=f"{prefix}.teleop@bancoproyecto.pe",
        password_hash=hash_password(PASSWORD), rol_id=rol.rol_id,
    )
    otro_rol = Rol(nombre=f"{prefix}_otro", descripcion="x")
    db.add(otro_rol)
    db.flush()
    db.add(RolPermiso(rol_id=otro_rol.rol_id, permiso_id=permiso.permiso_id))
    otro_teleop = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.otro", nombre_completo="Otro",
        email_corporativo=f"{prefix}.otro@bancoproyecto.pe",
        password_hash=hash_password(PASSWORD), rol_id=otro_rol.rol_id,
    )
    db.add_all([teleop, otro_teleop])
    campania = Campania(campania_id=uuid.uuid4(), nombre=f"{prefix} camp", producto="deposito",
                         fecha_inicio=datetime.date.today(), estado="activa")
    cliente = Cliente(
        cliente_id=uuid.uuid4(), nombre_cifrado=encrypt_field("A"), dni_cifrado=encrypt_field("1"),
        email_cifrado=encrypt_field("a@a.pe"), telefono_cifrado=encrypt_field("+51900000004"),
        direccion_cifrada=encrypt_field("d"), age=30, job="admin.", marital="single", education="secondary",
        default_credit="no", balance=0.0, housing="no", loan="no", contact="cellular", day=1, month="jan",
        duration=1, campaign=1, pdays=-1, previous=0, poutcome="unknown", deposit="no",
    )
    db.add_all([campania, cliente])
    db.flush()
    db.add(Consentimiento(consentimiento_id=uuid.uuid4(), cliente_id=cliente.cliente_id, estado="opt-in"))
    asignacion = Asignacion(asignacion_id=uuid.uuid4(), cliente_id=cliente.cliente_id,
                             campania_id=campania.campania_id, usuario_id=teleop.usuario_id)
    db.add(asignacion)
    db.commit()
    try:
        yield {"teleop": teleop, "otro_teleop": otro_teleop, "asignacion": asignacion}
    finally:
        db.query(ResultadoContacto).filter(ResultadoContacto.asignacion_id == asignacion.asignacion_id).delete()
        db.query(Asignacion).filter(Asignacion.asignacion_id == asignacion.asignacion_id).delete()
        db.query(Consentimiento).filter(Consentimiento.cliente_id == cliente.cliente_id).delete()
        db.query(Cliente).filter(Cliente.cliente_id == cliente.cliente_id).delete()
        db.query(Campania).filter(Campania.campania_id == campania.campania_id).delete()
        for u, r in ((teleop, rol), (otro_teleop, otro_rol)):
            db.query(Usuario).filter(Usuario.usuario_id == u.usuario_id).delete()
            db.query(RolPermiso).filter(RolPermiso.rol_id == r.rol_id).delete()
            db.query(Rol).filter(Rol.rol_id == r.rol_id).delete()
        db.commit()
        db.close()


def _login(username):
    resp = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_registrar_resultado_updates_asignacion_estado(scenario):
    headers = {"Authorization": f"Bearer {_login(scenario['teleop'].username)}"}
    asignacion_id = scenario["asignacion"].asignacion_id

    resp = client.post(
        f"/asignaciones/{asignacion_id}/resultado",
        json={"resultado": "contactado_interesado", "observacion": "Llamar de nuevo mañana"},
        headers=headers,
    )
    assert resp.status_code == 201

    db = SessionLocal()
    refreshed = db.query(Asignacion).filter(Asignacion.asignacion_id == asignacion_id).first()
    assert refreshed.estado_contacto == "contactado_interesado"
    db.close()


def test_otro_teleoperador_cannot_register_result_for_foreign_asignacion(scenario):
    headers = {"Authorization": f"Bearer {_login(scenario['otro_teleop'].username)}"}
    resp = client.post(
        f"/asignaciones/{scenario['asignacion'].asignacion_id}/resultado",
        json={"resultado": "no_contesta", "observacion": None},
        headers=headers,
    )
    assert resp.status_code == 403
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_resultados.py -v`
Expected: FAIL con `404 Not Found` en `POST /asignaciones/{id}/resultado`.

- [ ] **Step 3: Implementar**

```python
# backend/app/schemas/resultados.py
from datetime import datetime
from pydantic import BaseModel


class ResultadoCreate(BaseModel):
    resultado: str
    observacion: str | None = None


class ResultadoOut(BaseModel):
    resultado_id: str
    asignacion_id: str
    resultado: str
    observacion: str | None
    fecha_contacto: datetime | None
```

```python
# backend/app/routers/resultados.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asignacion, ResultadoContacto
from app.security.rbac import require_any_permission
from app.audit.logger import write_audit_log
from app.schemas.resultados import ResultadoCreate, ResultadoOut

router = APIRouter(tags=["resultados"])


def _to_out(r: ResultadoContacto) -> ResultadoOut:
    return ResultadoOut(
        resultado_id=str(r.resultado_id), asignacion_id=str(r.asignacion_id),
        resultado=r.resultado, observacion=r.observacion, fecha_contacto=r.fecha_contacto,
    )


@router.post("/asignaciones/{asignacion_id}/resultado", response_model=ResultadoOut, status_code=status.HTTP_201_CREATED)
def registrar_resultado(
    asignacion_id: str, body: ResultadoCreate, request: Request, db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("resultados:registrar")),
):
    asignacion = db.query(Asignacion).filter(Asignacion.asignacion_id == asignacion_id).first()
    if asignacion is None:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    if str(asignacion.usuario_id) != str(user["sub"]):
        write_audit_log(
            usuario_id=user["sub"], accion="acceso_denegado", recurso="resultado_contacto",
            recurso_id=asignacion_id, ip_origen=request.client.host if request.client else None,
            resultado="denegado", detalle="Asignación no pertenece al usuario",
        )
        raise HTTPException(status_code=403, detail="Esta asignación no le pertenece")

    resultado = ResultadoContacto(resultado_id=uuid.uuid4(), asignacion_id=asignacion_id, **body.model_dump())
    asignacion.estado_contacto = body.resultado
    db.add(resultado)
    db.add(asignacion)
    db.commit()
    db.refresh(resultado)
    write_audit_log(
        usuario_id=user["sub"], accion="registrar_resultado_contacto", recurso="resultado_contacto",
        recurso_id=str(resultado.resultado_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=body.resultado,
    )
    return _to_out(resultado)


@router.get("/asignaciones/{asignacion_id}/resultado", response_model=ResultadoOut)
def obtener_resultado(
    asignacion_id: str, db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("resultados:registrar", "campanias:crear_editar", "campanias:consultar")),
):
    resultado = db.query(ResultadoContacto).filter(ResultadoContacto.asignacion_id == asignacion_id).first()
    if resultado is None:
        raise HTTPException(status_code=404, detail="Resultado no registrado")
    return _to_out(resultado)
```

```python
# backend/app/main.py
from app.routers import auth, auditoria, dp, clientes, consentimientos, campanias, asignaciones, resultados
...
app.include_router(resultados.router)
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_resultados.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/resultados.py backend/app/schemas/resultados.py backend/app/main.py backend/tests/test_resultados.py
git commit -m "feat: add resultado-de-contacto endpoints scoped to owning teleoperador"
```

---

### Task 9: Router de usuarios, roles y permisos (administración)

**Files:**
- Create: `backend/app/schemas/usuarios.py`
- Create: `backend/app/routers/usuarios.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_usuarios.py`

**Interfaces:**
- Consumes: `require_any_permission`, `write_audit_log`, `hash_password`, `validate_password_policy` (ya existen en `app.security.hashing`), modelos `Usuario`, `Rol`, `Permiso`.
- Produces:
  - `GET /usuarios` → requiere `usuarios:gestionar`.
  - `POST /usuarios` → requiere `usuarios:gestionar`; body `{"username", "nombre_completo", "email_corporativo", "rol_id", "password"}`; valida la contraseña con `validate_password_policy` (422 con la lista de errores si falla) y la hashea con `hash_password`.
  - `PATCH /usuarios/{usuario_id}/activo` → requiere `usuarios:gestionar`; body `{"activo": bool}`.
  - `GET /roles` → requiere `usuarios:gestionar`.
  - `GET /permisos` → requiere `usuarios:gestionar`.

- [ ] **Step 1: Escribir el test que falla**

```python
# backend/tests/test_usuarios.py
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Usuario, Rol, Permiso, RolPermiso
from app.security.hashing import hash_password

client = TestClient(app)
PASSWORD = "Sup3rSecret!Pass"


def _make_permiso(db, nombre):
    p = db.query(Permiso).filter(Permiso.nombre == nombre).first()
    if p is None:
        p = Permiso(nombre=nombre, recurso=nombre.split(":")[0], accion=nombre.split(":")[1])
        db.add(p)
        db.flush()
    return p


@pytest.fixture
def admin_and_target_rol():
    db = SessionLocal()
    prefix = f"usrtest_{uuid.uuid4().hex[:8]}"
    rol_admin = Rol(nombre=f"{prefix}_admin", descripcion="x")
    rol_destino = Rol(nombre=f"{prefix}_teleoperador", descripcion="x")
    db.add_all([rol_admin, rol_destino])
    db.flush()
    permiso = _make_permiso(db, "usuarios:gestionar")
    db.add(RolPermiso(rol_id=rol_admin.rol_id, permiso_id=permiso.permiso_id))
    admin = Usuario(
        usuario_id=uuid.uuid4(), username=f"{prefix}.admin", nombre_completo="Admin",
        email_corporativo=f"{prefix}.admin@bancoproyecto.pe",
        password_hash=hash_password(PASSWORD), rol_id=rol_admin.rol_id,
    )
    db.add(admin)
    db.commit()
    try:
        yield {"admin": admin, "rol_destino": rol_destino}
    finally:
        nuevos = db.query(Usuario).filter(Usuario.username.like(f"{prefix}%")).all()
        for u in nuevos:
            db.delete(u)
        db.query(RolPermiso).filter(RolPermiso.rol_id == rol_admin.rol_id).delete()
        db.query(Rol).filter(Rol.rol_id.in_([rol_admin.rol_id, rol_destino.rol_id])).delete(synchronize_session=False)
        db.commit()
        db.close()


def _login(username):
    resp = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_admin_creates_user_and_toggles_activo(admin_and_target_rol):
    headers = {"Authorization": f"Bearer {_login(admin_and_target_rol['admin'].username)}"}
    rol_id = admin_and_target_rol["rol_destino"].rol_id

    resp = client.post(
        "/usuarios",
        json={
            "username": "usrtest.nuevo", "nombre_completo": "Nuevo Usuario",
            "email_corporativo": "usrtest.nuevo@bancoproyecto.pe",
            "rol_id": rol_id, "password": "ContrasenaSegura123",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    usuario_id = resp.json()["usuario_id"]

    resp_weak = client.post(
        "/usuarios",
        json={
            "username": "usrtest.debil", "nombre_completo": "Debil",
            "email_corporativo": "usrtest.debil@bancoproyecto.pe",
            "rol_id": rol_id, "password": "corta",
        },
        headers=headers,
    )
    assert resp_weak.status_code == 422

    resp_patch = client.patch(f"/usuarios/{usuario_id}/activo", json={"activo": False}, headers=headers)
    assert resp_patch.status_code == 200
    assert resp_patch.json()["activo"] is False
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd backend && pytest tests/test_usuarios.py -v`
Expected: FAIL con `404 Not Found` en `POST /usuarios`.

- [ ] **Step 3: Implementar**

```python
# backend/app/schemas/usuarios.py
from pydantic import BaseModel


class UsuarioCreate(BaseModel):
    username: str
    nombre_completo: str
    email_corporativo: str
    rol_id: int
    password: str


class UsuarioActivoUpdate(BaseModel):
    activo: bool


class UsuarioOut(BaseModel):
    usuario_id: str
    username: str
    nombre_completo: str
    email_corporativo: str
    rol_id: int
    activo: bool


class RolOut(BaseModel):
    rol_id: int
    nombre: str
    descripcion: str | None


class PermisoOut(BaseModel):
    permiso_id: int
    nombre: str
    recurso: str
    accion: str
```

```python
# backend/app/routers/usuarios.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Rol, Permiso
from app.security.rbac import require_any_permission
from app.security.hashing import hash_password, validate_password_policy
from app.audit.logger import write_audit_log
from app.schemas.usuarios import UsuarioCreate, UsuarioActivoUpdate, UsuarioOut, RolOut, PermisoOut

router = APIRouter(tags=["usuarios"])


def _to_out(u: Usuario) -> UsuarioOut:
    return UsuarioOut(
        usuario_id=str(u.usuario_id), username=u.username, nombre_completo=u.nombre_completo,
        email_corporativo=u.email_corporativo, rol_id=u.rol_id, activo=u.activo,
    )


@router.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db), user: dict = Depends(require_any_permission("usuarios:gestionar")),
):
    return [_to_out(u) for u in db.query(Usuario).all()]


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    body: UsuarioCreate, request: Request, db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("usuarios:gestionar")),
):
    errores = validate_password_policy(body.password)
    if errores:
        raise HTTPException(status_code=422, detail=errores)
    if db.query(Rol).filter(Rol.rol_id == body.rol_id).first() is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    nuevo = Usuario(
        usuario_id=uuid.uuid4(), username=body.username, nombre_completo=body.nombre_completo,
        email_corporativo=body.email_corporativo, rol_id=body.rol_id,
        password_hash=hash_password(body.password),
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    write_audit_log(
        usuario_id=user["sub"], accion="crear_usuario", recurso="usuario",
        recurso_id=str(nuevo.usuario_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=body.username,
    )
    return _to_out(nuevo)


@router.patch("/usuarios/{usuario_id}/activo", response_model=UsuarioOut)
def actualizar_activo(
    usuario_id: str, body: UsuarioActivoUpdate, request: Request, db: Session = Depends(get_db),
    user: dict = Depends(require_any_permission("usuarios:gestionar")),
):
    target = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    target.activo = body.activo
    db.add(target)
    db.commit()
    db.refresh(target)
    write_audit_log(
        usuario_id=user["sub"], accion="actualizar_estado_usuario", recurso="usuario",
        recurso_id=str(usuario_id), ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"activo={body.activo}",
    )
    return _to_out(target)


@router.get("/roles", response_model=list[RolOut])
def listar_roles(
    db: Session = Depends(get_db), user: dict = Depends(require_any_permission("usuarios:gestionar")),
):
    return [RolOut(rol_id=r.rol_id, nombre=r.nombre, descripcion=r.descripcion) for r in db.query(Rol).all()]


@router.get("/permisos", response_model=list[PermisoOut])
def listar_permisos(
    db: Session = Depends(get_db), user: dict = Depends(require_any_permission("usuarios:gestionar")),
):
    return [
        PermisoOut(permiso_id=p.permiso_id, nombre=p.nombre, recurso=p.recurso, accion=p.accion)
        for p in db.query(Permiso).all()
    ]
```

```python
# backend/app/main.py
from app.routers import auth, auditoria, dp, clientes, consentimientos, campanias, asignaciones, resultados, usuarios
...
app.include_router(usuarios.router)
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd backend && pytest tests/test_usuarios.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/usuarios.py backend/app/schemas/usuarios.py backend/app/main.py backend/tests/test_usuarios.py
git commit -m "feat: add usuarios/roles/permisos administration endpoints"
```

---

### Task 10: Suite completa y verificación final

**Files:**
- No crea archivos nuevos; ejecuta y corrige regresiones si aparecen.

- [ ] **Step 1: Ejecutar toda la suite backend**

Run: `cd backend && pytest -v`
Expected: Todos los tests pasan, incluyendo los preexistentes (`test_crypto.py`, `test_lockout.py`, `test_dp.py`, `test_models.py`, `test_seed_generation.py`, `test_hashing.py`, `test_auth.py`) y los nueve archivos nuevos de este plan.

- [ ] **Step 2: Revisar que `app/main.py` registre los ocho routers esperados**

Run: `cd backend && python -c "from app.main import app; print(sorted({r.path for r in app.routes}))"`
Expected: la lista incluye `/health`, `/auth/login`, `/auditoria/logs`, rutas de `/clientes...`, `/campanias...`, `/asignaciones...`, `/usuarios`, `/roles`, `/permisos`.

- [ ] **Step 3: Commit final (si quedó algo sin commitear)**

```bash
git status
```

Si hay cambios sin commitear (por ejemplo un ajuste hecho durante la Step 1), commitearlos con un mensaje descriptivo siguiendo el mismo patrón `feat: ...` / `fix: ...` de las tareas anteriores.

---

## Fuera de alcance de este plan (seguimiento recomendado)

Estas piezas del PDF quedan **fuera** de este plan porque son subsistemas independientes (frontend, infraestructura, operación) y deberían planificarse por separado una vez el backend esté verde:

1. **Frontend mínimo por rol** — reemplazar `frontend/src/App.tsx` (plantilla Vite) por router + vistas de login/dashboard/clientes/campañas/asignaciones/auditoría que consuman estos endpoints. Requiere resolver primero el error de `npm run build` en `frontend/tsconfig.app.json:20`.
2. **HTTPS/Nginx** — completar `infra/docker-compose.yml` (vacío) con Nginx + certificados autofirmados OpenSSL, según PDF §9.2.1 y §10.2.
3. **Backups cifrados** — script `pg_dump` + cifrado con `backup_encryption_key` (ya existe en `app/config.py` pero no se usa) y prueba de restauración, según PDF §10.1.3 y Tabla 14.
4. **Plan de respuesta ante incidentes** — documentar el procedimiento de PDF §10.6 en `docs/`, no requiere código.

## Execution Handoff

Plan completo y guardado en `docs/superpowers/plans/2026-07-08-flujo-bancario-backend.md`. Dos opciones de ejecución:

**1. Subagent-Driven (recomendado)** — despliego un subagente fresco por tarea, con revisión entre tareas.

**2. Inline Execution** — ejecuto las tareas en esta misma sesión, en lote con checkpoints de revisión.

¿Cuál prefieres?
