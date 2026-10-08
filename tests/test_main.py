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