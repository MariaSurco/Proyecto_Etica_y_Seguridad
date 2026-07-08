import numpy as np
from diffprivlib.mechanisms import Laplace
from diffprivlib.tools import histogram as dp_histogram
from diffprivlib.tools import mean as dp_mean

from app.dp.data import get_dataset


def query_mean_balance(epsilon: float) -> dict:
    df = get_dataset()
    true_value = float(df["balance"].mean())
    bounds = (float(df["balance"].min()), float(df["balance"].max()))
    dp_value = float(dp_mean(df["balance"].values, epsilon=epsilon, bounds=bounds))
    return {
        "true_value": true_value,
        "dp_value": dp_value,
        "absolute_error": abs(dp_value - true_value),
    }


def query_count_category(column: str, epsilon: float) -> dict:
    df = get_dataset()
    true_counts = df[column].value_counts()
    mech = Laplace(epsilon=epsilon, sensitivity=1.0)
    true_counts_dict = {str(k): float(v) for k, v in true_counts.items()}
    dp_counts = {k: float(mech.randomise(v)) for k, v in true_counts_dict.items()}
    mean_abs_error = float(np.mean([abs(dp_counts[k] - true_counts_dict[k]) for k in true_counts_dict]))
    return {
        "true_value": true_counts_dict,
        "dp_value": dp_counts,
        "absolute_error": mean_abs_error,
    }


def query_histogram_age(epsilon: float, bins: int = 15) -> dict:
    df = get_dataset()
    bounds = (int(df["age"].min()), int(df["age"].max()))
    true_hist, bin_edges = np.histogram(df["age"], bins=bins, range=bounds)
    dp_hist, _ = dp_histogram(df["age"].values, epsilon=epsilon, bins=bins, range=bounds)
    centers = ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist()
    return {
        "true_value": {"bin_centers": centers, "counts": [int(x) for x in true_hist]},
        "dp_value": {"bin_centers": centers, "counts": [float(x) for x in dp_hist]},
        "absolute_error": float(np.mean(np.abs(dp_hist - true_hist))),
    }


QUERY_DISPATCH = {
    "mean_balance": lambda epsilon: query_mean_balance(epsilon),
    "count_job": lambda epsilon: query_count_category("job", epsilon),
    "count_marital": lambda epsilon: query_count_category("marital", epsilon),
    "histogram_age": lambda epsilon: query_histogram_age(epsilon),
}
