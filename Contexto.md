# Contexto Completo del Proyecto

## Resumen General

**Proyecto Ética y Seguridad de Datos** es un sistema bancario integral diseñado como demostración de mejores prácticas en seguridad, privacidad y compliance. Es un sistema de **gestión de campañas bancarias** con controles robustos de acceso, encriptación y auditoría.

---

## Propósito Principal

Crear una plataforma funcional que demuestre cómo manejar datos sensibles (información de clientes bancarios) cumpliendo con:
- **Privacidad diferencial**: técnicas estadísticas para proteger datos individuales
- **Seguridad**: encriptación, hashing seguro, bloqueos por intentos fallidos
- **Auditoría completa**: registro de todas las acciones para compliance
- **Control de acceso basado en roles (RBAC)**: diferentes permisos por rol de usuario

---

## Arquitectura Técnica

### Stack Tecnológico
- **Backend**: FastAPI (Python 3.11+) con SQLAlchemy ORM
- **Base de Datos**: PostgreSQL
- **Frontend**: React + TypeScript + Vite
- **Infraestructura**: Docker Compose, Nginx con HTTPS local

### Componentes Principales

| Componente | Descripción |
|-----------|------------|
| **Backend** | API REST que gestiona lógica de negocio, seguridad y datos |
| **Frontend** | Consola web con interfaz específica por rol de usuario |
| **Infraestructura** | Demo integrada con Docker, HTTPS, backups cifrados |
| **Documentación** | Informes, guías operativas y evidencias técnicas |

---

## Funcionalidades Implementadas

### 🔐 Seguridad
- **Autenticación JWT**: tokens seguros para sesiones de usuario
- **RBAC (Role-Based Access Control)**: cuatro roles con permisos diferenciados
  - Administrador
  - Supervisor
  - Analista
  - Teleoperador
- **Encriptación AES-GCM**: protección de datos personales (PII)
- **Hashing Argon2**: contraseñas hash seguro
- **Bloqueo por intentos fallidos**: prevención de fuerza bruta

### 📊 Operacional
- **Gestión de clientes**: base de datos de clientes (dataset "Bank Marketing")
- **Gestión de consentimiento**: control `opt-in` de clientes para contacto
- **Campañas bancarias**: crear y gestionar campañas de marketing/contacto
- **Asignaciones**: distribuir clientes entre teleoperadores
- **Registro de resultados**: documentar outcome de cada contacto
- **Gestión de usuarios y roles**: CRUD de usuarios, permisos granulares

### 🔍 Auditoría & Compliance
- **Auditoría real en BD**: tabla `audit_log` que registra:
  - Quién realizó la acción
  - Qué se modificó
  - Cuándo ocurrió
  - Detalles de cambios
- **Trazabilidad completa**: cada operación está registrada

### 📈 Privacidad Diferencial
- **Notebook de privacidad diferencial**: análisis estadístico de datos sin exponer información individual
- *(Nota: hay un issue pendiente de compatibilidad entre diffprivlib y SciPy)*

---

## Estructura de Carpetas

```
backend/           → API FastAPI completa con routers, modelos, tests
├── app/
│   ├── main.py    → Punto de entrada
│   ├── routers/   → Endpoints por dominio (clientes, campañas, auditoría, etc.)
│   ├── models/    → Modelos SQLAlchemy
│   ├── schemas/   → Esquemas Pydantic para validación
│   ├── security/  → JWT, encriptación, hash
│   └── seed/      → Scripts para cargar datos iniciales
├── tests/         → Suite de tests completa

frontend/          → React + TypeScript + Vite
├── src/
│   ├── components/   → Componentes por rol
│   ├── pages/        → Vistas principales
│   └── api/          → Cliente HTTP para backend
├── public/         → Assets estáticos
└── package.json    → Dependencias Node.js

infra/             → Infraestructura
├── docker-compose.yml    → Orquestación de servicios
├── nginx/                → Configuración reversa proxy + HTTPS
├── certs/                → Certificados autofirmados
└── backups/              → Scripts de backup cifrado

docs/              → Documentación técnica
├── GUIA_OPERATIVA.md     → Cómo usar el sistema
├── INFORME_FINAL.md      → Análisis y conclusiones
└── ANALISIS_INICIAL.md   → Contexto histórico

notebooks/         → Jupyter notebooks de análisis
bank.csv           → Dataset base (Bank Marketing)
```

---

## Estado Actual

### ✅ Completado
- Flujo bancario principal funcional
- Todos los tests del flujo principal pasan
- Frontend compila sin errores (`npm run build`)
- Infraestructura Docker lista para demostración
- Documentación operativa disponible

### ⚠️ Pendiente
- 1 test falla en suite completa (`test_dp.py`): incompatibilidad entre `diffprivlib` y versión de SciPy (parámetro `iprint` deprecado)

---

## Flujo de Demostración

1. **Login**: Acceder como supervisor/administrador
2. **Revisar clientes**: Ver clientes bancarios elegibles
3. **Crear campaña**: Establecer una nueva campaña de contacto
4. **Asignar clientes**: Distribuir clientes `opt-in` entre teleoperadores
5. **Contactar**: Login como teleoperador y registrar resultados
6. **Auditar**: Login como admin y revisar log de auditoría para compliance

---

## Requisitos Técnicos

- Python 3.11+
- Node.js 22+
- PostgreSQL (o SQLite para desarrollo)
- Docker & Docker Compose (para demo integrada)

---

## Usuarios Demo

**Contraseña inicial**: `CambiarEnPrimerAcceso!123`

**Roles disponibles**:
- Administrador (acceso total)
- Supervisor (gestión de campañas)
- Analista (reportes y análisis)
- Teleoperador (contacto directo)

---

## Objetivo Educativo

Este proyecto demuestra a desarrolladores y stakeholders cómo construir un sistema financiero/bancario que:
- Protege datos sensibles sin comprometer la funcionalidad
- Mantiene trazabilidad completa para auditoría
- Implementa seguridad en capas (autenticación, autorización, encriptación, hashing)
- Utiliza técnicas avanzadas como privacidad diferencial
- Puede desplegarse de forma segura en producción

**En resumen**: Es un MVP (Minimum Viable Product) realista de una plataforma bancaria segura, con todas las capas de protección que requieren sistemas financieros reales.