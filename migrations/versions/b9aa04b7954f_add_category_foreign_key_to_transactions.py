"""add category foreign key to transactions

Revision ID: b9aa04b7954f
Revises: 5c70fed142fc
Create Date: 2026-10-12 16:15:53.336706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b9aa04b7954f'
down_revision: Union[str, Sequence[str], None] = '5c70fed142fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "transactions",
        sa.Column("category_id", sa.Integer(), nullable=True),
    )

    op.create_index(
        "ix_transactions_category_id",
        "transactions",
        ["category_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_transactions_category_id",
        "transactions",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_transactions_category_id",
        "transactions",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_transactions_category_id",
        table_name="transactions",
    )

    op.drop_column(
        "transactions",
        "category_id",
    )
