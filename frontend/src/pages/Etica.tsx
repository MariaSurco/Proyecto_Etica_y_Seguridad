import { BookOpen, ExternalLink, ScrollText } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const REFLECTIONS = [
  {
    title: "Sesgo algorítmico",
    refs: "Gender Shades (Buolamwini & Gebru, 2018) · COMPAS (Angwin et al., 2016)",
    body: "El modelo baseline de este proyecto ya muestra una brecha de tratamiento por grupo etario antes de aplicar cualquier mecanismo de privacidad. La lección metodológica de Gender Shades y COMPAS —reportar métricas desagregadas por grupo, no solo el desempeño global— es la que se aplica en la pestaña Modelo con DP.",
  },
  {
    title: "Transparencia",
    refs: "Principio de privacidad por diseño, D.S. 016-2024-JUS",
    body: "El slider de ε de este dashboard hace visible, en tiempo real, el efecto del presupuesto de privacidad sobre la utilidad y la equidad del sistema — en vez de dejar esa decisión oculta detrás de un valor fijo en un archivo de configuración.",
  },
  {
    title: "Consentimiento",
    refs: "Ley N.° 29733 · Sistema de opt-in/opt-out del backend",
    body: "El consentimiento opt-in/opt-out del cliente gobierna si puede ser contactado, pero no tiene forma de expresar preferencias sobre cuánto ruido de privacidad se aplica cuando su registro entra a un reporte agregado — una limitación estructural discutida en el informe.",
  },
  {
    title: "Tensión privacidad-equidad",
    refs: "Kleinberg, Mullainathan & Raghavan (2016)",
    body: "El teorema de imposibilidad de Kleinberg muestra que no existe, en general, un clasificador que satisfaga simultáneamente calibración y balance de errores entre grupos. La privacidad diferencial no resuelve esta tensión: solo desplaza el punto de operación del sistema a lo largo de un eje adicional (ε).",
  },
  {
    title: "Toeslagenaffaire",
    refs: "Amnesty International (2021)",
    body: "El escándalo de las prestaciones neerlandesas ilustra que ningún mecanismo técnico —ni cifrado, ni RBAC, ni privacidad diferencial— sustituye la necesidad de una auditoría de equidad recurrente e independiente antes de que un modelo de riesgo tome decisiones que afectan el acceso de una persona a un servicio financiero.",
  },
]

export function Etica() {
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-foreground">
            <BookOpen className="h-4 w-4 text-primary" />
            Sobre el proyecto
          </CardTitle>
          <CardDescription>
            Entrega final — DS3031 Ética y Seguridad de Datos, UTEC. Grupo 1: Mora Huamanchay, Angel Obed ·
            Surco Vergara, Maria Fernanda · Villarreal Falcon, Mishelle Stephany.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p>
            La entrega parcial de este proyecto abordó el <strong className="text-foreground">Bank Marketing Dataset</strong> desde
            la óptica de la seguridad de la información (cifrado, RBAC, auditoría). Esta entrega final reenfoca el mismo caso de
            negocio hacia la <strong className="text-foreground">privacidad diferencial</strong>: qué se puede inferir sobre un
            cliente incluso cuando nadie accede directamente a la base de datos, sino solo a un reporte agregado o a un modelo
            entrenado sobre ella.
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {REFLECTIONS.map((r) => (
          <Card key={r.title}>
            <CardHeader>
              <CardTitle className="text-base text-foreground">{r.title}</CardTitle>
              <Badge variant="outline" className="w-fit">
                {r.refs}
              </Badge>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">{r.body}</CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-foreground">
            <ScrollText className="h-4 w-4 text-primary" />
            Documentación completa
          </CardTitle>
          <CardDescription>DPIA formal, metodología y referencias académicas completas</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <a
            href="https://github.com"
            onClick={(e) => e.preventDefault()}
            className="flex w-fit items-center gap-1.5 text-primary transition-opacity hover:opacity-75"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <code className="font-mono text-xs">docs/INFORME_FINAL.md</code> — informe con DPIA y reflexión ética completa
          </a>
          <a
            href="https://github.com"
            onClick={(e) => e.preventDefault()}
            className="flex w-fit items-center gap-1.5 text-primary transition-opacity hover:opacity-75"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <code className="font-mono text-xs">notebooks/01_privacidad_diferencial.ipynb</code> — análisis técnico completo
          </a>
        </CardContent>
      </Card>
    </div>
  )
}
