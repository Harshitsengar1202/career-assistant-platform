import os
from functools import lru_cache

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")


@lru_cache
def get_engine():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def check_database():
    with get_engine().connect() as connection:
        return connection.execute(text("select now()")).scalar()


def fetch_all(query: str, params: dict | None = None):
    with get_engine().connect() as connection:
        result = connection.execute(text(query), params or {})
        return [dict(row._mapping) for row in result]


def fetch_one(query: str, params: dict | None = None):
    with get_engine().connect() as connection:
        result = connection.execute(text(query), params or {})
        row = result.mappings().first()
        return dict(row) if row else None


def execute_one(query: str, params: dict | None = None):
    with get_engine().begin() as connection:
        result = connection.execute(text(query), params or {})
        row = result.mappings().first()
        return dict(row) if row else None
