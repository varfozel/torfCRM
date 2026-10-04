from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import DeclarativeBase

# Use BigInteger in PostgreSQL and standard Integer in SQLite to ensure autoincrement works seamlessly in tests
BIGINT_ID = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass
