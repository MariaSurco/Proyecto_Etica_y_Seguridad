from datetime import datetime, timedelta

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

def is_locked_out(usuario) -> bool:
    if usuario.locked_until is None:
        return False
    return datetime.utcnow() < usuario.locked_until

def register_failed_attempt(db, usuario) -> None:
    usuario.failed_login_attempts = (usuario.failed_login_attempts or 0) + 1
    if usuario.failed_login_attempts >= MAX_ATTEMPTS:
        usuario.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
    if db is not None:
        db.add(usuario)
        db.commit()

def reset_failed_attempts(db, usuario) -> None:
    usuario.failed_login_attempts = 0
    usuario.locked_until = None
    if db is not None:
        db.add(usuario)
        db.commit()
