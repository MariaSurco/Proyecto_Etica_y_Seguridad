const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

export interface KAnonymityBucket {
  label: string
  count: number
}

export interface KAnonymitySummary {
  n_groups: number
  min_k: number
  pct_unique: number
  pct_k_lt5: number
  pct_k_lt10: number
  k_buckets: KAnonymityBucket[]
}

export interface DatasetSummary {
  n_records: number
  n_columns: number
  quasi_identifiers: string[]
  sensitive_attributes: string[]
  deposit_distribution: Record<string, number>
  k_anonymity: KAnonymitySummary
}

export type QueryType = "mean_balance" | "count_job" | "count_marital" | "histogram_age"

export interface DPQueryResult {
  query_type: QueryType
  epsilon: number
  true_value: number | Record<string, number> | { bin_centers: number[]; counts: number[] }
  dp_value: number | Record<string, number> | { bin_centers: number[]; counts: number[] }
  absolute_error: number
}

export interface DPModelMetrics {
  epsilon: number
  accuracy: number
  f1: number
  roc_auc: number | null
  demographic_parity_diff: number
  equal_opportunity_diff: number
}

export interface BaselineMetrics {
  accuracy: number
  f1: number
  roc_auc: number
  demographic_parity_diff: number
  equal_opportunity_diff: number
}

export interface DPModelResult {
  model: DPModelMetrics
  baseline: BaselineMetrics
}

export interface DPComparison {
  baseline: BaselineMetrics
  points: DPModelMetrics[]
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface Cliente {
  cliente_id: string
  deposit?: string | null
  nombre?: string
  dni?: string
  email?: string
  telefono?: string
  direccion?: string
  age?: number
  job?: string
  marital?: string
  education?: string
  balance?: string | number
  contact?: string
}

export interface Consentimiento {
  consentimiento_id: string
  cliente_id: string
  estado: "opt-in" | "opt-out" | "no informado"
  canal?: string | null
  fecha_actualizacion?: string | null
  actualizado_por?: string | null
}

export interface Campania {
  campania_id: string
  nombre: string
  producto: string
  fecha_inicio: string
  fecha_fin?: string | null
  estado: "planificada" | "activa" | "cerrada" | "cancelada"
}

export interface Asignacion {
  asignacion_id: string
  cliente_id: string
  campania_id: string
  usuario_id: string
  estado_contacto?: string | null
  fecha_asignacion?: string | null
}

export interface ResultadoContacto {
  resultado_id: string
  asignacion_id: string
  resultado: string
  observacion?: string | null
  fecha_contacto?: string | null
}

export interface Usuario {
  usuario_id: string
  username: string
  nombre_completo: string
  email_corporativo: string
  rol_id: number
  rol_nombre?: string | null
  activo: boolean
}

export interface Rol {
  rol_id: number
  nombre: string
  descripcion?: string | null
}

export interface AuditLog {
  log_id: string
  usuario_id?: string | null
  accion: string
  recurso: string
  recurso_id?: string | null
  resultado: string
  detalle?: string | null
  timestamp_evento?: string | null
}

class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit, token?: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const body = await res.text().catch(() => "")
    throw new ApiError(`${res.status} ${res.statusText}: ${body}`, res.status)
  }
  return res.json() as Promise<T>
}

export const api = {
  login: async (username: string, password: string) => {
    const body = new URLSearchParams({ username, password })
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    })
    if (!res.ok) {
      const text = await res.text().catch(() => "")
      throw new ApiError(`${res.status} ${res.statusText}: ${text}`, res.status)
    }
    return res.json() as Promise<LoginResponse>
  },

  getClientesElegibles: (token: string) => request<Cliente[]>("/clientes/elegibles", undefined, token),

  getClientesAsignados: (token: string) => request<Cliente[]>("/clientes/asignados", undefined, token),

  getConsentimiento: (token: string, clienteId: string) =>
    request<Consentimiento>(`/clientes/${clienteId}/consentimiento`, undefined, token),

  updateConsentimiento: (
    token: string,
    clienteId: string,
    payload: { estado: Consentimiento["estado"]; canal?: string },
  ) =>
    request<Consentimiento>(
      `/clientes/${clienteId}/consentimiento`,
      { method: "PATCH", body: JSON.stringify(payload) },
      token,
    ),

  getCampanias: (token: string) => request<Campania[]>("/campanias", undefined, token),

  createCampania: (token: string, payload: Omit<Campania, "campania_id" | "fecha_fin"> & { fecha_fin?: string }) =>
    request<Campania>("/campanias", { method: "POST", body: JSON.stringify(payload) }, token),

  updateCampania: (token: string, campaniaId: string, payload: Partial<Omit<Campania, "campania_id">>) =>
    request<Campania>(`/campanias/${campaniaId}`, { method: "PATCH", body: JSON.stringify(payload) }, token),

  createAsignacion: (token: string, payload: { cliente_id: string; campania_id: string; usuario_id: string }) =>
    request<Asignacion>("/asignaciones", { method: "POST", body: JSON.stringify(payload) }, token),

  getMisAsignaciones: (token: string) => request<Asignacion[]>("/asignaciones/mias", undefined, token),

  registerResultado: (token: string, asignacionId: string, payload: { resultado: string; observacion?: string }) =>
    request<ResultadoContacto>(
      `/asignaciones/${asignacionId}/resultado`,
      { method: "POST", body: JSON.stringify(payload) },
      token,
    ),

  getUsuarios: (token: string) => request<Usuario[]>("/usuarios", undefined, token),

  getTeleoperadores: (token: string) => request<Usuario[]>("/usuarios/teleoperadores", undefined, token),

  createUsuario: (
    token: string,
    payload: {
      username: string
      nombre_completo: string
      email_corporativo: string
      password: string
      rol_id: number
    },
  ) => request<Usuario>("/usuarios", { method: "POST", body: JSON.stringify(payload) }, token),

  updateUsuarioActivo: (token: string, usuarioId: string, activo: boolean) =>
    request<Usuario>(`/usuarios/${usuarioId}/activo`, { method: "PATCH", body: JSON.stringify({ activo }) }, token),

  getRoles: (token: string) => request<Rol[]>("/roles", undefined, token),

  getAuditLogs: (token: string) => request<AuditLog[]>("/auditoria/logs", undefined, token),

  getDatasetSummary: () => request<DatasetSummary>("/api/dataset/summary"),

  runDpQuery: (query_type: QueryType, epsilon: number) =>
    request<DPQueryResult>("/api/dp/query", {
      method: "POST",
      body: JSON.stringify({ query_type, epsilon }),
    }),

  runDpModel: (epsilon: number) =>
    request<DPModelResult>("/api/dp/model", {
      method: "POST",
      body: JSON.stringify({ epsilon }),
    }),

  getDpComparison: () => request<DPComparison>("/api/dp/comparison"),
}

export { ApiError }
