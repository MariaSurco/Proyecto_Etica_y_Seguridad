import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Database, Fingerprint, ShieldAlert, Users } from "lucide-react"
import { toast } from "sonner"

import { api, type DatasetSummary } from "@/lib/api"
import { StatTile } from "@/components/StatTile"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function Explorar() {
  const [summary, setSummary] = useState<DatasetSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getDatasetSummary()
      .then(setSummary)
      .catch(() => toast.error("No se pudo cargar el resumen del dataset. ¿Está corriendo el backend en :8000?"))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="animate-pulse text-sm text-muted-foreground">Cargando dataset…</div>
  }

  if (!summary) {
    return (
      <Card>
        <CardContent className="pt-5 text-sm text-muted-foreground">
          No hay datos disponibles. Verifica que el backend FastAPI esté corriendo y sea accesible desde esta URL.
        </CardContent>
      </Card>
    )
  }

  const kAnon = summary.k_anonymity
  const pctSafe = 100 - kAnon.pct_k_lt5

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Registros"
          value={summary.n_records.toLocaleString("es-PE")}
          hint={`${summary.n_columns} columnas`}
          icon={Database}
          accent="primary"
        />
        <StatTile
          label="Cuasi-identificadores"
          value={String(summary.quasi_identifiers.length)}
          hint={summary.quasi_identifiers.join(", ")}
          icon={Fingerprint}
          accent="secondary"
        />
        <StatTile
          label="Registros únicos (k=1)"
          value={`${kAnon.pct_unique.toFixed(1)}%`}
          hint={`${kAnon.n_groups.toLocaleString("es-PE")} combinaciones distintas`}
          icon={ShieldAlert}
          accent="destructive"
        />
        <StatTile
          label="Depósito contratado"
          value={`${(summary.deposit_distribution["yes"] ?? 0).toFixed(1)}%`}
          hint="Distribución de la variable objetivo"
          icon={Users}
          accent="accent"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Riesgo de reidentificación (k-anonimato empírico)</CardTitle>
            <CardDescription>
              Agrupando por {summary.quasi_identifiers.join(", ")} — {kAnon.n_groups.toLocaleString("es-PE")} combinaciones distintas, k mínimo = {kAnon.min_k}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={kAnon.k_buckets} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={{ stroke: "var(--border)" }} tickLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--surface)",
                      border: "1px solid var(--border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    labelFormatter={(label) => `Tamaño de grupo ${label}`}
                    formatter={(value) => [`${Number(value ?? 0).toLocaleString("es-PE")} combinaciones`, ""]}
                  />
                  <Bar dataKey="count" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              {kAnon.pct_unique.toFixed(1)}% de registros son únicos (k=1), {kAnon.pct_k_lt5.toFixed(1)}% tienen k&lt;5,{" "}
              {kAnon.pct_k_lt10.toFixed(1)}% tienen k&lt;10.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Atributos sensibles</CardTitle>
            <CardDescription>Clasificación de sensibilidad (Ley N.° 29733)</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div>
              <p className="mb-1.5 text-xs font-medium text-muted-foreground">Cuasi-identificadores</p>
              <div className="flex flex-wrap gap-1.5">
                {summary.quasi_identifiers.map((q) => (
                  <Badge key={q} variant="secondary">
                    {q}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-1.5 text-xs font-medium text-muted-foreground">Atributos sensibles</p>
              <div className="flex flex-wrap gap-1.5">
                {summary.sensitive_attributes.map((s) => (
                  <Badge key={s} variant="destructive">
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="mt-2 rounded-lg bg-surface-muted p-3">
              <p className="text-xs text-muted-foreground">
                <strong className="text-foreground">{pctSafe.toFixed(1)}%</strong> de los registros
                comparten su combinación de cuasi-identificadores con 5 o más personas —
                el resto queda expuesto a reidentificación directa si esos atributos se cruzan
                con una fuente externa.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
