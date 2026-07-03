from app.security.hashing import hash_password, verify_password, validate_password_policy

def test_hash_and_verify_roundtrip():
    h = hash_password("Sup3rSecret!Pass")
    assert h != "Sup3rSecret!Pass"
    assert verify_password("Sup3rSecret!Pass", h) is True
    assert verify_password("wrong-password", h) is False

def test_password_policy_rejects_short_passwords():
    errors = validate_password_policy("short1!")
    assert any("12" in e for e in errors)

def test_password_policy_accepts_valid_password():
    errors = validate_password_policy("Sup3rSecret!Pass")
    assert errors == []
