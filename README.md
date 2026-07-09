# Proyecto Ética y Seguridad de Datos

Sistema de apoyo a campañas bancarias con controles de seguridad, privacidad diferencial y una consola web por roles.

## Estado Actual

El flujo bancario principal está implementado:

- Login JWT y RBAC por permisos.
- Cifrado de PII con AES-GCM.
- Hashing Argon2 y bloqueo por intentos fallidos.
- Auditoría real en `audit_log`.
- Clientes elegibles filtrados por consentimiento `opt-in`.
- Gestión de consentimiento.
- Campañas, asignaciones y resultados de contacto.
- Gestión básica de usuarios, roles y permisos.
- Frontend React para operación por rol.
- Infra demo con Docker Compose, Nginx HTTPS local y scripts de backup cifrado.

Estado de validación:

- Frontend: `npm run build` pasa.
- Backend flujo bancario: tests pasan.
- Backend suite completa: queda 1 fallo en privacidad diferencial por compatibilidad `diffprivlib`/SciPy (`fmin_l_bfgs_b()` ya no acepta `iprint`).

## Estructura

```text
backend/     API FastAPI, modelos SQLAlchemy, seguridad, routers y tests
frontend/    App React + TypeScript + Vite
infra/       Docker Compose, Nginx, certificados y backups
docs/        Informe, guía operativa, planes y evidencias
notebooks/   Notebook de privacidad diferencial
bank.csv     Dataset Bank Marketing
```

## Requisitos

- Python 3.11 o superior.
- Node.js 22 o compatible.
- PostgreSQL para ejecución persistente.
- Docker y Docker Compose para la demo integrada.

## Backend Local

```bash
cd backend
cp .env.example .env
```

Configura `backend/.env` con:

```env
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
FIELD_ENCRYPTION_KEY=change-me-32-byte-base64-key==
BACKUP_ENCRYPTION_KEY=change-me-32-byte-base64-key==
```

Instala dependencias y ejecuta:

```bash
uv pip install -e ".[dev,notebook]"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Healthcheck:

```bash
curl http://127.0.0.1:8000/health
```

Tests del flujo bancario:

```bash
cd backend
./.venv/bin/python -m pytest tests/test_audit_logger.py tests/test_auditoria_router.py tests/test_clientes.py tests/test_consentimientos.py tests/test_campanias.py tests/test_asignaciones.py tests/test_usuarios.py -q
```

Suite completa:

```bash
cd backend
./.venv/bin/python -m pytest -q
```

Nota: la suite completa aún puede fallar en `tests/test_dp.py::test_dp_model_returns_metrics_and_baseline` por incompatibilidad entre `diffprivlib` y la versión instalada de SciPy.

## Frontend Local

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Build:

```bash
cd frontend
npm run build
```

La app usa `VITE_API_BASE_URL`; por defecto apunta a `http://localhost:8000`.

## Demo Con Docker Compose

Genera certificados autofirmados:

```bash
sh infra/certs/generate-self-signed.sh
```

Levanta la demo:

```bash
cd infra
docker compose up --build
```

URLs:

- Frontend HTTPS: `https://localhost:8443`
- HTTP local redirige desde `http://localhost:8080`

## Usuarios Demo

El seed genera usuarios internos por rol cuando se ejecuta `backend/app/seed/load_bank_csv.py`.

Contraseña inicial:

```text
CambiarEnPrimerAcceso!123
```

Roles esperados:

- `administrador`
- `supervisor`
- `analista`
- `teleoperador`

## Flujo De Demo

1. Iniciar sesión como supervisor o administrador.
2. Revisar clientes elegibles.
3. Crear o activar una campaña.
4. Asignar un cliente `opt-in` a un teleoperador.
5. Iniciar sesión como teleoperador.
6. Registrar resultado de contacto.
7. Iniciar sesión como administrador o auditor.
8. Revisar eventos en auditoría.

## Documentación

- [Guía operativa](docs/GUIA_OPERATIVA.md)
- [Informe final](docs/INFORME_FINAL.md)
- [Análisis inicial histórico](docs/ANALISIS_INICIAL.md)

