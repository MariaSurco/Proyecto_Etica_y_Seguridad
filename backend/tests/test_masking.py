import uuid
from app.models import Cliente
from app.security.crypto import encrypt_field
from app.security.masking import mask_cliente


def _cliente():
    return Cliente(
        cliente_id=uuid.uuid4(),
        nombre_cifrado=encrypt_field("Juan Perez"),
        dni_cifrado=encrypt_field("12345678"),
        email_cifrado=encrypt_field("juan@example.com"),
        telefono_cifrado=encrypt_field("+51999999999"),
        direccion_cifrada=encrypt_field("Av. Siempre Viva 123"),
        age=41, job="management", marital="married", education="tertiary",
        default_credit="no", balance=1200.50, housing="yes", loan="no",
        contact="cellular", day=5, month="may", duration=120, campaign=1,
        pdays=-1, previous=0, poutcome="unknown", deposit="yes",
    )


def test_admin_sees_full_pii():
    out = mask_cliente(_cliente(), "administrador")
    assert out["nombre"] == "Juan Perez"
    assert out["dni"] == "12345678"
    assert out["balance"] == 1200.50


def test_analista_sees_no_pii():
    out = mask_cliente(_cliente(), "analista")
    assert "nombre" not in out
    assert "dni" not in out
    assert "email" not in out
    assert out["job"] == "management"
    assert out["balance"] == 1200.50


def test_teleoperador_sees_only_contact_fields():
    out = mask_cliente(_cliente(), "teleoperador")
    assert out["nombre"] == "Juan Perez"
    assert out["telefono"] == "+51999999999"
    assert "dni" not in out
    assert "balance" not in out
    assert "email" not in out
