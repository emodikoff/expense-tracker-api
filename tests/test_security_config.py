import os
import subprocess
import sys
import pytest


@pytest.mark.parametrize(
    "algorithm, expiration",
    [
        ("none", "30"),
        ("HS512", "30"),
        ("HS256", "0"),
        ("HS256", "-10"),
    ]
)
def test_invalid_jwt_configurator(algorithm, expiration):
    env = os.environ.copy()

    env["JWT_SECRET_KEY"] = "test_only_secret_key"
    env["JWT_ALGORITHM"] = algorithm
    env["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = expiration
    env["PYTHON_DOTENV_DISABLED"] = "1"

    result = subprocess.run(
        [sys.executable, "-c", "import app.security"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode != 0
    assert "RuntimeError" in result.stderr


def test_missing_jwt_secret():
    env = os.environ.copy()

    env.pop("JWT_SECRET_KEY", None)
    env["JWT_ALGORITHM"] = "HS256"
    env["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    env["PYTHON_DOTENV_DISABLED"] = "1"

    result = subprocess.run(
        [sys.executable, "-c", "import app.security"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode != 0
    assert "JWT_SECRET_KEY not set" in result.stderr


def test_invalid_expiration_format():
    env = os.environ.copy()

    env["JWT_SECRET_KEY"] = "test_only_secret_key"
    env["JWT_ALGORITHM"] = "HS256"
    env["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "invalid"
    env["PYTHON_DOTENV_DISABLED"] = "1"

    result = subprocess.run(
        [sys.executable, "-c", "import app.security"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode != 0
    assert "ValueError" in result.stderr


def test_valid_jwt_configuration():
    env = os.environ.copy()

    env["JWT_SECRET_KEY"] = "test_only_secret_key"
    env["JWT_ALGORITHM"] = "HS256"
    env["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    env["PYTHON_DOTENV_DISABLED"] = "1"

    result = subprocess.run(
        [sys.executable, "-c", "import app.security"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0
