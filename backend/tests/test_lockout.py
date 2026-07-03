import uuid
from datetime import datetime, timedelta
from app.models.usuario import Usuario
from app.security.lockout import is_locked_out, register_failed_attempt, reset_failed_attempts, MAX_ATTEMPTS

def make_user():
    return Usuario(
        usuario_id=uuid.uuid4(), username="u", nombre_completo="U",
        email_corporativo="u@bank.pe", password_hash="x", rol_id=1,
        failed_login_attempts=0, locked_until=None,
    )

def test_lockout_triggers_after_max_attempts():
    user = make_user()
    for _ in range(MAX_ATTEMPTS):
        register_failed_attempt(None, user)
    assert is_locked_out(user) is True

def test_reset_clears_lockout():
    user = make_user()
    user.failed_login_attempts = MAX_ATTEMPTS
    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
    reset_failed_attempts(None, user)
    assert is_locked_out(user) is False
    assert user.failed_login_attempts == 0
