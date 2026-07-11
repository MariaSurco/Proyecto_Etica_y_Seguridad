import { NavLink } from "react-router-dom"
import { Compass, SlidersHorizontal, BrainCircuit, TrendingUp, HeartHandshake, ShieldCheck, Landmark, Users } from "lucide-react"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { to: "/", label: "Explorar dataset", icon: Compass, end: true },
  { to: "/queries", label: "Queries con DP", icon: SlidersHorizontal },
  { to: "/modelo", label: "Modelo con DP", icon: BrainCircuit },
  { to: "/trade-off", label: "Trade-off", icon: TrendingUp },
  { to: "/etica", label: "Resumen de proyecto", icon: HeartHandshake },
]

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-surface md:flex">
      <div className="flex items-center gap-2.5 px-5 py-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold">Privacidad Diferencial</span>
          <span className="text-xs text-muted-foreground">Campañas Bancarias</span>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-surface-muted hover:text-foreground",
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="flex flex-col gap-1 border-t border-border px-3 py-3">
        <NavLink
          to="/usuarios"
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150",
              isActive
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-surface-muted hover:text-foreground",
            )
          }
        >
          <Users className="h-4 w-4 shrink-0" />
          Usuarios del sistema
        </NavLink>
        <NavLink
          to="/banca"
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors duration-150 hover:bg-surface-muted hover:text-foreground"
        >
          <Landmark className="h-4 w-4 shrink-0" />
          Operación bancaria
        </NavLink>
      </div>

      <div className="px-5 py-4 text-[11px] text-muted-foreground">Mishelle · Mafer · Angel</div>
    </aside>
  )
}
