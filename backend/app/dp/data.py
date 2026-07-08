import os

import pandas as pd

QUASI_IDENTIFIERS = ["age", "job", "marital", "education"]
SENSITIVE_ATTRS = ["balance", "default", "housing", "loan", "deposit"]
FEATURES_NUM = ["age", "balance", "day", "campaign", "pdays", "previous"]
FEATURES_CAT = ["job", "marital", "education", "default", "housing", "loan",
                "contact", "month", "poutcome"]

BANK_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "bank.csv")

_df_cache: pd.DataFrame | None = None


def get_dataset() -> pd.DataFrame:
    global _df_cache
    if _df_cache is None:
        _df_cache = pd.read_csv(BANK_CSV_PATH)
    return _df_cache


K_BUCKET_LABELS = ["k=1", "k=2", "k=3-4", "k=5-9", "k=10-19", "k=20-49", "k>=50"]
K_BUCKET_EDGES = [1, 2, 3, 5, 10, 20, 50, float("inf")]


def compute_k_anonymity(df: pd.DataFrame) -> dict:
    group_sizes = df.groupby(QUASI_IDENTIFIERS).size().reset_index(name="k")
    merged = df.merge(group_sizes, on=QUASI_IDENTIFIERS)

    buckets = pd.cut(group_sizes["k"], bins=K_BUCKET_EDGES, right=False, labels=K_BUCKET_LABELS)
    bucket_counts = buckets.value_counts().reindex(K_BUCKET_LABELS, fill_value=0)
    k_buckets = [{"label": label, "count": int(count)} for label, count in bucket_counts.items()]

    return {
        "n_groups": int(len(group_sizes)),
        "min_k": int(group_sizes["k"].min()),
        "pct_unique": float((merged["k"] == 1).mean() * 100),
        "pct_k_lt5": float((merged["k"] < 5).mean() * 100),
        "pct_k_lt10": float((merged["k"] < 10).mean() * 100),
        "k_buckets": k_buckets,
    }


def dataset_summary() -> dict:
    df = get_dataset()
    deposit_dist = (df["deposit"].value_counts(normalize=True) * 100).round(2).to_dict()
    return {
        "n_records": int(df.shape[0]),
        "n_columns": int(df.shape[1]),
        "quasi_identifiers": QUASI_IDENTIFIERS,
        "sensitive_attributes": SENSITIVE_ATTRS,
        "deposit_distribution": deposit_dist,
        "k_anonymity": compute_k_anonymity(df),
    }
