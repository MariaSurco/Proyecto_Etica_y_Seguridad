import numpy as np
from diffprivlib.models import LogisticRegression as DPLogisticRegression
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.dp.data import FEATURES_CAT, FEATURES_NUM, get_dataset

SEED = 42

_state_cache: dict = {}


def _prepare() -> dict:
    if _state_cache:
        return _state_cache

    df = get_dataset()
    X = df[FEATURES_NUM + FEATURES_CAT].copy()
    y = (df["deposit"] == "yes").astype(int)
    age_group = np.where(df["age"] < 35, "joven", "no_joven")

    X_train, X_test, y_train, y_test, _, ag_test = train_test_split(
        X, y, age_group, test_size=0.25, random_state=SEED, stratify=y
    )

    preprocess = ColumnTransformer([
        ("num", StandardScaler(), FEATURES_NUM),
        ("cat", OneHotEncoder(handle_unknown="ignore"), FEATURES_CAT),
    ])
    preprocess.fit(X_train)
    Xtr = preprocess.transform(X_train)
    Xte = preprocess.transform(X_test)
    if hasattr(Xtr, "toarray"):
        Xtr = Xtr.toarray()
        Xte = Xte.toarray()

    row_norms = np.linalg.norm(Xtr, axis=1)
    data_norm = float(np.percentile(row_norms, 95))

    _state_cache.update({
        "Xtr": Xtr, "Xte": Xte, "y_train": y_train, "y_test": y_test,
        "ag_test": ag_test, "data_norm": data_norm,
    })
    return _state_cache


def _fairness_diffs(y_true, y_pred, group) -> tuple[float, float]:
    y_true = np.asarray(y_true)
    stats = {}
    for g in np.unique(group):
        mask = group == g
        pos_mask = mask & (y_true == 1)
        stats[g] = {
            "pr_pos": y_pred[mask].mean(),
            "tpr": y_pred[pos_mask].mean() if pos_mask.sum() > 0 else float("nan"),
        }
    groups = sorted(stats.keys())
    dp_diff = abs(stats[groups[0]]["pr_pos"] - stats[groups[1]]["pr_pos"])
    eo_diff = abs(stats[groups[0]]["tpr"] - stats[groups[1]]["tpr"])
    return float(dp_diff), float(eo_diff)


def get_baseline_metrics() -> dict:
    state = _prepare()
    if "baseline" in state:
        return state["baseline"]

    clf = LogisticRegression(max_iter=2000, random_state=SEED)
    clf.fit(state["Xtr"], state["y_train"].values)
    pred = clf.predict(state["Xte"])
    proba = clf.predict_proba(state["Xte"])[:, 1]
    dp_diff, eo_diff = _fairness_diffs(state["y_test"], pred, state["ag_test"])

    baseline = {
        "accuracy": float(accuracy_score(state["y_test"], pred)),
        "f1": float(f1_score(state["y_test"], pred)),
        "roc_auc": float(roc_auc_score(state["y_test"], proba)),
        "demographic_parity_diff": dp_diff,
        "equal_opportunity_diff": eo_diff,
    }
    state["baseline"] = baseline
    return baseline


def train_dp_model(epsilon: float) -> dict:
    state = _prepare()
    clf = DPLogisticRegression(epsilon=epsilon, data_norm=state["data_norm"],
                                max_iter=200, random_state=SEED)
    clf.fit(state["Xtr"], state["y_train"].values)
    pred = clf.predict(state["Xte"])
    proba = clf.predict_proba(state["Xte"])[:, 1]
    dp_diff, eo_diff = _fairness_diffs(state["y_test"], pred, state["ag_test"])

    try:
        auc = float(roc_auc_score(state["y_test"], proba))
    except ValueError:
        auc = None

    return {
        "epsilon": epsilon,
        "accuracy": float(accuracy_score(state["y_test"], pred)),
        "f1": float(f1_score(state["y_test"], pred)),
        "roc_auc": auc,
        "demographic_parity_diff": dp_diff,
        "equal_opportunity_diff": eo_diff,
    }
