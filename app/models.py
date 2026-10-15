from datetime import datetime, timezone, date
from sqlalchemy import (Column, Integer,
                        String, Numeric,
                        CheckConstraint, DateTime,
                        ForeignKey, UniqueConstraint,
                        Index, func, Date)
from sqlalchemy import text as sa_text
from sqlalchemy.orm import relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    __table_args__ = (
        CheckConstraint(
            "type IN ('income', 'expense')",
            name="check_transaction_type"
        ),
        CheckConstraint(
            "amount > 0",
            name="check_transaction_amount_positive"
        ),
        Index(
            "ix_transactions_user_date",
            "user_id",
            "transaction_date",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
    )
    amount = Column(
        Numeric(10, 2),
        nullable=False)
    transaction_date = Column(
        Date,
        nullable=True,
        default=date.today,
    )
    category = Column(
        String,
        nullable=False)
    category_id = Column(
        Integer,
        ForeignKey("categories.id",
                   name="fk_transactions_category_id",
                   ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    description = Column(
        String,
        nullable=False)
    type = Column(
        String,
        nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user = relationship("User", back_populates="transactions")

    category_ref = relationship("Category", foreign_keys=[category_id])


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    transactions = relationship(
        "Transaction",
        back_populates="user",
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    categories = relationship("Category", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    __table_args__ = (
        CheckConstraint(
            "type IN ('income', 'expense')",
            name="check_category_type"
        ),
        Index(
            "uq_global_category_name_type",
            sa_text("lower(name)"),
            "type",
            unique=True,
            postgresql_where=sa_text("user_id IS NULL"),
        ),
        Index(
            "uq_category_user_lower_name_type",
            "user_id",
            sa_text("lower(name)"),
            "type",
            unique=True,
            postgresql_where=sa_text("user_id IS NOT NULL"),
        )
    )

    id = Column(Integer, primary_key=True)

    name = Column(String(100), nullable=False)

    type = Column(String(20), nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="categories")
