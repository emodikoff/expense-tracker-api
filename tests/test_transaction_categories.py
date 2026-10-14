from app.models import Category, Transaction


def test_create_transaction_with_own_category(authenticated_client, db_session):
    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    transaction_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 120.50,
            "category": "Muay Thai",
            "category_id": category_id,
            "description": "Monthly training fee",
            "type": "expense",
        },
    )

    assert transaction_response.status_code == 200
    transaction_id = transaction_response.json()["id"]

    db_session.expire_all()
    db_transaction = db_session.get(Transaction, transaction_id)

    assert db_transaction is not None
    assert db_transaction.category_id == category_id
    assert db_transaction.category == "Muay Thai"


def test_create_transaction_with_global_category(authenticated_client, db_session):
    global_category = Category(
        name="Global food",
        type="expense",
        user_id=None,
    )

    db_session.add(global_category)
    db_session.commit()
    db_session.refresh(global_category)

    category_id = global_category.id

    response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 75.50,
            "category": "Global food",
            "category_id": category_id,
            "description": "Weekly groceries",
            "type": "expense",
        },
    )

    assert response.status_code == 200
    transaction_id = response.json()["id"]

    db_session.expire_all()

    transaction = db_session.get(Transaction, transaction_id)

    assert transaction is not None
    assert transaction.category_id == category_id
    assert transaction.category == "Global food"


def test_cannot_create_transaction_with_another_users_category(client, authenticated_client, db_session):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": "bob@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert login_response.status_code == 200

    bob_token = login_response.json()["access_token"]

    category_response = client.post(
        "/categories",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={
            "name": "Private gym",
            "type": "expense",
        }
    )

    assert category_response.status_code == 201
    bob_category_id = category_response.json()["id"]

    transaction_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "Private gym",
            "category_id": bob_category_id,
            "description": "Monthly membership",
            "type": "expense",
        },
    )

    assert transaction_response.status_code == 404
    assert transaction_response.json()["detail"] == "Category not found"


def test_create_transactions_with_nonexistent_category(authenticated_client, db_session):
    count_before = db_session.query(Transaction).count()

    response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "Global food",
            "category_id": 999999,
            "description": "Weekly groceries",
            "type": "expense",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"

    db_session.expire_all()

    count_after = db_session.query(Transaction).count()

    assert count_before == count_after


def test_create_transaction_with_mismatched_category_type(authenticated_client, db_session):
    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Salary",
            "type": "income",
        },
    )

    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    count_before = db_session.query(Transaction).count()

    transaction_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 150,
            "category": "Salary",
            "category_id": category_id,
            "description": "Invalid expense",
            "type": "expense",
        },
    )

    assert transaction_response.status_code == 422
    assert transaction_response.json()["detail"] == "Category type does not match transaction type"

    db_session.expire_all()

    count_after = db_session.query(Transaction).count()

    assert count_before == count_after


def test_transaction_category_name_comes_from_database(authenticated_client, db_session):
    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    transaction_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 120,
            "category": "Wrong category",
            "category_id": category_id,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert transaction_response.status_code == 200

    data = transaction_response.json()

    assert data["category"] == "Muay Thai"

    db_session.expire_all()

    db_transaction = db_session.get(Transaction, data["id"])

    assert db_transaction is not None
    assert db_transaction.category == "Muay Thai"
    assert db_transaction.category_id == category_id


def test_deleting_category_preserves_transaction(authenticated_client, db_session):
    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    transaction_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 120,
            "category": "Wrong name",
            "category_id": category_id,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert transaction_response.status_code == 200
    transaction_id = transaction_response.json()["id"]

    delete_response = authenticated_client.delete(
        f"/categories/{category_id}",
    )

    assert delete_response.status_code == 204
    db_session.expire_all()

    transaction = db_session.get(Transaction, transaction_id)

    assert transaction is not None
    assert float(transaction.amount) == 120
    assert transaction.category_id is None
    assert transaction.category == "Muay Thai"
    assert transaction.description == "Monthly training"

    assert db_session.get(Category, category_id) is None


def test_update_transaction_change_category(authenticated_client, db_session):
    muay_thai_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert muay_thai_response.status_code == 201
    muay_thai_id = muay_thai_response.json()["id"]

    gym_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Gym",
            "type": "expense",
        },
    )

    assert gym_response.status_code == 201
    gym_id = gym_response.json()["id"]

    create_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category": "Muay Thai",
            "category_id": muay_thai_id,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    update_response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 80,
            "category": "Incorrect name",
            "category_id": gym_id,
            "description": "Gym membership",
            "type": "expense",
        },
    )

    assert update_response.status_code == 200
    data = update_response.json()

    assert data["id"] == transaction_id
    assert data["amount"] == "80.00"
    assert data["category"] == "Gym"
    assert data["description"] == "Gym membership"

    db_session.expire_all()

    transaction = db_session.get(Transaction, transaction_id)

    assert transaction is not None
    assert transaction.category_id == gym_id
    assert transaction.category == "Gym"
    assert float(transaction.amount) == 80


def test_cannot_update_transaction_with_another_users_category(client, authenticated_client, db_session):
    create_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category": "Muay Thai",
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    register_response = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "MySecurePass123!",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": "bob@example.com",
            "password": "MySecurePass123!",
        },
    )

    assert login_response.status_code == 200
    bob_token = login_response.json()["access_token"]

    category_response = client.post(
        "/categories",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={
            "name": "Private gym",
            "type": "expense",
        },
    )

    assert category_response.status_code == 201
    bob_category_id = category_response.json()["id"]

    update_response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 80,
            "category": "Private gym",
            "category_id": bob_category_id,
            "description": "Unauthorized update",
            "type": "expense",
        },
    )

    assert update_response.status_code == 404
    assert update_response.json()["detail"] == "Category not found"

    db_session.expire_all()

    transaction = db_session.get(Transaction, transaction_id)

    assert transaction is not None
    assert float(transaction.amount) == 70
    assert transaction.category == "Muay Thai"
    assert transaction.category_id is None
    assert transaction.description == "Monthly training"


