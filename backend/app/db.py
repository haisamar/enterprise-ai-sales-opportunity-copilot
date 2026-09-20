from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings


def normalize_database_url(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


database_url = normalize_database_url(settings.database_url)
_is_sqlite = database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
}
if not _is_sqlite:
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_columns():
    if not database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        columns = {row[1] for row in conn.execute(text("PRAGMA table_info(analysis_runs)")).fetchall()}
        if columns and "repair_attempted" not in columns:
            conn.execute(text("ALTER TABLE analysis_runs ADD COLUMN repair_attempted BOOLEAN DEFAULT 0"))
