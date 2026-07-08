# Análisis Inicial — Entrega Final DS3031 (Privacidad Diferencial)

Fecha del análisis: 2026-07-03
Rama actual: `feature/sistema-campanas-bancarias`

## 0. Nota importante sobre la fuente de verdad

Se pidió leer `docs/Esquema_Proyecto_de_Ética_y_Seguridad_de_datos__Final_.pdf`. **Ese archivo no existe en el repositorio.** Lo único presente en `docs/` es:

- `docs/Esquema Proyecto de Ética y Seguridad de datos (Parcial) .pdf` — es el esquema **Tipo 1** (seguridad), el mismo que rigió la entrega parcial. Rúbrica de 4 criterios a 4 puntos c/u (seguridad, funcionalidad, informe: contenido, diseño, informe: redacción — en realidad 5 filas de rúbrica ahí). **No menciona privacidad diferencial ni DPIA en ningún punto.**
- `Proyecto___Grupo_1___EyS.pdf` (raíz) — el informe ya entregado y calificado 10/10, 33 páginas.

No hay ningún PDF con "Final" en el nombre. Por lo tanto, para los criterios de la entrega final (informe con DPIA + reflexión ética, presentación, demo en vivo, requerimientos técnicos, 5 pts c/u = 20 pts) me baso **únicamente en la descripción que diste en el mensaje**, no en un documento fuente verificable. Si tienes el PDF del esquema final (probablemente el profesor lo compartió por separado, quizás "Tipo 2"), súbelo a `docs/` y ajusto el análisis — especialmente si trae sub-criterios o pesos distintos a los 4×5 que describiste.

## 1. Estado actual del repo, componente por componente

### `backend/` (FastAPI + SQLAlchemy + PostgreSQL en Railway)

Historial de commits confirma que se implementaron las **Tareas 1–6** de un plan de 7+ tareas documentado en `docs/superpowers/plans/2026-07-02-sistema-campanas-bancarias.md`:

| Componente | Estado | Detalle |
|---|---|---|
| Modelos SQLAlchemy | ✅ Completo | `rol, permiso, rol_permiso, usuario, cliente, consentimiento, campania, asignacion, resultado_contacto, audit_log` — 10 tablas, migración Alembic aplicada (`93ea5a51b955_initial_schema...py`) |
| Hashing de contraseñas | ✅ Completo | Argon2id (`memory_cost=65536, time_cost=3`), política de longitud mínima 12 |
| Lockout de login | ✅ Completo | Bloqueo tras 5 intentos, 15 min |
| Cifrado de PII | ✅ Completo | AES-256-GCM (`crypto.py`), nonce aleatorio por campo, clave en `.env` |
| Generación de datos sintéticos | ✅ Completo | Faker (`es_MX`, corregido desde `es_ES`), seed 42, genera cliente/consentimiento/roles/usuarios ligados a `bank.csv` |
| Auth JWT | ✅ Completo | `POST /auth/login`, tokens con `sub/rol/permisos`, dependencia `get_current_user` |
| RBAC | ✅ Completo | `require_permission(...)` como dependencia FastAPI, 403 + auditoría en denegado |
| **Audit logger real** | ⚠️ **Stub** | `app/audit/logger.py` solo tiene `def write_audit_log(**kwargs): pass` — nunca escribe a la tabla `audit_log`. Esto es Tarea 8 del plan original, nunca ejecutada. |
| Endpoints de clientes/consentimiento | ❌ No implementado | Existe `.superpowers/sdd/task-7-brief.md` (briefed) pero no `task-7-report.md` — la tarea se preparó pero no se ejecutó. No hay `routers/clientes.py` ni `routers/consentimientos.py`. |
| Endpoints de campañas/asignaciones/métricas/usuarios/roles | ❌ No implementado | Nunca se llegó a esas tareas del plan original |
| Routers activos hoy | Solo `auth.py` y `auditoria.py` (este último con un único endpoint `GET /auditoria/logs` que siempre devuelve `[]`) |
| Tests | ✅ 6 archivos, cubren hashing/crypto/lockout/auth/models/seed | `test_auth.py` tiene teardown agregado en el commit más reciente para correr repetidamente contra la DB de Railway |

**Conexión con privacidad diferencial:** ninguna todavía. El backend está 100% orientado a seguridad (cifrado, RBAC, auditoría, consentimiento binario opt-in/opt-out). No hay ninguna noción de "ruido", "epsilon", ni librería de DP en `pyproject.toml`. Esto es terreno limpio para la Fase 2 — no hay que reemplazar nada, solo añadir endpoints nuevos (`/api/dataset/summary`, `/api/dp/query`, `/api/dp/model`, `/api/dp/comparison`) que se apoyan en `bank.csv` (ya cargado y accesible vía `pandas` en `seed/load_bank_csv.py`) sin depender de las tablas cifradas.

