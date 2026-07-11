import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Copy, ShieldCheck, Megaphone, Search, PhoneCall } from "lucide-react"

import { api, type DemoUsuario } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const DEMO_PASSWORD = "CambiarEnPrimerAcceso!123"

const ROLE_INFO: Record<string, { label: string; description: string; icon: typeof ShieldCheck; permisos: string[] }> = {
  administrador: {
    label: "Administrador",
    description: "Gestiona usuarios y roles, accede a clientes y campañas, revisa auditoría completa.",
    icon: ShieldCheck,
    permisos: ["clientes:ver_sensible", "clientes:exportar", "campanias:crear_editar", "campanias:consultar", "usuarios:gestionar", "auditoria:consultar"],
  },
  supervisor: {
    label: "Supervisor",
    description: "Crea y cierra campañas, asigna clientes a teleoperadores, accede a clientes y auditoría.",
    icon: Megaphone,
    permisos: ["clientes:ver_sensible", "clientes:exportar", "campanias:crear_editar", "campanias:consultar", "auditoria:consultar"],
  },
  analista: {
    label: "Analista",
    description: "Consulta clientes (vista parcial) y campañas, sin permisos de edición.",
    icon: Search,
    permisos: ["clientes:ver_parcial", "campanias:consultar"],
  },
  teleoperador: {
    label: "Teleoperador",
    description: "Ve solo sus clientes asignados y registra resultados de contacto.",
    icon: PhoneCall,
    permisos: ["clientes:ver_asignados", "campanias:consultar_asignadas", "resultados:registrar"],
  },
}

const ROLE_ORDER = ["administrador", "supervisor", "analista", "teleoperador"]

function copyToClipboard(text: string, label: string) {
  navigator.clipboard
    .writeText(text)
    .then(() => toast.success(`${label} copiado al portapapeles`))
    .catch(() => toast.error("No se pudo copiar"))
}

export function Usuarios() {
  const [usuarios, setUsuarios] = useState<DemoUsuario[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getDemoUsuarios()
      .then(setUsuarios)
      .catch(() => toast.error("No se pudo cargar la lista de usuarios. ¿Está corriendo el backend en :8000?"))
      .finally(() => setLoading(false))
  }, [])

  const grouped = ROLE_ORDER.map((rol) => ({
    rol,
    info: ROLE_INFO[rol],
    users: usuarios.filter((u) => u.rol === rol),
  }))

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Contraseña de acceso</CardTitle>
          <CardDescription>Misma contraseña temporal para todos los usuarios de esta demo</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between rounded-lg border border-primary/30 bg-primary/5 px-4 py-3">
            <span className="font-mono text-lg font-semibold tracking-tight text-primary">{DEMO_PASSWORD}</span>
            <Button size="sm" variant="outline" onClick={() => copyToClipboard(DEMO_PASSWORD, "Contraseña")}>
              <Copy className="h-3.5 w-3.5" />
              Copiar
            </Button>
          </div>
        </CardContent>
      </Card>

      {loading && <div className="animate-pulse text-sm text-muted-foreground">Cargando usuarios…</div>}

      {!loading && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {grouped.map(({ rol, info, users }) => (
            <Card key={rol}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base text-foreground">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <info.icon className="h-4 w-4" />
                  </span>
                  {info.label}
                  <Badge variant="secondary" className="ml-auto">
                    {users.length} usuario{users.length === 1 ? "" : "s"}
                  </Badge>
                </CardTitle>
                <CardDescription>{info.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <div className="flex flex-wrap gap-1.5">
                  {info.permisos.map((p) => (
                    <Badge key={p} variant="outline" className="font-mono text-[10px]">
                      {p}
                    </Badge>
                  ))}
                </div>
                <div className="flex flex-col divide-y divide-border rounded-lg border border-border">
                  {users.map((u) => (
                    <button
                      key={u.username}
                      onClick={() => copyToClipboard(u.username, "Usuario")}
                      className="flex items-center justify-between gap-3 px-3 py-2 text-left text-sm transition-colors duration-150 hover:bg-surface-muted"
                      title="Copiar username"
                    >
                      <div className="min-w-0">
                        <p className="truncate font-medium text-foreground">{u.nombre_completo}</p>
                        <p className="truncate font-mono text-xs text-muted-foreground">{u.username}</p>
                      </div>
                      <Copy className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                    </button>
                  ))}
                  {users.length === 0 && (
                    <p className="px-3 py-2 text-xs text-muted-foreground">Sin usuarios para este rol.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
