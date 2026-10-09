from app.models import User
from app.security import verify_password


def test_register_user(client, db_session):
    payload = {
        "email": "test@example.com",
        "password": "MySecurePassword1234",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == payload["email"]
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data

    db_user = db_session.query(User).filter(User.email == payload["email"]).first()

    assert db_user is not None
    assert db_user.hashed_password != payload["password"]
    assert verify_password(payload["password"], db_user.hashed_password)


def test_register_user_with_existing_email(client):
    payload = {
        "email": "test@example.com",
        "password": "MySecurePassword1234",
    }

    first_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201

    second_response = client.post("/auth/register", json=payload)

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already registered"


def test_register_user_with_invalid_email(client):
    payload = {
        "email": "not-an-email",
        "password": "MySecurePassword123!",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_user_with_short_password(client):
    payload = {
        "email": "test@example.com",
        "password": "short",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
