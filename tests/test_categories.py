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


def test_update_own_category(authenticated_client, db_session):
    create_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    original_category = db_session.get(Category, category_id)
    original_user_id = original_category.user_id

    update_response = authenticated_client.put(
        f"/categories/{category_id}",
        json={
            "name": "Martial Arts",
            "type": "expense",
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["id"] == category_id
    assert data["name"] == "Martial Arts"
    assert data["type"] == "expense"

    db_session.expire_all()

    update_category = db_session.get(Category, category_id)

    assert update_category is not None
    assert update_category.name == "Martial Arts"
    assert update_category.user_id == original_user_id


def test_cannot_update_another_user_category(client, db_session, authenticated_client):
    # Alice ceates a category
    create_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    # Bob registers
    register_response = authenticated_client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "SecurePassword123!",
        },
    )

    assert register_response.status_code == 201

    # Bob logs in
    login_response = authenticated_client.post(
        "/auth/login",
        data={
            "username": "bob@example.com",
            "password": "SecurePassword123!",
        },
    )

    assert login_response.status_code == 200

    bob_token = login_response.json()["access_token"]

    # Bob attempts to update Alice's category
    update_response = authenticated_client.put(
        f"/categories/{category_id}",
        headers={"Authorization": f"Bearer {bob_token}"
                 },
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert update_response.status_code == 404
    assert update_response.json()["detail"] == "Category not found"

    # Verify Alice's category was not modified
    db_session.expire_all()

    category = db_session.get(Category, category_id)

    assert category is not None
    assert category.name == "Muay Thai"


def test_cannot_update_global_category(authenticated_client, db_session):
    global_category = Category(
        name="Global food",
        type="expense",
        user_id=None
    )

    db_session.add(global_category)
    db_session.commit()
    db_session.refresh(global_category)

    category_id = global_category.id

    response = authenticated_client.put(
        f"/categories/{category_id}",
        json={
            "name": "Modified food",
            "type": "income",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"

    db_session.expire_all()

    category = db_session.get(Category, category_id)

    assert category is not None
    assert category.name == "Global food"
    assert category.type == "expense"
    assert category.user_id is None


def test_update_category_duplicate_name(authenticated_client, db_session):
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
            "name": "Gym",
            "type": "expense",
        },
    )

    assert second_response.status_code == 201

    gym_category_id = second_response.json()["id"]

    update_response = authenticated_client.put(
        f"/categories/{gym_category_id}",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert update_response.status_code == 409
    assert update_response.json()["detail"] == "Category already exists"

    db_session.expire_all()

    gym_category = db_session.get(Category, gym_category_id)

    assert gym_category is not None
    assert gym_category.name == "Gym"
    assert gym_category.type == "expense"


def test_update_category_without_authentication(client):
    response = client.put(
        "/categories/999999999",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert response.status_code == 401


def test_delete_own_category(authenticated_client, db_session):
    create_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    delete_response = authenticated_client.delete(f"/categories/{category_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    db_session.expire_all()

    deleted_category = db_session.get(Category, category_id)

    assert deleted_category is None


def test_delete_category_twice(authenticated_client):
    create_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    first_delete = authenticated_client.delete(f"/categories/{category_id}")
    assert first_delete.status_code == 204

    second_delete = authenticated_client.delete(f"/categories/{category_id}")
    assert second_delete.status_code == 404
    assert second_delete.json()["detail"] == "Category not found"


def test_cannot_delete_another_users_category(client, authenticated_client, db_session):
    # Alice creates category
    create_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert create_response.status_code == 201
    category_id = create_response.json()["id"]

    # Bob registers
    register_response = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert register_response.status_code == 201

    # Bob logs in
    login_response = client.post(
        "/auth/login",
        data={
            "username": "bob@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert login_response.status_code == 200
    bob_token = login_response.json()["access_token"]

    # Bob attempts to delete Alice category
    delete_response = client.delete(
        f"/categories/{category_id}",
        headers={"Authorization": f"Bearer {bob_token}"}
    )

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Category not found"

    db_session.expire_all()

    category = db_session.get(Category, category_id)

    assert category is not None
    assert category.name == "Muay Thai"


def test_cannot_delete_global_category(authenticated_client, db_session):
    global_category = Category(
        name="Global food",
        type="expense",
        user_id=None,
    )

    db_session.add(global_category)
    db_session.commit()
    db_session.refresh(global_category)

    category_id = global_category.id

    delete_response = authenticated_client.delete(f"/categories/{category_id}")

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Category not found"

    db_session.expire_all()

    category = db_session.get(Category, category_id)

    assert category is not None
    assert category.name == "Global food"
    assert category.user_id is None


def test_delete_category_without_authorization(client):
    response = client.delete("/categories/999999999")

    assert response.status_code == 401


def test_get_categories(authenticated_client):
    response = authenticated_client.get("/categories")

    assert response.status_code == 200
    assert response.json() == []


def test_get_system_categories(authenticated_client, db_session):
    categories = [
        Category(name='Food', type='expense', user_id=None),
        Category(name='Salary', type='income', user_id=None),
    ]

    db_session.add_all(categories)
    db_session.commit()

    response = authenticated_client.get("/categories")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert [category["name"] for category in data] == ["Food", "Salary"]


def test_get_categories_filtered_by_type(authenticated_client, db_session):
    categories = [
        Category(name='Food', type='expense', user_id=None),
        Category(name='Transport', type='expense', user_id=None),
        Category(name='Salary', type='income', user_id=None),
    ]

    db_session.add_all(categories)
    db_session.commit()

    expense_response = authenticated_client.get("/categories?type=expense")

    assert expense_response.status_code == 200
    expense_data = expense_response.json()

    assert len(expense_data) == 2
    assert [category["name"] for category in expense_data] == ["Food", "Transport"]

    income_response = authenticated_client.get("/categories?type=income")

    assert income_response.status_code == 200
    income_data = income_response.json()

    assert len(income_data) == 1
    assert income_data[0]["name"] == "Salary"


def test_get_categories_excludes_user_categories(authenticated_client, db_session):
    user = User(
        email="test@exapmle.com",
        hashed_password="dummy_hash",
    )

    db_session.add(user)
    db_session.flush()

    categories = [
        Category(name='Food', type='expense', user_id=None),
        Category(name='Gaming', type='expense', user_id=user.id),
    ]

    db_session.add_all(categories)
    db_session.commit()

    response = authenticated_client.get("/categories")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Food"
