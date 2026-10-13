from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import User
from app.models import Category as CategoryModel
from app.schemas import TransactionCreate


def resolve_transaction_category(
    transaction: TransactionCreate,
    db: Session,
    current_user: User,
) -> str:
    if transaction.category_id is None:
        assert transaction.category is not None
        return transaction.category

    db_category = (
        db.query(CategoryModel)
        .filter(
            CategoryModel.id == transaction.category_id,
            or_(
                CategoryModel.user_id.is_(None),
                CategoryModel.user_id == current_user.id,
            ),
        )
        .first()
    )

    if db_category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    if db_category.type != transaction.type:
        raise HTTPException(
            status_code=422,
            detail="Category type does not match transaction type",
        )

    return db_category.name