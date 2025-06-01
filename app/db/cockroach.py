# app/db/cockroach.py

# ─── Monkey-patch to skip CockroachDB version parsing ───────────────
from sqlalchemy.dialects.postgresql.base import PGDialect
# Always report a valid Postgres version tuple (e.g. 9.6)
PGDialect._get_server_version_info = lambda *args, **kwargs: (9, 6)
# ─────────────────────────────────────────────────────────────────────

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

DATABASE_URL = str(settings.cockroach_database_url)

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

Base = declarative_base()
