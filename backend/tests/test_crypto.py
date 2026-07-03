from app.security.crypto import encrypt_field, decrypt_field


def test_encrypt_decrypt_roundtrip():
    plaintext = "Juan Pérez - DNI 12345678"
    token = encrypt_field(plaintext)
    assert token != plaintext
    assert decrypt_field(token) == plaintext


def test_ciphertext_is_nondeterministic():
    token_a = encrypt_field("same value")
    token_b = encrypt_field("same value")
    assert token_a != token_b  # random nonce per call
