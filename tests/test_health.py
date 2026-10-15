from unittest.mock import Mock

from fastapi import HTTPException

from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_liveness(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "live"}


def test_readiness(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_database_unavailable(client):
    def broken_db():
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
        yield

    original_override = app.dependency_overrides.get(get_db)

    app.dependency_overrides[get_db] = broken_db

    try:
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {
            "detail": "Database unavailable"
        }
    finally:
        if original_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original_override


def test_readiness_when_database_query_fails(client):
    mock_db = Mock()

    mock_db.execute.side_effect = OperationalError(
        "SELECT 1",
        {},
        Exception("Database connection failed"),
    )

    def override_broken_db():
        yield mock_db

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_broken_db

    try:
        response = client.get("/health/ready")

        assert response.status_code == 503
        assert response.json() == {
            "detail": "Database unavailable"
        }

        mock_db.execute.assert_called_once()

    finally:
        if original_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original_override
