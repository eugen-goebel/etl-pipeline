"""Database connection and session management."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_PATH = os.environ.get("DATABASE_PATH", "output/shopflow.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_engine(db_path: str | None = None):
    """Return an engine for the given path, or the default engine."""
    if db_path:
        return create_engine(f"sqlite:///{db_path}", echo=False)
    return engine


def execute_sql(sql: str, engine=None, params: dict | None = None):
    """Execute raw SQL and return results as list of dicts."""
    eng = engine if engine is not None else get_engine()
    with eng.connect() as conn:
        result = conn.execute(text(sql), params or {})
        if result.returns_rows:
            columns = list(result.keys())
            return [dict(zip(columns, row)) for row in result.fetchall()]
        conn.commit()
        return []
