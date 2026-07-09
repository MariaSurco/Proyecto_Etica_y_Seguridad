# Frontend

Aplicación React + TypeScript + Vite para operar el sistema de campañas bancarias por rol.

## Funcionalidad

- Login contra `POST /auth/login`.
- Persistencia local de JWT.
- Navegación según permisos del token.
- Clientes elegibles y gestión de consentimiento.
- Campañas: creación, listado y cierre.
- Asignaciones: selección de cliente, campaña y teleoperador.
- Mis contactos: registro de resultado de contacto.
- Usuarios: creación y activar/desactivar.
- Auditoría: últimos eventos del sistema.
- Estados de carga, errores, refresh y mensajes de éxito.

## Configuración

La URL base del backend se toma de:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Si no está definida, la app usa `http://localhost:8000`.

## Instalación

```bash
cd frontend
npm install
```

## Desarrollo

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Abrir:

```text
http://127.0.0.1:5173
```

## Build

```bash
npm run build
```

## Preview

```bash
npm run preview
```

## Scripts

- `npm run dev`: servidor Vite.
- `npm run build`: chequeo TypeScript y build de producción.
- `npm run lint`: oxlint.
- `npm run preview`: previsualización del build.

## Roles Esperados

La interfaz muestra secciones según permisos:

- `clientes:ver_sensible` o `clientes:ver_parcial`: clientes y consentimiento.
- `campanias:consultar`: campañas.
- `campanias:crear_editar`: creación/cierre de campañas y asignaciones.
- `clientes:ver_asignados`: mis contactos.
- `resultados:registrar`: registro de resultado.
- `usuarios:gestionar`: usuarios, roles y teleoperadores.
- `auditoria:consultar`: auditoría.

## Estado

`npm run build` pasa correctamente.

