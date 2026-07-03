from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Usuario, RolPermiso, Permiso
from app.security.hashing import verify_password
from app.security.jwt import create_access_token
from app.security.lockout import is_locked_out, register_failed_attempt, reset_failed_attempts
from app.audit.logger import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    usuario = db.query(Usuario).filter(Usuario.username == form.username).first()
    if usuario is None or not usuario.activo:
        write_audit_log(usuario_id=None, accion="login_fallido", recurso="auth",
                         recurso_id=form.username, ip_origen=ip, resultado="fallo",
                         detalle="usuario inexistente o inactivo")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if is_locked_out(usuario):
        write_audit_log(usuario_id=str(usuario.usuario_id), accion="login_bloqueado", recurso="auth",
                         recurso_id=form.username, ip_origen=ip, resultado="fallo",
                         detalle="cuenta bloqueada temporalmente")
        raise HTTPException(status_code=401, detail="Cuenta bloqueada temporalmente")
    if not verify_password(form.password, usuario.password_hash):
        register_failed_attempt(db, usuario)
        write_audit_log(usuario_id=str(usuario.usuario_id), accion="login_fallido", recurso="auth",
                         recurso_id=form.username, ip_origen=ip, resultado="fallo",
                         detalle="password incorrecto")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    reset_failed_attempts(db, usuario)
    permisos = (
        db.query(Permiso.nombre)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.permiso_id)
        .filter(RolPermiso.rol_id == usuario.rol_id)
        .all()
    )
    permisos_list = [p[0] for p in permisos]
    rol_nombre = usuario.rol.nombre if usuario.rol else ""
    token = create_access_token(str(usuario.usuario_id), rol_nombre, permisos_list)
    write_audit_log(usuario_id=str(usuario.usuario_id), accion="login_exitoso", recurso="auth",
                     recurso_id=form.username, ip_origen=ip, resultado="exito", detalle=None)
    return {"access_token": token, "token_type": "bearer"}