### `frontend/`
**No existe.** Hay que crearlo desde cero (React + Vite + TS + Tailwind + shadcn/ui, como indicaste).

### `infra/`
Solo `infra/docker-compose.yml`, que es un placeholder vacío (`services: {}`). No hay Nginx, no hay certificados TLS/OpenSSL a pesar de que el esquema del parcial y el informe (§10.2) los mencionan como requerimiento. Fuera del alcance de la entrega final según tu instrucción de reenfoque hacia privacidad — lo dejo tal cual salvo que me indiques lo contrario.

### `docs/`
- `docs/superpowers/plans/2026-07-02-sistema-campanas-bancarias.md` — plan de implementación del sistema del parcial (2895 líneas), generado con el skill `subagent-driven-development`. Sirve como referencia técnica de lo ya construido, pero **no** es el esquema de evaluación.
- El PDF del esquema parcial (Tipo 1, seguridad).
- No hay ningún documento de informe final, DPIA, notebook, ni nada relacionado a privacidad diferencial todavía.

### `notebooks/`
**No existe.** Confirmado: cero trabajo de privacidad diferencial iniciado en todo el repo (sin `diffprivlib`, sin `opendp`, sin `scikit-learn` en dependencias, sin ningún archivo `.ipynb`).

### Dataset
- `bank.csv` en la raíz: 11,162 filas + encabezado, 17 columnas (`age, job, marital, education, default, balance, housing, loan, contact, day, month, duration, campaign, pdays, previous, poutcome, deposit`). Coincide exactamente con lo descrito en el informe del parcial (versión balanceada de Kaggle, Moro et al. 2014).
- Está **sin trackear en git** (aparece como `??` en `git status`) — no está en `.gitignore` tampoco. Puede ser intencional (dataset pesado) o un descuido del parcial. Lo dejo como está salvo que quieras que lo agregue.

### `.claude/` y `.superpowers/`
Configuración de permisos y artefactos del flujo de desarrollo dirigido por subagentes (SDD) usado para construir el backend del parcial. `.superpowers/` está gitignored completo — es scaffolding local, no forma parte del entregable.

## 2. Qué es reciclable del parcial para el informe final

El informe de 33 páginas (`Proyecto___Grupo_1___EyS.pdf`) tiene contenido directamente reutilizable:

- **Marco legal peruano completo** (§8): Ley N.° 29733, D.S. N.° 016-2024-JUS (reglamento vigente desde 29-mar-2025), ANPDP, principios rectores (legalidad, consentimiento, finalidad, proporcionalidad, calidad, seguridad, disposición de recurso), más estándares internacionales (ISO 27001/27701, NIST SP 800-53/800-61, OWASP Top 10). Tabla de mapeo requerimiento normativo → control técnico (Cuadro 7).
- **Descripción del dataset** (§6): Bank Marketing Dataset, Moro et al. (2014)/Kaggle, 11,162 registros, 17 atributos, sin nulos, balance de clases ~47/53%, nota crítica sobre el **balanceo artificial** (tasa real de conversión ~11-12%, no 47%) y sobre `duration` (fuga de información — solo se conoce post-llamada) y `pdays=-1` (categoría especial, 75% de registros). Clasificación de sensibilidad por columna (Cuadro 4) — **directamente reutilizable como base de los cuasi-identificadores/atributos sensibles que pide el notebook.**
- **Consentimiento** (§10.4): estados opt-in/opt-out/no informado, 70/20/10 en los datos sintéticos — útil para la sección de reflexión ética sobre consentimiento, y contrastable con la idea de que la privacidad diferencial protege incluso a quienes no pueden dar consentimiento informado sobre "cuánto ruido" se les aplica.
- **Referencias en formato académico** ya listas (Anderson 2020, Moro et al. 2014, Ley 29733, D.S. 016-2024-JUS, NIST SP 800-61/63B, OWASP) — cuentan para el mínimo de 15 referencias del informe final, solo faltan las de DP (Dwork & Roth, Holohan et al., US Census 2020, Apple, Kleinberg, etc.)
- **Recomendación futura explícita en el propio informe parcial** (§10.8, punto 6): *"Aplicación de técnicas de privacidad diferencial en reportes agregados"* — es decir, el equipo ya había anticipado este pivote como trabajo futuro. Buen gancho narrativo para la introducción del informe final ("reencuadrar el caso desde privacidad", como pediste).
- **KPIs/OKRs de negocio** (§5) — reutilizables para justificar por qué la utilidad del modelo importa (trade-off con DP no es solo académico, tiene impacto directo en KR 1.1-1.3).

