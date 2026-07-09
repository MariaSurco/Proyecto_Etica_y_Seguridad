# Guía Operativa

## Ejecución HTTPS local

1. Generar certificado autofirmado:
   ```bash
   sh infra/certs/generate-self-signed.sh
   ```
2. Levantar servicios:
   ```bash
   cd infra
   docker compose up --build
   ```
3. Abrir `https://localhost:8443`.

El puerto `8080` redirige a HTTPS. Para una demo local, el navegador mostrará advertencia por certificado autofirmado.

## Backups cifrados

Crear backup:
```bash
DATABASE_URL="postgresql://user:pass@host:5432/db" \
BACKUP_ENCRYPTION_KEY="clave-larga" \
sh infra/backup/backup_db.sh
```

Restaurar backup:
```bash
DATABASE_URL="postgresql://user:pass@host:5432/db" \
BACKUP_ENCRYPTION_KEY="clave-larga" \
sh infra/backup/restore_db.sh backups/archivo.sql.enc
```

## Respuesta a incidentes

Preparación:
- Mantener roles mínimos, JWT con expiración corta, backups cifrados y auditoría activa.
- Restringir acceso a llaves `FIELD_ENCRYPTION_KEY`, `JWT_SECRET` y `BACKUP_ENCRYPTION_KEY`.

Detección:
- Revisar `/auditoria/logs` por `login_fallido`, `login_bloqueado` y `acceso_denegado`.
- Identificar usuario, IP, recurso y ventana de tiempo afectada.

Contención:
- Desactivar usuarios comprometidos con `PATCH /usuarios/{usuario_id}/activo`.
- Rotar secretos si hay sospecha de exposición.
- Suspender temporalmente campañas si hay riesgo sobre consentimiento o contacto indebido.

Recuperación:
- Restaurar desde backup cifrado si hubo corrupción o pérdida de datos.
- Verificar integridad de usuarios, roles, permisos, consentimientos y asignaciones.

Revisión posterior:
- Documentar causa, alcance, datos afectados, controles fallidos y correcciones.
- Agregar tests o reglas de auditoría para evitar recurrencia.

## Política de contraseñas

Aplicada en `backend/app/security/hashing.py` (`validate_password_policy`) y `backend/app/security/lockout.py`.

- Longitud mínima: 12 caracteres.
- Rechazo de contraseñas comunes/comprometidas: se valida contra una lista de valores conocidos (p. ej. `password123456`, `123456789012`, `qwertyuiop12`); no se aceptan aunque cumplan la longitud mínima.
- El hash se almacena con Argon2 (`passlib.hash.argon2`, `memory_cost=65536`, `time_cost=3`, `parallelism=1`); nunca se guarda ni se registra la contraseña en texto plano.
- Bloqueo de cuenta por intentos fallidos (`lockout.py`): tras `MAX_ATTEMPTS = 5` intentos de login fallidos consecutivos, la cuenta queda bloqueada durante `LOCKOUT_MINUTES = 15` minutos (`locked_until`). El contador se reinicia (`failed_login_attempts = 0`) tras un login exitoso.
- Recomendación operativa: comunicar estos requisitos a usuarios nuevos al momento del alta y evitar reutilizar contraseñas usadas en otros sistemas, aunque esta segunda regla no se valide automáticamente en el código.

## Capacitación del personal

Roles del sistema (`backend/app/seed/generate_synthetic.py`): `administrador`, `supervisor`, `analista`, `teleoperador`. Cada rol ve un subconjunto distinto de datos de clientes (`clientes:ver_sensible`, `clientes:ver_parcial`, `clientes:ver_asignados`), por lo que la capacitación debe ser proporcional al acceso de cada uno.

Para todo el personal:
- No compartir credenciales ni contraseñas entre compañeros, ni reutilizarlas en otros sistemas.
- Reconocer intentos de phishing dirigidos a obtener credenciales o datos de clientes; reportar correos o mensajes sospechosos antes de hacer clic en enlaces adjuntos.
- Reportar de inmediato cualquier acceso o comportamiento sospechoso (sesiones no reconocidas, solicitudes de datos fuera de proceso) para su revisión en `/auditoria/logs`.
- Cerrar sesión al dejar el puesto de trabajo y no dejar pantallas con datos de clientes visibles sin supervisión.

Por rol:
- **Administrador**: dado su acceso a gestión de usuarios/roles y a `clientes:ver_sensible`/`clientes:exportar`, requiere capacitación adicional sobre manejo de exportaciones de datos personales (minimizar, cifrar, eliminar copias temporales) y sobre el procedimiento de desactivación de usuarios (`PATCH /usuarios/{usuario_id}/activo`) ante sospecha de compromiso.
- **Supervisor**: mismo nivel de visibilidad de clientes que administrador; debe conocer el criterio de asignación de teleoperadores y evitar exponer datos sensibles de clientes fuera del flujo de la campaña.
- **Analista**: solo ve datos parciales de clientes (`clientes:ver_parcial`); debe entender que no está autorizado a solicitar acceso ampliado y que cualquier necesidad de datos sensibles debe canalizarse a través de un administrador o supervisor.
- **Teleoperador**: solo ve clientes asignados (`clientes:ver_asignados`); debe recibir recordatorios sobre no anotar ni transcribir datos de clientes fuera del sistema (hojas sueltas, chats personales) y sobre verificar el consentimiento del cliente antes de contactarlo.
