# Sistema Seguro de Apoyo a Campañas Bancarias — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full prototype described in `Proyecto___Grupo_1___EyS.pdf`: a role-based, audited, encrypted banking-campaign support system covering data generation, a PostgreSQL schema, a FastAPI backend (auth, RBAC, consent-aware endpoints, audit logging), a role-scoped React frontend, TLS via self-signed certs, and the security tests/docs required by Bloque IV and V of the report.

**Architecture:** Layered architecture matching Figure 1 of the PDF: React SPA → Nginx reverse proxy (TLS termination, self-signed X.509) → FastAPI backend (JWT auth, RBAC middleware, audit interceptor, AES-256-GCM field encryption) → PostgreSQL (relational schema from §9.3.4) → encrypted `pg_dump` backups. Synthetic data (Faker, seed 42, `es_PE` locale) links to `bank.csv` (11,162 rows) via a generated `cliente_id`.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0 + Alembic, PostgreSQL 15, Faker, passlib[argon2] (Argon2id), PyJWT, `cryptography` (AES-256-GCM), pytest + httpx, React 18 + Vite + React Router, Nginx, OpenSSL.

## Global Constraints

- Dataset base: `bank.csv`, 11,162 records, 17 columns, no nulls — path `/Users/angel/etica_seguridad_datos/proyecto/bank.csv`. Do not modify this file.
- Faker must use `Faker("es_PE")` and `Faker.seed(42)` for reproducibility (§7).
- Passwords: Argon2id only, `memory_cost=65536, time_cost=3, parallelism=1` (§10.1.2). Never store plaintext or use SHA-256/bcrypt-only.
- PII columns (`nombre`, `dni`, `email`, `telefono`, `direccion`) must be encrypted at rest with AES-256-GCM; encryption key lives in an environment variable, never in the DB (§10.1.1).
- All internal traffic between frontend and backend must go through Nginx over HTTPS/TLS 1.2+ using OpenSSL self-signed certs (§10.2). No plaintext HTTP in the served path.
- RBAC roles are fixed: `administrador`, `supervisor`, `analista`, `teleoperador` (§9.3.1). Permission matrix must match Cuadro 15 exactly.
- Every access to sensitive client data, consent change, export, and denied (403) request must produce an `audit_log` row (§10.5, Cuadro 16, KR 2.3: 100% coverage).
- Clients with consent `opt-out` must never appear in eligible-client queries or assignments (§10.4, RF-06, RF-11).
- SQL access must use parameterized queries only (SQLAlchemy ORM/Core bound params) — no string-built SQL (§11.2, "Prevención de inyección SQL").
- Password policy: min length 12, lockout after repeated failed attempts, constant-time comparison (§10.7.1).
- Out of scope (do NOT build): real ML propensity model (use simulated scoring), integration with real bank systems, public CA certificates, SIEM. These are explicitly excluded (§4 "Fuera de alcance").
- **Database is an externally managed Railway PostgreSQL instance, not a local Docker container.** The engineer's own machine is outside Railway's private network, so it must connect using the **public** connection string (Railway's `DATABASE_PUBLIC_URL`, host `thomas.proxy.rlwy.net:17156`, db `railway`), not the internal `postgres.railway.internal` host (that only resolves from inside Railway). The actual credentials are already known to the project owner — **never paste the real password into any file that gets committed** (this plan, README, or any doc). It only ever goes into the local, gitignored `backend/.env` (`DATABASE_URL=...`) and, when deploying the backend itself to Railway, into that service's environment variables panel (where `DATABASE_URL` with the internal host is preferred for lower latency between Railway services).

---

## File Structure

```
proyecto/
├── bank.csv                          # existing, untouched
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── rol.py, permiso.py, rol_permiso.py, usuario.py
│   │   │   ├── cliente.py, consentimiento.py
│   │   │   ├── campania.py, asignacion.py, resultado_contacto.py
│   │   │   └── audit_log.py
│   │   ├── schemas/                  # Pydantic request/response models
│   │   ├── security/
│   │   │   ├── hashing.py            # Argon2id
│   │   │   ├── jwt.py                # token issue/verify
│   │   │   ├── crypto.py             # AES-256-GCM field encryption
│   │   │   ├── rbac.py               # permission-checking dependency
│   │   │   └── lockout.py            # failed-login tracking
│   │   ├── audit/
│   │   │   └── logger.py             # audit_log writer + FastAPI middleware
│   │   ├── routers/
│   │   │   ├── auth.py, usuarios.py, roles.py
│   │   │   ├── clientes.py, campanias.py, asignaciones.py
│   │   │   ├── consentimientos.py, metricas.py, auditoria.py
│   │   └── seed/
│   │       ├── generate_synthetic.py # Faker generation script (§7)
│   │       └── load_bank_csv.py
│   └── tests/
│       ├── test_auth.py, test_rbac.py, test_consent.py
│       ├── test_audit.py, test_crypto.py, test_sql_injection.py
├── frontend/
│   ├── package.json, vite.config.ts
│   └── src/
│       ├── main.tsx, App.tsx, api/client.ts, auth/AuthContext.tsx
│       ├── pages/Login.tsx
│       ├── pages/admin/{Users,Roles,AuditLog}.tsx
│       ├── pages/supervisor/{Metrics,Assignments}.tsx
│       ├── pages/analista/PrioritizedClients.tsx
│       └── pages/teleoperador/{MyClients,ContactResult}.tsx
├── infra/
│   ├── nginx/nginx.conf
│   ├── certs/gen_certs.sh
│   └── docker-compose.yml
└── docs/
    ├── INSTALL.md
    ├── incident_response_plan.md
    └── security_policies.md
```

---

## Task 1: Repository & environment scaffolding

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `infra/docker-compose.yml`
- Create: `.gitignore`

**Interfaces:**
- Produces: confirmed connectivity to the externally managed Railway PostgreSQL 15 instance (db `railway`) via its public proxy endpoint, and a Python virtualenv with backend deps installed.

- [ ] **Step 1: Initialize git repo (root has no VCS yet)**

```bash
cd /Users/angel/etica_seguridad_datos/proyecto
git init
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
node_modules/
dist/
*.env
infra/certs/*.key
infra/certs/*.crt
infra/certs/*.csr
backups/
.pytest_cache/
```

- [ ] **Step 3: Create `backend/pyproject.toml`**

```toml
[project]
name = "bank-campaigns-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "psycopg2-binary>=2.9",
    "pydantic-settings>=2.3",
    "passlib[argon2]>=1.7.4",
    "pyjwt>=2.8",
    "cryptography>=42.0",
    "faker>=25.0",
    "pandas>=2.2",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = ["pytest>=8.2", "httpx>=0.27", "pytest-cov>=5.0"]

[tool.pytest.ini_options]
pythonpath = ["."]
```

- [ ] **Step 4: Create `backend/.env.example`** (placeholders only — the real Railway URL never goes in this tracked file)

```
# Local dev connects to Railway's PUBLIC endpoint (this machine is outside Railway's private network).
# Copy the value of Railway's DATABASE_PUBLIC_URL into your local backend/.env, swapping the driver prefix
# to postgresql+psycopg2:// (SQLAlchemy needs the +psycopg2 dialect suffix; Railway's raw value uses postgresql://).
DATABASE_URL=postgresql+psycopg2://postgres:<password>@<public-proxy-host>:<public-port>/railway
JWT_SECRET=change-me-to-a-random-64-char-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
FIELD_ENCRYPTION_KEY=change-me-32-byte-base64-key==
BACKUP_ENCRYPTION_KEY=change-me-32-byte-base64-key==
```

- [ ] **Step 5: Create `backend/.env` locally (gitignored) with the real Railway public URL**

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set `DATABASE_URL` to the **public** Railway connection string (the one whose host is the `*.proxy.rlwy.net` proxy, port `17156`, NOT `postgres.railway.internal` — that internal hostname only resolves from inside Railway's own network). Use the `postgresql+psycopg2://` prefix. Leave `JWT_SECRET`, `FIELD_ENCRYPTION_KEY`, `BACKUP_ENCRYPTION_KEY` as generated in later tasks. **Do not commit `.env`** — it is already covered by `.gitignore` (`*.env`).

- [ ] **Step 6: Install backend deps and verify connectivity to the Railway DB**

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python3 -c "
from app.config import Settings
import sqlalchemy
s = Settings(_env_file='.env')
engine = sqlalchemy.create_engine(s.database_url)
with engine.connect() as conn:
    print(conn.execute(sqlalchemy.text('SELECT version();')).scalar())
"
```

Expected: prints the PostgreSQL version string from the Railway instance (confirms the public URL and driver prefix are correct) — this requires `app/config.py` from Task 2 Step 1 to exist first; if run before Task 2, use `psql "$DATABASE_URL_RAW"` (Railway's `DATABASE_PUBLIC_URL` verbatim, `postgresql://` prefix) instead as a quicker connectivity check: `psql "postgresql://postgres:<password>@thomas.proxy.rlwy.net:17156/railway" -c "SELECT 1;"`.

- [ ] **Step 7: Note on `infra/docker-compose.yml` — no local `db` service**

Because Postgres is Railway-managed, `infra/docker-compose.yml` will only ever define `backend` and `nginx` services (added in Task 10); it never defines a `db` service, and no local Postgres container or volume is created at any point in this plan. Create the file now as an empty placeholder that Task 10 will populate:

```yaml
services: {}
```

- [ ] **Step 8: Commit**

```bash
cd /Users/angel/etica_seguridad_datos/proyecto
git add .gitignore backend/pyproject.toml backend/.env.example infra/docker-compose.yml
git commit -m "chore: scaffold repo, backend deps, Railway Postgres connectivity check"
```

---

## Task 2: SQLAlchemy models and Alembic migration (schema from §9.3.4)

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/rol.py`
- Create: `backend/app/models/permiso.py`
- Create: `backend/app/models/rol_permiso.py`
- Create: `backend/app/models/usuario.py`
- Create: `backend/app/models/cliente.py`
- Create: `backend/app/models/consentimiento.py`
- Create: `backend/app/models/campania.py`
- Create: `backend/app/models/asignacion.py`
- Create: `backend/app/models/resultado_contacto.py`
- Create: `backend/app/models/audit_log.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Produces: `Base` (declarative base) in `app.database`, ORM classes `Rol, Permiso, RolPermiso, Usuario, Cliente, Consentimiento, Campania, Asignacion, ResultadoContacto, AuditLog` importable from `app.models`, each with a `.__tablename__` matching Cuadro 11 exactly (`rol, permiso, rol_permiso, usuario, cliente, consentimiento, campania, asignacion, resultado_contacto, audit_log`).

- [ ] **Step 1: `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    field_encryption_key: str
    backup_encryption_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 2: `backend/app/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: `backend/app/models/rol.py`**

```python
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Rol(Base):
    __tablename__ = "rol"
    rol_id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text)
    permisos = relationship("RolPermiso", back_populates="rol")
```

- [ ] **Step 4: `backend/app/models/permiso.py`**

```python
from sqlalchemy import Column, Integer, String
from app.database import Base

class Permiso(Base):
    __tablename__ = "permiso"
    permiso_id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    recurso = Column(String(100), nullable=False)
    accion = Column(String(50), nullable=False)
```

- [ ] **Step 5: `backend/app/models/rol_permiso.py`**

```python
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class RolPermiso(Base):
    __tablename__ = "rol_permiso"
    rol_id = Column(Integer, ForeignKey("rol.rol_id"), primary_key=True)
    permiso_id = Column(Integer, ForeignKey("permiso.permiso_id"), primary_key=True)
    rol = relationship("Rol", back_populates="permisos")
    permiso = relationship("Permiso")
```

- [ ] **Step 6: `backend/app/models/usuario.py`**

```python
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuario"
    usuario_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), nullable=False, unique=True)
    nombre_completo = Column(String(120), nullable=False)
    email_corporativo = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    rol_id = Column(Integer, ForeignKey("rol.rol_id"), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
```

- [ ] **Step 7: `backend/app/models/cliente.py`** (field names match §9.3.4 exactly; PII columns store ciphertext)

```python
import uuid
from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Cliente(Base):
    __tablename__ = "cliente"
    cliente_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_cifrado = Column(String)
    dni_cifrado = Column(String)
    email_cifrado = Column(String)
    telefono_cifrado = Column(String)
    direccion_cifrada = Column(String)
    age = Column(Integer)
    job = Column(String(50))
    marital = Column(String(30))
    education = Column(String(30))
    default_credit = Column(String(5))
    balance = Column(Numeric(12, 2))
    housing = Column(String(5))
    loan = Column(String(5))
    contact = Column(String(30))
    day = Column(Integer)
    month = Column(String(10))
    duration = Column(Integer)
    campaign = Column(Integer)
    pdays = Column(Integer)
    previous = Column(Integer)
    poutcome = Column(String(30))
    deposit = Column(String(5))
```

- [ ] **Step 8: `backend/app/models/consentimiento.py`**

```python
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Consentimiento(Base):
    __tablename__ = "consentimiento"
    consentimiento_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("cliente.cliente_id"), nullable=False)
    estado = Column(String(20), nullable=False)
    canal = Column(String(30))
    fecha_registro = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    actualizado_por = Column(UUID(as_uuid=True), ForeignKey("usuario.usuario_id"))

    __table_args__ = (
        CheckConstraint("estado IN ('opt-in','opt-out','no informado')", name="ck_consentimiento_estado"),
    )
```

- [ ] **Step 9: `backend/app/models/campania.py`, `asignacion.py`, `resultado_contacto.py`, `audit_log.py`**

```python
# backend/app/models/campania.py
import uuid
from sqlalchemy import Column, String, Date, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Campania(Base):
    __tablename__ = "campania"
    campania_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(120), nullable=False)
    producto = Column(String(80), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date)
    estado = Column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint("estado IN ('planificada','activa','cerrada','cancelada')", name="ck_campania_estado"),
    )
```

```python
# backend/app/models/asignacion.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Asignacion(Base):
    __tablename__ = "asignacion"
    asignacion_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("cliente.cliente_id"), nullable=False)
    campania_id = Column(UUID(as_uuid=True), ForeignKey("campania.campania_id"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuario.usuario_id"), nullable=False)
    estado_contacto = Column(String(30), default="pendiente")
    fecha_asignacion = Column(DateTime, server_default=func.now())
```

```python
# backend/app/models/resultado_contacto.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class ResultadoContacto(Base):
    __tablename__ = "resultado_contacto"
    resultado_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asignacion_id = Column(UUID(as_uuid=True), ForeignKey("asignacion.asignacion_id"), nullable=False)
    resultado = Column(String(40), nullable=False)
    observacion = Column(Text)
    fecha_contacto = Column(DateTime, server_default=func.now())
```

```python
# backend/app/models/audit_log.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuario.usuario_id"))
    accion = Column(String(100), nullable=False)
    recurso = Column(String(100), nullable=False)
    recurso_id = Column(String(100))
    ip_origen = Column(String(45))
    resultado = Column(String(30), nullable=False)
    detalle = Column(Text)
    timestamp_evento = Column(DateTime, server_default=func.now())
```

- [ ] **Step 10: `backend/app/models/__init__.py`** re-exports all models so Alembic autogeneration sees them

```python
from app.models.rol import Rol
from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.consentimiento import Consentimiento
from app.models.campania import Campania
from app.models.asignacion import Asignacion
from app.models.resultado_contacto import ResultadoContacto
from app.models.audit_log import AuditLog

__all__ = [
    "Rol", "Permiso", "RolPermiso", "Usuario", "Cliente", "Consentimiento",
    "Campania", "Asignacion", "ResultadoContacto", "AuditLog",
]
```

- [ ] **Step 11: Initialize Alembic and point it at `Base.metadata`**

```bash
cd backend
alembic init alembic
```

Edit `backend/alembic/env.py`: add near the top
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.database import Base
from app.config import settings
import app.models  # noqa: F401 ensures all models are registered
target_metadata = Base.metadata
```
and replace the `sqlalchemy.url` resolution with:
```python
config.set_main_option("sqlalchemy.url", settings.database_url)
```

- [ ] **Step 12: Write `backend/tests/test_models.py`**

```python
from app.database import Base, engine
from sqlalchemy import inspect

def test_all_expected_tables_are_registered():
    import app.models  # noqa
    tables = set(Base.metadata.tables.keys())
    expected = {
        "rol", "permiso", "rol_permiso", "usuario", "cliente",
        "consentimiento", "campania", "asignacion",
        "resultado_contacto", "audit_log",
    }
    assert expected.issubset(tables)
```

- [ ] **Step 13: Run test to verify it fails (models not yet imported anywhere)**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: PASS actually once files above exist — if it fails, check `app/models/__init__.py` imports.

- [ ] **Step 14: Generate and apply the migration**

```bash
cd backend
alembic revision --autogenerate -m "initial schema from §9.3.4"
alembic upgrade head
```

Expected: migration file created under `alembic/versions/`, `alembic upgrade head` prints `Running upgrade -> ..., initial schema`.

- [ ] **Step 15: Verify tables exist**

```bash
psql "$DATABASE_URL_RAW" -c "\dt"
```

Where `DATABASE_URL_RAW` is Railway's `DATABASE_PUBLIC_URL` verbatim (`postgresql://...@thomas.proxy.rlwy.net:17156/railway`) exported in your shell only for this command, e.g. `export DATABASE_URL_RAW="$(grep DATABASE_URL .env | cut -d= -f2- | sed 's/+psycopg2//')"`. Expected: lists all 10 tables.

- [ ] **Step 16: Commit**

```bash
git add backend/app backend/alembic backend/alembic.ini backend/tests/test_models.py
git commit -m "feat: add SQLAlchemy models and initial Alembic migration"
```

---

## Task 3: Argon2id password hashing and lockout policy (§10.1.2, §10.7.1)

**Files:**
- Create: `backend/app/security/hashing.py`
- Create: `backend/app/security/lockout.py`
- Test: `backend/tests/test_hashing.py`

**Interfaces:**
- Produces: `hash_password(raw: str) -> str`, `verify_password(raw: str, stored_hash: str) -> bool`, `validate_password_policy(raw: str) -> list[str]` (returns list of violated rules, empty if OK), `is_locked_out(usuario: Usuario) -> bool`, `register_failed_attempt(db, usuario) -> None`, `reset_failed_attempts(db, usuario) -> None`.

- [ ] **Step 1: Write failing test for hashing**

```python
# backend/tests/test_hashing.py
from app.security.hashing import hash_password, verify_password, validate_password_policy

def test_hash_and_verify_roundtrip():
    h = hash_password("Sup3rSecret!Pass")
    assert h != "Sup3rSecret!Pass"
    assert verify_password("Sup3rSecret!Pass", h) is True
    assert verify_password("wrong-password", h) is False

def test_password_policy_rejects_short_passwords():
    errors = validate_password_policy("short1!")
    assert any("12" in e for e in errors)

def test_password_policy_accepts_valid_password():
    errors = validate_password_policy("Sup3rSecret!Pass")
    assert errors == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_hashing.py -v`
Expected: FAIL — `ModuleNotFoundError: app.security.hashing`

- [ ] **Step 3: Implement `backend/app/security/hashing.py`**

```python
from passlib.hash import argon2

_argon2 = argon2.using(memory_cost=65536, time_cost=3, parallelism=1)

def hash_password(raw_password: str) -> str:
    return _argon2.hash(raw_password)

def verify_password(raw_password: str, stored_hash: str) -> bool:
    try:
        return _argon2.verify(raw_password, stored_hash)
    except ValueError:
        return False

def validate_password_policy(raw_password: str) -> list[str]:
    errors = []
    if len(raw_password) < 12:
        errors.append("La contraseña debe tener al menos 12 caracteres.")
    common_passwords = {"password123456", "123456789012", "qwertyuiop12"}
    if raw_password.lower() in common_passwords:
        errors.append("La contraseña está en la lista de contraseñas comprometidas.")
    return errors
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_hashing.py -v`
Expected: 3 passed

- [ ] **Step 5: Write failing test for lockout**

```python
# backend/tests/test_lockout.py
import uuid
from datetime import datetime, timedelta
from app.models.usuario import Usuario
from app.security.lockout import is_locked_out, register_failed_attempt, reset_failed_attempts, MAX_ATTEMPTS

def make_user():
    return Usuario(
        usuario_id=uuid.uuid4(), username="u", nombre_completo="U",
        email_corporativo="u@bank.pe", password_hash="x", rol_id=1,
        failed_login_attempts=0, locked_until=None,
    )

def test_lockout_triggers_after_max_attempts():
    user = make_user()
    for _ in range(MAX_ATTEMPTS):
        register_failed_attempt(None, user)
    assert is_locked_out(user) is True

def test_reset_clears_lockout():
    user = make_user()
    user.failed_login_attempts = MAX_ATTEMPTS
    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
    reset_failed_attempts(None, user)
    assert is_locked_out(user) is False
    assert user.failed_login_attempts == 0
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd backend && pytest tests/test_lockout.py -v`
Expected: FAIL — `ModuleNotFoundError: app.security.lockout`

- [ ] **Step 7: Implement `backend/app/security/lockout.py`**

```python
from datetime import datetime, timedelta

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

def is_locked_out(usuario) -> bool:
    if usuario.locked_until is None:
        return False
    return datetime.utcnow() < usuario.locked_until

def register_failed_attempt(db, usuario) -> None:
    usuario.failed_login_attempts = (usuario.failed_login_attempts or 0) + 1
    if usuario.failed_login_attempts >= MAX_ATTEMPTS:
        usuario.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
    if db is not None:
        db.add(usuario)
        db.commit()

def reset_failed_attempts(db, usuario) -> None:
    usuario.failed_login_attempts = 0
    usuario.locked_until = None
    if db is not None:
        db.add(usuario)
        db.commit()
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_hashing.py tests/test_lockout.py -v`
Expected: 5 passed

- [ ] **Step 9: Commit**

```bash
git add backend/app/security/hashing.py backend/app/security/lockout.py backend/tests/test_hashing.py backend/tests/test_lockout.py
git commit -m "feat: Argon2id hashing and login lockout policy"
```

---

## Task 4: AES-256-GCM field encryption for PII (§10.1.1)

**Files:**
- Create: `backend/app/security/crypto.py`
- Test: `backend/tests/test_crypto.py`

**Interfaces:**
- Produces: `encrypt_field(plaintext: str) -> str` (base64 of `nonce || ciphertext || tag`), `decrypt_field(token: str) -> str`. Both read the key from `settings.field_encryption_key` (32-byte base64).

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_crypto.py
from app.security.crypto import encrypt_field, decrypt_field

def test_encrypt_decrypt_roundtrip():
    plaintext = "Juan Pérez - DNI 12345678"
    token = encrypt_field(plaintext)
    assert token != plaintext
    assert decrypt_field(token) == plaintext

def test_ciphertext_is_nondeterministic():
    token_a = encrypt_field("same value")
    token_b = encrypt_field("same value")
    assert token_a != token_b  # random nonce per call
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_crypto.py -v`
Expected: FAIL — `ModuleNotFoundError: app.security.crypto`

- [ ] **Step 3: Implement `backend/app/security/crypto.py`**

```python
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

def _key_bytes() -> bytes:
    return base64.b64decode(settings.field_encryption_key)

def encrypt_field(plaintext: str) -> str:
    key = _key_bytes()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")

def decrypt_field(token: str) -> str:
    key = _key_bytes()
    raw = base64.b64decode(token)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
```

- [ ] **Step 4: Set a real 32-byte base64 key in `backend/.env`**

```bash
cd backend
python3 -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
```
Copy the printed value into `FIELD_ENCRYPTION_KEY=` in `.env`.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_crypto.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/security/crypto.py backend/tests/test_crypto.py
git commit -m "feat: AES-256-GCM field-level encryption for PII"
```

---

## Task 5: Synthetic data generation script (§7, Cuadro 5, example code)

**Files:**
- Create: `backend/app/seed/generate_synthetic.py`
- Create: `backend/app/seed/load_bank_csv.py`
- Test: `backend/tests/test_seed_generation.py`

**Interfaces:**
- Produces: `generate_clientes(df_base: pandas.DataFrame) -> list[dict]` (each dict has `cliente_id, nombre, dni, email, telefono, direccion` plus the 17 base columns), `generate_consentimientos(cliente_ids: list[str]) -> list[dict]` (70% opt-in / 20% no informado / 10% opt-out), `generate_roles_and_permisos() -> tuple[list[dict], list[dict], list[dict]]` (roles, permisos, rol_permiso matching Cuadro 15), `generate_usuarios_internos(n_per_role: dict[str,int]) -> list[dict]`, `main()` orchestrates loading `bank.csv`, generating everything, and inserting via SQLAlchemy session.

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_seed_generation.py
import pandas as pd
from app.seed.generate_synthetic import generate_clientes, generate_consentimientos

def test_generate_clientes_matches_row_count_and_has_required_fields():
    df = pd.DataFrame({
        "age": [59, 56], "job": ["admin.", "admin."], "marital": ["married", "married"],
        "education": ["secondary", "secondary"], "default": ["no", "no"],
        "balance": [2343, 45], "housing": ["yes", "no"], "loan": ["no", "no"],
        "contact": ["unknown", "unknown"], "day": [5, 5], "month": ["may", "may"],
        "duration": [1042, 1467], "campaign": [1, 1], "pdays": [-1, -1],
        "previous": [0, 0], "poutcome": ["unknown", "unknown"], "deposit": ["yes", "yes"],
    })
    clientes = generate_clientes(df)
    assert len(clientes) == 2
    for c in clientes:
        for field in ("cliente_id", "nombre", "dni", "email", "telefono", "direccion", "age", "deposit"):
            assert field in c

def test_generate_consentimientos_uses_expected_states():
    ids = [f"id-{i}" for i in range(1000)]
    consentimientos = generate_consentimientos(ids)
    estados = {c["estado"] for c in consentimientos}
    assert estados <= {"opt-in", "opt-out", "no informado"}
    opt_in_share = sum(1 for c in consentimientos if c["estado"] == "opt-in") / len(consentimientos)
    assert 0.55 < opt_in_share < 0.85  # ~70% with sampling noise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_seed_generation.py -v`
Expected: FAIL — `ModuleNotFoundError: app.seed.generate_synthetic`

- [ ] **Step 3: Implement `backend/app/seed/generate_synthetic.py`**

```python
import uuid
import random
import pandas as pd
from faker import Faker

fake = Faker("es_PE")
Faker.seed(42)
random.seed(42)

BASE_COLUMNS = [
    "age", "job", "marital", "education", "default", "balance", "housing",
    "loan", "contact", "day", "month", "duration", "campaign", "pdays",
    "previous", "poutcome", "deposit",
]

def generate_clientes(df_base: pd.DataFrame) -> list[dict]:
    n = len(df_base)
    records = []
    for i in range(n):
        row = df_base.iloc[i]
        record = {
            "cliente_id": str(uuid.uuid4()),
            "nombre": fake.name(),
            "dni": fake.unique.bothify("########"),
            "email": fake.unique.email(),
            "telefono": fake.phone_number(),
            "direccion": fake.address(),
        }
        for col in BASE_COLUMNS:
            record[col] = row[col]
        records.append(record)
    return records

def generate_consentimientos(cliente_ids: list[str]) -> list[dict]:
    estados_pool = (["opt-in"] * 70) + (["no informado"] * 20) + (["opt-out"] * 10)
    canales = ["email", "sms", "llamada", "formulario_web"]
    consentimientos = []
    for cid in cliente_ids:
        estado = random.choice(estados_pool)
        consentimientos.append({
            "consentimiento_id": str(uuid.uuid4()),
            "cliente_id": cid,
            "estado": estado,
            "canal": random.choice(canales),
        })
    return consentimientos

def generate_roles_and_permisos():
    roles = [
        {"nombre": "administrador", "descripcion": "Gestiona usuarios, roles y auditoría."},
        {"nombre": "supervisor", "descripcion": "Supervisa campañas y asigna teleoperadores."},
        {"nombre": "analista", "descripcion": "Consulta clientes priorizados por campaña."},
        {"nombre": "teleoperador", "descripcion": "Contacta clientes asignados."},
    ]
    permisos = [
        {"nombre": "clientes:ver_sensible", "recurso": "clientes", "accion": "ver_sensible"},
        {"nombre": "clientes:ver_parcial", "recurso": "clientes", "accion": "ver_parcial"},
        {"nombre": "clientes:ver_asignados", "recurso": "clientes", "accion": "ver_asignados"},
        {"nombre": "clientes:exportar", "recurso": "clientes", "accion": "exportar"},
        {"nombre": "campanias:crear_editar", "recurso": "campanias", "accion": "crear_editar"},
        {"nombre": "campanias:consultar", "recurso": "campanias", "accion": "consultar"},
        {"nombre": "campanias:consultar_asignadas", "recurso": "campanias", "accion": "consultar_asignadas"},
        {"nombre": "resultados:registrar", "recurso": "resultados", "accion": "registrar"},
        {"nombre": "usuarios:gestionar", "recurso": "usuarios", "accion": "gestionar"},
        {"nombre": "auditoria:consultar", "recurso": "auditoria", "accion": "consultar"},
    ]
    matrix = {
        "administrador": ["clientes:ver_sensible", "clientes:exportar", "campanias:crear_editar",
                           "campanias:consultar", "usuarios:gestionar", "auditoria:consultar"],
        "supervisor": ["clientes:ver_sensible", "clientes:exportar", "campanias:crear_editar",
                       "campanias:consultar", "auditoria:consultar"],
        "analista": ["clientes:ver_parcial", "campanias:consultar"],
        "teleoperador": ["clientes:ver_asignados", "campanias:consultar_asignadas", "resultados:registrar"],
    }
    rol_permiso = [{"rol_nombre": rol, "permiso_nombre": p} for rol, perms in matrix.items() for p in perms]
    return roles, permisos, rol_permiso

def generate_usuarios_internos(n_per_role: dict[str, int]) -> list[dict]:
    usuarios = []
    for rol_nombre, n in n_per_role.items():
        for _ in range(n):
            full_name = fake.name()
            username = full_name.lower().replace(" ", ".")
            usuarios.append({
                "usuario_id": str(uuid.uuid4()),
                "username": username,
                "nombre_completo": full_name,
                "email_corporativo": f"{username}@bancoproyecto.pe",
                "rol_nombre": rol_nombre,
            })
    return usuarios
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_seed_generation.py -v`
Expected: 2 passed

- [ ] **Step 5: Implement `backend/app/seed/load_bank_csv.py`** (orchestrator that persists everything)

```python
import sys
import os
import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Rol, Permiso, RolPermiso, Usuario, Cliente, Consentimiento
from app.security.hashing import hash_password
from app.security.crypto import encrypt_field
from app.seed.generate_synthetic import (
    generate_clientes, generate_consentimientos,
    generate_roles_and_permisos, generate_usuarios_internos,
)

BANK_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "bank.csv")

def seed_roles_permisos(db: Session) -> dict[str, int]:
    roles, permisos, rol_permiso = generate_roles_and_permisos()
    rol_by_name = {}
    for r in roles:
        obj = Rol(nombre=r["nombre"], descripcion=r["descripcion"])
        db.add(obj)
        db.flush()
        rol_by_name[r["nombre"]] = obj.rol_id
    permiso_by_name = {}
    for p in permisos:
        obj = Permiso(nombre=p["nombre"], recurso=p["recurso"], accion=p["accion"])
        db.add(obj)
        db.flush()
        permiso_by_name[p["nombre"]] = obj.permiso_id
    for rp in rol_permiso:
        db.add(RolPermiso(rol_id=rol_by_name[rp["rol_nombre"]], permiso_id=permiso_by_name[rp["permiso_nombre"]]))
    db.commit()
    return rol_by_name

def seed_usuarios(db: Session, rol_by_name: dict[str, int]) -> None:
    usuarios = generate_usuarios_internos({"administrador": 1, "supervisor": 2, "analista": 3, "teleoperador": 8})
    default_password = "CambiarEnPrimerAcceso!123"
    for u in usuarios:
        db.add(Usuario(
            usuario_id=u["usuario_id"], username=u["username"],
            nombre_completo=u["nombre_completo"], email_corporativo=u["email_corporativo"],
            password_hash=hash_password(default_password),
            rol_id=rol_by_name[u["rol_nombre"]],
        ))
    db.commit()

def seed_clientes_y_consentimientos(db: Session) -> None:
    df_base = pd.read_csv(BANK_CSV_PATH)
    clientes = generate_clientes(df_base)
    for c in clientes:
        db.add(Cliente(
            cliente_id=c["cliente_id"],
            nombre_cifrado=encrypt_field(c["nombre"]),
            dni_cifrado=encrypt_field(c["dni"]),
            email_cifrado=encrypt_field(c["email"]),
            telefono_cifrado=encrypt_field(c["telefono"]),
            direccion_cifrada=encrypt_field(c["direccion"]),
            age=c["age"], job=c["job"], marital=c["marital"], education=c["education"],
            default_credit=c["default"], balance=c["balance"], housing=c["housing"],
            loan=c["loan"], contact=c["contact"], day=c["day"], month=c["month"],
            duration=c["duration"], campaign=c["campaign"], pdays=c["pdays"],
            previous=c["previous"], poutcome=c["poutcome"], deposit=c["deposit"],
        ))
    db.commit()
    cliente_ids = [c["cliente_id"] for c in clientes]
    for cons in generate_consentimientos(cliente_ids):
        db.add(Consentimiento(
            consentimiento_id=cons["consentimiento_id"], cliente_id=cons["cliente_id"],
            estado=cons["estado"], canal=cons["canal"],
        ))
    db.commit()

def main():
    db = SessionLocal()
    try:
        rol_by_name = seed_roles_permisos(db)
        seed_usuarios(db, rol_by_name)
        seed_clientes_y_consentimientos(db)
        print("Seed completed.")
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run the seed against the real DB**

```bash
cd backend
source .venv/bin/activate
python -m app.seed.load_bank_csv
```

Expected: prints `Seed completed.`; `SELECT count(*) FROM cliente;` returns 11162.

- [ ] **Step 7: Commit**

```bash
git add backend/app/seed backend/tests/test_seed_generation.py
git commit -m "feat: synthetic data generation and bank.csv seed loader"
```

---

## Task 6: JWT auth, login endpoint, RBAC dependency (§9.1.2 flow 1, §10.3, RF-01/02/16)

**Files:**
- Create: `backend/app/security/jwt.py`
- Create: `backend/app/security/rbac.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/routers/auth.py`
- Create: `backend/app/main.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Produces: `create_access_token(usuario_id: str, rol_nombre: str, permisos: list[str]) -> str`, `decode_access_token(token: str) -> dict`, FastAPI dependency `get_current_user(token: str = Depends(oauth2_scheme)) -> dict` (payload with `sub`, `rol`, `permisos`), `require_permission(permiso_nombre: str)` returning a FastAPI dependency that 403s + audits if missing, `POST /auth/login` returning `{"access_token": str, "token_type": "bearer"}`.

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_auth.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_auth.py -v`
Expected: FAIL — `ModuleNotFoundError: app.main`

- [ ] **Step 3: Implement `backend/app/security/jwt.py`**

```python
import jwt
from datetime import datetime, timedelta
from app.config import settings

def create_access_token(usuario_id: str, rol_nombre: str, permisos: list[str]) -> str:
    payload = {
        "sub": usuario_id,
        "rol": rol_nombre,
        "permisos": permisos,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
```

- [ ] **Step 4: Implement `backend/app/security/rbac.py`**

```python
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from app.security.jwt import decode_access_token
from app.audit.logger import write_audit_log

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return decode_access_token(token)
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o expiradas")

def require_permission(permiso_nombre: str):
    def dependency(request: Request, user: dict = Depends(get_current_user)) -> dict:
        if permiso_nombre not in user.get("permisos", []):
            write_audit_log(
                usuario_id=user.get("sub"), accion="acceso_denegado",
                recurso=permiso_nombre, recurso_id=None,
                ip_origen=request.client.host if request.client else None,
                resultado="denegado", detalle=f"Falta permiso {permiso_nombre}",
            )
            raise HTTPException(status_code=403, detail="No autorizado para este recurso")
        return user
    return dependency
```

- [ ] **Step 5: Implement `backend/app/routers/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Usuario, RolPermiso, Permiso
from app.security.hashing import verify_password
from app.security.jwt import create_access_token
from app.security.lockout import is_locked_out, register_failed_attempt, reset_failed_attempts
from app.audit.logger import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    usuario = db.query(Usuario).filter(Usuario.username == form.username).first()
    if usuario is None or not usuario.activo:
        write_audit_log(usuario_id=None, accion="login_fallido", recurso="auth",
                         recurso_id=form.username, ip_origen=ip, resultado="fallo",
                         detalle="usuario inexistente o inactivo")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if is_locked_out(usuario):
        write_audit_log(usuario_id=str(usuario.usuario_id), accion="login_bloqueado", recurso="auth",
                         recurso_id=form.username, ip_origen=ip, resultado="fallo",
                         detalle="cuenta bloqueada temporalmente")
        raise HTTPException(status_code=401, detail="Cuenta bloqueada temporalmente")
    if not verify_password(form.password, usuario.password_hash):
        register_failed_attempt(db, usuario)
        write_audit_log(usuario_id=str(usuario.usuario_id), accion="login_fallido", recurso="auth",
                         recurso_id=form.username, ip_origen=ip, resultado="fallo",
                         detalle="password incorrecto")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    reset_failed_attempts(db, usuario)
    permisos = (
        db.query(Permiso.nombre)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.permiso_id)
        .filter(RolPermiso.rol_id == usuario.rol_id)
        .all()
    )
    permisos_list = [p[0] for p in permisos]
    rol_nombre = usuario.rol.nombre if usuario.rol else ""
    token = create_access_token(str(usuario.usuario_id), rol_nombre, permisos_list)
    write_audit_log(usuario_id=str(usuario.usuario_id), accion="login_exitoso", recurso="auth",
                     recurso_id=form.username, ip_origen=ip, resultado="exito", detalle=None)
    return {"access_token": token, "token_type": "bearer"}
```

Add the `rol` relationship to `Usuario` (edit `backend/app/models/usuario.py`, append):
```python
from sqlalchemy.orm import relationship
Usuario.rol = relationship("Rol")
```

- [ ] **Step 6: Implement `backend/app/main.py`**

```python
from fastapi import FastAPI
from app.routers import auth

app = FastAPI(title="Sistema Seguro de Apoyo a Campañas Bancarias")
app.include_router(auth.router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

(Stub `backend/app/audit/logger.py` minimally for now — it is completed in Task 8.)

```python
# backend/app/audit/logger.py (temporary stub, replaced in Task 8)
def write_audit_log(**kwargs):
    pass
```

- [ ] **Step 7: Add a placeholder `/auditoria/logs` route so the 401 test is meaningful (real implementation in Task 9)**

```python
# backend/app/routers/auditoria.py
from fastapi import APIRouter, Depends
from app.security.rbac import require_permission

router = APIRouter(prefix="/auditoria", tags=["auditoria"])

@router.get("/logs")
def list_logs(user: dict = Depends(require_permission("auditoria:consultar"))):
    return []
```

Register it in `main.py`:
```python
from app.routers import auth, auditoria
app.include_router(auth.router)
app.include_router(auditoria.router)
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_auth.py -v`
Expected: 3 passed

- [ ] **Step 9: Commit**

```bash
git add backend/app/security/jwt.py backend/app/security/rbac.py backend/app/routers/auth.py backend/app/routers/auditoria.py backend/app/main.py backend/app/audit/logger.py backend/tests/test_auth.py
git commit -m "feat: JWT login endpoint and RBAC permission dependency"
```

---

## Task 7: Consent-aware client endpoints (RF-06, RF-07, RF-09, RF-11, §10.4)

**Files:**
- Create: `backend/app/schemas/cliente.py`
- Create: `backend/app/routers/clientes.py`
- Create: `backend/app/routers/consentimientos.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_consent.py`

**Interfaces:**
- Consumes: `require_permission`, `get_db`, `Cliente`, `Consentimiento`, `decrypt_field`.
- Produces: `GET /clientes/elegibles?campania_id=...` → list of clients with `estado_consentimiento != 'opt-out'`; `PATCH /consentimientos/{cliente_id}` body `{"estado": "opt-in"|"opt-out"|"no informado"}` → updates and audits.

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_consent.py
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Cliente, Consentimiento

client = TestClient(app)

def _seed_two_clients():
    db = SessionLocal()
    optin_id = uuid.uuid4()
    optout_id = uuid.uuid4()
    db.add(Cliente(cliente_id=optin_id, age=30, job="admin.", deposit="yes"))
    db.add(Cliente(cliente_id=optout_id, age=40, job="technician", deposit="no"))
    db.add(Consentimiento(cliente_id=optin_id, estado="opt-in"))
    db.add(Consentimiento(cliente_id=optout_id, estado="opt-out"))
    db.commit()
    db.close()
    return str(optin_id), str(optout_id)

def test_opt_out_clients_excluded_from_eligible_list(monkeypatch):
    optin_id, optout_id = _seed_two_clients()
    from app.security import rbac
    monkeypatch.setattr(rbac, "get_current_user", lambda: {"sub": "tester", "permisos": ["campanias:consultar"]})
    app.dependency_overrides[rbac.get_current_user] = lambda: {"sub": "tester", "permisos": ["campanias:consultar"]}
    resp = client.get("/clientes/elegibles")
    ids = [c["cliente_id"] for c in resp.json()]
    assert optin_id in ids
    assert optout_id not in ids
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_consent.py -v`
Expected: FAIL — `ModuleNotFoundError: app.routers.clientes`

- [ ] **Step 3: Implement `backend/app/schemas/cliente.py`**

```python
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from typing import Optional

class ClienteElegible(BaseModel):
    cliente_id: UUID
    age: int
    job: Optional[str]
    balance: Optional[Decimal]
    estado_consentimiento: str

    class Config:
        from_attributes = True

class ConsentimientoUpdate(BaseModel):
    estado: str  # 'opt-in' | 'opt-out' | 'no informado'
```

- [ ] **Step 4: Implement `backend/app/routers/clientes.py`**

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Consentimiento
from app.security.rbac import require_permission
from app.audit.logger import write_audit_log

router = APIRouter(prefix="/clientes", tags=["clientes"])

@router.get("/elegibles")
def clientes_elegibles(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("campanias:consultar")),
):
    rows = (
        db.query(Cliente, Consentimiento.estado)
        .join(Consentimiento, Consentimiento.cliente_id == Cliente.cliente_id)
        .filter(Consentimiento.estado != "opt-out")
        .all()
    )
    write_audit_log(
        usuario_id=user["sub"], accion="consulta_clientes_elegibles", recurso="clientes",
        recurso_id=None, ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"{len(rows)} clientes devueltos",
    )
    return [
        {
            "cliente_id": str(cliente.cliente_id),
            "age": cliente.age,
            "job": cliente.job,
            "balance": cliente.balance,
            "estado_consentimiento": estado,
        }
        for cliente, estado in rows
    ]
```

- [ ] **Step 5: Implement `backend/app/routers/consentimientos.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Consentimiento
from app.schemas.cliente import ConsentimientoUpdate
from app.security.rbac import require_permission
from app.audit.logger import write_audit_log

router = APIRouter(prefix="/consentimientos", tags=["consentimientos"])

VALID_STATES = {"opt-in", "opt-out", "no informado"}

@router.patch("/{cliente_id}")
def update_consentimiento(
    cliente_id: str,
    body: ConsentimientoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("clientes:ver_sensible")),
):
    if body.estado not in VALID_STATES:
        raise HTTPException(status_code=422, detail="Estado de consentimiento inválido")
    consentimiento = db.query(Consentimiento).filter(Consentimiento.cliente_id == cliente_id).first()
    if consentimiento is None:
        raise HTTPException(status_code=404, detail="Cliente sin registro de consentimiento")
    estado_anterior = consentimiento.estado
    consentimiento.estado = body.estado
    consentimiento.actualizado_por = user["sub"]
    db.add(consentimiento)
    db.commit()
    write_audit_log(
        usuario_id=user["sub"], accion="actualizacion_consentimiento", recurso="consentimiento",
        recurso_id=cliente_id, ip_origen=request.client.host if request.client else None,
        resultado="exito", detalle=f"{estado_anterior} -> {body.estado}",
    )
    return {"cliente_id": cliente_id, "estado": body.estado}
```

- [ ] **Step 6: Register routers in `backend/app/main.py`**

```python
from app.routers import auth, auditoria, clientes, consentimientos
app.include_router(auth.router)
app.include_router(auditoria.router)
app.include_router(clientes.router)
app.include_router(consentimientos.router)
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && pytest tests/test_consent.py -v`
Expected: 1 passed

- [ ] **Step 8: Commit**

```bash
git add backend/app/schemas/cliente.py backend/app/routers/clientes.py backend/app/routers/consentimientos.py backend/app/main.py backend/tests/test_consent.py
git commit -m "feat: consent-aware eligible-clients endpoint and consent update endpoint"
```

---

## Task 8: Campaigns, assignments, contact results (RF-05, RF-08, RF-09, RF-10, CU-04..CU-08)

**Files:**
- Create: `backend/app/schemas/campania.py`
- Create: `backend/app/routers/campanias.py`
- Create: `backend/app/routers/asignaciones.py`
- Create: `backend/app/routers/metricas.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_campanias_flow.py`

**Interfaces:**
- Produces: `POST /campanias` (crear/editar, permission `campanias:crear_editar`), `GET /campanias` (consultar), `POST /asignaciones` body `{cliente_id, campania_id, usuario_id}` (permission `campanias:crear_editar`, i.e. supervisor/admin), `GET /asignaciones/mias` (teleoperador's own assignments, permission `clientes:ver_asignados`), `POST /asignaciones/{asignacion_id}/resultado` body `{resultado, observacion}` (permission `resultados:registrar`), `GET /metricas/campania/{campania_id}` aggregated KPIs (permission `campanias:consultar`).

- [ ] **Step 1: Write failing integration test covering the end-to-end flow**

```python
# backend/tests/test_campanias_flow.py
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Cliente, Consentimiento
from app.security import rbac

client = TestClient(app)

def _override_user(permisos, sub="00000000-0000-0000-0000-000000000001"):
    app.dependency_overrides[rbac.get_current_user] = lambda: {"sub": sub, "permisos": permisos}

def test_full_campaign_assignment_and_contact_result_flow():
    db = SessionLocal()
    cliente_id = uuid.uuid4()
    db.add(Cliente(cliente_id=cliente_id, age=35, job="management", deposit="no"))
    db.add(Consentimiento(cliente_id=cliente_id, estado="opt-in"))
    db.commit()
    db.close()

    _override_user(["campanias:crear_editar"])
    resp = client.post("/campanias", json={
        "nombre": "Depósitos Plazo Q3", "producto": "deposito_plazo",
        "fecha_inicio": "2026-07-01", "estado": "activa",
    })
    assert resp.status_code == 201
    campania_id = resp.json()["campania_id"]

    resp = client.post("/asignaciones", json={
        "cliente_id": str(cliente_id), "campania_id": campania_id,
        "usuario_id": "00000000-0000-0000-0000-000000000002",
    })
    assert resp.status_code == 201
    asignacion_id = resp.json()["asignacion_id"]

    _override_user(["resultados:registrar"], sub="00000000-0000-0000-0000-000000000002")
    resp = client.post(f"/asignaciones/{asignacion_id}/resultado", json={
        "resultado": "contactado_interesado", "observacion": "Llamar de nuevo mañana",
    })
    assert resp.status_code == 201

    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_campanias_flow.py -v`
Expected: FAIL — `ModuleNotFoundError: app.routers.campanias`

- [ ] **Step 3: Implement `backend/app/schemas/campania.py`**

```python
from pydantic import BaseModel
from datetime import date
from typing import Optional
from uuid import UUID

class CampaniaCreate(BaseModel):
    nombre: str
    producto: str
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    estado: str

class AsignacionCreate(BaseModel):
    cliente_id: UUID
    campania_id: UUID
    usuario_id: UUID

class ResultadoContactoCreate(BaseModel):
    resultado: str
    observacion: Optional[str] = None
```

- [ ] **Step 4: Implement `backend/app/routers/campanias.py`**

```python
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Campania
from app.schemas.campania import CampaniaCreate
from app.security.rbac import require_permission
from app.audit.logger import write_audit_log

router = APIRouter(prefix="/campanias", tags=["campanias"])

@router.post("", status_code=201)
def crear_campania(
    body: CampaniaCreate, request: Request, response: Response,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("campanias:crear_editar")),
):
    campania = Campania(**body.model_dump())
    db.add(campania)
    db.commit()
    write_audit_log(usuario_id=user["sub"], accion="crear_campania", recurso="campania",
                     recurso_id=str(campania.campania_id),
                     ip_origen=request.client.host if request.client else None,
                     resultado="exito", detalle=body.nombre)
    return {"campania_id": str(campania.campania_id)}

@router.get("")
def listar_campanias(
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("campanias:consultar")),
):
    campanias = db.query(Campania).all()
    return [
        {"campania_id": str(c.campania_id), "nombre": c.nombre, "producto": c.producto,
         "estado": c.estado, "fecha_inicio": str(c.fecha_inicio)}
        for c in campanias
    ]
```

- [ ] **Step 5: Implement `backend/app/routers/asignaciones.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asignacion, ResultadoContacto, Consentimiento
from app.schemas.campania import AsignacionCreate, ResultadoContactoCreate
from app.security.rbac import require_permission
from app.audit.logger import write_audit_log

router = APIRouter(prefix="/asignaciones", tags=["asignaciones"])

@router.post("", status_code=201)
def crear_asignacion(
    body: AsignacionCreate, request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("campanias:crear_editar")),
):
    consentimiento = db.query(Consentimiento).filter(Consentimiento.cliente_id == str(body.cliente_id)).first()
    if consentimiento is None or consentimiento.estado == "opt-out":
        raise HTTPException(status_code=409, detail="El cliente no tiene consentimiento válido para ser asignado")
    asignacion = Asignacion(**body.model_dump())
    db.add(asignacion)
    db.commit()
    write_audit_log(usuario_id=user["sub"], accion="crear_asignacion", recurso="asignacion",
                     recurso_id=str(asignacion.asignacion_id),
                     ip_origen=request.client.host if request.client else None,
                     resultado="exito", detalle=None)
    return {"asignacion_id": str(asignacion.asignacion_id)}

@router.get("/mias")
def mis_asignaciones(
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("clientes:ver_asignados")),
):
    asignaciones = db.query(Asignacion).filter(Asignacion.usuario_id == user["sub"]).all()
    return [
        {"asignacion_id": str(a.asignacion_id), "cliente_id": str(a.cliente_id),
         "campania_id": str(a.campania_id), "estado_contacto": a.estado_contacto}
        for a in asignaciones
    ]

@router.post("/{asignacion_id}/resultado", status_code=201)
def registrar_resultado(
    asignacion_id: str, body: ResultadoContactoCreate, request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("resultados:registrar")),
):
    asignacion = db.query(Asignacion).filter(Asignacion.asignacion_id == asignacion_id).first()
    if asignacion is None:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    if str(asignacion.usuario_id) != user["sub"]:
        raise HTTPException(status_code=403, detail="Solo el teleoperador asignado puede registrar el resultado")
    resultado = ResultadoContacto(asignacion_id=asignacion_id, **body.model_dump())
    asignacion.estado_contacto = "contactado"
    db.add(resultado)
    db.add(asignacion)
    db.commit()
    write_audit_log(usuario_id=user["sub"], accion="registrar_resultado_contacto", recurso="resultado_contacto",
                     recurso_id=str(resultado.resultado_id),
                     ip_origen=request.client.host if request.client else None,
                     resultado="exito", detalle=body.resultado)
    return {"resultado_id": str(resultado.resultado_id)}
```

- [ ] **Step 6: Implement `backend/app/routers/metricas.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asignacion, ResultadoContacto
from app.security.rbac import require_permission

router = APIRouter(prefix="/metricas", tags=["metricas"])

@router.get("/campania/{campania_id}")
def metricas_campania(
    campania_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("campanias:consultar")),
):
    total = db.query(func.count(Asignacion.asignacion_id)).filter(Asignacion.campania_id == campania_id).scalar()
    contactados = (
        db.query(func.count(Asignacion.asignacion_id))
        .filter(Asignacion.campania_id == campania_id, Asignacion.estado_contacto == "contactado")
        .scalar()
    )
    return {
        "campania_id": campania_id,
        "total_asignados": total,
        "total_contactados": contactados,
        "tasa_contacto": round((contactados / total * 100), 2) if total else 0.0,
    }
```

- [ ] **Step 7: Register routers in `backend/app/main.py`**

```python
from app.routers import auth, auditoria, clientes, consentimientos, campanias, asignaciones, metricas
app.include_router(auth.router)
app.include_router(auditoria.router)
app.include_router(clientes.router)
app.include_router(consentimientos.router)
app.include_router(campanias.router)
app.include_router(asignaciones.router)
app.include_router(metricas.router)
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd backend && pytest tests/test_campanias_flow.py -v`
Expected: 1 passed

- [ ] **Step 9: Commit**

```bash
git add backend/app/schemas/campania.py backend/app/routers/campanias.py backend/app/routers/asignaciones.py backend/app/routers/metricas.py backend/app/main.py backend/tests/test_campanias_flow.py
git commit -m "feat: campaign, assignment, contact-result, and metrics endpoints"
```

---

## Task 9: Real audit logging service + user/role management endpoints (§10.5, Cuadro 16, RF-03/04/13, CU-02/03/10)

**Files:**
- Modify: `backend/app/audit/logger.py`
- Create: `backend/app/routers/usuarios.py`
- Create: `backend/app/routers/roles.py`
- Modify: `backend/app/routers/auditoria.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_audit.py`
- Test: `backend/tests/test_usuarios_roles.py`

**Interfaces:**
- Produces: `write_audit_log(usuario_id, accion, recurso, recurso_id, ip_origen, resultado, detalle, db=None) -> None` that persists an `AuditLog` row (opens its own session if `db` not given), `GET /auditoria/logs?limit=&accion=` (permission `auditoria:consultar`), `POST /usuarios` / `PATCH /usuarios/{id}` (permission `usuarios:gestionar`), `GET /roles` (permission `usuarios:gestionar`).

- [ ] **Step 1: Write failing test for real audit persistence**

```python
# backend/tests/test_audit.py
from app.database import SessionLocal
from app.models import AuditLog
from app.audit.logger import write_audit_log

def test_write_audit_log_persists_row():
    write_audit_log(
        usuario_id=None, accion="test_event", recurso="test_resource",
        recurso_id="abc", ip_origen="127.0.0.1", resultado="exito", detalle="unit test",
    )
    db = SessionLocal()
    row = db.query(AuditLog).filter(AuditLog.accion == "test_event").order_by(AuditLog.timestamp_evento.desc()).first()
    db.close()
    assert row is not None
    assert row.recurso == "test_resource"
    assert row.resultado == "exito"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_audit.py -v`
Expected: FAIL — the stub `write_audit_log` does nothing, so `row is None`.

- [ ] **Step 3: Implement real `backend/app/audit/logger.py`**

```python
from typing import Optional
from app.database import SessionLocal
from app.models import AuditLog

def write_audit_log(
    usuario_id: Optional[str],
    accion: str,
    recurso: str,
    recurso_id: Optional[str],
    ip_origen: Optional[str],
    resultado: str,
    detalle: Optional[str],
    db=None,
) -> None:
    owns_session = db is None
    session = db or SessionLocal()
    try:
        session.add(AuditLog(
            usuario_id=usuario_id, accion=accion, recurso=recurso,
            recurso_id=recurso_id, ip_origen=ip_origen, resultado=resultado, detalle=detalle,
        ))
        session.commit()
    finally:
        if owns_session:
            session.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_audit.py -v`
Expected: 1 passed

- [ ] **Step 5: Implement `GET /auditoria/logs` in `backend/app/routers/auditoria.py`**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditLog
from app.security.rbac import require_permission

router = APIRouter(prefix="/auditoria", tags=["auditoria"])

@router.get("/logs")
def list_logs(
    limit: int = Query(default=100, le=1000),
    accion: str | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("auditoria:consultar")),
):
    query = db.query(AuditLog)
    if accion:
        query = query.filter(AuditLog.accion == accion)
    rows = query.order_by(AuditLog.timestamp_evento.desc()).limit(limit).all()
    return [
        {
            "log_id": str(r.log_id), "usuario_id": str(r.usuario_id) if r.usuario_id else None,
            "accion": r.accion, "recurso": r.recurso, "recurso_id": r.recurso_id,
            "ip_origen": r.ip_origen, "resultado": r.resultado, "detalle": r.detalle,
            "timestamp_evento": str(r.timestamp_evento),
        }
        for r in rows
    ]
```

- [ ] **Step 6: Write failing test for user/role management**

```python
# backend/tests/test_usuarios_roles.py
from fastapi.testclient import TestClient
from app.main import app
from app.security import rbac

client = TestClient(app)

def test_admin_can_list_roles():
    app.dependency_overrides[rbac.get_current_user] = lambda: {"sub": "admin-1", "permisos": ["usuarios:gestionar"]}
    resp = client.get("/roles")
    assert resp.status_code == 200
    assert any(r["nombre"] == "administrador" for r in resp.json())
    app.dependency_overrides.clear()

def test_non_admin_cannot_create_user():
    app.dependency_overrides[rbac.get_current_user] = lambda: {"sub": "teleop-1", "permisos": ["clientes:ver_asignados"]}
    resp = client.post("/usuarios", json={
        "username": "nuevo.usuario", "nombre_completo": "Nuevo Usuario",
        "email_corporativo": "nuevo@bancoproyecto.pe", "password": "Sup3rSecret!Pass", "rol_id": 1,
    })
    assert resp.status_code == 403
    app.dependency_overrides.clear()
```

- [ ] **Step 7: Run test to verify it fails**

Run: `cd backend && pytest tests/test_usuarios_roles.py -v`
Expected: FAIL — `ModuleNotFoundError: app.routers.usuarios`

- [ ] **Step 8: Implement `backend/app/routers/roles.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Rol
from app.security.rbac import require_permission

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("")
def listar_roles(
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("usuarios:gestionar")),
):
    roles = db.query(Rol).all()
    return [{"rol_id": r.rol_id, "nombre": r.nombre, "descripcion": r.descripcion} for r in roles]
```

- [ ] **Step 9: Implement `backend/app/schemas/usuario.py` and `backend/app/routers/usuarios.py`**

```python
# backend/app/schemas/usuario.py
from pydantic import BaseModel, EmailStr

class UsuarioCreate(BaseModel):
    username: str
    nombre_completo: str
    email_corporativo: EmailStr
    password: str
    rol_id: int

class UsuarioUpdate(BaseModel):
    nombre_completo: str | None = None
    rol_id: int | None = None
    activo: bool | None = None
```

```python
# backend/app/routers/usuarios.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.security.hashing import hash_password, validate_password_policy
from app.security.rbac import require_permission
from app.audit.logger import write_audit_log

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.post("", status_code=201)
def crear_usuario(
    body: UsuarioCreate, request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("usuarios:gestionar")),
):
    errors = validate_password_policy(body.password)
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    usuario = Usuario(
        username=body.username, nombre_completo=body.nombre_completo,
        email_corporativo=body.email_corporativo,
        password_hash=hash_password(body.password), rol_id=body.rol_id,
    )
    db.add(usuario)
    db.commit()
    write_audit_log(usuario_id=user["sub"], accion="crear_usuario", recurso="usuario",
                     recurso_id=str(usuario.usuario_id),
                     ip_origen=request.client.host if request.client else None,
                     resultado="exito", detalle=body.username)
    return {"usuario_id": str(usuario.usuario_id)}

@router.patch("/{usuario_id}")
def actualizar_usuario(
    usuario_id: str, body: UsuarioUpdate, request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_permission("usuarios:gestionar")),
):
    usuario = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(usuario, field, value)
    db.add(usuario)
    db.commit()
    write_audit_log(usuario_id=user["sub"], accion="actualizar_usuario", recurso="usuario",
                     recurso_id=usuario_id, ip_origen=request.client.host if request.client else None,
                     resultado="exito", detalle=str(body.model_dump(exclude_unset=True)))
    return {"usuario_id": usuario_id}
