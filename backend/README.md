# Backend

API FastAPI para el sistema de campañas bancarias.

## Funcionalidad

- Auth con JWT.
- RBAC por permisos.
- Auditoría real en tabla `audit_log`.
- Cifrado de PII con AES-GCM.
- Hashing Argon2 y lockout de login.
- Clientes elegibles con filtro de consentimiento `opt-in`.
- Gestión de consentimiento.
- Campañas, asignaciones y resultados de contacto.
- Administración básica de usuarios, roles y permisos.
- Endpoints de privacidad diferencial bajo `/api`.

## Configuración

Crear `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
FIELD_ENCRYPTION_KEY=change-me-32-byte-base64-key==
BACKUP_ENCRYPTION_KEY=change-me-32-byte-base64-key==
```

## Ejecución

```bash
cd backend
uv pip install -e ".[dev,notebook]"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Endpoints Principales

- `POST /auth/login`
- `GET /clientes/elegibles`
- `GET /clientes/asignados`
- `GET /clientes/{cliente_id}`
- `GET /clientes/{cliente_id}/consentimiento`
- `PATCH /clientes/{cliente_id}/consentimiento`
- `GET /campanias`
- `POST /campanias`
- `PATCH /campanias/{campania_id}`
- `GET /campanias/{campania_id}/clientes-elegibles`
- `POST /asignaciones`
- `GET /asignaciones/mias`
- `POST /asignaciones/{asignacion_id}/resultado`
- `GET /usuarios`
- `GET /usuarios/teleoperadores`
- `POST /usuarios`
- `PATCH /usuarios/{usuario_id}/activo`
- `GET /roles`
- `GET /permisos`
- `GET /auditoria/logs`
- `GET /api/dataset/summary`
- `POST /api/dp/query`
- `POST /api/dp/model`
- `GET /api/dp/comparison`

## Tests

Tests del flujo bancario:

```bash
./.venv/bin/python -m pytest tests/test_audit_logger.py tests/test_auditoria_router.py tests/test_clientes.py tests/test_consentimientos.py tests/test_campanias.py tests/test_asignaciones.py tests/test_usuarios.py -q
```

Suite completa:

```bash
./.venv/bin/python -m pytest -q
```

Nota: la suite completa tiene un fallo pendiente en `tests/test_dp.py::test_dp_model_returns_metrics_and_baseline` por incompatibilidad `diffprivlib`/SciPy.

## Seed

Para cargar roles, usuarios, clientes y consentimientos desde `bank.csv`:

```bash
cd backend
python -m app.seed.load_bank_csv
```

Contraseña inicial de usuarios seed:

```text
CambiarEnPrimerAcceso!123
```

