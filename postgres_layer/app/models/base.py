"""SQLAlchemy declarative base — async-ready."""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData


# Naming convention for FK / index / constraint names — predictable for Alembic autogen
NAMING = {
    "ix":  "ix_%(column_0_label)s",
    "uq":  "uq_%(table_name)s_%(column_0_name)s",
    "ck":  "ck_%(table_name)s_%(constraint_name)s",
    "fk":  "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk":  "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Async-compatible declarative base. Mapped[T] only — never legacy Column()."""
    metadata = MetaData(naming_convention=NAMING)
