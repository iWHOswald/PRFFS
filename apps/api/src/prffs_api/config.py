from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


# Installed wheels do not retain the repository's directory layout.
ROOT_DIR = Path(os.environ.get("PRFFS_ROOT_DIR") or next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "apps/api/pyproject.toml").is_file()),
    Path.cwd(),
)).resolve()
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    app_name: str = "PRFFS"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = f"sqlite:///{ROOT_DIR / 'var' / 'prffs.db'}"
    league_id: int = 917761
    espn_s2: str | None = None
    espn_swid: str | None = None
    media_root: Path = ROOT_DIR
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    poll_interval_seconds: int = 60
    admin_token: str | None = None
    app_env: str = "development"
    initialize_database_on_startup: bool = True

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    def normalized_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url

    def validate_runtime(self, *, require_admin: bool = False) -> None:
        if self.app_env == "production":
            if not self.normalized_database_url().startswith("postgresql+psycopg://"):
                raise RuntimeError("Production requires a PostgreSQL DATABASE_URL")
            if require_admin and len((self.admin_token or "").strip()) < 32:
                raise RuntimeError("Production requires an ADMIN_TOKEN of at least 32 characters")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.espn_s2:
        settings.espn_s2 = os.getenv("espn") or os.getenv("ESPN")
    if not settings.espn_swid:
        settings.espn_swid = os.getenv("password") or os.getenv("PASSWORD")
    return settings
