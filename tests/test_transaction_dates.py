from datetime import date


def test_create_transaction_with_specific_date(authenticated_client):
    response = authenticated_client.post(
        "/transactions/",
        json={
            "amount": 100,
            "category": "Muay Thai",
            "description": "Training",
            "type": "expense",
            "transaction_date": "2026-10-10"
        },
    )

    assert response.status_code == 200
    assert response.json()["transaction_date"] == "2026-10-10"


def test_create_transaction_without_date_uses_today(authenticated_client):
    before = date.today()

    response = authenticated_client.post(
        "/transactions/",
        json={
            "amount": 25,
            "category": "Food",
            "description": "Lunch",
            "type": "expense",
        },
    )

    after = date.today()

    assert response.status_code == 200

    saved_date = date.fromisoformat(response.json()["transaction_date"])
    assert before <= saved_date <= after


def test_update_transaction_preserves_date(authenticated_client):
    create_response = authenticated_client.post(
        "/transactions/",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Original purchase",
            "type": "expense",
            "transaction_date": "2026-09-15"
        },
    )

    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    update_response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 80,
            "category": "Food",
            "description": "Update purchase",
            "type": "expense",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["transaction_date"] == "2026-09-15"
    assert update_response.json()["amount"] == "80.00"


def test_update_transaction_change_date(authenticated_client):
    create_response = authenticated_client.post(
        "/transactions/",
        json={
            "amount": 100,
            "category": "Food",
            "description": "Groceries",
            "type": "expense",
            "transaction_date": "2026-09-15"
        },
    )

    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    update_response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Groceries",
            "type": "expense",
            "transaction_date": "2026-10-10"
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["transaction_date"] == "2026-10-10"

    get_response = authenticated_client.get(f"/transactions/{transaction_id}")

    assert get_response.status_code == 200
    assert get_response.json()["transaction_date"] == "2026-10-10"


def test_create_transaction_with_invalid_date(authenticated_client):
    response = authenticated_client.post(
        "/transactions/",
        json={
            "amount": 100,
            "category": "Food",
            "description": "Groceries",
            "type": "expense",
            "transaction_date": "2026-02-30"
        },
    )

    assert response.status_code == 422