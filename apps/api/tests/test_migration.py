from datetime import datetime
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, MetaData, String, Table, create_engine, func, inspect, select, text

from prffs_api.migrate_db import _fingerprint, _target_engine, migrate_database


@unittest.skipUnless(os.environ.get("PRFFS_TEST_DATABASE_URL"), "Set PRFFS_TEST_DATABASE_URL to a disposable PostgreSQL database")
class PostgresMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="prffs-migration-tests-")
        self.root = Path(self.temporary.name)
        self.source = self.root / "source.db"
        self.admin_engine = _target_engine(os.environ["PRFFS_TEST_DATABASE_URL"])
        self.schema = "prffs_test_" + uuid.uuid4().hex
        with self.admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{self.schema}"'))
        self.url = self.admin_engine.url.update_query_dict({"options": f"-csearch_path={self.schema}"}).render_as_string(hide_password=False)
        self.target = _target_engine(self.url)
        self.source_engine = create_engine(f"sqlite:///{self.source}")
        metadata = MetaData()
        seasons = Table("seasons", metadata, Column("id", Integer, primary_key=True), Column("league_id", Integer), Column("year", Integer), Column("source", String(255)), Column("imported_at", DateTime))
        self.extra = Table("legacy_experiences", metadata, Column("id", Integer, primary_key=True), Column("title", String), Column("active", Boolean, server_default=text("0")), Column("score", Float), Column("payload", JSON), Column("created_at", DateTime))
        metadata.create_all(self.source_engine)
        with self.source_engine.begin() as connection:
            connection.execute(seasons.insert(), {"id": 14, "league_id": 917761, "year": 2025, "source": "test", "imported_at": datetime(2026, 1, 2, 3, 4, 5, 123456)})
            connection.execute(self.extra.insert(), {"id": 42, "title": "Preserve 🏈", "active": True, "score": 123.45, "payload": {"nested": [None, True, "notes"]}, "created_at": datetime(2026, 1, 2)})

    def tearDown(self):
        self.source_engine.dispose()
        self.target.dispose()
        with self.admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{self.schema}" CASCADE'))
        self.admin_engine.dispose()
        self.temporary.cleanup()

    def migrate(self, apply=False):
        return migrate_database(self.source, self.url, apply=apply, backup_dir=self.root / "backups")

    def test_dry_run_creates_backup_but_no_target_tables(self):
        before = hashlib.sha256(self.source.read_bytes()).digest()
        report = self.migrate()
        self.assertFalse(report["applied"])
        self.assertEqual(report["tables"]["legacy_experiences"], 1)
        self.assertEqual(inspect(self.target).get_table_names(), [])
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).digest(), before)
        self.assertEqual(Path(report["backup"]).stat().st_mode & 0o777, 0o600)

    def test_preserves_unmodeled_tables_and_resets_id_sequences(self):
        report = self.migrate(apply=True)
        self.assertTrue(report["applied"])
        with self.source_engine.connect() as source, self.target.begin() as target:
            self.assertEqual(_fingerprint(source, self.extra), _fingerprint(target, self.extra))
            new_id = target.scalar(self.extra.insert().values(title="New record").returning(self.extra.c.id))
            self.assertEqual(new_id, 43)
            self.assertFalse(target.scalar(select(self.extra.c.active).where(self.extra.c.id == new_id)))

    def test_refuses_to_overwrite_an_existing_database(self):
        self.migrate(apply=True)
        with self.assertRaisesRegex(ValueError, "Target is not empty"):
            self.migrate(apply=True)
        with self.target.connect() as connection:
            self.assertEqual(connection.scalar(select(func.count()).select_from(self.extra)), 1)

    def test_copy_error_rolls_back_all_tables_and_rows(self):
        # This destination table cannot fit the existing title.
        with self.target.begin() as connection:
            connection.execute(text("CREATE TABLE legacy_experiences (id SERIAL PRIMARY KEY, title VARCHAR(1), active BOOLEAN, score DOUBLE PRECISION, payload JSON, created_at TIMESTAMP)"))
        with self.assertRaises(Exception):
            self.migrate(apply=True)
        self.assertEqual(inspect(self.target).get_table_names(), ["legacy_experiences"])
        with self.target.connect() as connection:
            self.assertEqual(connection.scalar(text("SELECT COUNT(*) FROM legacy_experiences")), 0)


if __name__ == "__main__":
    unittest.main()
