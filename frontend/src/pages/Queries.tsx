import { useEffect, useState } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { toast } from "sonner"

import { api, type DPQueryResult, type QueryType } from "@/lib/api"
import { EpsilonControl, PrivacyBadge } from "@/components/EpsilonControl"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const QUERY_LABELS: Record<QueryType, string> = {
  mean_balance: "Media de balance (EUR)",
  count_job: "Conteo de clientes por ocupación",
  count_marital: "Conteo de clientes por estado civil",
  histogram_age: "Histograma de edad",
}

function formatNumber(n: number): string {
  return n.toLocaleString("es-PE", { maximumFractionDigits: 2 })
}

type QueryChartDatum = {
  name: string | number
  real: number
  dp: number
}

export function Queries() {
  const [queryType, setQueryType] = useState<QueryType>("mean_balance")
  const [epsilon, setEpsilon] = useState(1.0)
  const [result, setResult] = useState<DPQueryResult | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchResult = (type: QueryType, eps: number) => {
    setLoading(true)
    api
      .runDpQuery(type, eps)
      .then(setResult)
      .catch(() => toast.error("No se pudo ejecutar la consulta con DP."))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchResult(queryType, epsilon)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryType])

  const chartData: QueryChartDatum[] = (() => {
    if (!result) return []
    if (result.query_type === "mean_balance") return []
    if (result.query_type === "histogram_age") {
      const trueVal = result.true_value as { bin_centers: number[]; counts: number[] }
      const dpVal = result.dp_value as { bin_centers: number[]; counts: number[] }
      return trueVal.bin_centers.map((center, i) => ({
        name: Math.round(center),
        real: trueVal.counts[i],
        dp: Math.max(0, dpVal.counts[i]),
      }))
    }
    const trueVal = result.true_value as Record<string, number>
    const dpVal = result.dp_value as Record<string, number>
    return Object.keys(trueVal).map((key) => ({
      name: key,
      real: trueVal[key],
      dp: Math.max(0, dpVal[key]),
    }))
  })()

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Configurar consulta</CardTitle>
          <CardDescription>Elige qué agregado consultar y con qué presupuesto de privacidad</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-muted-foreground">Tipo de consulta</label>
            <Select value={queryType} onValueChange={(v) => setQueryType(v as QueryType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(QUERY_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <EpsilonControl
            value={epsilon}
            onChange={setEpsilon}
            onDebouncedChange={(eps) => fetchResult(queryType, eps)}
          />

          {result && (
            <div className="flex items-center justify-between rounded-lg bg-surface-muted px-3 py-2.5">
              <span className="text-xs text-muted-foreground">Nivel de protección</span>
              <PrivacyBadge epsilon={epsilon} />
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>{QUERY_LABELS[queryType]}</CardTitle>
          <CardDescription>Valor real vs. valor con mecanismo de Laplace (ε = {epsilon.toFixed(2)})</CardDescription>
        </CardHeader>
        <CardContent>
          {loading && <div className="animate-pulse text-sm text-muted-foreground">Calculando…</div>}

          {!loading && result && result.query_type === "mean_balance" && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-lg border border-border p-4">
                <p className="text-xs text-muted-foreground">Valor real</p>
                <p className="font-mono text-xl font-semibold tabular-nums">
                  {formatNumber(result.true_value as number)} €
                </p>
              </div>
              <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
                <p className="text-xs text-muted-foreground">Con privacidad diferencial</p>
                <p className="font-mono text-xl font-semibold tabular-nums text-primary">
                  {formatNumber(result.dp_value as number)} €
                </p>
              </div>
              <div className="rounded-lg border border-border p-4">
                <p className="text-xs text-muted-foreground">Error absoluto</p>
                <p className="font-mono text-xl font-semibold tabular-nums">
                  {formatNumber(result.absolute_error)} €
                </p>
              </div>
            </div>
          )}

          {!loading && result && result.query_type !== "mean_balance" && (
            <>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={{ stroke: "var(--border)" }} tickLine={false} />
                    <YAxis tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "var(--surface)",
                        border: "1px solid var(--border)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="real" name="Real (sin DP)" fill="var(--chart-baseline)" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="dp" name="Con DP" fill="var(--chart-1)" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-3 text-xs text-muted-foreground">
                Error absoluto medio: <span className="font-mono tabular-nums">{formatNumber(result.absolute_error)}</span>
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