```

- [ ] **Step 10: Register routers in `backend/app/main.py`**

```python
from app.routers import (
    auth, auditoria, clientes, consentimientos, campanias,
    asignaciones, metricas, usuarios, roles,
)
app.include_router(auth.router)
app.include_router(auditoria.router)
app.include_router(clientes.router)
app.include_router(consentimientos.router)
app.include_router(campanias.router)
app.include_router(asignaciones.router)
app.include_router(metricas.router)
app.include_router(usuarios.router)
app.include_router(roles.router)
```

- [ ] **Step 11: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_usuarios_roles.py tests/test_audit.py -v`
Expected: 3 passed

- [ ] **Step 12: Commit**

```bash
git add backend/app/audit/logger.py backend/app/routers/auditoria.py backend/app/routers/roles.py backend/app/routers/usuarios.py backend/app/schemas/usuario.py backend/app/main.py backend/tests/test_audit.py backend/tests/test_usuarios_roles.py
git commit -m "feat: persistent audit logging and user/role management endpoints"
```

---

## Task 10: TLS via Nginx + OpenSSL self-signed certs (§9.2.1, §10.2)

**Files:**
- Create: `infra/certs/gen_certs.sh`
- Create: `infra/nginx/nginx.conf`
- Modify: `infra/docker-compose.yml`

