from passlib.hash import argon2

_argon2 = argon2.using(memory_cost=65536, time_cost=3, parallelism=1)

def hash_password(raw_password: str) -> str:
    return _argon2.hash(raw_password)

def verify_password(raw_password: str, stored_hash: str) -> bool:
    try:
        return _argon2.verify(raw_password, stored_hash)
    except ValueError:
        return False

def validate_password_policy(raw_password: str) -> list[str]:
    errors = []
    if len(raw_password) < 12:
        errors.append("La contraseña debe tener al menos 12 caracteres.")
    common_passwords = {"password123456", "123456789012", "qwertyuiop12"}
    if raw_password.lower() in common_passwords:
        errors.append("La contraseña está en la lista de contraseñas comprometidas.")
    return errors
