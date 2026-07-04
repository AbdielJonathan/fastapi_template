"""agregar sexo

Revision ID: 5732a9521743
Revises: fdd812fef97f
Create Date: 2026-07-04 01:58:13.152053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5732a9521743'
down_revision: Union[str, Sequence[str], None] = 'fdd812fef97f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("sexo", sa.CHAR, nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "sexo")
