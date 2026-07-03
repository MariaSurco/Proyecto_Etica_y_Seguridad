import pandas as pd
from app.seed.generate_synthetic import generate_clientes, generate_consentimientos

def test_generate_clientes_matches_row_count_and_has_required_fields():
    df = pd.DataFrame({
        "age": [59, 56], "job": ["admin.", "admin."], "marital": ["married", "married"],
        "education": ["secondary", "secondary"], "default": ["no", "no"],
        "balance": [2343, 45], "housing": ["yes", "no"], "loan": ["no", "no"],
        "contact": ["unknown", "unknown"], "day": [5, 5], "month": ["may", "may"],
        "duration": [1042, 1467], "campaign": [1, 1], "pdays": [-1, -1],
        "previous": [0, 0], "poutcome": ["unknown", "unknown"], "deposit": ["yes", "yes"],
    })
    clientes = generate_clientes(df)
    assert len(clientes) == 2
    for c in clientes:
        for field in ("cliente_id", "nombre", "dni", "email", "telefono", "direccion", "age", "deposit"):
            assert field in c

def test_generate_consentimientos_uses_expected_states():
    ids = [f"id-{i}" for i in range(1000)]
    consentimientos = generate_consentimientos(ids)
    estados = {c["estado"] for c in consentimientos}
    assert estados <= {"opt-in", "opt-out", "no informado"}
    opt_in_share = sum(1 for c in consentimientos if c["estado"] == "opt-in") / len(consentimientos)
    assert 0.55 < opt_in_share < 0.85  # ~70% with sampling noise
