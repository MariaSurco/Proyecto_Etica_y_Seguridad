import jwt
from datetime import datetime, timedelta
from app.config import settings

def create_access_token(usuario_id: str, rol_nombre: str, permisos: list[str]) -> str:
    payload = {
        "sub": usuario_id,
        "rol": rol_nombre,
        "permisos": permisos,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
