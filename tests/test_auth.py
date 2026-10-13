from decimal import Decimal

import jwt

from datetime import datetime, timedelta, timezone

from app.models import User, Transaction
from app.security import verify_password, SECRET_KEY, ALGORITHM, create_access_token


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


def test_get_current_user_success(client):
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

    access_token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200

    user_data = me_response.json()

    assert user_data["id"] == register_response.json()["id"]
    assert user_data["email"] == registration_data["email"]

    assert "password" not in user_data
    assert "hashed_password" not in user_data


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_current_user_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer this.is.not.valid",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_current_user_with_expired_token(client):
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    token = jwt.encode(
        {
            "sub": "5",
            "exp": expired_at,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_current_user_with_nonexistent_user(client):
    token = create_access_token(user_id=999999)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_current_user_with_invalid_subject(client):
    token = jwt.encode(
        {
            "sub": "not-a-user-id",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_create_transaction_with_authenticated_user(client, db_session):
    registration_data = {
        "email": "owner@example.com",
        "password": "MySecurePassword123!",
    }

    register_response = client.post(
        "/auth/register",
        json=registration_data,
    )
    assert register_response.status_code == 201

    user_id = register_response.json()["id"]

    login_response = client.post(
        "/auth/login",
        data={
            "username": registration_data["email"],
            "password": registration_data["password"],
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    transaction_data = {
        "amount": 50.00,
        "category": "Food",
        "description": "Lunch",
        "type": "expense",
    }

    response = client.post(
        "/transactions",
        json=transaction_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    transaction_id = response.json()["id"]

    db_transaction = db_session.get(Transaction, transaction_id)

    assert db_transaction is not None
    assert db_transaction.user_id == user_id


def test_create_transaction_without_token(client):
    transaction_data = {
        "amount": 50.00,
        "category": "Food",
        "description": "Lunch",
        "type": "expense",
    }

    response = client.post(
        "/transactions",
        json=transaction_data,
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_cannot_override_transaction_owner(client, db_session):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "owner@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert register_response.status_code == 201
    real_user_id = register_response.json()["id"]

    token = create_access_token(real_user_id)

    response = client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Lunch",
            "type": "expense",
            "user_id": 999,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    transaction_id = response.json()["id"]
    db_transaction = db_session.get(Transaction, transaction_id)

    assert db_transaction is not None
    assert db_transaction.user_id == real_user_id
    assert db_transaction.user_id != 999


def test_users_can_only_see_their_own_transactions(client):
    alice = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "MySecurePassword123!",
        },
    )
    assert alice.status_code == 201

    bob = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "MySecurePassword123!",
        },
    )
    assert bob.status_code == 201

    alice_token = create_access_token(alice.json()["id"])
    bob_token = create_access_token(bob.json()["id"])

    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    alice_transaction = client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Alice lunch",
            "type": "expense",
        },
        headers=alice_headers,
    )
    assert alice_transaction.status_code == 200

    bob_transaction = client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "Transport",
            "description": "Bob taxi",
            "type": "expense",
        },
        headers=bob_headers,
    )
    assert bob_transaction.status_code == 200

    alice_response = client.get(
        "/transactions",
        headers=alice_headers,
    )

    bob_response = client.get(
        "/transactions",
        headers=bob_headers,
    )

    assert alice_response.status_code == 200
    assert bob_response.status_code == 200

    alice_transactions = alice_response.json()
    bob_transactions = bob_response.json()

    assert len(alice_transactions) == 1
    assert len(bob_transactions) == 1

    assert alice_transactions[0]["id"] == alice_transaction.json()["id"]
    assert bob_transactions[0]["id"] == bob_transaction.json()["id"]

    assert alice_transactions[0]["description"] == "Alice lunch"
    assert bob_transactions[0]["description"] == "Bob taxi"


