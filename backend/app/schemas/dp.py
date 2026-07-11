from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class KAnonymityBucket(BaseModel):
    label: str
    count: int


class KAnonymitySummary(BaseModel):
    n_groups: int
    min_k: int
    pct_unique: float
    pct_k_lt5: float
    pct_k_lt10: float
    k_buckets: list[KAnonymityBucket]


class DatasetSummaryResponse(BaseModel):
    n_records: int
    n_columns: int
    quasi_identifiers: list[str]
    sensitive_attributes: list[str]
    deposit_distribution: dict[str, float]
    k_anonymity: KAnonymitySummary


class DPQueryRequest(BaseModel):
    query_type: Literal["mean_balance", "count_job", "count_marital", "histogram_age"]
    epsilon: float = Field(gt=0, le=50)


class DPQueryResponse(BaseModel):
    query_type: str
    epsilon: float
    true_value: Any
    dp_value: Any
    absolute_error: float


class DPModelRequest(BaseModel):
    epsilon: float = Field(gt=0, le=50)


class DPModelMetrics(BaseModel):
    epsilon: float
    accuracy: float
    f1: float
    roc_auc: Optional[float]
    demographic_parity_diff: float
    equal_opportunity_diff: float


class BaselineMetrics(BaseModel):
    accuracy: float
    f1: float
    roc_auc: float
    demographic_parity_diff: float
    equal_opportunity_diff: float


class DPModelResponse(BaseModel):
    model: DPModelMetrics
    baseline: BaselineMetrics


class DPComparisonResponse(BaseModel):
    baseline: BaselineMetrics
    points: list[DPModelMetrics]


class DemoUsuario(BaseModel):
    username: str
    nombre_completo: str
    rol: str
    activo: bool
