"""Genera app/dp/comparison_precomputed.json (curva epsilon vs utilidad).

Se ejecuta una vez de forma offline -- GET /api/dp/comparison sirve este
archivo directamente en vez de reentrenar el modelo en cada request.

Uso: python -m app.dp.precompute_comparison
"""
import json
import os

import numpy as np
from diffprivlib.models import LogisticRegression as DPLogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

from app.dp.model import SEED, _fairness_diffs, _prepare, get_baseline_metrics

N_REPS = 25
EPSILONS = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

OUT_PATH = os.path.join(os.path.dirname(__file__), "comparison_precomputed.json")


def main() -> None:
    state = _prepare()
    baseline = get_baseline_metrics()

    points = []
    for eps in EPSILONS:
        accs, f1s, aucs, dp_diffs, eo_diffs = [], [], [], [], []
        for rep in range(N_REPS):
            clf = DPLogisticRegression(epsilon=eps, data_norm=state["data_norm"],
                                        max_iter=200, random_state=SEED + rep)
            clf.fit(state["Xtr"], state["y_train"].values)
            pred = clf.predict(state["Xte"])
            proba = clf.predict_proba(state["Xte"])[:, 1]

            accs.append(accuracy_score(state["y_test"], pred))
            f1s.append(f1_score(state["y_test"], pred))
            try:
                aucs.append(roc_auc_score(state["y_test"], proba))
            except ValueError:
                pass
            dp_diff, eo_diff = _fairness_diffs(state["y_test"], pred, state["ag_test"])
            dp_diffs.append(dp_diff)
            eo_diffs.append(eo_diff)

        points.append({
            "epsilon": eps,
            "accuracy": float(np.mean(accs)),
            "f1": float(np.mean(f1s)),
            "roc_auc": float(np.mean(aucs)) if aucs else None,
            "demographic_parity_diff": float(np.mean(dp_diffs)),
            "equal_opportunity_diff": float(np.mean(eo_diffs)),
        })
        print(f"epsilon={eps}: f1={points[-1]['f1']:.4f}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"baseline": baseline, "points": points}, f, indent=2)
    print("Escrito", OUT_PATH)


if __name__ == "__main__":
    main()
