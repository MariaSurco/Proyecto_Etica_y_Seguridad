import { useEffect, useMemo, useState } from "react"
import type { FormEvent, ReactNode } from "react"
import {
  AlertCircle,
  CheckCircle2,
  ClipboardCheck,
  FileClock,
  Loader2,
  LogOut,
  Megaphone,
  PhoneCall,
  RefreshCw,
  ShieldCheck,
  UserPlus,
  Users,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api, ApiError } from "@/lib/api"
import type { Asignacion, AuditLog, Campania, Cliente, Consentimiento, Rol, Usuario } from "@/lib/api"
import { cn } from "@/lib/utils"

type Session = {
  token: string
  usuarioId: string
  rol: string
  permisos: string[]
}

type View = "clientes" | "campanias" | "asignaciones" | "mis-asignaciones" | "usuarios" | "auditoria"
type LoadState = "idle" | "loading" | "ready" | "error"

const SESSION_KEY = "bank_campaigns_session"

function decodeSession(token: string): Session {
  const [, payload] = token.split(".")
  const normalized = payload.replace(/-/g, "+").replace(/_/g, "/")
  const parsed = JSON.parse(atob(normalized)) as { sub: string; rol: string; permisos?: string[] }
  return { token, usuarioId: parsed.sub, rol: parsed.rol, permisos: parsed.permisos ?? [] }
}

function readStoredSession() {
  const stored = localStorage.getItem(SESSION_KEY)
  if (!stored) return null
  try {
    return decodeSession(stored)
  } catch {
    localStorage.removeItem(SESSION_KEY)
    return null
  }
}

function can(session: Session | null, permiso: string) {
  return Boolean(session?.permisos.includes(permiso))
}

function shortId(id: string) {
  return `${id.slice(0, 8)}...${id.slice(-4)}`
}

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function errorMessage(err: unknown) {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return "Ocurrió un error inesperado"
}

