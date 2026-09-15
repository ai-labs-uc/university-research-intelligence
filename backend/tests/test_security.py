import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)


def test_password_hash_rejects_wrong_password():
    hashed = hash_password("correct horse battery staple")
    assert not verify_password("wrong password", hashed)


def test_verify_password_handles_missing_hash():
    # A Google-only account has no password_hash — must fail closed,
    # not raise, so a password-login attempt on it is just "wrong
    # password" rather than a 500.
    assert not verify_password("anything", None)
    assert not verify_password("anything", "")


def test_access_token_roundtrip():
    token = create_access_token(user_id=42, email="researcher@uc-bcf.edu.ph")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["email"] == "researcher@uc-bcf.edu.ph"


def test_decode_access_token_rejects_garbage():
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        decode_access_token("not.a.valid.token")


def test_decode_access_token_rejects_wrong_signature():
    from fastapi import HTTPException

    # Signed with a different key than the app's configured secret_key
    # — must be rejected, not silently trusted.
    forged = jwt.encode(
        {"sub": "1", "email": "attacker@example.com"},
        "a-completely-different-secret",
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(HTTPException):
        decode_access_token(forged)
