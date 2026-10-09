"""seed default categories

Revision ID: 149ccebeec38
Revises: d74e66bd3c85
Create Date: 2026-10-09 08:50:54.264940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert

# revision identifiers, used by Alembic.
revision: str = '149ccebeec38'
down_revision: Union[str, Sequence[str], None] = 'd74e66bd3c85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CATEGORIES = {
    "expense": [
        "Food",
        "Transport",
        "Housing",
        "Utilities",
        "Health",
        "Entertainment",
        "Shopping",
        "Education",
    ],
    "income": [
        "Salary",
        "Freelance",
        "Investments",
        "Gifts",
        "Other Income",
    ],
}


def upgrade() -> None:
    categories = sa.table(
        "categories",
        sa.column("name", sa.String),
        sa.column("type", sa.String),
        sa.column("user_id", sa.Integer),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    now = datetime.now(timezone.utc)

    rows = [
        {
            "name": name,
            "type": category_type,
            "user_id": None,
            "created_at": now,
        }
        for category_type, names in DEFAULT_CATEGORIES.items()
        for name in names
    ]

    statement = insert(categories).values(rows)

    statement = statement.on_conflict_do_nothing(
        index_elements=["name", "type"],
        index_where=sa.text("user_id is NULL"),
    )

    op.get_bind().execute(statement)


def downgrade() -> None:
    raise RuntimeError(
        "Default categories seed migration cannot be safely reversed automatically"
    )
