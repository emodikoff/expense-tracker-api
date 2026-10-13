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

When both `category` and `category_id` are provided, the stored category name is taken from the category record in PostgreSQL.

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

The foreign key uses `ON DELETE SET NULL`, meaning that the transaction remains available while its `category_id` becomes `null`.

The stored text category name is preserved.

### Category Renaming

Renaming a category does not automatically update the stored category name in existing transactions. However, a subsequent full transaction update using `category_id` resolves and stores the category's current name.

## API Documentation

FastAPI automatically generates interactive API documentation:

- `/docs` — Swagger UI
- `/redoc` — ReDoc

## Database Migrations

Database schema changes are managed using Alembic.

```bash
alembic upgrade head
```

## Running Tests

Run the full automated test suite:

```bash
python -m pytest -q
```

The test suite covers authentication, transaction management, category management, authorization, data validation, and database relationships.

## Project Status

Backend development is ongoing. Planned improvements include financial analytics, containerization, CI/CD, and deployment.