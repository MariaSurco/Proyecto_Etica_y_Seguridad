import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { toast } from "sonner"
import { Activity, Gauge, Scale, Target } from "lucide-react"

import { api, type DPModelResult } from "@/lib/api"
import { EpsilonControl, PrivacyBadge } from "@/components/EpsilonControl"
import { StatTile } from "@/components/StatTile"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

function pct(n: number): string {
  return `${(n * 100).toFixed(1)}%`
}

export function Modelo() {
  const [epsilon, setEpsilon] = useState(1.0)
  const [result, setResult] = useState<DPModelResult | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchResult = (eps: number) => {
    setLoading(true)
    api
      .runDpModel(eps)
      .then(setResult)
      .catch(() => toast.error("No se pudo entrenar el modelo con DP."))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchResult(epsilon)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const metricsChartData = result
    ? [
        { name: "Accuracy", baseline: result.baseline.accuracy, dp: result.model.accuracy },
        { name: "F1", baseline: result.baseline.f1, dp: result.model.f1 },
        { name: "ROC-AUC", baseline: result.baseline.roc_auc, dp: result.model.roc_auc ?? 0 },
      ]
    : []

  const fairnessChartData = result
    ? [
        {
          name: "Paridad demográfica",
          baseline: result.baseline.demographic_parity_diff,
          dp: result.model.demographic_parity_diff,
        },
        {
          name: "Igualdad de oportunidad",
          baseline: result.baseline.equal_opportunity_diff,
          dp: result.model.equal_opportunity_diff,
        },
      ]
    : []

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Entrenar con privacidad diferencial</CardTitle>
          <CardDescription>
            diffprivlib.LogisticRegression (perturbación objetiva) vs. LogisticRegression sin protección
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-w-xl">
            <EpsilonControl value={epsilon} onChange={setEpsilon} onDebouncedChange={fetchResult} />
          </div>
        </CardContent>
      </Card>

      {loading && <div className="animate-pulse text-sm text-muted-foreground">Entrenando modelo…</div>}

      {!loading && result && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="F1 con DP" value={pct(result.model.f1)} hint={`Baseline: ${pct(result.baseline.f1)}`} icon={Target} accent="primary" />
            <StatTile label="Accuracy con DP" value={pct(result.model.accuracy)} hint={`Baseline: ${pct(result.baseline.accuracy)}`} icon={Gauge} accent="secondary" />
            <StatTile
              label="ROC-AUC con DP"
              value={result.model.roc_auc ? pct(result.model.roc_auc) : "N/D"}
              hint={`Baseline: ${pct(result.baseline.roc_auc)}`}
              icon={Activity}
              accent="accent"
            />
            <StatTile
              label="Brecha de paridad"
              value={result.model.demographic_parity_diff.toFixed(3)}
              hint={`Baseline: ${result.baseline.demographic_parity_diff.toFixed(3)}`}
              icon={Scale}
              accent="destructive"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Desempeño: baseline vs. con DP</CardTitle>
                <CardDescription className="flex items-center gap-2">
                  ε = {epsilon.toFixed(2)} <PrivacyBadge epsilon={epsilon} />
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={metricsChartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={{ stroke: "var(--border)" }} tickLine={false} />
                      <YAxis domain={[0, 1]} tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Bar dataKey="baseline" name="Baseline" fill="var(--chart-baseline)" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="dp" name="Con DP" fill="var(--chart-1)" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Fairness: baseline vs. con DP</CardTitle>
                <CardDescription>Diferencia absoluta entre grupos (joven vs. no_joven) — menor es más equitativo</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={fairnessChartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={{ stroke: "var(--border)" }} tickLine={false} />
                      <YAxis tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Bar dataKey="baseline" name="Baseline" fill="var(--chart-baseline)" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="dp" name="Con DP" fill="var(--chart-5)" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
