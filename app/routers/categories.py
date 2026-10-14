from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.models import Category as CategoryModel
from app.schemas import CategoryCreate, CategoryResponse

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.get("", response_model=list[CategoryResponse])
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


@router.post("", response_model=CategoryResponse, status_code=201)
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


@router.put("/{category_id}", response_model=CategoryResponse)
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


@router.delete("/{category_id}", status_code=204)
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
