import jwt
from app.models import User
from app.security import verify_password, SECRET_KEY, ALGORITHM


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


def test_login_user_success(client):
    registration_data = {
        "email": "test@example.com",
        "password": "MySecurePassword123!",
    }

    register_response = client.post(
        "/auth/register",
        json=registration_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": registration_data["email"],
            "password": registration_data["password"],
        },
    )

    assert login_response.status_code == 200

    token_data = login_response.json()

    assert token_data["token_type"] == "bearer"
    assert "access_token" in token_data

    decoded_token = jwt.decode(
        token_data["access_token"],
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    assert decoded_token["sub"] == str(register_response.json()["id"])


def test_login_user_with_wrong_password(client):
    registration_data = {
        "email": "test@example.com",
        "password": "MySecurePassword123!",
    }

    response = client.post(
        "/auth/register",
        json=registration_data,
    )

    assert response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": registration_data["email"],
            "password": "WrongPassword123!",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password"


def test_login_user_with_nonexistent_email(client):
    login_response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password"
