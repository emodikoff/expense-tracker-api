import os

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url

from app.database import Base, get_db, DATABASE_URL
from app.main import app
from app.security import create_access_token

import pytest

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is missing from environment")

main_db = make_url(DATABASE_URL)
test_db = make_url(TEST_DATABASE_URL)

if main_db.set(password=None) == test_db.set(password=None):
    raise RuntimeError(
        "TEST_DATABASE_URL must point to a different database"
    )

test_engine = create_engine(TEST_DATABASE_URL)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_test_database(setup_test_database):
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "MySecurePassword123!",
        },
    )

    assert response.status_code == 201

    user_id = response.json()["id"]
    token = create_access_token(user_id)

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def authenticated_client(client, auth_headers):
    client.headers.update(auth_headers)
    yield client