**Interfaces:**
- Produces: `infra/certs/server.key`, `infra/certs/server.crt` (gitignored), an Nginx service in `docker-compose.yml` proxying `https://localhost:8443` → backend `http://backend:8000` and → frontend static files.

- [ ] **Step 1: Write `infra/certs/gen_certs.sh`** (exact commands from §10.2)

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

openssl genrsa -out server.key 2048

openssl req -new -key server.key -out server.csr \
  -subj "/C=PE/ST=Lima/O=BancoProyecto/CN=localhost"

openssl x509 -req -days 365 -in server.csr \
  -signkey server.key -out server.crt

echo "Certificados generados: server.key, server.crt"
```

- [ ] **Step 2: Make it executable and run it**

```bash
chmod +x infra/certs/gen_certs.sh
./infra/certs/gen_certs.sh
```

Expected: `server.key` and `server.crt` created in `infra/certs/`.

- [ ] **Step 3: Write `infra/nginx/nginx.conf`**

```nginx
events {}

http {
    server {
        listen 8443 ssl;
        server_name localhost;

        ssl_certificate     /etc/nginx/certs/server.crt;
        ssl_certificate_key /etc/nginx/certs/server.key;
        ssl_protocols       TLSv1.2 TLSv1.3;

        location /api/ {
            proxy_pass http://backend:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location / {
            root /usr/share/nginx/html;
            try_files $uri /index.html;
        }
    }

    server {
        listen 8080;
        server_name localhost;
        return 301 https://$host:8443$request_uri;
    }
}
```

- [ ] **Step 4: Add `backend` and `nginx` services to `infra/docker-compose.yml`** (no `db` service — Postgres is the externally managed Railway instance; `backend` reaches it via `DATABASE_URL` in `backend/.env`, which must hold the **public** Railway proxy URL since these containers run on the developer's machine, not inside Railway's network)

```yaml
services:
  backend:
    build: ../backend
    env_file: ../backend/.env
    ports:
      - "8000:8000"

  nginx:
    image: nginx:1.27
    depends_on:
      - backend
    ports:
      - "8443:8443"
      - "8080:8080"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
      - ../frontend/dist:/usr/share/nginx/html:ro
