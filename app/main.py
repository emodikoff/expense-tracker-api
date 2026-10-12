from fastapi import FastAPI, Depends, HTTPException, Query
from typing import Literal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.schemas import TransactionCreate, TransactionResponse, TransactionSummary, CategoryResponse, CategoryCreate
from app.database import get_db
from app.models import User
from app.models import Transaction as TransactionModel
from app.models import Category as CategoryModel
from app.routers import auth
from app.dependencies import get_current_user

app = FastAPI()

app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "ExpenseTracker API is running"}


@app.get("/categories", response_model=list[CategoryResponse])
def get_categories(
        type: Literal["income", "expense"] | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    query = db.query(CategoryModel).filter(
        or_(CategoryModel.user_id.is_(None),
            CategoryModel.user_id == current_user.id)
    )

    if type is not None:
        query = query.filter(CategoryModel.type == type)

    return query.order_by(CategoryModel.name).all()


@app.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(
        category: CategoryCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    db_category = CategoryModel(
        name=category.name,
        type=category.type,
        user_id=current_user.id,
    )

    db.add(db_category)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        sqlstate = getattr(exc.orig, "sqlstate", None)
        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None
        )

        if (
                sqlstate == "23505"
                and constraint_name == "uq_category_user_lower_name_type"
        ):
            raise HTTPException(
                status_code=409,
                detail="Category already exists",
            )

        raise HTTPException(
            status_code=409,
            detail="Category already exists",
        )

    db.refresh(db_category)

    return db_category


@app.put("/categories/{category_id}",response_model=CategoryResponse)
def update_category(
        category_id: int,
        category: CategoryCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    db_category = (
        db.query(CategoryModel)
        .filter(
            CategoryModel.id == category_id,
            CategoryModel.user_id == current_user.id,
        )
        .first()
    )

    if db_category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    db_category.name = category.name
    db_category.type = category.type

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        sqlstate = getattr(exc.orig, "sqlstate", None)
        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )

        if (
                sqlstate == "23505"
                and constraint_name == "uq_category_user_lower_name_type"
        ):
            raise HTTPException(
                status_code=409,
                detail="Category already exists",
            ) from exc
        raise

    db.refresh(db_category)
    return db_category


@app.delete("/categories/{category_id}", status_code=204)
def delete_category(
        category_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    category = (
        db.query(CategoryModel)
        .filter(
            CategoryModel.id == category_id,
            CategoryModel.user_id == current_user.id,
        )
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    db.delete(category)
    db.commit()


@app.get("/transactions/summary", response_model=TransactionSummary)
def get_transaction_summary(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    total_income = (
        db.query(func.coalesce(func.sum(TransactionModel.amount), 0))
        .filter(
            TransactionModel.type == "income",
            TransactionModel.user_id == current_user.id,
        )
        .scalar()
    )

    total_expenses = (
        db.query(func.coalesce(func.sum(TransactionModel.amount), 0))
        .filter(
            TransactionModel.type == "expense",
            TransactionModel.user_id == current_user.id,
        )
        .scalar()
    )

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
    }


@app.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=100),
        type: Literal["income", "expense"] | None = None,
        category: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    query = db.query(TransactionModel).filter(
        TransactionModel.user_id == current_user.id
    )

    if type is not None:
        query = query.filter(TransactionModel.type == type)

    if category is not None:
        query = query.filter(TransactionModel.category == category)

    return (
        query
        .order_by(TransactionModel.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@app.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
        transaction_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    db_transaction = (
        db.query(TransactionModel)
        .filter(
            TransactionModel.id == transaction_id,
            TransactionModel.user_id == current_user.id,
        )
        .first()
    )

    if db_transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return db_transaction


@app.post("/transactions", response_model=TransactionResponse)
def create_transaction(
        transaction: TransactionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    db_transaction = TransactionModel(
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description,
        type=transaction.type,
        user_id=current_user.id,
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction


@app.put("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
        transaction_id: int,
        transaction: TransactionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    db_transaction = (
        db.query(TransactionModel)
        .filter(
            TransactionModel.id == transaction_id,
            TransactionModel.user_id == current_user.id,
        )
        .first()
    )

    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db_transaction.amount = transaction.amount
    db_transaction.category = transaction.category
    db_transaction.description = transaction.description
    db_transaction.type = transaction.type

    db.commit()
    db.refresh(db_transaction)

    return db_transaction


@app.delete("/transactions/{transaction_id}")
def delete_transaction(
        transaction_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    db_transaction = (
        db.query(TransactionModel)
        .filter(
            TransactionModel.id == transaction_id,
            TransactionModel.user_id == current_user.id,
        )
        .first()
    )

    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(db_transaction)
    db.commit()

    return {"message": "Transaction deleted successfully"}
