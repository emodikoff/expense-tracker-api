from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.models import Transaction as TransactionModel
from app.schemas import TransactionCreate, TransactionResponse, TransactionSummary
from app.services.categories import resolve_transaction_category


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)

@router.get("", response_model=list[TransactionResponse])
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


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
        transaction_id: int = Path(gt=0, le=2_147_483_647),
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


@router.post("", response_model=TransactionResponse)
def create_transaction(
        transaction: TransactionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),

):
    category_name = resolve_transaction_category(
        transaction=transaction,
        db=db,
        current_user=current_user,
    )

    db_transaction = TransactionModel(
        amount=transaction.amount,
        category=category_name,
        category_id=transaction.category_id,
        description=transaction.description,
        type=transaction.type,
        user_id=current_user.id,
        transaction_date=transaction.transaction_date or date.today(),
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
        transaction: TransactionCreate,
        transaction_id: int = Path(gt=0, le=2_147_483_647),
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

    category_name = resolve_transaction_category(
        transaction=transaction,
        db=db,
        current_user=current_user,
    )

    db_transaction.amount = transaction.amount
    db_transaction.category = category_name
    db_transaction.category_id = transaction.category_id
    db_transaction.description = transaction.description
    db_transaction.type = transaction.type

    if transaction.transaction_date is not None:
        db_transaction.transaction_date = transaction.transaction_date

    db.commit()
    db.refresh(db_transaction)

    return db_transaction


@router.delete("/{transaction_id}")
def delete_transaction(
        transaction_id: int = Path(gt=0, le=2_147_483_647),
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
