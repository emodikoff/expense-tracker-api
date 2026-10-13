from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from datetime import date

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.models import Transaction as TransactionModel
from app.schemas import TransactionSummary, MonthlyTransactionSummary, MonthlyCategoryExpenseSummary
from app.services.analytics import get_month_date_range

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


@router.get(
    "/analytics/monthly",
    response_model=MonthlyTransactionSummary,
)
def get_monthly_transaction_summary(
        year: int = Query(ge=1, le=9999),
        month: int = Query(ge=1, le=12),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    start_date, end_date = get_month_date_range(year, month)

    totals = (
        db.query(
            func.coalesce(
                func.sum(
                    case(
                        (
                            TransactionModel.type == "income",
                            TransactionModel.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            TransactionModel.type == "expense",
                            TransactionModel.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("total_expenses"),
        )
        .filter(
            TransactionModel.user_id == current_user.id,
            TransactionModel.transaction_date >= start_date,
            TransactionModel.transaction_date < end_date,
        )
        .one()
    )

    return {
        "year": year,
        "month": month,
        "total_income": totals.total_income,
        "total_expenses": totals.total_expenses,
        "balance": totals.total_income - totals.total_expenses,
    }


@router.get(
    "/analytics/categories",
    response_model=MonthlyCategoryExpenseSummary,
)
def get_monthly_expenses_by_category(
        year: int = Query(ge=1, le=9999),
        month: int = Query(ge=1, le=12),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    start_date, end_date = get_month_date_range(year, month)

    results = (
        db.query(
            TransactionModel.category,
            func.sum(TransactionModel.amount).label("total"),
        )
        .filter(
            TransactionModel.user_id == current_user.id,
            TransactionModel.type == "expense",
            TransactionModel.transaction_date >= start_date,
            TransactionModel.transaction_date < end_date,
        )
        .group_by(TransactionModel.category)
        .order_by(func.sum(TransactionModel.amount).desc())
        .all()
    )

    categories = [
        {
            "category": row.category,
            "total": row.total,
        }
        for row in results
    ]

    total_expenses = sum(row.total for row in results)

    return {
        "year": year,
        "month": month,
        "total_expenses": total_expenses,
        "categories": categories,
    }