```

- [ ] **Step 5: Create `backend/Dockerfile`** so `backend` builds in compose

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 6: Verify TLS end-to-end**

```bash
cd infra
docker compose up -d
curl -k https://localhost:8443/api/health
```

Expected: `{"status":"ok"}` returned over HTTPS; `curl -k` needed only because the cert is self-signed (expected in this academic prototype per §10.2).

- [ ] **Step 7: Commit**

```bash
git add infra/certs/gen_certs.sh infra/nginx/nginx.conf infra/docker-compose.yml backend/Dockerfile
git commit -m "feat: TLS termination via nginx with OpenSSL self-signed certificate"
```

---

## Task 11: Encrypted backup script (§10.1.3, Cuadro 14)

**Files:**
- Create: `infra/backup/run_backup.sh`
- Create: `infra/backup/restore_backup.sh`
- Test: `backend/tests/test_backup_script.py`

**Interfaces:**
- Produces: `infra/backup/run_backup.sh` — runs `pg_dump`, encrypts the output with AES-256 via OpenSSL using `BACKUP_ENCRYPTION_KEY`, writes to `backups/<timestamp>.sql.enc`. `restore_backup.sh <file>` reverses it.

- [ ] **Step 1: Write `infra/backup/run_backup.sh`** (reads the Railway connection string from `backend/.env` at runtime — never hardcode it in the script)

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR="../../backups"
mkdir -p "$OUT_DIR"

: "${BACKUP_ENCRYPTION_KEY:?Set BACKUP_ENCRYPTION_KEY in the environment}"

# DATABASE_URL_RAW must be the postgresql:// (no +psycopg2) form of Railway's public proxy URL,
# exported from backend/.env, e.g.:
#   export DATABASE_URL_RAW="$(grep DATABASE_URL ../../backend/.env | cut -d= -f2- | sed 's/+psycopg2//')"
: "${DATABASE_URL_RAW:?Set DATABASE_URL_RAW to the postgresql:// Railway public connection string}"

pg_dump "$DATABASE_URL_RAW" \
  | openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_ENCRYPTION_KEY \
  > "$OUT_DIR/backup_${TIMESTAMP}.sql.enc"

echo "Backup cifrado creado en $OUT_DIR/backup_${TIMESTAMP}.sql.enc"
```

