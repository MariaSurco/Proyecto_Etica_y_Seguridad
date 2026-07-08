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

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!res.ok) {
    const body = await res.text().catch(() => "")
    throw new ApiError(`${res.status} ${res.statusText}: ${body}`, res.status)
  }
  return res.json() as Promise<T>
}

export const api = {
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
