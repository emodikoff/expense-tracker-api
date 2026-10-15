import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

from pwdlib import PasswordHash

load_dotenv()
password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY not set")

if ALGORITHM != "HS256":
    raise RuntimeError("Only HS256 algorithm is supported")

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be positive")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