- [ ] **Step 2: Write `infra/backup/restore_backup.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

FILE="${1:?Uso: restore_backup.sh <archivo.sql.enc>}"
: "${BACKUP_ENCRYPTION_KEY:?Set BACKUP_ENCRYPTION_KEY in the environment}"
: "${DATABASE_URL_RAW:?Set DATABASE_URL_RAW to the postgresql:// Railway public connection string}"

openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_ENCRYPTION_KEY -in "$FILE" \
  | psql "$DATABASE_URL_RAW"

echo "Restauración completada desde $FILE"
```

- [ ] **Step 3: Make both scripts executable**

```bash
chmod +x infra/backup/run_backup.sh infra/backup/restore_backup.sh
```

- [ ] **Step 4: Write a smoke test verifying the roundtrip using a temp directory (not the real DB)**

```python
# backend/tests/test_backup_script.py
import os
import subprocess
import tempfile

def test_backup_and_restore_roundtrip_with_plain_file():
    key = "test-backup-key-0123456789"
    with tempfile.TemporaryDirectory() as tmp:
        plain_path = os.path.join(tmp, "sample.sql")
        enc_path = os.path.join(tmp, "sample.sql.enc")
        dec_path = os.path.join(tmp, "sample.decrypted.sql")
        with open(plain_path, "w") as f:
            f.write("SELECT 1;")

        subprocess.run(
            ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt",
             "-pass", f"pass:{key}", "-in", plain_path, "-out", enc_path],
            check=True,
        )
        subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
             "-pass", f"pass:{key}", "-in", enc_path, "-out", dec_path],
            check=True,
        )
        with open(dec_path) as f:
            assert f.read() == "SELECT 1;"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_backup_script.py -v`