**No reciclable / hay que dejarlo fuera:** todo el bloque de diseño de RBAC, cifrado AES, Argon2id, TLS/certificados, plan de incidentes — es válido como sistema pero es el enfoque del parcial (seguridad), no el de privacidad diferencial. Se puede mencionar brevemente como "capa de seguridad ya existente sobre la que se añade la capa de privacidad", pero no debe ser el centro del informe final.

## 3. Qué falta para cubrir los 4 criterios de la rúbrica final (según tu descripción)

| Criterio (5 pts c/u) | Estado actual | Falta |
|---|---|---|
| Informe escrito (DPIA + reflexión ética) | 0% — no existe `docs/INFORME_FINAL.md` | Todo: DPIA formal, metodología DP, resultados, reflexión ética, referencias |
| Presentación | 0% — no existe `docs/presentacion/slides.md` | Todo |
| Demostración en vivo | 0% — no hay frontend ni endpoints de DP | Todo: notebook, endpoints backend, frontend, guion de demo |
| Requerimientos técnicos | Parcialmente: hay backend+DB+auth (heredado del parcial), pero cero DP | Notebook, endpoints DP, librería diffprivlib, comparativa opcional OpenDP, frontend nuevo |

## 4. Plan de trabajo por fases (respetando lo existente)

- [ ] **Fase 0 — Análisis inicial** (este documento) — esperando tu confirmación
- [ ] **Fase 1 — Notebook `notebooks/01_privacidad_diferencial.ipynb`** (prioridad más alta, corazón técnico)
  - [ ] Setup: crear `notebooks/`, añadir `diffprivlib`, `opendp` (opcional), `scikit-learn`, `jupyter` a `backend/pyproject.toml` (o un `notebooks/requirements.txt` separado si prefieres no mezclar con el backend productivo — a decidir contigo)
  - [ ] Introducción reencuadrando el caso del parcial desde privacidad (aprovechando §10.8 punto 6 del informe parcial)
  - [ ] EDA con lente de privacidad: cuasi-identificadores, atributos sensibles, k-anonimato empírico
  - [ ] Baseline sin DP: clasificador `deposit`, métricas + fairness por grupo
  - [ ] Queries agregadas con Laplace, ε ∈ {0.1,...,10}, gráfico error vs ε
  - [ ] Modelo con `diffprivlib.models.LogisticRegression` a distintos ε
  - [ ] Trade-off ε vs utilidad (gráfico central)
  - [ ] Fairness bajo DP + conexión con Kleinberg
  - [ ] Conclusiones técnicas, seeds fijos
- [ ] **Fase 2 — Informe `docs/INFORME_FINAL.md`** (segunda prioridad)
  - [ ] Introducción, marco legal (reciclado), DPIA completa, metodología DP, resultados embebidos del notebook, reflexión ética (Gender Shades, COMPAS, Toeslagenaffaire, Kleinberg), conclusiones, ≥15 referencias
- [ ] **Fase 3 — Backend: endpoints DP**
  - [ ] `GET /api/dataset/summary`
  - [ ] `POST /api/dp/query`
  - [ ] `POST /api/dp/model`
  - [ ] `GET /api/dp/comparison`
  - [ ] Decidir contigo si mantener JWT/RBAC existente delante de estos endpoints o dejarlos abiertos para la demo
- [ ] **Fase 4 — Frontend** (`frontend/`, nuevo)
  - [ ] Scaffold Vite + React + TS + Tailwind + shadcn/ui
  - [ ] Vistas: Home/Explorar, Playground de queries, Modelo con DP, Trade-off, Ética
  - [ ] Slider de ε logarítmico + recharts + dark/light mode
- [ ] **Fase 5 — Presentación y guion de demo**
  - [ ] `docs/presentacion/slides.md` (12-15 slides)
  - [ ] `docs/GUION_DEMO.md` (5-7 min)

Cada fase termina con revisión tuya antes de continuar, commits atómicos (`feat:`, `docs:`, `experiment:`), y sin tocar `.env` (nuevas variables van a `.env.example` con aviso).

## 5. Preguntas abiertas antes de codear

1. ¿Tienes el PDF real del esquema "Tipo 2" / final? Si existe y difiere de lo que describiste en el chat, cambia el análisis de la sección 3.
2. Para los endpoints de DP, ¿los dejamos completamente sin auth (como sugeriste) o reusamos el JWT existente pero con un permiso nuevo tipo `dp:consultar`?
3. ¿Las dependencias de DP (diffprivlib, scikit-learn, jupyter) van en `backend/pyproject.toml` o en un `requirements.txt` separado dentro de `notebooks/` para no mezclar con el entorno productivo del backend?
