from fastapi import FastAPI, Depends, HTTPException, Query
from app.schemas import TransactionCreate, TransactionResponse, TransactionSummary, CategoryResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transaction as TransactionModel
from app.models import Category as CategoryModel
from typing import Literal
from app.routers import auth

app = FastAPI()

app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "ExpenseTracker API is running"}


@app.get("/categories", response_model=list[CategoryResponse])
def get_categories(
        type: Literal["income", "expense"] | None = None,
        db: Session = Depends(get_db),
):
    query = db.query(CategoryModel).filter(CategoryModel.user_id.is_(None))

    if type is not None:
        query = query.filter(CategoryModel.type == type)

    return query.order_by(CategoryModel.name).all()


@app.get("/transactions/summary", response_model=TransactionSummary)
def get_transaction_summary(db: Session = Depends(get_db)):
    total_income = (
        db.query(func.coalesce(func.sum(TransactionModel.amount), 0))
        .filter(TransactionModel.type == "income")
        .scalar()
    )

    total_expenses = (
        db.query(func.coalesce(func.sum(TransactionModel.amount), 0))
        .filter(TransactionModel.type == "expense")
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
        db: Session = Depends(get_db)
):
    query = db.query(TransactionModel)

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
):
    db_transaction = (
        db.query(TransactionModel)
        .filter(TransactionModel.id == transaction_id)
        .first()
    )

    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return db_transaction


@app.post("/transactions", response_model=TransactionResponse)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = TransactionModel(
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description,
        type=transaction.type,
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
):
    db_transaction = (
        db.query(TransactionModel)
        .filter(TransactionModel.id == transaction_id)
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
):
    db_transaction = (
        db.query(TransactionModel)
        .filter(TransactionModel.id == transaction_id)
        .first()
    )

    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(db_transaction)
    db.commit()

    return {"message": "Transaction deleted successfully"}