Expected: 1 passed (validates the same OpenSSL AES-256-CBC/PBKDF2 roundtrip used by the backup scripts).

- [ ] **Step 6: Commit**

```bash
git add infra/backup backend/tests/test_backup_script.py
git commit -m "feat: encrypted PostgreSQL backup and restore scripts"
```

---

## Task 12: Frontend scaffold, auth context, login page (§9.1.2 flow 1)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/auth/AuthContext.tsx`
- Create: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/App.tsx`

**Interfaces:**
- Produces: `apiClient` (axios instance with `baseURL="/api"`, attaches `Authorization: Bearer <token>`), `AuthProvider`/`useAuth()` exposing `{ token, rol, permisos, login(username, password), logout() }`, `<Login />` page posting to `/api/auth/login`.

- [ ] **Step 1: Scaffold with Vite**

```bash
cd /Users/angel/etica_seguridad_datos/proyecto
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install axios react-router-dom
```

- [ ] **Step 2: `frontend/vite.config.ts`** — proxy `/api` to the backend during dev

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

- [ ] **Step 3: `frontend/src/api/client.ts`**

```typescript
import axios from "axios";

export const apiClient = axios.create({ baseURL: "/api" });

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

- [ ] **Step 4: `frontend/src/auth/AuthContext.tsx`**

