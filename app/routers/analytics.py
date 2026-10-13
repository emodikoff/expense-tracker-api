from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.models import Transaction as TransactionModel
from app.schemas import TransactionSummary


router = APIRouter(
    prefix="/transactions",
    tags=["Analytics"],
)


@router.get("/summary", response_model=TransactionSummary)
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
