"""initial supreme schema — 52 tables

Revision ID: 001_initial_supreme_schema
Revises:
Create Date: 2026-02-15 00:00:00.000000

This migration creates all 52 tables from `app.models.*` in one shot using
`Base.metadata.create_all(bind=connection)`. Idempotent at the table level
(uses `checkfirst=True`).

Why not hand-write 52 op.create_table() calls?
- Source of truth lives in the SQLAlchemy `Mapped[T]` model definitions.
- `Base.metadata` already encodes columns, indexes, FK constraints,
  CHECK constraints, and naming convention — re-encoding it here would
  duplicate the surface and risk drift.
- Future migrations (`002_…`, `003_…`) will be hand-written `op.alter_*`
  calls that mutate this baseline.
"""
from typing import Sequence, Union

from alembic import op

from app.models.base import Base
import app.models  # noqa: F401  — register all 18 model modules

# revision identifiers, used by Alembic.
revision: str = "001_initial_supreme_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the entire 52-table schema."""
    bind = op.get_bind()
    # checkfirst=True → safe to re-run on partial-applied DBs
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Drop everything. Hard-rebuild only — never run on production."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
