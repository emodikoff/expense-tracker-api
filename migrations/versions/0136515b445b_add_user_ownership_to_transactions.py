"""add user ownership to transactions

Revision ID: 0136515b445b
Revises: 149ccebeec38
Create Date: 2026-10-09 16:28:43.771637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0136515b445b'
down_revision: Union[str, Sequence[str], None] = '149ccebeec38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    op.create_index(
        "ix_transactions_user_id",
        "transactions",
        ["user_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_transactions_user_id_users",
        "transactions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_transactions_user_id_users",
        "transactions",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_transactions_user_id",
        table_name="transactions",
    )

    op.drop_column("transactions", "user_id")
