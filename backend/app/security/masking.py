from app.models import Cliente
from app.security.crypto import decrypt_field

_DEMOGRAPHIC_FIELDS = [
    "age", "job", "marital", "education", "default_credit", "balance",
    "housing", "loan", "contact", "day", "month", "duration", "campaign",
    "pdays", "previous", "poutcome", "deposit",
]


def _demographic_dict(cliente: Cliente) -> dict:
    return {field: getattr(cliente, field) for field in _DEMOGRAPHIC_FIELDS}


def mask_cliente(cliente: Cliente, rol_nombre: str) -> dict:
    base = {"cliente_id": str(cliente.cliente_id), "deposit": cliente.deposit}

    if rol_nombre in ("administrador", "supervisor"):
        return {
            **base,
            "nombre": decrypt_field(cliente.nombre_cifrado),
            "dni": decrypt_field(cliente.dni_cifrado),
            "email": decrypt_field(cliente.email_cifrado),
            "telefono": decrypt_field(cliente.telefono_cifrado),
            "direccion": decrypt_field(cliente.direccion_cifrada),
            **_demographic_dict(cliente),
        }

    if rol_nombre == "analista":
        return {**base, **_demographic_dict(cliente)}

    if rol_nombre == "teleoperador":
        return {
            **base,
            "nombre": decrypt_field(cliente.nombre_cifrado),
            "telefono": decrypt_field(cliente.telefono_cifrado),
        }

    return base
