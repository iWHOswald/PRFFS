from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Connection, create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    settings = get_settings()
    url = settings.normalized_database_url()
    if url.startswith("sqlite:///"):
        Path(url.replace("sqlite:///", "", 1)).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Shared by deploy jobs and the data migration so schema changes cannot race.
SCHEMA_LOCK_ID = 9177610001


def initialize_schema(connection: Connection) -> None:
    from . import models  # noqa: F401

    if connection.dialect.name == "postgresql":
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": SCHEMA_LOCK_ID})
    Base.metadata.create_all(bind=connection)
    _ensure_incremental_columns(connection)


def init_db() -> None:
    get_settings().validate_runtime()
    with engine.begin() as connection:
        initialize_schema(connection)


def main() -> None:
    init_db()
    print("Database schema ready; existing data preserved.")


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def _ensure_incremental_columns(connection: Connection) -> None:
    inspector = inspect(connection)
    table_names = set(inspector.get_table_names())
    statements = []
    if "weekly_team_results" in table_names:
        existing = {column["name"] for column in inspector.get_columns("weekly_team_results")}
        if "is_playoff" not in existing:
            if connection.dialect.name == "postgresql":
                statements.append("ALTER TABLE weekly_team_results ADD COLUMN is_playoff BOOLEAN DEFAULT FALSE")
            else:
                statements.append("ALTER TABLE weekly_team_results ADD COLUMN is_playoff BOOLEAN DEFAULT 0")
        if "season_phase" not in existing:
            statements.append("ALTER TABLE weekly_team_results ADD COLUMN season_phase VARCHAR(32) DEFAULT 'regular'")
    if "owner_contexts" in table_names:
        existing = {column["name"] for column in inspector.get_columns("owner_contexts")}
        if "political_affiliation" not in existing:
            statements.append("ALTER TABLE owner_contexts ADD COLUMN political_affiliation VARCHAR(64) DEFAULT 'unassigned'")
        if "veto_hunter" not in existing:
            statements.append("ALTER TABLE owner_contexts ADD COLUMN veto_hunter VARCHAR(32) DEFAULT 'unknown'")
        if "rival_owner" not in existing:
            statements.append("ALTER TABLE owner_contexts ADD COLUMN rival_owner VARCHAR(255) DEFAULT ''")
    if not statements:
        return
    for statement in statements:
        connection.execute(text(statement))


if __name__ == "__main__":
    main()
