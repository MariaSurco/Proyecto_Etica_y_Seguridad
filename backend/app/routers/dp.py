import json
import os

from fastapi import APIRouter

from app.dp.data import dataset_summary
from app.dp.model import get_baseline_metrics, train_dp_model
from app.dp.queries import QUERY_DISPATCH
from app.schemas.dp import (
    DatasetSummaryResponse,
    DPComparisonResponse,
    DPModelRequest,
    DPModelResponse,
    DPQueryRequest,
    DPQueryResponse,
)

router = APIRouter(prefix="/api", tags=["privacidad-diferencial"])

_COMPARISON_PATH = os.path.join(os.path.dirname(__file__), "..", "dp", "comparison_precomputed.json")


@router.get("/dataset/summary", response_model=DatasetSummaryResponse)
def get_dataset_summary():
    return dataset_summary()


@router.post("/dp/query", response_model=DPQueryResponse)
def run_dp_query(request: DPQueryRequest):
    result = QUERY_DISPATCH[request.query_type](request.epsilon)
    return {"query_type": request.query_type, "epsilon": request.epsilon, **result}


@router.post("/dp/model", response_model=DPModelResponse)
def run_dp_model(request: DPModelRequest):
    return {"model": train_dp_model(request.epsilon), "baseline": get_baseline_metrics()}


@router.get("/dp/comparison", response_model=DPComparisonResponse)
def get_dp_comparison():
    with open(_COMPARISON_PATH, encoding="utf-8") as f:
        return json.load(f)
