# ExpenseTracker API

A REST API for managing personal income and expenses, built with FastAPI, PostgreSQL, and SQLAlchemy.

## Tech Stack

- Python 3.14
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic v2
- PyJWT
- Argon2 password hashing
- pytest
- Docker & Docker Compose

## Features

### Authentication

- User registration and login
- JWT-based authentication
- Secure password hashing
- Protected user endpoints

### Transactions

- Create, read, update, and delete transactions
- Track income and expenses
- User-specific transaction access
- Retrieve transaction summaries
- Associate transactions with categories

### Categories

- Global categories available to all authenticated users
- Personal categories owned by individual users
- Create, list, update, and delete personal categories
- Case-insensitive category name uniqueness
- Ownership and category type validation

### Analytics

- Calculate total income, expenses, and balance
- Retrieve monthly income and expense summaries
- Analyze monthly expenses grouped by category
- Filter analytics by year and month
- Use Decimal for precise financial calculations

## Transaction Categories

Transactions can reference a category using `category_id`.

**Recommended request format:**

```json
{
  "amount": 120.50,
  "category_id": 3,
  "description": "Monthly training",
  "type": "expense"
}
```

For backward compatibility, the API also accepts a category name without a category ID:

```json
{
  "amount": 120.50,
  "category": "Muay Thai",
  "description": "Monthly training",
  "type": "expense"
}
```

When both `category` and `category_id` are provided, the stored category name is taken from the category record in
PostgreSQL.

At least one of `category` or `category_id` must be provided.

### Category Validation

When a transaction references a category:

- The category must exist.
- The category must be global or owned by the authenticated user.
- The category type must match the transaction type (`income` or `expense`).
- Unauthorized or nonexistent category references return `404 Not Found`.
- Category type mismatches return `422`.

### Category Deletion

Deleting a category does not delete the associated transactions.

The foreign key uses `ON DELETE SET NULL`, meaning that the transaction remains available while its `category_id`
becomes `null`.

The stored text category name is preserved.

### Category Renaming

Renaming a category does not automatically update the stored category name in existing transactions. However, a
subsequent full transaction update using `category_id` resolves and stores the category's current name.

## API Documentation

FastAPI automatically generates interactive API documentation:

- `/docs` — Swagger UI
- `/redoc` — ReDoc

## Database Migrations

Database schema changes are managed using Alembic.

```bash
alembic upgrade head
```

## Running with Docker

The application can run using Docker Compose with two main services:

- **api** — FastAPI application running on port 8000
- **db** — PostgreSQL 17 with persistent storage

Alembic migrations run through a separate `migrate` service.

### Prerequisites

- Docker Engine
- Docker Compose

### 1. Configure environment variables

Copy the example environment file:

```bash
cp .env.docker.example .env.docker
```

Edit `.env.docker` and replace the placeholder PostgreSQL password and JWT secret with secure values.

The `.env.docker` file is excluded from Git.

### 2. Start PostgreSQL

```bash
docker compose --env-file .env.docker up -d db
```

Docker Compose creates the PostgreSQL container, network, and persistent volume.

### 3. Apply database migrations

```bash
docker compose --env-file .env.docker run --rm migrate
```

This initializes the database schema using Alembic.

### 4. Start FastAPI

```bash
docker compose --env-file .env.docker up -d api
```

Open the interactive API documentation at:

http://localhost:8000/docs

### 5. Check container status

```bash
docker compose --env-file .env.docker ps
```

### 6. View application logs

```bash
docker compose --env-file .env.docker logs -f api
```

### 7. Stop the application

```bash
docker compose --env-file .env.docker down
```

PostgreSQL data is stored in a named Docker volume and survives container recreation.

**Warning:** Running `docker compose down -v` removes the project's named volumes and can permanently delete the
database data.

### Rebuilding after code changes

The API source code is copied into the Docker image during the build. After changing the application code, rebuild and
restart the API:

```bash
docker compose --env-file .env.docker up -d --build api
```

When new database migrations are introduced, apply them using the `migrate` service before starting the updated
application.

## Running Tests

Run the full automated test suite:

```bash
python -m pytest -q
```

The test suite covers authentication, transaction management, category management, authorization, data validation, and
database relationships.

## Project Status

The API currently includes:

- JWT authentication and secure password hashing
- Transaction and category management
- Financial analytics with Decimal precision
- Automated tests with pytest
- PostgreSQL indexing and database migrations
- Docker Compose containerization with persistent PostgreSQL storage

Planned improvements include CI/CD, deployment, observability, and additional security enhancements.
