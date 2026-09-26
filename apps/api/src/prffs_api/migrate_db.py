"""Copy a consistent SQLite backup into an empty PostgreSQL database.

The source is never modified. All user tables are reflected, including tables
not currently represented by ORM models. A dry run is the default.
"""

from __future__ import annotations

import argparse
from contextlib import closing
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid

from sqlalchemy import Boolean, DefaultClause, MetaData, create_engine, func, inspect, select, text
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.exc import SQLAlchemyError

from .config import ROOT_DIR
from .database import SCHEMA_LOCK_ID, initialize_schema


def backup_sqlite(source: Path, backup_dir: Path) -> Path:
    source = source.resolve(strict=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = backup_dir / f"prffs-{stamp}-{uuid.uuid4().hex[:8]}.db"
    # Backups include private league notes. Do not inherit a permissive umask.
    descriptor = os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)) as original:
            with closing(sqlite3.connect(backup)) as destination:
                original.backup(destination)
                if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("SQLite backup failed its integrity check")
    except Exception:
        backup.unlink(missing_ok=True)
        raise
    return backup


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, bytes):
        return {"bytes": value.hex()}
    raise TypeError(f"Unsupported migration value type: {type(value).__name__}")


def _fingerprint(connection: Connection, table) -> tuple[int, str]:
    # Sorting row hashes makes verification independent of database row order.
    hashes = []
    for row in connection.execute(select(table)).mappings():
        value = json.dumps(dict(row), sort_keys=True, default=_json_value, allow_nan=False, separators=(",", ":"))
        hashes.append(hashlib.sha256(value.encode()).digest())
    return len(hashes), hashlib.sha256(b"".join(sorted(hashes))).hexdigest()


def _require_empty(connection: Connection) -> None:
    existing = MetaData()
    existing.reflect(bind=connection)
    occupied = [table.name for table in existing.sorted_tables if connection.scalar(select(func.count()).select_from(table))]
    if occupied:
        raise ValueError("Target is not empty; refusing to overwrite tables: " + ", ".join(occupied))


def _target_engine(url: str) -> Engine:
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql" and parsed.drivername != "postgres":
        raise ValueError("The migration target must be PostgreSQL")
    return create_engine(parsed.set(drivername="postgresql+psycopg"), pool_pre_ping=True, hide_parameters=True)


def migrate_database(
    source: Path,
    target_url: str | None,
    *,
    apply: bool = False,
    backup_dir: Path | None = None,
) -> dict:
    if apply and not target_url:
        raise ValueError("Set PRFFS_TARGET_DATABASE_URL before applying the migration")
    backup = backup_sqlite(source, backup_dir or ROOT_DIR / "var/backups")
    source_engine = create_engine(f"sqlite:///{backup}")
    target_engine = _target_engine(target_url) if target_url else None
    try:
        source_metadata = MetaData()
        source_metadata.reflect(bind=source_engine)
        if "seasons" not in source_metadata.tables:
            raise ValueError("Source does not look like a PRFFS database (seasons table missing)")

        # SQLite DATETIME and dialect-specific types must become portable types.
        target_metadata = MetaData()
        for table in source_metadata.sorted_tables:
            copied = table.to_metadata(target_metadata)
            for column in copied.columns:
                column.type = column.type.as_generic()
                if isinstance(column.type, Boolean) and column.server_default is not None:
                    default = str(column.server_default.arg).strip("()'\" ").lower()
                    if default in {"0", "false"}:
                        column.server_default = DefaultClause(text("false"))
                    elif default in {"1", "true"}:
                        column.server_default = DefaultClause(text("true"))
                    else:
                        raise ValueError(f"Unsupported boolean default in {table.name}.{column.name}")

        with source_engine.connect() as source_connection:
            fingerprints = {table.name: _fingerprint(source_connection, table) for table in source_metadata.sorted_tables}
            report = {
                "backup": str(backup),
                "applied": False,
                "target_checked": target_engine is not None,
                "tables": {name: result[0] for name, result in fingerprints.items()},
            }
            if not target_engine:
                return report
            if not apply:
                with target_engine.connect() as connection:
                    _require_empty(connection)
                return report

            with target_engine.begin() as connection:
                connection.execute(text("SET LOCAL lock_timeout = '10s'"))
                connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": SCHEMA_LOCK_ID})
                quote = connection.dialect.identifier_preparer.quote
                # Block writes to existing empty tables during the copy.
                for name in sorted(inspect(connection).get_table_names()):
                    connection.execute(text(f"LOCK TABLE {quote(name)} IN ACCESS EXCLUSIVE MODE"))
                _require_empty(connection)
                target_metadata.create_all(bind=connection)
                for table in source_metadata.sorted_tables:
                    target = target_metadata.tables[table.name]
                    existing_columns = {column["name"] for column in inspect(connection).get_columns(table.name)}
                    if set(table.columns.keys()) - existing_columns:
                        raise ValueError(f"Target schema is missing source columns in {table.name}")
                    rows = source_connection.execute(select(table)).mappings()
                    for batch in rows.partitions(500):
                        connection.execute(target.insert(), [dict(row) for row in batch])
                    if _fingerprint(connection, target) != fingerprints[table.name]:
                        raise ValueError(f"Data verification failed for {table.name}; migration rolled back")

                    # Explicitly copied IDs must not collide with future inserts.
                    for column in target.primary_key.columns:
                        sequence = connection.scalar(
                            text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
                            {"table_name": quote(table.name), "column_name": column.name},
                        )
                        if sequence:
                            maximum = connection.scalar(select(func.max(column)))
                            connection.execute(
                                text("SELECT setval(CAST(:sequence AS regclass), :value, :called)"),
                                {"sequence": sequence, "value": maximum if maximum is not None else 1, "called": maximum is not None},
                            )
                initialize_schema(connection)
            report["applied"] = True
            report["verified"] = "Every source table matched by row count and content fingerprint"
            return report
    finally:
        source_engine.dispose()
        if target_engine:
            target_engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT_DIR / "var/prffs.db")
    parser.add_argument("--backup-dir", type=Path, default=ROOT_DIR / "var/backups")
    parser.add_argument("--apply", action="store_true", help="Copy data to the empty PostgreSQL target; otherwise inspect only")
    args = parser.parse_args()
    try:
        report = migrate_database(
            args.source,
            os.environ.get("PRFFS_TARGET_DATABASE_URL"),
            apply=args.apply,
            backup_dir=args.backup_dir,
        )
    except SQLAlchemyError as exc:
        # Driver messages may contain connection details or private row values.
        parser.exit(1, f"Migration failed ({type(exc).__name__}); no data was committed. Check connectivity, permissions, and schema compatibility.\n")
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f"Migration stopped: {exc}\n")
    print(json.dumps(report, indent=2))
    if not args.apply:
        print("Dry run only. Stop local writers, set PRFFS_TARGET_DATABASE_URL, and repeat with --apply when ready.")


if __name__ == "__main__":
    main()
