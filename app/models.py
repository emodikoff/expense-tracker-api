from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, CheckConstraint, DateTime
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
    )

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

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
