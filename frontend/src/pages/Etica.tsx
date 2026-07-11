import { BookOpen } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const REFLECTIONS = [
  {
    title: "Sesgo algorítmico",
    body: "El modelo baseline de este proyecto ya muestra una brecha de tratamiento por grupo etario antes de aplicar cualquier mecanismo de privacidad. La lección metodológica de casos como Gender Shades y COMPAS —reportar métricas desagregadas por grupo, no solo el desempeño global— es la que se aplica en la pestaña Modelo con DP.",
  },
  {
    title: "Transparencia",
    body: "El slider de ε de este dashboard hace visible, en tiempo real, el efecto del presupuesto de privacidad sobre la utilidad y la equidad del sistema — en vez de dejar esa decisión oculta detrás de un valor fijo en un archivo de configuración.",
  },
  {
    title: "Consentimiento",
    body: "El consentimiento opt-in/opt-out del cliente gobierna si puede ser contactado, pero no tiene forma de expresar preferencias sobre cuánto ruido de privacidad se aplica cuando su registro entra a un reporte agregado — una limitación estructural del sistema.",
  },
  {
    title: "Tensión privacidad-equidad",
    body: "No existe, en general, un clasificador que satisfaga simultáneamente calibración y balance de errores entre grupos. La privacidad diferencial no resuelve esta tensión: solo desplaza el punto de operación del sistema a lo largo de un eje adicional (ε).",
  },
  {
    title: "Auditoría y rendición de cuentas",
    body: "Casos reales de sistemas de riesgo financiero automatizados muestran que ningún mecanismo técnico —ni cifrado, ni control de accesos, ni privacidad diferencial— sustituye la necesidad de una auditoría de equidad recurrente e independiente antes de que un modelo tome decisiones que afectan el acceso de una persona a un servicio financiero.",
  },
]

export function Etica() {
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-foreground">
            <BookOpen className="h-4 w-4 text-primary" />
            Resumen de proyecto
          </CardTitle>
          <CardDescription>Mishelle · Mafer · Angel</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p>
            Este proyecto aplica <strong className="text-foreground">privacidad diferencial</strong> sobre el{" "}
            <strong className="text-foreground">Bank Marketing Dataset</strong>: qué se puede inferir sobre un
            cliente incluso cuando nadie accede directamente a la base de datos, sino solo a un reporte agregado o
            a un modelo entrenado sobre ella.
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {REFLECTIONS.map((r) => (
          <Card key={r.title}>
            <CardHeader>
              <CardTitle className="text-base text-foreground">{r.title}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">{r.body}</CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
