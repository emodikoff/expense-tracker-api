import pytest


@pytest.mark.parametrize(
    "amount",
    [
        "0",
        "-10.00",
        "125.999",
        "100000000.00",
    ],
)
def test_transaction_rejects_invalid_amounts(
        authenticated_client,
        amount,
):
    response = authenticated_client.post(
        "/transactions",
        json={
            "amount": amount,
            "category": "Food",
            "description": "Invalid amount",
            "type": "expense",
        },
    )

    assert response.status_code == 422, response.json()


def test_transaction_accepts_valid_decimal_amount(
        authenticated_client,
):
    response = authenticated_client.post(
        "/transactions",
        json={
            "amount": "125.50",
            "category": "Food",
            "description": "Valid decimal amount",
            "type": "expense",
        },
    )

    assert response.status_code == 200, response.json()
    assert response.json()["amount"] == "125.50"


@pytest.mark.parametrize(
    "amount",
    [
        "0",
        "-10.00",
        "125.999",
        "100000000.00",
    ],
)
def test_update_transaction_rejects_invalid_amounts(
        authenticated_client,
        amount,
):
    create_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": "100.00",
            "category": "Food",
            "description": "Original transaction",
            "type": "expense",
        },
    )

    assert create_response.status_code == 200

    transaction_id = create_response.json()["id"]

    response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": amount,
            "category": "Food",
            "description": "Updated transaction",
            "type": "expense",
        },
    )

    assert response.status_code == 422, response.json()


def test_invalid_update_preserves_original_amount(
        authenticated_client,
):
    create_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": "100.50",
            "category": "Food",
            "description": "Original transaction",
            "type": "expense",
        },
    )

    assert create_response.status_code == 200

    transaction_id = create_response.json()["id"]

    update_response = authenticated_client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": "999.999",
            "category": "Food",
            "description": "Invalid update",
            "type": "expense",
        },
    )

    assert update_response.status_code == 422

    get_response = authenticated_client.get(
        f"/transactions/{transaction_id}"
    )

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["amount"] == "100.50"
    assert data["description"] == "Original transaction"


def test_transaction_response_preserves_decimal_precision(
        authenticated_client,
):
    response = authenticated_client.post(
        "/transactions",
        json={
            "amount": "125.50",
            "category": "Food",
            "description": "Decimal precision test",
            "type": "expense",
        },
    )

    assert response.status_code == 200, response.json()

    data = response.json()

    assert data["amount"] == "125.50"

    transaction_id = data["id"]

    get_response = authenticated_client.get(
        f"/transactions/{transaction_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["amount"] == "125.50"
