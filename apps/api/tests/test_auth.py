import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

# Tests must never read or modify the league's actual database or credentials.
_temporary = tempfile.TemporaryDirectory(prefix="prffs-auth-tests-")
os.environ.update({
    "DATABASE_URL": f"sqlite:///{Path(_temporary.name) / 'test.db'}",
    "APP_ENV": "test",
    "ADMIN_TOKEN": "test-admin-credential-at-least-32-characters",
    "INITIALIZE_DATABASE_ON_STARTUP": "true",
    "ESPN_S2": "unused-test-value",
    "ESPN_SWID": "unused-test-value",
})

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from prffs_api.config import Settings, get_settings
from prffs_api.database import Base, SessionLocal, engine, get_session
from prffs_api.main import app
from prffs_api.models import LeagueContext


class AdminAccessTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        self.client = TestClient(app)
        self.client.__enter__()
        self.headers = {"X-Admin-Token": get_settings().admin_token}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        app.dependency_overrides.clear()

    def test_every_admin_route_rejects_missing_and_wrong_credentials(self):
        routes = [
            ("GET", "/api/admin/session", None),
            ("GET", "/api/admin/context", None),
            ("GET", "/api/admin/matchup-briefs", None),
            ("POST", "/api/admin/context", {"league_context": {}, "weekly_context": {}}),
            ("POST", "/api/admin/import-local?reset=true", None),
            ("POST", "/api/draft/live/manual", {"owner": "Test", "player_name": "Test", "bid_amount": 1}),
            ("GET", "/api/draft/live?poll_espn=true", None),
        ]
        for method, route, payload in routes:
            for headers in ({}, {"X-Admin-Token": "wrong"}):
                with self.subTest(method=method, route=route, headers=headers):
                    response = self.client.request(method, route, json=payload, headers=headers)
                    self.assertEqual(response.status_code, 401)

    def test_missing_server_secret_disables_admin_access(self):
        with patch.object(get_settings(), "admin_token", None):
            response = self.client.get("/api/admin/session", headers=self.headers)
            self.assertEqual(response.status_code, 503)

    def test_authenticated_admin_can_write_and_read_context(self):
        with patch("prffs_api.services.matchup_experiences.current_season_payload", return_value={"teams": [], "matchups": [], "display_week": 1}):
            response = self.client.post("/api/admin/context", headers=self.headers, json={
                "league_context": {"public_notes": "saved through authenticated request"}, "weekly_context": {},
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.client.get("/api/admin/context", headers=self.headers).status_code, 200)
        with SessionLocal() as session:
            self.assertEqual(session.scalar(select(LeagueContext)).public_notes, "saved through authenticated request")

    def test_local_import_is_disabled_in_production_even_for_admin(self):
        with patch.object(get_settings(), "app_env", "production"):
            self.assertEqual(self.client.post("/api/admin/import-local", headers=self.headers).status_code, 403)

    def test_public_stats_still_work(self):
        for route in ["/health", "/api/seasons", "/api/records", "/api/draft/summary", "/api/history/summary"]:
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 200)

    def test_health_reports_database_failure(self):
        class UnavailableSession:
            def execute(self, statement):
                raise OperationalError("SELECT 1", {}, Exception("database down"))
        app.dependency_overrides[get_session] = lambda: UnavailableSession()
        self.assertEqual(self.client.get("/health").status_code, 503)

    def test_production_requires_postgres_and_a_strong_admin_secret(self):
        with self.assertRaises(RuntimeError):
            Settings(app_env="production", database_url="sqlite:///unused.db").validate_runtime()
        with self.assertRaises(RuntimeError):
            Settings(app_env="production", database_url="postgresql://user@localhost/db", admin_token="short").validate_runtime(require_admin=True)


if __name__ == "__main__":
    unittest.main()