```tsx
import { createContext, useContext, useState, ReactNode } from "react";
import { apiClient } from "../api/client";

type AuthState = {
  token: string | null;
  rol: string | null;
  permisos: string[];
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | undefined>(undefined);

function decodeJwtPayload(token: string): { rol: string; permisos: string[] } {
  const payload = JSON.parse(atob(token.split(".")[1]));
  return { rol: payload.rol, permisos: payload.permisos };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [rol, setRol] = useState<string | null>(null);
  const [permisos, setPermisos] = useState<string[]>([]);

  async function login(username: string, password: string) {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);
    const resp = await apiClient.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    const accessToken = resp.data.access_token as string;
    localStorage.setItem("access_token", accessToken);
    const decoded = decodeJwtPayload(accessToken);
    setToken(accessToken);
    setRol(decoded.rol);
    setPermisos(decoded.permisos);
  }

  function logout() {
    localStorage.removeItem("access_token");
    setToken(null);
    setRol(null);
    setPermisos([]);
  }

  return (
    <AuthContext.Provider value={{ token, rol, permisos, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
```

- [ ] **Step 5: `frontend/src/pages/Login.tsx`**

```tsx
import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(username, password);
      navigate("/");
    } catch {
      setError("Usuario o contraseña incorrectos.");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Ingreso al Sistema</h1>
      <label>
        Usuario
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />
      </label>
      <label>
        Contraseña
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit">Ingresar</button>
    </form>
  );
}
```

- [ ] **Step 6: `frontend/src/App.tsx`** and `frontend/src/main.tsx`

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import Login from "./pages/Login";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" replace />;
}

function Home() {
  const { rol, logout } = useAuth();
  return (
    <div>
      <p>Sesión iniciada como: {rol}</p>
      <button onClick={logout}>Cerrar sesión</button>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
```

```tsx
// frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 7: Run dev server and manually verify login**

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173/login`, log in with a seeded user (e.g. `carlos.test` if Task 6's test user exists, or a seeded teleoperador from Task 5) and confirm redirect to `/` shows the role.

- [ ] **Step 8: Commit**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/src
git commit -m "feat: frontend scaffold with JWT auth context and login page"
```

---

## Task 13: Role-scoped dashboards (§9.1.1 actors, CU-02..CU-10)

**Files:**
- Create: `frontend/src/pages/admin/Users.tsx`
- Create: `frontend/src/pages/admin/AuditLog.tsx`
- Create: `frontend/src/pages/supervisor/Metrics.tsx`
- Create: `frontend/src/pages/supervisor/Assignments.tsx`
- Create: `frontend/src/pages/analista/PrioritizedClients.tsx`
- Create: `frontend/src/pages/teleoperador/MyClients.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `apiClient`, `useAuth()`.
- Produces: one route per role gated by `rol`, e.g. `/admin/usuarios`, `/admin/auditoria`, `/supervisor/metricas`, `/supervisor/asignaciones`, `/analista/clientes`, `/teleoperador/mis-clientes`.

- [ ] **Step 1: `frontend/src/pages/admin/Users.tsx`**

```tsx
import { useEffect, useState } from "react";
import { apiClient } from "../../api/client";

type Rol = { rol_id: number; nombre: string; descripcion: string };

export default function Users() {
  const [roles, setRoles] = useState<Rol[]>([]);
  const [form, setForm] = useState({ username: "", nombre_completo: "", email_corporativo: "", password: "", rol_id: 0 });
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    apiClient.get("/roles").then((resp) => setRoles(resp.data));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await apiClient.post("/usuarios", form);
      setMessage("Usuario creado correctamente.");
    } catch {
      setMessage("No se pudo crear el usuario.");
    }
  }

  return (
    <div>
      <h2>Gestión de usuarios internos</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Usuario" onChange={(e) => setForm({ ...form, username: e.target.value })} />
        <input placeholder="Nombre completo" onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })} />
        <input placeholder="Email corporativo" onChange={(e) => setForm({ ...form, email_corporativo: e.target.value })} />
        <input placeholder="Contraseña temporal" type="password" onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <select onChange={(e) => setForm({ ...form, rol_id: Number(e.target.value) })}>
          <option value="">Seleccione un rol</option>
          {roles.map((r) => <option key={r.rol_id} value={r.rol_id}>{r.nombre}</option>)}
        </select>
        <button type="submit">Crear usuario</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}
```

- [ ] **Step 2: `frontend/src/pages/admin/AuditLog.tsx`**

```tsx
import { useEffect, useState } from "react";
import { apiClient } from "../../api/client";

type LogEntry = {
  log_id: string; accion: string; recurso: string; resultado: string; timestamp_evento: string;
};

