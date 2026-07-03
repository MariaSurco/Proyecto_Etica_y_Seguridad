from app.database import Base, engine
from sqlalchemy import inspect

def test_all_expected_tables_are_registered():
    import app.models  # noqa
    tables = set(Base.metadata.tables.keys())
    expected = {
        "rol", "permiso", "rol_permiso", "usuario", "cliente",
        "consentimiento", "campania", "asignacion",
        "resultado_contacto", "audit_log",
    }
    assert expected.issubset(tables)