function App() {
  const [session, setSession] = useState<Session | null>(readStoredSession)
  const [view, setView] = useState<View>("clientes")

  const navItems = useMemo(() => {
    if (!session) return []
    return [
      {
        id: "clientes" as const,
        label: "Clientes",
        icon: Users,
        show: can(session, "clientes:ver_sensible") || can(session, "clientes:ver_parcial"),
      },
      {
        id: "campanias" as const,
        label: "Campañas",
        icon: Megaphone,
        show: can(session, "campanias:consultar") || can(session, "campanias:consultar_asignadas"),
      },
      {
        id: "asignaciones" as const,
        label: "Asignar",
        icon: ClipboardCheck,
        show: can(session, "campanias:crear_editar"),
      },
      {
        id: "mis-asignaciones" as const,
        label: "Mis contactos",
        icon: PhoneCall,
        show: can(session, "clientes:ver_asignados"),
      },
      {
        id: "usuarios" as const,
        label: "Usuarios",
        icon: UserPlus,
        show: can(session, "usuarios:gestionar"),
      },
      {
        id: "auditoria" as const,
        label: "Auditoría",
        icon: FileClock,
        show: can(session, "auditoria:consultar"),
      },
    ].filter((item) => item.show)
  }, [session])

  useEffect(() => {
    if (!session || navItems.some((item) => item.id === view)) return
    setView(navItems[0]?.id ?? "campanias")
  }, [navItems, session, view])

  function handleLogin(nextToken: string) {
    localStorage.setItem(SESSION_KEY, nextToken)
    const nextSession = decodeSession(nextToken)
    setSession(nextSession)
    if (nextSession.permisos.includes("clientes:ver_asignados")) setView("mis-asignaciones")
    else if (nextSession.permisos.includes("clientes:ver_sensible") || nextSession.permisos.includes("clientes:ver_parcial")) setView("clientes")
    else setView("campanias")
  }

  function handleLogout() {
    localStorage.removeItem(SESSION_KEY)
    setSession(null)
  }

  if (!session) return <LoginScreen onLogin={handleLogin} />

  return (
    <div className="min-h-screen bg-background text-foreground">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-surface md:block">
        <div className="flex h-16 items-center gap-3 border-b border-border px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary/15 text-secondary">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-semibold">Banco Campañas</div>
            <div className="text-xs text-muted-foreground">Operación segura</div>
          </div>
        </div>
        <nav className="space-y-1 px-3 py-4">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setView(id)}
              className={cn(
                "flex h-10 w-full items-center gap-3 rounded-lg px-3 text-left text-sm font-medium transition-colors",
                view === id ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-surface-muted",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
      </aside>

      <div className="md:pl-64">
        <header className="sticky top-0 z-10 border-b border-border bg-surface/95 backdrop-blur">
          <div className="flex min-h-16 flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between md:px-6">
            <div>
              <h1 className="text-lg font-semibold">Flujo bancario seguro</h1>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <Badge variant="secondary">{session.rol || "sin rol"}</Badge>
                <span>{shortId(session.usuarioId)}</span>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex gap-1 overflow-x-auto md:hidden">
                {navItems.map(({ id, label }) => (
                  <Button key={id} size="sm" variant={view === id ? "default" : "outline"} onClick={() => setView(id)}>
                    {label}
                  </Button>
                ))}
              </div>
              <Button variant="ghost" size="icon" onClick={handleLogout} title="Cerrar sesión" aria-label="Cerrar sesión">
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </header>

        <main className="px-4 py-5 md:px-6">
          <Dashboard session={session} />
          {view === "clientes" && <ClientesView session={session} />}
          {view === "campanias" && <CampaniasView session={session} />}
          {view === "asignaciones" && <AsignacionesView session={session} />}
          {view === "mis-asignaciones" && <MisAsignacionesView session={session} />}
          {view === "usuarios" && <UsuariosView session={session} />}
          {view === "auditoria" && <AuditoriaView session={session} />}
        </main>
      </div>
    </div>
  )
}

function LoginScreen({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError("")
    try {
      const response = await api.login(username.trim(), password)
      onLogin(response.access_token)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-background px-4">
      <Card className="w-full max-w-sm rounded-lg">
        <CardHeader>
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-secondary/15 text-secondary">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <CardTitle className="text-base text-foreground">Sistema de campañas bancarias</CardTitle>
          <p className="text-xs text-muted-foreground">Acceso con JWT, roles y auditoría de eventos.</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-3" onSubmit={submit}>
            <Field label="Usuario" value={username} onChange={setUsername} autoComplete="username" />
            <Field
              label="Contraseña"
              value={password}
              onChange={setPassword}
              type="password"
              autoComplete="current-password"
            />
            {error && <Alert tone="error">{error}</Alert>}
            <Button className="w-full" disabled={loading || !username || !password}>
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Ingresando..." : "Ingresar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}

function Dashboard({ session }: { session: Session }) {
  const items = [
    { label: "Rol activo", value: session.rol || "N/A" },
    { label: "Permisos", value: session.permisos.length },
    { label: "Sesión", value: "JWT válido" },
  ]
  return (
    <section className="mb-5 grid gap-3 md:grid-cols-3">
      {items.map((item) => (
        <Card key={item.label} className="rounded-lg">
          <CardContent className="px-4 py-3">
            <div className="text-xs text-muted-foreground">{item.label}</div>
            <div className="mt-1 text-xl font-semibold tabular-nums">{item.value}</div>
          </CardContent>
        </Card>
      ))}
    </section>
  )
}

function ClientesView({ session }: { session: Session }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [selected, setSelected] = useState("")
  const [consentimiento, setConsentimiento] = useState<Consentimiento | null>(null)
  const [estado, setEstado] = useState<Consentimiento["estado"]>("opt-in")
  const [status, setStatus] = useState<LoadState>("idle")
  const [message, setMessage] = useState("")

  async function refresh() {
    setStatus("loading")
    setMessage("")
    try {
      setClientes(await api.getClientesElegibles(session.token))
      setStatus("ready")
    } catch (err) {
      setMessage(errorMessage(err))
      setStatus("error")
    }
  }

  useEffect(() => {
    refresh()
  }, [session.token])

  async function loadConsentimiento(clienteId: string) {
    setSelected(clienteId)
    setMessage("")
    try {
      const data = await api.getConsentimiento(session.token, clienteId)
      setConsentimiento(data)
      setEstado(data.estado)
    } catch (err) {
      setConsentimiento(null)
      setMessage(errorMessage(err))
    }
  }

  async function updateConsentimiento() {
    if (!selected) return
    try {
      const data = await api.updateConsentimiento(session.token, selected, { estado, canal: "web" })
      setConsentimiento(data)
      setMessage("Consentimiento actualizado")
      await refresh()
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <section className="grid gap-4 xl:grid-cols-[1fr_360px]">
      <Card className="overflow-hidden rounded-lg">
        <SectionHeader
          title="Clientes elegibles"
          subtitle="Solo aparecen clientes con consentimiento opt-in."
          action={<RefreshButton loading={status === "loading"} onClick={refresh} />}
        />
        <CardContent className="px-0 pb-0">
          <DataTable
            columns={["Cliente", "Perfil", "Contacto", "Depósito", ""]}
            rows={clientes}
            empty={status === "loading" ? "Cargando clientes..." : "No hay clientes opt-in visibles para este rol."}
            render={(cliente) => (
              <tr key={cliente.cliente_id} className="border-b border-border last:border-0">
                <td className="px-3 py-2 font-mono text-xs">{shortId(cliente.cliente_id)}</td>
                <td className="px-3 py-2">
                  <div className="font-medium">{cliente.nombre ?? cliente.job ?? "Cliente"}</div>
                  <div className="text-xs text-muted-foreground">{cliente.age ? `${cliente.age} años` : cliente.education ?? "-"}</div>
                </td>
                <td className="px-3 py-2">{cliente.telefono ?? cliente.email ?? cliente.contact ?? "-"}</td>
                <td className="px-3 py-2">
                  <Badge variant={cliente.deposit === "yes" ? "secondary" : "outline"}>{cliente.deposit ?? "N/A"}</Badge>
                </td>
                <td className="px-3 py-2 text-right">
                  <Button size="sm" variant="outline" onClick={() => loadConsentimiento(cliente.cliente_id)}>
                    Consentimiento
                  </Button>
                </td>
              </tr>
            )}
          />
          {status === "error" && <div className="px-5 pb-5"><Alert tone="error">{message}</Alert></div>}
        </CardContent>
      </Card>

      <Card className="rounded-lg">
        <SectionHeader title="Gestión de consentimiento" subtitle="Los cambios quedan auditados." />
        <CardContent className="space-y-3">
          <div className="rounded-lg border border-border bg-surface-muted px-3 py-2 font-mono text-xs text-muted-foreground">
            {selected ? shortId(selected) : "Selecciona un cliente"}
          </div>
          {consentimiento ? (
            <>
              <SelectField
                label="Estado"
                value={estado}
                onChange={(value) => setEstado(value as Consentimiento["estado"])}
                options={[
                  { value: "opt-in", label: "opt-in" },
                  { value: "opt-out", label: "opt-out" },
                  { value: "no informado", label: "no informado" },
                ]}
              />
              <div className="text-xs text-muted-foreground">
                Canal: {consentimiento.canal ?? "sin canal"} · Última actualización:{" "}
                {consentimiento.fecha_actualizacion?.slice(0, 10) ?? "N/A"}
              </div>
              <Button onClick={updateConsentimiento} disabled={!can(session, "clientes:ver_sensible")}>
                Guardar cambio
              </Button>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">El detalle se cargará aquí.</p>
          )}
          {message && status !== "error" && <Alert tone={message.includes("actualizado") ? "success" : "info"}>{message}</Alert>}
        </CardContent>
      </Card>
    </section>
  )
}

function CampaniasView({ session }: { session: Session }) {
  const [campanias, setCampanias] = useState<Campania[]>([])
  const [nombre, setNombre] = useState("")
  const [producto, setProducto] = useState("deposito")
  const [fechaInicio, setFechaInicio] = useState(todayIso())
  const [estado, setEstado] = useState<Campania["estado"]>("planificada")
  const [status, setStatus] = useState<LoadState>("idle")
  const [message, setMessage] = useState("")

  async function refresh() {
    setStatus("loading")
    setMessage("")
    try {
      setCampanias(await api.getCampanias(session.token))
      setStatus("ready")
    } catch (err) {
      setMessage(errorMessage(err))
      setStatus("error")
    }
  }

  useEffect(() => {
    refresh()
  }, [session.token])

  async function create(event: FormEvent) {
    event.preventDefault()
    try {
      await api.createCampania(session.token, { nombre: nombre.trim(), producto: producto.trim(), fecha_inicio: fechaInicio, estado })
      setNombre("")
      setProducto("deposito")
      setEstado("planificada")
      setMessage("Campaña creada")
      await refresh()
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  async function closeCampaign(campania: Campania) {
    await api.updateCampania(session.token, campania.campania_id, { estado: "cerrada" })
    await refresh()
  }

  return (
    <section className="grid gap-4 xl:grid-cols-[360px_1fr]">
      <Card className="rounded-lg">
        <SectionHeader title="Nueva campaña" subtitle="Disponible para supervisores y administradores." />
        <CardContent>
          <form className="space-y-3" onSubmit={create}>
            <Field label="Nombre" value={nombre} onChange={setNombre} />
            <Field label="Producto" value={producto} onChange={setProducto} />
            <Field label="Fecha de inicio" value={fechaInicio} onChange={setFechaInicio} type="date" />
            <SelectField
              label="Estado"
              value={estado}
              onChange={(value) => setEstado(value as Campania["estado"])}
              options={[
                { value: "planificada", label: "planificada" },
                { value: "activa", label: "activa" },
              ]}
            />
            <Button disabled={!nombre || !producto || !can(session, "campanias:crear_editar")}>Crear campaña</Button>
          </form>
          {message && <div className="mt-3"><Alert tone={message.includes("creada") ? "success" : "error"}>{message}</Alert></div>}
        </CardContent>
      </Card>

      <Card className="overflow-hidden rounded-lg">
        <SectionHeader
          title="Campañas"
          subtitle="Estado operativo de las campañas registradas."
          action={<RefreshButton loading={status === "loading"} onClick={refresh} />}
        />
        <CardContent className="px-0 pb-0">
          <DataTable
            columns={["Nombre", "Producto", "Inicio", "Estado", ""]}
            rows={campanias}
            empty={status === "loading" ? "Cargando campañas..." : "No hay campañas registradas."}
            render={(campania) => (
              <tr key={campania.campania_id} className="border-b border-border last:border-0">
                <td className="px-3 py-2 font-medium">{campania.nombre}</td>
                <td className="px-3 py-2">{campania.producto}</td>
                <td className="px-3 py-2">{campania.fecha_inicio}</td>
                <td className="px-3 py-2"><StatusBadge value={campania.estado} /></td>
                <td className="px-3 py-2 text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!can(session, "campanias:crear_editar") || campania.estado === "cerrada"}
                    onClick={() => closeCampaign(campania)}
                  >
                    Cerrar
                  </Button>
                </td>
              </tr>
            )}
          />
          {status === "error" && <div className="px-5 pb-5"><Alert tone="error">{message}</Alert></div>}
        </CardContent>
      </Card>
    </section>
  )
}

function AsignacionesView({ session }: { session: Session }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [campanias, setCampanias] = useState<Campania[]>([])
  const [teleoperadores, setTeleoperadores] = useState<Usuario[]>([])
  const [clienteId, setClienteId] = useState("")
  const [campaniaId, setCampaniaId] = useState("")
  const [usuarioId, setUsuarioId] = useState("")
  const [status, setStatus] = useState<LoadState>("idle")
  const [message, setMessage] = useState("")

  async function refresh() {
    setStatus("loading")
    setMessage("")
    try {
      const [clientesData, campaniasData, teleoperadoresData] = await Promise.all([
        api.getClientesElegibles(session.token),
        api.getCampanias(session.token),
        api.getTeleoperadores(session.token),
      ])
      setClientes(clientesData)
      setCampanias(campaniasData.filter((campania) => campania.estado !== "cerrada" && campania.estado !== "cancelada"))
      setTeleoperadores(teleoperadoresData)
      setStatus("ready")
    } catch (err) {
      setMessage(errorMessage(err))
      setStatus("error")
    }
  }

  useEffect(() => {
    refresh()
  }, [session.token])

  async function submit(event: FormEvent) {
    event.preventDefault()
    try {
      const created = await api.createAsignacion(session.token, { cliente_id: clienteId, campania_id: campaniaId, usuario_id: usuarioId })
      setMessage(`Asignación creada: ${shortId(created.asignacion_id)}`)
      setClienteId("")
      await refresh()
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <Card className="rounded-lg">
      <SectionHeader
        title="Asignar cliente opt-in"
        subtitle="El sistema bloquea clientes sin consentimiento y duplicados por campaña."
        action={<RefreshButton loading={status === "loading"} onClick={refresh} />}
      />
      <CardContent>
        <form className="grid gap-3 lg:grid-cols-[1fr_1fr_1fr_auto]" onSubmit={submit}>
          <SelectField
            label="Cliente"
            value={clienteId}
            onChange={setClienteId}
            options={clientes.map((cliente) => ({
              value: cliente.cliente_id,
              label: cliente.nombre ?? `${cliente.job ?? "Cliente"} · ${shortId(cliente.cliente_id)}`,
            }))}
          />
          <SelectField
            label="Campaña"
            value={campaniaId}
            onChange={setCampaniaId}
            options={campanias.map((campania) => ({ value: campania.campania_id, label: campania.nombre }))}
          />
          <SelectField
            label="Teleoperador"
            value={usuarioId}
            onChange={setUsuarioId}
            options={teleoperadores.map((usuario) => ({ value: usuario.usuario_id, label: usuario.username }))}
          />
          <div className="flex items-end">
            <Button disabled={!clienteId || !campaniaId || !usuarioId || status === "loading"}>Asignar</Button>
          </div>
        </form>
        {message && <div className="mt-3"><Alert tone={message.includes("creada") ? "success" : "error"}>{message}</Alert></div>}
      </CardContent>
    </Card>
  )
}

function MisAsignacionesView({ session }: { session: Session }) {
  const [rows, setRows] = useState<Asignacion[]>([])
  const [resultado, setResultado] = useState("contactado")
  const [observacion, setObservacion] = useState("")
  const [status, setStatus] = useState<LoadState>("idle")
  const [message, setMessage] = useState("")

  async function refresh() {
    setStatus("loading")
    setMessage("")
    try {
      setRows(await api.getMisAsignaciones(session.token))
      setStatus("ready")
    } catch (err) {
      setMessage(errorMessage(err))
      setStatus("error")
    }
  }

  useEffect(() => {
    refresh()
  }, [session.token])

  async function register(asignacionId: string) {
    try {
      await api.registerResultado(session.token, asignacionId, { resultado, observacion: observacion.trim() || undefined })
      setObservacion("")
      setMessage("Resultado registrado")
      await refresh()
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <section className="space-y-4">
      <Card className="rounded-lg">
        <SectionHeader title="Resultado de contacto" subtitle="Se registra sobre una asignación propia del teleoperador." />
        <CardContent className="grid gap-3 md:grid-cols-[220px_1fr]">
          <SelectField
            label="Resultado"
            value={resultado}
            onChange={setResultado}
            options={[
              { value: "contactado", label: "contactado" },
              { value: "no_contesta", label: "no contesta" },
              { value: "rechaza", label: "rechaza" },
              { value: "interesado", label: "interesado" },
            ]}
          />
          <Field label="Observación" value={observacion} onChange={setObservacion} />
        </CardContent>
      </Card>

      <Card className="overflow-hidden rounded-lg">
        <SectionHeader
          title="Mis asignaciones"
          subtitle="Clientes asignados al usuario autenticado."
          action={<RefreshButton loading={status === "loading"} onClick={refresh} />}
        />
        <CardContent className="px-0 pb-0">
          <DataTable
            columns={["Asignación", "Cliente", "Estado", ""]}
            rows={rows}
            empty={status === "loading" ? "Cargando asignaciones..." : "No tienes clientes asignados."}
            render={(row) => (
              <tr key={row.asignacion_id} className="border-b border-border last:border-0">
                <td className="px-3 py-2 font-mono text-xs">{shortId(row.asignacion_id)}</td>
                <td className="px-3 py-2 font-mono text-xs">{shortId(row.cliente_id)}</td>
                <td className="px-3 py-2"><StatusBadge value={row.estado_contacto ?? "pendiente"} /></td>
                <td className="px-3 py-2 text-right"><Button size="sm" onClick={() => register(row.asignacion_id)}>Registrar</Button></td>
              </tr>
            )}
          />
          {message && <div className="px-5 pb-5"><Alert tone={message.includes("registrado") ? "success" : "error"}>{message}</Alert></div>}
        </CardContent>
      </Card>
    </section>
  )
}

function UsuariosView({ session }: { session: Session }) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [roles, setRoles] = useState<Rol[]>([])
  const [status, setStatus] = useState<LoadState>("idle")
  const [message, setMessage] = useState("")
  const [form, setForm] = useState({
    username: "",
    nombre_completo: "",
    email_corporativo: "",
    password: "",
    rol_id: "",
  })

  async function refresh() {
    setStatus("loading")
    setMessage("")
    try {
      const [usuariosData, rolesData] = await Promise.all([api.getUsuarios(session.token), api.getRoles(session.token)])
      setUsuarios(usuariosData)
      setRoles(rolesData)
      setStatus("ready")
    } catch (err) {
      setMessage(errorMessage(err))
      setStatus("error")
    }
  }

  useEffect(() => {
    refresh()
  }, [session.token])

  async function create(event: FormEvent) {
    event.preventDefault()
    try {
      await api.createUsuario(session.token, {
        username: form.username.trim(),
        nombre_completo: form.nombre_completo.trim(),
        email_corporativo: form.email_corporativo.trim(),
        password: form.password,
        rol_id: Number(form.rol_id),
      })
      setForm({ username: "", nombre_completo: "", email_corporativo: "", password: "", rol_id: "" })
      setMessage("Usuario creado")
      await refresh()
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  async function toggle(usuario: Usuario) {
    await api.updateUsuarioActivo(session.token, usuario.usuario_id, !usuario.activo)
    await refresh()
  }

  return (
    <section className="grid gap-4 xl:grid-cols-[420px_1fr]">
      <Card className="rounded-lg">
        <SectionHeader title="Crear usuario" subtitle="Aplica política mínima de contraseña." />
        <CardContent>
          <form className="space-y-3" onSubmit={create}>
            <Field label="Username" value={form.username} onChange={(value) => setForm((current) => ({ ...current, username: value }))} />
            <Field label="Nombre completo" value={form.nombre_completo} onChange={(value) => setForm((current) => ({ ...current, nombre_completo: value }))} />
            <Field label="Email corporativo" value={form.email_corporativo} onChange={(value) => setForm((current) => ({ ...current, email_corporativo: value }))} type="email" />
            <Field label="Contraseña temporal" value={form.password} onChange={(value) => setForm((current) => ({ ...current, password: value }))} type="password" />
            <SelectField
              label="Rol"
              value={form.rol_id}
              onChange={(value) => setForm((current) => ({ ...current, rol_id: value }))}
              options={roles.map((rol) => ({ value: String(rol.rol_id), label: rol.nombre }))}
            />
            <Button disabled={!form.username || !form.nombre_completo || !form.email_corporativo || !form.password || !form.rol_id}>
              Crear usuario
            </Button>
          </form>
          {message && <div className="mt-3"><Alert tone={message.includes("creado") ? "success" : status === "error" ? "error" : "info"}>{message}</Alert></div>}
        </CardContent>
      </Card>

      <Card className="overflow-hidden rounded-lg">
        <SectionHeader
          title="Usuarios"
          subtitle="Administración de estado de acceso."
          action={<RefreshButton loading={status === "loading"} onClick={refresh} />}
        />
        <CardContent className="px-0 pb-0">
          <DataTable
            columns={["Usuario", "Nombre", "Rol", "Estado", ""]}
            rows={usuarios}
            empty={status === "loading" ? "Cargando usuarios..." : "Sin usuarios visibles."}
            render={(usuario) => (
              <tr key={usuario.usuario_id} className="border-b border-border last:border-0">
                <td className="px-3 py-2 font-medium">{usuario.username}</td>
                <td className="px-3 py-2">{usuario.nombre_completo}</td>
                <td className="px-3 py-2"><Badge variant="secondary">{usuario.rol_nombre ?? usuario.rol_id}</Badge></td>
                <td className="px-3 py-2"><Badge variant={usuario.activo ? "default" : "destructive"}>{usuario.activo ? "activo" : "inactivo"}</Badge></td>
                <td className="px-3 py-2 text-right">
                  <Button size="sm" variant="outline" onClick={() => toggle(usuario)}>
                    {usuario.activo ? "Desactivar" : "Activar"}
                  </Button>
                </td>
              </tr>
            )}
          />
        </CardContent>
      </Card>
    </section>
  )
}

function AuditoriaView({ session }: { session: Session }) {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [status, setStatus] = useState<LoadState>("idle")
  const [message, setMessage] = useState("")

  async function refresh() {
    setStatus("loading")
    setMessage("")
    try {
      setLogs(await api.getAuditLogs(session.token))
      setStatus("ready")
    } catch (err) {
      setMessage(errorMessage(err))
      setStatus("error")
    }
  }

  useEffect(() => {
    refresh()
  }, [session.token])

  return (
    <Card className="overflow-hidden rounded-lg">
      <SectionHeader
        title="Auditoría"
        subtitle="Últimos 200 eventos relevantes del sistema."
        action={<RefreshButton loading={status === "loading"} onClick={refresh} />}
      />
      <CardContent className="px-0 pb-0">
        <DataTable
          columns={["Acción", "Recurso", "Resultado", "Detalle", "Fecha"]}
          rows={logs}
          empty={status === "loading" ? "Cargando eventos..." : "No hay eventos de auditoría."}
          render={(log) => (
            <tr key={log.log_id} className="border-b border-border last:border-0">
              <td className="px-3 py-2 font-medium">{log.accion}</td>
              <td className="px-3 py-2">{log.recurso}</td>
              <td className="px-3 py-2"><Badge variant={log.resultado === "exito" ? "secondary" : "destructive"}>{log.resultado}</Badge></td>
              <td className="max-w-[320px] truncate px-3 py-2 text-xs text-muted-foreground">{log.detalle ?? log.recurso_id ?? "-"}</td>
              <td className="px-3 py-2 text-xs text-muted-foreground">{log.timestamp_evento?.slice(0, 19).replace("T", " ") ?? "-"}</td>
            </tr>
          )}
        />
        {status === "error" && <div className="px-5 pb-5"><Alert tone="error">{message}</Alert></div>}
      </CardContent>
    </Card>
  )
}

function SectionHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <CardHeader className="flex-row items-start justify-between gap-3">
      <div>
        <CardTitle className="text-sm text-foreground">{title}</CardTitle>
        {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
      </div>
      {action}
    </CardHeader>
  )
}

function DataTable<T>({
  columns,
  rows,
  empty,
  render,
}: {
  columns: string[]
  rows: T[]
  empty: string
  render: (row: T) => ReactNode
}) {
  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-y border-border bg-surface-muted/70 text-xs uppercase text-muted-foreground">
            <tr>{columns.map((column) => <th key={column} className="px-3 py-2 font-medium">{column}</th>)}</tr>
          </thead>
          <tbody>{rows.map(render)}</tbody>
        </table>
      </div>
      {rows.length === 0 && <div className="px-5 py-5 text-sm text-muted-foreground">{empty}</div>}
    </>
  )
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  autoComplete,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  type?: string
  autoComplete?: string
}) {
  return (
    <label className="block text-xs font-medium text-muted-foreground">
      {label}
      <input
        className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-3 text-sm text-foreground shadow-sm"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        type={type}
        autoComplete={autoComplete}
      />
    </label>
  )
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
}) {
  const fallback = useMemo(() => [{ value: "", label: "Seleccionar" }, ...options], [options])
  return (
    <label className="block text-xs font-medium text-muted-foreground">
      {label}
      <select
        className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-3 text-sm text-foreground shadow-sm"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {fallback.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  )
}

function RefreshButton({ loading, onClick }: { loading: boolean; onClick: () => void }) {
  return (
    <Button size="icon" variant="ghost" onClick={onClick} disabled={loading} title="Actualizar" aria-label="Actualizar">
      <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
    </Button>
  )
}

function StatusBadge({ value }: { value: string }) {
  if (["activa", "contactado", "interesado"].includes(value)) return <Badge variant="secondary">{value}</Badge>
  if (["cerrada", "rechaza", "cancelada"].includes(value)) return <Badge variant="destructive">{value}</Badge>
  if (["pendiente", "planificada"].includes(value)) return <Badge variant="accent">{value}</Badge>
  return <Badge variant="outline">{value}</Badge>
}

function Alert({ tone, children }: { tone: "success" | "error" | "info"; children: ReactNode }) {
  const Icon = tone === "success" ? CheckCircle2 : AlertCircle
  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-md border px-3 py-2 text-xs",
        tone === "success" && "border-secondary/30 bg-secondary/10 text-secondary",
        tone === "error" && "border-destructive/30 bg-destructive/10 text-destructive",
        tone === "info" && "border-border bg-surface-muted text-muted-foreground",
      )}
    >
      <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
      <span className="min-w-0 break-words">{children}</span>
    </div>
  )
}

export default App
