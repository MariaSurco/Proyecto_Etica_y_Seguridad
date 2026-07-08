from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dataset_summary():
    resp = client.get("/api/dataset/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["n_records"] == 11162
    assert data["n_columns"] == 17
    assert data["k_anonymity"]["min_k"] == 1
    assert 0 < data["k_anonymity"]["pct_unique"] < 100
    assert len(data["k_anonymity"]["k_buckets"]) == 7
    assert sum(b["count"] for b in data["k_anonymity"]["k_buckets"]) == data["k_anonymity"]["n_groups"]


def test_dp_query_mean_balance():
    resp = client.post("/api/dp/query", json={"query_type": "mean_balance", "epsilon": 1.0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_type"] == "mean_balance"
    assert isinstance(data["true_value"], float)
    assert isinstance(data["dp_value"], float)
    assert data["absolute_error"] >= 0


def test_dp_query_count_job():
    resp = client.post("/api/dp/query", json={"query_type": "count_job", "epsilon": 1.0})
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["true_value"].keys()) == set(data["dp_value"].keys())


def test_dp_query_histogram_age():
    resp = client.post("/api/dp/query", json={"query_type": "histogram_age", "epsilon": 1.0})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["true_value"]["counts"]) == len(data["dp_value"]["counts"])


def test_dp_query_rejects_invalid_type():
    resp = client.post("/api/dp/query", json={"query_type": "bogus", "epsilon": 1.0})
    assert resp.status_code == 422


def test_dp_query_rejects_non_positive_epsilon():
    resp = client.post("/api/dp/query", json={"query_type": "mean_balance", "epsilon": 0})
    assert resp.status_code == 422


def test_dp_model_returns_metrics_and_baseline():
    resp = client.post("/api/dp/model", json={"epsilon": 1.0})
    assert resp.status_code == 200
    data = resp.json()
    assert 0 <= data["model"]["f1"] <= 1
    assert 0 <= data["baseline"]["f1"] <= 1
    assert data["model"]["epsilon"] == 1.0


def test_dp_comparison_has_all_epsilons():
    resp = client.get("/api/dp/comparison")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["points"]) == 6
    assert "baseline" in data
