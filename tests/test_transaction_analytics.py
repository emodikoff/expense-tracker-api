from datetime import date

import pytest

from app.models import User, Transaction
from app.security import create_access_token
from sqlalchemy import update
from decimal import Decimal


def test_monthly_analytics_calculates_correct_totals(authenticated_client):
    transactions = [
        {
            "amount": 3000,
            "category": "Salary",
            "description": "October salary",
            "type": "income",
            "transaction_date": "2026-10-05"
        },
        {
            "amount": 500,
            "category": "Food",
            "description": "Groceries",
            "type": "expense",
            "transaction_date": "2026-10-10"
        },
        {
            "amount": 200,
            "category": "Muay Thai",
            "description": "Training",
            "type": "expense",
            "transaction_date": "2026-10-15"
        },
        {
            "amount": 100,
            "category": "Food",
            "description": "November groceries",
            "type": "expense",
            "transaction_date": "2026-11-01"
        },
    ]

    for transaction in transactions:
        response = authenticated_client.post("/transactions", json=transaction)
        assert response.status_code == 200

    response = authenticated_client.get(
        "/transactions/analytics/monthly",
        params={"year": 2026, "month": 10}
    )
    assert response.status_code == 200

    data = response.json()

    assert data["year"] == 2026
    assert data["month"] == 10
    assert Decimal(data["total_income"]) == Decimal("3000.00")
    assert Decimal(data["total_expenses"]) == Decimal("700.00")
    assert Decimal(data["balance"]) == Decimal("2300.00")


def test_monthly_analytics_with_no_transactions(authenticated_client):
    response = authenticated_client.get(
        "/transactions/analytics/monthly",
        params={"year": 2026, "month": 2},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["year"] == 2026
    assert data["month"] == 2

    assert isinstance(data["total_income"], str)
    assert isinstance(data["total_expenses"], str)
    assert isinstance(data["balance"], str)

    assert Decimal(data["total_income"]) == Decimal("0")
    assert Decimal(data["total_expenses"]) == Decimal("0")
    assert Decimal(data["balance"]) == Decimal("0")


def test_monthly_analytics_december_year_boundry(authenticated_client):
    transactions = [
        {
            "amount": 3000,
            "category": "Salary",
            "description": "December salary",
            "type": "income",
            "transaction_date": "2026-12-31"
        },
        {
            "amount": 500,
            "category": "Food",
            "description": "January groceries",
            "type": "expense",
            "transaction_date": "2027-01-01"
        },
    ]

    for transaction in transactions:
        response = authenticated_client.post(
            "/transactions",
            json=transaction
        )
        assert response.status_code == 200

    response = authenticated_client.get(
        "/transactions/analytics/monthly",
        params={"year": 2026, "month": 12},
    )

    assert response.status_code == 200

    data = response.json()

    assert Decimal(data["total_income"]) == Decimal("3000.00")
    assert Decimal(data["total_expenses"]) == Decimal("0")
    assert Decimal(data["balance"]) == Decimal("3000.00")


def test_monthly_analytics_only_includes_current_user(client, db_session):
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

    alice_transaction = Transaction(
        amount=3000,
        category="Salary",
        description="Alice salary",
        type="income",
        transaction_date=date(2026, 10, 5),
        user_id=alice.id,
    )

    bob_transaction = Transaction(
        amount=5000,
        category="Salary",
        description="Bob salary",
        type="income",
        transaction_date=date(2026, 10, 5),
        user_id=bob.id,
    )

    db_session.add_all([alice_transaction, bob_transaction])
    db_session.commit()

    alice_token = create_access_token(alice.id)

    response = client.get(
        "/transactions/analytics/monthly",
        params={"year": 2026, "month": 10},
        headers={"Authorization": f"Bearer {alice_token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert Decimal(data["total_income"]) == Decimal("3000.00")
    assert Decimal(data["total_expenses"]) == Decimal("0")
    assert Decimal(data["balance"]) == Decimal("3000.00")


@pytest.mark.parametrize(
    "year, month",
    [
        (2026, 0),
        (2026, 13),
        (0, 10),
        (10000, 10),
        (9999, 12)
    ],
)
def test_monthly_analytics_invalid_period(
        authenticated_client,
        year,
        month,
):
    response = authenticated_client.get(
        "/transactions/analytics/monthly",
        params={"year": year, "month": month},
    )

    assert response.status_code == 422


def test_monthly_analytics_excludes_transactions_without_date(
        authenticated_client,
        db_session,
):
    valid_response = authenticated_client.post(
        "/transactions",
        json={
            "amount": 500,
            "category": "Salary",
            "description": "October income",
            "type": "income",
            "transaction_date": "2026-10-10"
        },
    )

    assert valid_response.status_code == 200

    user_id = valid_response.json()["id"]

    create_transaction = db_session.get(Transaction, user_id)
    assert create_transaction is not None

    legacy_transaction = Transaction(
        amount=1000,
        category="Salary",
        description="Legacy transaction without date",
        type="income",
        user_id=create_transaction.user_id,
        transaction_date=None,
    )

    db_session.add(legacy_transaction)
    db_session.flush()

    db_session.execute(
        update(Transaction)
        .where(Transaction.id == legacy_transaction.id)
        .values(transaction_date=None)
    )
    db_session.commit()

    response = authenticated_client.get(
        "/transactions/analytics/monthly",
        params={"year": 2026, "month": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert Decimal(data["total_income"]) == Decimal("500.00")
    assert Decimal(data["total_expenses"]) == Decimal("0")
    assert Decimal(data["balance"]) == Decimal("500.00")


def test_monthly_analytics_preserves_decimal_precision(
        authenticated_client,
):
    for amount in ["0.10", "0.20"]:
        response = authenticated_client.post(
            "/transactions",
            json={
                "amount": amount,
                "category": "Food",
                "description": "Decimal precision test",
                "type": "expense",
                "transaction_date": "2026-10-10",
            },
        )

        assert response.status_code == 200, response.json()

    response = authenticated_client.get(
        "/transactions/analytics/monthly",
        params={"year": 2026, "month": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["total_expenses"], str)
    assert isinstance(data["balance"], str)

    assert Decimal(data["total_expenses"]) == Decimal("0.30")
    assert Decimal(data["balance"]) == Decimal("-0.30")


def test_monthly_analytics_large_decimal_amounts(
        authenticated_client,
):
    amounts = [
        "12345678.91",
        "12345678.92",
        "0.17",
    ]

    for amount in amounts:
        response = authenticated_client.post(
            "/transactions",
            json={
                "amount": amount,
                "category": "Salary",
                "description": "Large decimal precision test",
                "type": "income",
                "transaction_date": "2026-10-10",
            },
        )

        assert response.status_code == 200, response.json()

    response = authenticated_client.get(
        "/transactions/analytics/monthly",
        params={"year": 2026, "month": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["total_income"], str)
    assert Decimal(data["total_income"]) == Decimal("24691358.00")
    assert Decimal(data["total_expenses"]) == Decimal("0")
    assert Decimal(data["balance"]) == Decimal("24691358.00")
