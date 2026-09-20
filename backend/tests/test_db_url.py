from app.db import normalize_database_url


def test_sqlite_url_unchanged():
    assert normalize_database_url("sqlite:///./copilot.db") == "sqlite:///./copilot.db"


def test_postgres_scheme_uses_psycopg_dialect():
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_postgresql_scheme_uses_psycopg_dialect():
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_psycopg_dialect_is_not_double_prefixed():
    url = "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url(url) == url
