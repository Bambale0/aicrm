"""add_updated_at_to_processes_table

Revision ID: 712168a7d302
Revises: b08ad829700e
Create Date: 2026-01-16 12:59:09.715668

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "712168a7d302"
down_revision: Union[str, Sequence[str], None] = "b08ad829700e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("processes", sa.Column("updated_at", sa.DateTime(), nullable=True))
    # Устанавливаем значение updated_at = created_at для существующих записей
    op.execute("UPDATE processes SET updated_at = created_at WHERE updated_at IS NULL")
    # Меняем на NOT NULL с дефолтным значением
    op.alter_column(
        "processes",
        "updated_at",
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("processes", "updated_at")
