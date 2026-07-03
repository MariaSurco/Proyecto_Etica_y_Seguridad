import uuid
import random
import pandas as pd
from faker import Faker

# NOTE: Faker has no "es_PE" (Peru) locale in the installed version (40.28.1);
# "es_PE" is not a valid Faker locale in any released version. Using "es_ES" as
# the closest available Spanish-language locale to satisfy the spirit of the
# plan's constraint (Spanish-language synthetic PII) without crashing at import.
fake = Faker("es_ES")
Faker.seed(42)
random.seed(42)

BASE_COLUMNS = [
    "age", "job", "marital", "education", "default", "balance", "housing",
    "loan", "contact", "day", "month", "duration", "campaign", "pdays",
    "previous", "poutcome", "deposit",
]


def generate_clientes(df_base: pd.DataFrame) -> list[dict]:
    n = len(df_base)
    records = []
    for i in range(n):
        row = df_base.iloc[i]
        record = {
            "cliente_id": str(uuid.uuid4()),
            "nombre": fake.name(),
            "dni": fake.unique.bothify("########"),
            "email": fake.unique.email(),
            "telefono": fake.phone_number(),
            "direccion": fake.address(),
        }
        for col in BASE_COLUMNS:
            value = row[col]
            if hasattr(value, "item"):
                value = value.item()
            record[col] = value
        records.append(record)
    return records


def generate_consentimientos(cliente_ids: list[str]) -> list[dict]:
    estados_pool = (["opt-in"] * 70) + (["no informado"] * 20) + (["opt-out"] * 10)
    canales = ["email", "sms", "llamada", "formulario_web"]
    consentimientos = []
    for cid in cliente_ids:
        estado = random.choice(estados_pool)
        consentimientos.append({
            "consentimiento_id": str(uuid.uuid4()),
            "cliente_id": cid,
            "estado": estado,
            "canal": random.choice(canales),
        })
    return consentimientos


def generate_roles_and_permisos():
    roles = [
        {"nombre": "administrador", "descripcion": "Gestiona usuarios, roles y auditoría."},
        {"nombre": "supervisor", "descripcion": "Supervisa campañas y asigna teleoperadores."},
        {"nombre": "analista", "descripcion": "Consulta clientes priorizados por campaña."},
        {"nombre": "teleoperador", "descripcion": "Contacta clientes asignados."},
    ]
    permisos = [
        {"nombre": "clientes:ver_sensible", "recurso": "clientes", "accion": "ver_sensible"},
        {"nombre": "clientes:ver_parcial", "recurso": "clientes", "accion": "ver_parcial"},
        {"nombre": "clientes:ver_asignados", "recurso": "clientes", "accion": "ver_asignados"},
        {"nombre": "clientes:exportar", "recurso": "clientes", "accion": "exportar"},
        {"nombre": "campanias:crear_editar", "recurso": "campanias", "accion": "crear_editar"},
        {"nombre": "campanias:consultar", "recurso": "campanias", "accion": "consultar"},
        {"nombre": "campanias:consultar_asignadas", "recurso": "campanias", "accion": "consultar_asignadas"},
        {"nombre": "resultados:registrar", "recurso": "resultados", "accion": "registrar"},
        {"nombre": "usuarios:gestionar", "recurso": "usuarios", "accion": "gestionar"},
        {"nombre": "auditoria:consultar", "recurso": "auditoria", "accion": "consultar"},
    ]
    matrix = {
        "administrador": ["clientes:ver_sensible", "clientes:exportar", "campanias:crear_editar",
                           "campanias:consultar", "usuarios:gestionar", "auditoria:consultar"],
        "supervisor": ["clientes:ver_sensible", "clientes:exportar", "campanias:crear_editar",
                       "campanias:consultar", "auditoria:consultar"],
        "analista": ["clientes:ver_parcial", "campanias:consultar"],
        "teleoperador": ["clientes:ver_asignados", "campanias:consultar_asignadas", "resultados:registrar"],
    }
    rol_permiso = [{"rol_nombre": rol, "permiso_nombre": p} for rol, perms in matrix.items() for p in perms]
    return roles, permisos, rol_permiso


def generate_usuarios_internos(n_per_role: dict[str, int]) -> list[dict]:
    usuarios = []
    for rol_nombre, n in n_per_role.items():
        for _ in range(n):
            full_name = fake.name()
            username = full_name.lower().replace(" ", ".")
            usuarios.append({
                "usuario_id": str(uuid.uuid4()),
                "username": username,
                "nombre_completo": full_name,
                "email_corporativo": f"{username}@bancoproyecto.pe",
                "rol_nombre": rol_nombre,
            })
    return usuarios
