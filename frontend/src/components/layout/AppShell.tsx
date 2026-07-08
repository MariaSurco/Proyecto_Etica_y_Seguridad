import { Outlet, useLocation } from "react-router-dom"
import { Sidebar } from "./Sidebar"
import { MobileNav } from "./MobileNav"
import { ThemeToggle } from "./ThemeToggle"

const TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": {
    title: "Explorar el dataset",
    subtitle: "Bank Marketing Dataset — riesgo de reidentificación y estadísticas base",
  },
  "/queries": {
    title: "Playground de queries con DP",
    subtitle: "Compara el valor real contra su versión con privacidad diferencial",
  },
  "/modelo": {
    title: "Modelo con privacidad diferencial",
    subtitle: "diffprivlib.LogisticRegression vs. baseline sin privacidad",
  },
  "/trade-off": {
    title: "Trade-off privacidad ↔ utilidad",
    subtitle: "Curva ε vs. desempeño del modelo y fairness",
  },
  "/etica": {
    title: "Sobre el proyecto",
    subtitle: "Marco ético, DPIA y referencias del curso DS3031",
  },
}

export function AppShell() {
  const location = useLocation()
  const meta = TITLES[location.pathname] ?? TITLES["/"]

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <MobileNav />
        <header className="flex items-center justify-between border-b border-border bg-surface/60 px-6 py-5 backdrop-blur-sm">
          <div>
            <h1 className="text-lg font-semibold text-foreground">{meta.title}</h1>
            <p className="text-sm text-muted-foreground">{meta.subtitle}</p>
          </div>
          <ThemeToggle />
        </header>
        <main className="flex-1 overflow-y-auto px-6 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
