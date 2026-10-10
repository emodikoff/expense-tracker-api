from app.models import User, Category
from app.security import create_access_token


def test_users_see_global_and_own_categories(client, db_session):
    alice = User(
        email='alice@example.com',
        hashed_password='test-hash1234',
    )

    bob = User(
        email='bob@example.com',
        hashed_password='test_hash4321',
    )

    db_session.add_all([alice, bob])
    db_session.flush()

    categories = [
        Category(
            name="Food",
            type="expense",
            user_id=None,
        ),
        Category(
            name="Supplements",
            type="expense",
            user_id=alice.id,
        ),
        Category(
            name="Muay Thai",
            type="expense",
            user_id=bob.id,
        ),
    ]

    db_session.add_all(categories)
    db_session.commit()

    alice_token = create_access_token(alice.id)
    bob_token = create_access_token(bob.id)

    alice_response = client.get(
        '/categories',
        headers={"Authorization": f"Bearer {alice_token}"},
    )

    bob_response = client.get(
        '/categories',
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    assert alice_response.status_code == 200
    assert bob_response.status_code == 200

    alice_categories = {
        category["name"] for category in alice_response.json()
    }

    bob_categories = {
        category["name"] for category in bob_response.json()
    }

    assert alice_categories == {"Food", "Supplements"}
    assert bob_categories == {"Food", "Muay Thai"}


def test_create_category_with_authenticated_user(client, db_session):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "test-hash1234"
        },
    )

    assert register_response.status_code == 201

    user_id = register_response.json()["id"]
    token = create_access_token(user_id)

    response = client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Muay Thai"
    assert data["type"] == "expense"

    db_category = db_session.get(Category, data["id"])

    assert db_category is not None
    assert db_category.user_id == user_id


def test_create_category_without_token(client):
    response = client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert response.status_code == 401


def test_create_duplicate_category(authenticated_client, db_session):
    category_data = {
        "name": "Muay Thai",
        "type": "expense",
    }

    first_response = authenticated_client.post(
        "/categories",
        json=category_data,
    )

    assert first_response.status_code == 201

    second_response = authenticated_client.post(
        "/categories",
        json=category_data,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Category already exists"

    categories = (
        db_session.query(Category)
        .filter(
            Category.name == "Muay Thai",
            Category.type == "expense",
        )
        .all()
    )

    assert len(categories) == 1


def test_different_users_can_create_same_category(client, db_session):
    alice = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "test-pass1234",
        },
    )

    bob = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "test_pass4321",
        },
    )

    assert alice.status_code == 201
    assert bob.status_code == 201

    alice_id = alice.json()["id"]
    bob_id = bob.json()["id"]

    alice_headers = {"Authorization": f"Bearer {create_access_token(alice_id)}"}
    bob_headers = {"Authorization": f"Bearer {create_access_token(bob_id)}"}

    category_data = {
        "name": "Muay Thai",
        "type": "expense",
    }

    alice_response = client.post(
        '/categories',
        json=category_data,
        headers=alice_headers,
    )

    bob_response = client.post(
        '/categories',
        json=category_data,
        headers=bob_headers,
    )

    assert alice_response.status_code == 201
    assert bob_response.status_code == 201

    assert alice_response.json()["id"] != bob_response.json()["id"]

    alice_category = db_session.get(
        Category,
        alice_response.json()["id"],
    )

    bob_category = db_session.get(
        Category,
        bob_response.json()["id"],
    )

    assert alice_category.user_id == alice_id
    assert bob_category.user_id == bob_id

    assert alice_category.name == bob_category.name


def test_category_names_are_case_insensitive(authenticated_client, db_session):
    first_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert first_response.status_code == 201

    second_response = authenticated_client.post(
        "/categories",
        json={
            "name": "muay thai",
            "type": "expense",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Category already exists"

    db_session.expire_all()

    categories = (
        db_session.query(Category)
        .filter(Category.type == "expense")
        .all()
    )

    assert len(categories) == 1
    assert categories[0].name == "Muay Thai"


def test_category_name_whitespace_normalization(authenticated_client):
    first_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert first_response.status_code == 201
    assert first_response.json()["name"] == "Muay Thai"

    duplicate_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert duplicate_response.status_code == 409

    invalid_response = authenticated_client.post(
        "/categories",
        json={
            "name": " ",
            "type": "expense",
        },
    )

    assert invalid_response.status_code == 422
