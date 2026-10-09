"""initial transactions schema

Revision ID: b8ed42b26c9a
Revises: 
Create Date: 2026-10-09 07:45:08.181722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b8ed42b26c9a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.CheckConstraint(
            "type IN ('income', 'expense')",
            name="check_transaction_type",
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="check_transaction_amount_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_transactions_id",
        "transactions",
        ["id"],
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_id", table_name="transactions")
    op.drop_table("transactions")
