import email
import json
from datetime import date

from app.models import User, Transaction
from app.routers import categories
from app.security import create_access_token


def test_monthly_expenses_grouped_by_category(authenticated_client):
    transactions = [
        {
            "amount": 100,
            "category": "Food",
            "description": "Groceries",
            "type": "expense",
            "transaction_date": "2026-10-05",
        },
        {
            "amount": 200,
            "category": "Food",
            "description": "Restaurant",
            "type": "expense",
            "transaction_date": "2026-10-10",
        },
        {
            "amount": 150,
            "category": "Muay Thai",
            "description": "Training",
            "type": "expense",
            "transaction_date": "2026-10-15",
        },
        {
            "amount": 3000,
            "category": "Salary",
            "description": "Monthly salary",
            "type": "income",
            "transaction_date": "2026-10-05",
        },
        {
            "amount": 500,
            "category": "Food",
            "description": "November groceries",
            "type": "expense",
            "transaction_date": "2026-11-05",
        },
    ]

    for transaction in transactions:
        response = authenticated_client.post(
            "/transactions",
            json=transaction,
        )
        assert response.status_code == 200, response.json()

    response = authenticated_client.get(
        "/transactions/analytics/categories",
        params={"year": 2026, "month": 10},
    )

    assert response.status_code == 200, response.json()

    data = response.json()

    assert data["year"] == 2026
    assert data["month"] == 10
    assert data["total_expenses"] == 450.0

    assert data["categories"] == [
        {"category": "Food", "total": 300.0},
        {"category": "Muay Thai", "total": 150.0},
    ]


def test_category_analytics_preserves_deleted_category(
        authenticated_client,
        db_session,
):
    from app.models import Transaction

    response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 250,
            "category": "Food",
            "description": "Groceries",
            "type": "expense",
            "transaction_date": "2026-10-10",
        },
    )

    assert response.status_code == 200, response.json()

    transaction_id = response.json()["id"]

    transaction = db_session.get(Transaction, transaction_id)

    assert transaction is not None

    transaction.category_id = None
    db_session.commit()

    response = authenticated_client.get(
        "/transactions/analytics/categories",
        params={"year": 2026, "month": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_expenses"] == 250.0
    assert data["categories"] == [
        {"category": "Food", "total": 250.0},
    ]


def test_category_analytics_empty_month(authenticated_client):
    response = authenticated_client.get(
        "/transactions/analytics/categories",
        params={"year": 2026, "month": 2},
    )

    assert response.status_code == 200

    assert response.json() == {
        "year": 2026,
        "month": 2,
        "total_expenses": 0.0,
        "categories": [],
    }


def test_category_analytics_only_includes_current_user(
        client,
        db_session,
):
    alice = User(
        email="alice@example.com",
        hashed_password="test-pass-alice"
    )

    bob = User(
        email="bob@example.com",
        hashed_password="test-pass-bob"
    )

    db_session.add_all([alice, bob])
    db_session.flush()

    transaction = [
        Transaction(
            amount=300,
            category="Food",
            description="Alice groceries",
            type="expense",
            transaction_date=date(2026, 10, 5),
            user_id=alice.id,
        ),
        Transaction(
            amount=5000,
            category="Bob groceries",
            description="Bob groceries",
            type="expense",
            transaction_date=date(2026, 10, 5),
            user_id=bob.id,
        ),
    ]

    db_session.add_all(transaction)
    db_session.commit()

    alice_token = create_access_token(alice.id)

    response = client.get(
        "/transactions/analytics/categories",
        params={"year": 2026, "month": 10},
        headers={"Authorization": f"Bearer {alice_token}"},
    )

    assert response.status_code == 200, response.json()

    assert response.json() == {
        "year": 2026,
        "month": 10,
        "total_expenses": 300.0,
        "categories": [
            {"category": "Food", "total": 300.0},
        ],
    }