def test_user_cannot_read_another_users_transaction(client):
    alice = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "MySecurePassword123!",
        },
    )

    bob = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert alice.status_code == 201
    assert bob.status_code == 201

    alice_token = create_access_token(alice.json()["id"])
    bob_token = create_access_token(bob.json()["id"])

    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    transaction_response = client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Alice lunch",
            "type": "expense",
        },
        headers=alice_headers,
    )

    assert transaction_response.status_code == 200

    transaction_id = transaction_response.json()["id"]

    alice_response = client.get(
        f"/transactions/{transaction_id}",
        headers=alice_headers,
    )

    bob_response = client.get(
        f"/transactions/{transaction_id}",
        headers=bob_headers,
    )

    assert alice_response.status_code == 200
    assert bob_response.status_code == 404
    assert bob_response.json()["detail"] == "Transaction not found"


def test_user_cannot_update_another_users_transaction(client, db_session):
    alice = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "MySecurePassword123!",
        },
    )

    bob = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert alice.status_code == 201
    assert bob.status_code == 201

    alice_token = create_access_token(alice.json()["id"])
    bob_token = create_access_token(bob.json()["id"])

    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    transaction_response = client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Alice lunch",
            "type": "expense",
        },
        headers=alice_headers,
    )

    assert transaction_response.status_code == 200

    transaction_id = transaction_response.json()["id"]

    update_response = client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 9999,
            "category": "Shopping",
            "description": "Hacked transaction",
            "type": "expense",
        },
        headers=bob_headers,
    )

    assert update_response.status_code == 404
    assert update_response.json()["detail"] == "Transaction not found"

    db_session.expire_all()
    db_transaction = db_session.get(Transaction, transaction_id)

    assert db_transaction is not None
    assert float(db_transaction.amount) == 50.0
    assert db_transaction.category == "Food"
    assert db_transaction.description == "Alice lunch"
    assert db_transaction.user_id == alice.json()["id"]


def test_user_cannot_delete_another_users_transaction(client, db_session):
    alice = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "MySecurePassword123!",
        },
    )

    bob = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert alice.status_code == 201
    assert bob.status_code == 201

    alice_token = create_access_token(alice.json()["id"])
    bob_token = create_access_token(bob.json()["id"])

    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    create_response = client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Alice lunch",
            "type": "expense",
        },
        headers=alice_headers,
    )

    assert create_response.status_code == 200

    transaction_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/transactions/{transaction_id}",
        headers=bob_headers,
    )

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Transaction not found"

    db_session.expire_all()
    db_transaction = db_session.get(Transaction, transaction_id)

    assert db_transaction is not None
    assert db_transaction.user_id == alice.json()["id"]
    assert db_transaction.description == "Alice lunch"


def test_users_have_separate_transaction_summaries(client):
    alice = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "MySecurePassword123!",
        },
    )

    bob = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert alice.status_code == 201
    assert bob.status_code == 201

    alice_token = create_access_token(alice.json()["id"])
    bob_token = create_access_token(bob.json()["id"])

    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    transactions = [
        (alice_headers, 5000, "income"),
        (alice_headers, 2000, "expense"),
        (bob_headers, 10000, "income"),
        (bob_headers, 4000, "expense"),
    ]

    for headers, amount, transaction_type in transactions:
        response = client.post(
            "/transactions",
            json={
                "amount": amount,
                "category": "Test",
                "description": "Summary isolation test",
                "type": transaction_type,
            },
            headers=headers,
        )

        assert response.status_code == 200

    alice_summary = client.get(
        "/transactions/summary",
        headers=alice_headers,
    )

    bob_summary = client.get(
        "/transactions/summary",
        headers=bob_headers,
    )

    assert alice_summary.status_code == 200
    assert bob_summary.status_code == 200

    alice_data = alice_summary.json()

    assert Decimal(alice_data["total_income"]) == Decimal("5000.00")
    assert Decimal(alice_data["total_expenses"]) == Decimal("2000.00")
    assert Decimal(alice_data["balance"]) == Decimal("3000.00")

    bob_data = bob_summary.json()

    assert Decimal(bob_data["total_income"]) == Decimal("10000.00")
    assert Decimal(bob_data["total_expenses"]) == Decimal("4000.00")
    assert Decimal(bob_data["balance"]) == Decimal("6000.00")


def test_get_current_user_with_missing_exp(client):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "noexp@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert register_response.status_code == 201

    user_id = register_response.json()["id"]

    token = jwt.encode(
        {"sub": str(user_id)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
