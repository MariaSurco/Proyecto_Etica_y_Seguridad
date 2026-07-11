import { NavLink } from "react-router-dom"
import { Compass, SlidersHorizontal, BrainCircuit, TrendingUp, HeartHandshake, Users } from "lucide-react"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { to: "/", label: "Explorar", icon: Compass, end: true },
  { to: "/queries", label: "Queries", icon: SlidersHorizontal },
  { to: "/modelo", label: "Modelo", icon: BrainCircuit },
  { to: "/trade-off", label: "Trade-off", icon: TrendingUp },
  { to: "/etica", label: "Resumen", icon: HeartHandshake },
  { to: "/usuarios", label: "Usuarios", icon: Users },
]

export function MobileNav() {
  return (
    <nav className="flex items-center gap-1 overflow-x-auto border-b border-border bg-surface px-2 py-2 md:hidden">
      {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors duration-150",
              isActive
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-surface-muted",
            )
          }
        >
          <Icon className="h-3.5 w-3.5" />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
