from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from app.security.jwt import decode_access_token
from app.audit.logger import write_audit_log

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return decode_access_token(token)
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o expiradas")

def require_permission(permiso_nombre: str):
    def dependency(request: Request, user: dict = Depends(get_current_user)) -> dict:
        if permiso_nombre not in user.get("permisos", []):
            write_audit_log(
                usuario_id=user.get("sub"), accion="acceso_denegado",
                recurso=permiso_nombre, recurso_id=None,
                ip_origen=request.client.host if request.client else None,
                resultado="denegado", detalle=f"Falta permiso {permiso_nombre}",
            )
            raise HTTPException(status_code=403, detail="No autorizado para este recurso")
        return user
    return dependency
