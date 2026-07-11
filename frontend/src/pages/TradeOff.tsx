import { useEffect, useState } from "react"
import {
  CartesianGrid,
  Label,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { toast } from "sonner"

import { api, type DPComparison } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function TradeOff() {
  const [data, setData] = useState<DPComparison | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getDpComparison()
      .then(setData)
      .catch(() => toast.error("No se pudo cargar la curva de comparación precomputada."))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="animate-pulse text-sm text-muted-foreground">Cargando curva ε–utilidad…</div>
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="pt-5 text-sm text-muted-foreground">
          No hay datos de comparación disponibles. Ejecuta{" "}
          <code className="font-mono">python -m app.dp.precompute_comparison</code> en el backend.
        </CardContent>
      </Card>
    )
  }

  const chartData = data.points.map((p) => ({
    epsilon: p.epsilon,
    f1: p.f1,
    roc_auc: p.roc_auc,
  }))

  const fairnessData = data.points.map((p) => ({
    epsilon: p.epsilon,
    demographic_parity_diff: p.demographic_parity_diff,
    equal_opportunity_diff: p.equal_opportunity_diff,
  }))

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Trade-off privacidad ↔ utilidad</CardTitle>
          <CardDescription>
            F1 del modelo con DP vs. ε (escala logarítmica) — línea punteada: baseline sin privacidad (F1 = {data.baseline.f1.toFixed(3)})
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 16, right: 24, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="epsilon"
                  scale="log"
                  domain={["auto", "auto"]}
                  type="number"
                  ticks={[0.1, 0.5, 1, 2, 5, 10]}
                  tick={{ fontSize: 12, fill: "var(--muted-foreground)" }}
                  axisLine={{ stroke: "var(--border)" }}
                  tickLine={false}
                >
                  <Label value="ε (presupuesto de privacidad, escala log)" offset={-4} position="insideBottom" fill="var(--muted-foreground)" fontSize={12} />
                </XAxis>
                <YAxis domain={[0.4, 1]} tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
                  labelFormatter={(v) => `ε = ${v}`}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine y={data.baseline.f1} stroke="var(--chart-baseline)" strokeDasharray="6 4" label={{ value: "Baseline F1", position: "right", fontSize: 11, fill: "var(--muted-foreground)" }} />
                <Line type="monotone" dataKey="f1" name="F1 con DP" stroke="var(--chart-1)" strokeWidth={2.5} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Fairness bajo distintos niveles de privacidad</CardTitle>
          <CardDescription>Diferencia absoluta entre grupos (joven vs. no_joven) por métrica</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={fairnessData} margin={{ top: 16, right: 24, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="epsilon"
                  scale="log"
                  domain={["auto", "auto"]}
                  type="number"
                  ticks={[0.1, 0.5, 1, 2, 5, 10]}
                  tick={{ fontSize: 12, fill: "var(--muted-foreground)" }}
                  axisLine={{ stroke: "var(--border)" }}
                  tickLine={false}
                >
                  <Label value="ε (escala log)" offset={-4} position="insideBottom" fill="var(--muted-foreground)" fontSize={12} />
                </XAxis>
                <YAxis tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
                  labelFormatter={(v) => `ε = ${v}`}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine y={data.baseline.demographic_parity_diff} stroke="var(--chart-1)" strokeDasharray="4 3" />
                <ReferenceLine y={data.baseline.equal_opportunity_diff} stroke="var(--chart-2)" strokeDasharray="4 3" />
                <Line type="monotone" dataKey="demographic_parity_diff" name="Paridad demográfica" stroke="var(--chart-1)" strokeWidth={2.5} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="equal_opportunity_diff" name="Igualdad de oportunidad" stroke="var(--chart-2)" strokeWidth={2.5} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Líneas punteadas: valor del baseline sin privacidad para cada métrica.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
