from app.security import hash_password, verify_password
import pytest
import jwt
from app.security import create_access_token, SECRET_KEY, ALGORITHM
from datetime import datetime, timedelta, timezone


def test_hashed_password():
    password = "MySecurePassword1234"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2id$")


def test_verify_password():
    password = "MySecurePassword1234"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_hash_password_uses_random_salt():
    password = "MySecurePassword1234"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash

    assert verify_password(password, first_hash) is True
    assert verify_password(password, second_hash) is True


def test_create_access_token():
    token = create_access_token(user_id=5)

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    assert payload["sub"] == "5"
    assert "exp" in payload


def test_access_token_with_invalid_signature():
    token = create_access_token(user_id=5)

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            token,
            "completely-different-secret-key-for-testing-only",
            algorithms=[ALGORITHM],
        )


def test_expired_access_token():
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    token = jwt.encode(
        {
            "sub": "5",
            "exp": expired_at,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
