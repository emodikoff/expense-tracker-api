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
