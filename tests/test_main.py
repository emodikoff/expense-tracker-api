from app.models import Category, User


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "ExpenseTracker API is running"}


def test_create_transaction(client):
    response = client.post(
        "/transactions",
        json={
            "amount": 42.50,
            "category": "food",
            "description": "Test lunch",
            "type": "expense",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["amount"] == 42.50
    assert data["category"] == "food"
    assert data["description"] == "Test lunch"
    assert data["type"] == "expense"
    assert "id" in data


def test_get_transaction(client):
    client.post(
        "/transactions",
        json={
            "amount": 42.50,
            "category": "food",
            "description": "Test lunch",
            "type": "expense",
        },
    )

    client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "salary",
            "description": "Monthly salary",
            "type": "income",
        },
    )

    response = client.get(f"/transactions")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    transaction_by_category = {
        transaction["category"]: transaction for transaction in data
    }

    assert transaction_by_category["food"]["amount"] == 42.50
    assert transaction_by_category["salary"]["amount"] == 100


def test_transaction_with_invalid_amount(client):
    response = client.post(
        "/transactions",
        json={
            "amount": -42.50,
            "category": "food",
            "description": "Invalid transaction amount",
            "type": "expense",
        },
    )

    assert response.status_code == 422


def test_create_transaction_with_invalid_type(client):
    response = client.post(
        "/transactions",
        json={
            "amount": 10,
            "category": "food",
            "description": "Invalid transaction type",
            "type": "invalid",
        },
    )

    assert response.status_code == 422


def test_get_transaction_by_id(client):
    create_response = client.post(
        "/transactions",
        json={
            "amount": 25,
            "category": "transport",
            "description": "Bus ticket",
            "type": "expense",
        },
    )

    transaction_id = create_response.json()["id"]

    response = client.get(f"/transactions/{transaction_id}")

    assert response.status_code == 200
    assert response.json()["id"] == transaction_id
    assert response.json()["category"] == "transport"


def test_get_nonexistent_transaction(client):
    response = client.get(f"/transactions/9999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_update_transaction(client):
    create_response = client.post(
        "/transactions",
        json={
            "amount": 25,
            "category": "transport",
            "description": "Bus ticket",
            "type": "expense",
        },
    )

    transaction_id = create_response.json()["id"]

    update_response = client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 40,
            "category": "food",
            "description": "Update transaction",
            "type": "expense",
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()
    assert data["id"] == transaction_id
    assert data["amount"] == 40
    assert data["category"] == "food"
    assert data["description"] == "Update transaction"


def test_update_nonexistent_transaction(client):
    response = client.put(
        f"/transactions/999999",
        json={
            "amount": 40,
            "category": "food",
            "description": "Update transaction",
            "type": "expense",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_delete_transaction(client):
    create_response = client.post(
        "/transactions",
        json={
            "amount": 25,
            "category": "transport",
            "description": "Bus ticket",
            "type": "expense",
        },
    )

    transaction_id = create_response.json()["id"]

    delete_response = client.delete(f"/transactions/{transaction_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Transaction deleted successfully"

    get_response = client.get(f"/transactions/{transaction_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_transaction(client):
    response = client.delete(f"/transactions/9999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_get_transaction_with_pagination(client):
    for amount in (10, 20, 30):
        client.post(
            "/transactions",
            json={
                "amount": amount,
                "category": "food",
                "description": f"Transaction {amount}",
                "type": "expense",
            },
        )

    response = client.get(f"/transactions?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == 20


def test_get_transactions_with_invalid_pagination(client):
    response = client.get(f"/transactions?skip=-1&limit=0")

    assert response.status_code == 422


def test_filter_transaction_by_type(client):
    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "food",
            "description": "Lunch",
            "type": "expense",
        },
    )
    client.post(
        "/transactions",
        json={
            "amount": 2000,
            "category": "salary",
            "description": "Monthly salary",
            "type": "income",
        },
    )

    response = client.get(f"/transactions?type=expense")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "expense"
    assert data[0]["amount"] == 50


def test_filter_transaction_by_category(client):
    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "food",
            "description": "Lunch",
            "type": "expense",
        },
    )
    client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "transport",
            "description": "Bus ticket",
            "type": "expense",
        }
    )

    response = client.get(f"/transactions?category=food")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "food"
    assert data[0]["amount"] == 50


def test_filter_transaction_with_invalid_type(client):
    response = client.get(f"/transactions?type=banana")

    assert response.status_code == 422


def test_filter_transaction_by_type_and_category(client):
    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "food",
            "description": "Lunch",
            "type": "expense",
        },
    )
    client.post(
        "/transactions",
        json={
            "amount": 2000,
            "category": "salary",
            "description": "Monthly salary",
            "type": "income",
        },
    )
    client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "food",
            "description": "Food refund",
            "type": "income",
        },
    )

    response = client.get(f"/transactions?type=expense&category=food")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "expense"
    assert data[0]["category"] == "food"
    assert data[0]["amount"] == 50


def test_transaction_summary(client):
    transactions = [
        {
            "amount": 1000,
            "category": "salary",
            "description": "First salary",
            "type": "income",
        },
        {
            "amount": 500,
            "category": "freelance",
            "description": "Freelance work",
            "type": "income",
        },
        {
            "amount": 300,
            "category": "food",
            "description": "Groceries",
            "type": "expense",
        },
    ]

    for transaction in transactions:
        response = client.post("/transactions", json=transaction)
        assert response.status_code == 200

    response = client.get("/transactions/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 1500
    assert data["total_expenses"] == 300
    assert data["balance"] == 1200


def test_transaction_summary_with_empty_db(client):
    response = client.get("/transactions/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 0
    assert data["total_expenses"] == 0
    assert data["balance"] == 0


def test_get_categories(client):
    response = client.get("/categories")

    assert response.status_code == 200
    assert response.json() == []


def test_get_system_categories(client, db_session):
    categories = [
        Category(name='Food', type='expense', user_id=None),
        Category(name='Salary', type='income', user_id=None),
    ]

    db_session.add_all(categories)
    db_session.commit()

    response = client.get("/categories")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert [category["name"] for category in data] == ["Food", "Salary"]


def test_get_categories_filtered_by_type(client, db_session):
    categories = [
        Category(name='Food', type='expense', user_id=None),
        Category(name='Transport', type='expense', user_id=None),
        Category(name='Salary', type='income', user_id=None),
    ]

    db_session.add_all(categories)
    db_session.commit()

    expense_response = client.get("/categories?type=expense")

    assert expense_response.status_code == 200
    expense_data = expense_response.json()

    assert len(expense_data) == 2
    assert [category["name"] for category in expense_data] == ["Food", "Transport"]

    income_response = client.get("/categories?type=income")

    assert income_response.status_code == 200
    income_data = income_response.json()

    assert len(income_data) == 1
    assert income_data[0]["name"] == "Salary"


def test_get_categories_excludes_user_categories(client, db_session):
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

    response = client.get("/categories")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Food"