export default function AuditLogPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    apiClient.get("/auditoria/logs").then((resp) => setLogs(resp.data));
  }, []);

  return (
    <div>
      <h2>Registros de auditoría</h2>
      <table>
        <thead><tr><th>Acción</th><th>Recurso</th><th>Resultado</th><th>Fecha</th></tr></thead>
        <tbody>
          {logs.map((l) => (
            <tr key={l.log_id}>
              <td>{l.accion}</td><td>{l.recurso}</td><td>{l.resultado}</td><td>{l.timestamp_evento}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 3: `frontend/src/pages/supervisor/Metrics.tsx`**

```tsx
import { useState } from "react";
import { apiClient } from "../../api/client";

export default function Metrics() {
  const [campaniaId, setCampaniaId] = useState("");
  const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null);

  async function fetchMetrics() {
    const resp = await apiClient.get(`/metricas/campania/${campaniaId}`);
    setMetrics(resp.data);
  }

  return (
    <div>
      <h2>Métricas de campaña</h2>
      <input placeholder="ID de campaña" value={campaniaId} onChange={(e) => setCampaniaId(e.target.value)} />
      <button onClick={fetchMetrics}>Consultar</button>
      {metrics && <pre>{JSON.stringify(metrics, null, 2)}</pre>}
    </div>
  );
}
```

- [ ] **Step 4: `frontend/src/pages/supervisor/Assignments.tsx`**

```tsx
import { useState } from "react";
import { apiClient } from "../../api/client";

export default function Assignments() {
  const [form, setForm] = useState({ cliente_id: "", campania_id: "", usuario_id: "" });
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await apiClient.post("/asignaciones", form);
      setMessage("Cliente asignado correctamente.");
    } catch {
      setMessage("No se pudo asignar (verifique el consentimiento del cliente).");
    }
  }

  return (
    <div>
      <h2>Asignar cliente a teleoperador</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Cliente ID" onChange={(e) => setForm({ ...form, cliente_id: e.target.value })} />
        <input placeholder="Campaña ID" onChange={(e) => setForm({ ...form, campania_id: e.target.value })} />
        <input placeholder="Teleoperador ID" onChange={(e) => setForm({ ...form, usuario_id: e.target.value })} />
        <button type="submit">Asignar</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}
```

- [ ] **Step 5: `frontend/src/pages/analista/PrioritizedClients.tsx`**

```tsx
import { useEffect, useState } from "react";
import { apiClient } from "../../api/client";

type Cliente = { cliente_id: string; age: number; job: string; balance: string; estado_consentimiento: string };

export default function PrioritizedClients() {
  const [clientes, setClientes] = useState<Cliente[]>([]);

  useEffect(() => {
    apiClient.get("/clientes/elegibles").then((resp) => setClientes(resp.data));
  }, []);

  return (
    <div>
      <h2>Clientes priorizados</h2>
      <table>
        <thead><tr><th>Edad</th><th>Ocupación</th><th>Balance</th><th>Consentimiento</th></tr></thead>
        <tbody>
          {clientes.map((c) => (
            <tr key={c.cliente_id}>
              <td>{c.age}</td><td>{c.job}</td><td>{c.balance}</td><td>{c.estado_consentimiento}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 6: `frontend/src/pages/teleoperador/MyClients.tsx`**

```tsx
import { useEffect, useState } from "react";
import { apiClient } from "../../api/client";

type Asignacion = { asignacion_id: string; cliente_id: string; estado_contacto: string };

export default function MyClients() {
  const [asignaciones, setAsignaciones] = useState<Asignacion[]>([]);
  const [observacion, setObservacion] = useState("");

  useEffect(() => {
    apiClient.get("/asignaciones/mias").then((resp) => setAsignaciones(resp.data));
  }, []);

  async function registrarResultado(asignacionId: string, resultado: string) {
    await apiClient.post(`/asignaciones/${asignacionId}/resultado`, { resultado, observacion });
    const resp = await apiClient.get("/asignaciones/mias");
    setAsignaciones(resp.data);
  }

  return (
    <div>
      <h2>Mis clientes asignados</h2>
      <input placeholder="Observación" value={observacion} onChange={(e) => setObservacion(e.target.value)} />
      <ul>
        {asignaciones.map((a) => (
          <li key={a.asignacion_id}>
            Cliente {a.cliente_id} — {a.estado_contacto}
            <button onClick={() => registrarResultado(a.asignacion_id, "contactado_interesado")}>Interesado</button>
            <button onClick={() => registrarResultado(a.asignacion_id, "contactado_no_interesado")}>No interesado</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 7: Wire routes into `frontend/src/App.tsx`** (append inside `<Routes>`, each wrapped in `RequireAuth` plus a role check)

```tsx
import Users from "./pages/admin/Users";
import AuditLogPage from "./pages/admin/AuditLog";
import Metrics from "./pages/supervisor/Metrics";
import Assignments from "./pages/supervisor/Assignments";
import PrioritizedClients from "./pages/analista/PrioritizedClients";
import MyClients from "./pages/teleoperador/MyClients";

function RequireRole({ roles, children }: { roles: string[]; children: JSX.Element }) {
  const { rol } = useAuth();
  return rol && roles.includes(rol) ? children : <Navigate to="/" replace />;
}

// inside <Routes>, in addition to /login and /:
<Route path="/admin/usuarios" element={<RequireAuth><RequireRole roles={["administrador"]}><Users /></RequireRole></RequireAuth>} />
<Route path="/admin/auditoria" element={<RequireAuth><RequireRole roles={["administrador", "supervisor"]}><AuditLogPage /></RequireRole></RequireAuth>} />
<Route path="/supervisor/metricas" element={<RequireAuth><RequireRole roles={["supervisor", "administrador"]}><Metrics /></RequireRole></RequireAuth>} />
<Route path="/supervisor/asignaciones" element={<RequireAuth><RequireRole roles={["supervisor", "administrador"]}><Assignments /></RequireRole></RequireAuth>} />
<Route path="/analista/clientes" element={<RequireAuth><RequireRole roles={["analista", "supervisor", "administrador"]}><PrioritizedClients /></RequireRole></RequireAuth>} />
<Route path="/teleoperador/mis-clientes" element={<RequireAuth><RequireRole roles={["teleoperador"]}><MyClients /></RequireRole></RequireAuth>} />
```

- [ ] **Step 8: Manually verify each role sees only its pages**

```bash
cd frontend && npm run dev
```

Log in as a seeded `teleoperador` and confirm navigating to `/admin/usuarios` redirects to `/`; repeat for `administrador` confirming it can reach `/admin/usuarios`.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/pages frontend/src/App.tsx
git commit -m "feat: role-scoped dashboards for admin, supervisor, analista, teleoperador"
```

---

## Task 14: Security test suite for Bloque V §11.2 (RBAC, consent, auth, TLS, SQLi)

**Files:**
- Create: `backend/tests/test_rbac_matrix.py`
- Create: `backend/tests/test_sql_injection.py`
- Create: `backend/tests/test_tls_smoke.py`

**Interfaces:**
- Consumes: existing routers and `require_permission`.
- Produces: automated coverage for every bullet in §11.2 ("Pruebas de seguridad").

- [ ] **Step 1: Write `backend/tests/test_rbac_matrix.py`** verifying Cuadro 15 for the two hardest rows (teleoperador cannot manage users; teleoperador cannot see unassigned clients)

```python
from fastapi.testclient import TestClient
from app.main import app
from app.security import rbac

client = TestClient(app)

def test_teleoperador_cannot_manage_usuarios():
    app.dependency_overrides[rbac.get_current_user] = lambda: {"sub": "t1", "permisos": ["clientes:ver_asignados"]}
    resp = client.post("/usuarios", json={
        "username": "x", "nombre_completo": "X", "email_corporativo": "x@bancoproyecto.pe",
        "password": "Sup3rSecret!Pass", "rol_id": 1,
    })
    assert resp.status_code == 403
    app.dependency_overrides.clear()

def test_teleoperador_cannot_list_all_eligible_clients_without_permission():
    app.dependency_overrides[rbac.get_current_user] = lambda: {"sub": "t1", "permisos": ["clientes:ver_asignados"]}
    resp = client.get("/clientes/elegibles")
    assert resp.status_code == 403
    app.dependency_overrides.clear()

def test_analista_cannot_create_campania():
    app.dependency_overrides[rbac.get_current_user] = lambda: {"sub": "a1", "permisos": ["clientes:ver_parcial", "campanias:consultar"]}
    resp = client.post("/campanias", json={
        "nombre": "x", "producto": "y", "fecha_inicio": "2026-01-01", "estado": "activa",
    })
    assert resp.status_code == 403
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails first (sanity: none of these routes should currently allow it, so this should pass immediately — run to confirm no regressions)**

Run: `cd backend && pytest tests/test_rbac_matrix.py -v`
Expected: 3 passed (if any fail, the corresponding router in Task 6-9 is missing its `require_permission` guard — fix it there).

- [ ] **Step 3: Write `backend/tests/test_sql_injection.py`**

```python
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Cliente, Consentimiento
from app.security import rbac

client = TestClient(app)

def test_accion_filter_is_parameterized_and_rejects_injection_payload():
    app.dependency_overrides[rbac.get_current_user] = lambda: {"sub": "admin-1", "permisos": ["auditoria:consultar"]}
    payload = "x'; DROP TABLE audit_log; --"
    resp = client.get("/auditoria/logs", params={"accion": payload})
    assert resp.status_code == 200
    db = SessionLocal()
    from app.models import AuditLog
    count = db.query(AuditLog).count()
    db.close()
    assert count >= 0  # table still exists; query didn't error
    app.dependency_overrides.clear()

def test_consent_update_rejects_invalid_state_instead_of_executing_arbitrary_sql():
    db = SessionLocal()
    cid = uuid.uuid4()
    db.add(Cliente(cliente_id=cid, age=25, job="student", deposit="no"))
    db.add(Consentimiento(cliente_id=cid, estado="opt-in"))
    db.commit()
    db.close()

    app.dependency_overrides[rbac.get_current_user] = lambda: {"sub": "s1", "permisos": ["clientes:ver_sensible"]}
    resp = client.patch(f"/consentimientos/{cid}", json={"estado": "opt-in'; DROP TABLE cliente; --"})
    assert resp.status_code == 422
    app.dependency_overrides.clear()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_sql_injection.py -v`
Expected: 2 passed

- [ ] **Step 5: Write `backend/tests/test_tls_smoke.py`** (skips if the stack isn't running locally, documents the manual check from §11.2)

```python
import socket
import ssl
import pytest

def test_nginx_tls_endpoint_accepts_tls_1_2_or_higher():
    try:
        sock = socket.create_connection(("localhost", 8443), timeout=2)
    except (ConnectionRefusedError, OSError):
        pytest.skip("Stack de infra (nginx) no está corriendo en este entorno de test")
    ctx = ssl._create_unverified_context()
    with ctx.wrap_socket(sock, server_hostname="localhost") as tls_sock:
        assert tls_sock.version() in ("TLSv1.2", "TLSv1.3")
    sock.close()
```

- [ ] **Step 6: Run full backend test suite**

Run: `cd backend && pytest -v`
Expected: all tests pass (the TLS test may skip if `docker compose up` from Task 10 isn't running; that's acceptable — run `docker compose -f infra/docker-compose.yml up -d` first to exercise it for real).

- [ ] **Step 7: Commit**

```bash
git add backend/tests/test_rbac_matrix.py backend/tests/test_sql_injection.py backend/tests/test_tls_smoke.py
git commit -m "test: security test suite covering RBAC matrix, SQLi resistance, and TLS"
```

---

## Task 15: Documentation deliverables (§11.3, §10.6, §10.7)

**Files:**
- Create: `docs/INSTALL.md`
- Create: `docs/incident_response_plan.md`
- Create: `docs/security_policies.md`
- Create: `README.md`

**Interfaces:**
- Produces: the four documents required for the final delivery in §11.3 ("Documentación final") beyond the report itself.

- [ ] **Step 1: Write `docs/INSTALL.md`** covering: prerequisites (Docker, Python 3.11, Node 18+), `.env` setup, `docker compose up -d db`, `alembic upgrade head`, `python -m app.seed.load_bank_csv`, `uvicorn app.main:app --reload`, `npm run dev` / `npm run build`, and the full-stack TLS path via `docker compose up -d` in `infra/`.

- [ ] **Step 2: Write `docs/incident_response_plan.md`** transcribing and operationalizing the NIST SP 800-61 stages from §10.6 and the P1/P2/P3 table (Cuadro 17): preparación, detección, contención (bloqueo de cuentas comprometidas + `UPDATE usuario SET activo=false`, revocación de sesiones by rotating `JWT_SECRET`), recuperación, revisión posterior, and the ANPDP notification obligation from §8 (D.S. 016-2024-JUS) with the response-time targets (<4h P1, <24h P2, <72h P3).

- [ ] **Step 3: Write `docs/security_policies.md`** transcribing the password policy (§10.7.1: min 12 chars, breach-list check, lockout, no forced periodic rotation) and staff training topics (§10.7.2: phishing, social engineering, secure session use, incident reporting), plus the backup policy table (Cuadro 14) and the RBAC matrix (Cuadro 15) as the living reference for future admins.

- [ ] **Step 4: Write `README.md`** at repo root summarizing the project (link back to `Proyecto___Grupo_1___EyS.pdf`), architecture diagram description, quick-start pointing to `docs/INSTALL.md`, and a table mapping each Bloque of the PDF to the corresponding code/docs artifact (Bloque III → `backend/app/models` + `backend/alembic`; Bloque IV → `backend/app/security`, `infra/certs`, `infra/backup`, `docs/incident_response_plan.md`; Bloque V → `backend/tests`, `docs/INSTALL.md`).

- [ ] **Step 5: Commit**

```bash
git add docs/INSTALL.md docs/incident_response_plan.md docs/security_policies.md README.md
git commit -m "docs: installation guide, incident response plan, and security policies"
```

---

## Task 16: Final end-to-end verification against the PDF's scope

**Files:** none created — this task is a verification pass only.

- [ ] **Step 1: Run the entire backend test suite with coverage**

```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

Expected: all tests pass; review coverage gaps in `app/routers` and `app/security`.

- [ ] **Step 2: Bring up the full stack and smoke-test each role manually**

```bash
cd infra
docker compose up -d
```

Log in via `https://localhost:8443` (accept the self-signed cert warning) as one seeded user per role (`administrador`, `supervisor`, `analista`, `teleoperador` from Task 5's seed) and confirm each lands on its own dashboard with no access to others' routes (Task 13's `RequireRole` guards).

- [ ] **Step 3: Verify KR 2.3 (100% audit coverage) empirically**

```bash
curl -k -X POST https://localhost:8443/api/auth/login -d "username=<seeded>&password=<default>"
curl -k -H "Authorization: Bearer <token>" https://localhost:8443/api/auditoria/logs
```

Expected: the login itself appears as a `login_exitoso` row, confirming the flow from Task 9 fires on every authenticated action exercised in Step 2.

- [ ] **Step 4: Cross-check every PDF requirement against delivered artifacts**

Confirm each row of Cuadro 13 (RF-01..RF-16) maps to a passing test or manual check performed above; confirm Alcance (§4) items are all present (DB model ✓ Task 2, backend auth/authorization/filtered endpoints ✓ Tasks 6-9, minimal frontend per role ✓ Tasks 12-13, self-signed TLS certs ✓ Task 10, policy/incident/backup docs ✓ Tasks 11 & 15); confirm nothing from "Fuera de alcance" was accidentally built (no real ML model, no real bank integration, no public CA, no SIEM).

- [ ] **Step 5: Final commit tagging the prototype milestone**

```bash
git add -A
git commit -m "chore: prototype complete — full coverage of PDF Bloques III-V"
git tag v0.1.0-prototype
```