def test_update_transaction_with_nonexistent_category(authenticated_client, db_session):
    create_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category": "Muay Thai",
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    update_response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 80,
            "category": "Unknown category",
            "category_id": 99999999,
            "description": "Update training",
            "type": "expense",
        },
    )

    assert update_response.status_code == 404
    assert update_response.json()["detail"] == "Category not found"

    db_session.expire_all()
    db_transaction = db_session.get(Transaction, transaction_id)

    assert db_transaction is not None
    assert float(db_transaction.amount) == 70
    assert db_transaction.category == "Muay Thai"
    assert db_transaction.category_id is None
    assert db_transaction.description == "Monthly training"


def test_update_transaction_with_mismatched_category_type(authenticated_client, db_session):
    create_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category": "Muay Thai",
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Salary",
            "type": "income",
        },
    )

    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    update_response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 80,
            "category": "Salary",
            "category_id": category_id,
            "description": "Invalid update",
            "type": "expense",
        },
    )

    assert update_response.status_code == 422
    assert update_response.json()["detail"] == "Category type does not match transaction type"

    db_session.expire_all()
    db_transaction = db_session.get(Transaction, transaction_id)

    assert db_transaction is not None
    assert float(db_transaction.amount) == 70
    assert db_transaction.category == "Muay Thai"
    assert db_transaction.category_id is None
    assert db_transaction.type == "expense"
    assert db_transaction.description == "Monthly training"


def test_renaming_category_preserves_transaction_snapshot(authenticated_client, db_session):
    create_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert create_response.status_code == 201
    category_id = create_response.json()["id"]

    transaction_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category": "Muay Thai",
            "category_id": category_id,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert transaction_response.status_code == 200
    transaction_id = transaction_response.json()["id"]

    update_response = authenticated_client.put(
        f"/categories/{category_id}",
        json={
            "name": "Martial arts",
            "type": "expense",
        },
    )

    assert update_response.status_code == 200

    db_session.expire_all()

    category = db_session.get(Category, category_id)
    transaction = db_session.get(Transaction, transaction_id)

    assert category is not None
    assert category.name == "Martial arts"

    assert transaction is not None
    assert transaction.category_id == category_id
    assert transaction.category == "Muay Thai"


def test_create_transaction_with_category_id_only(authenticated_client, db_session):
    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    transaction_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category_id": category_id,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert transaction_response.status_code == 200
    data = transaction_response.json()

    assert data["category"] == "Muay Thai"

    db_session.expire_all()

    transaction = db_session.get(Transaction, data["id"])

    assert transaction is not None
    assert transaction.category_id == category_id
    assert transaction.category == "Muay Thai"


def test_create_transaction_without_category(authenticated_client):
    response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert response.status_code == 422


def test_update_transaction_with_category_id_only(authenticated_client, db_session):
    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    create_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category": "Training",
            "description": "Old description",
            "type": "expense",
        },
    )

    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    update_response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 80,
            "category_id": category_id,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert update_response.status_code == 200
    data = update_response.json()

    assert data["id"] == transaction_id
    assert data["category"] == "Muay Thai"
    assert data["amount"] == "80.00"

    db_session.expire_all()

    db_transaction = db_session.get(Transaction, transaction_id)

    assert db_transaction is not None
    assert db_transaction.category_id == category_id
    assert db_transaction.category == "Muay Thai"
    assert float(db_transaction.amount) == 80


def test_update_transaction_without_category(authenticated_client, db_session):
    create_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category": "Training",
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    update_response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 80,
            "description": "Update training",
            "type": "expense",
        },
    )

    assert update_response.status_code == 422

    db_session.expire_all()
    db_transaction = db_session.get(Transaction, transaction_id)

    assert db_transaction is not None
    assert float(db_transaction.amount) == 70
    assert db_transaction.category == "Training"
    assert db_transaction.category_id is None
    assert db_transaction.description == "Monthly training"


def test_transaction_response_includes_category_id(authenticated_client):
    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    transaction_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category_id": category_id,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert transaction_response.status_code == 200

    data = transaction_response.json()

    assert data["category_id"] == category_id
    assert data["category"] == "Muay Thai"


def test_get_transaction_includes_category_id(authenticated_client):
    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    create_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category_id": category_id,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    get_response = authenticated_client.get(f"/transactions/{transaction_id}")

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["id"] == transaction_id
    assert data["category_id"] == category_id
    assert data["category"] == "Muay Thai"


def test_list_transactions_includes_category_id(authenticated_client):
    category_response = authenticated_client.post(
        "/categories",
        json={
            "name": "Muay Thai",
            "type": "expense",
        },
    )

    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    first_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 70,
            "category_id": category_id,
            "description": "Monthly training",
            "type": "expense",
        },
    )

    assert first_response.status_code == 200

    second_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 30,
            "category": "Transport",
            "description": "Bus ticket",
            "type": "expense",
        },
    )

    response = authenticated_client.get("/transactions")

    assert second_response.status_code == 200

    transactions = response.json()

    first_id = first_response.json()["id"]
    second_id = second_response.json()["id"]

    transaction_by_id = {
        transaction["id"]: transaction
        for transaction in transactions
    }

    assert transaction_by_id[first_id]["category_id"] == category_id
    assert transaction_by_id[first_id]["category"] == "Muay Thai"

    assert transaction_by_id[second_id]["category_id"] is None
    assert transaction_by_id[second_id]["category"] == "Transport"
