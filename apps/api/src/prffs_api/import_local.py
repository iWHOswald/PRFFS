import argparse
from pathlib import Path

from .config import ROOT_DIR, get_settings
from .database import SessionLocal, init_db
from .services.importer import import_local_history


def main() -> None:
    parser = argparse.ArgumentParser(description="Import local CSVs. Existing seasons in these files are replaced.")
    parser.add_argument("--reset", action="store_true", help="Delete all historical data before importing")
    parser.add_argument("--allow-production", action="store_true", help="Explicitly permit a production CSV import")
    args = parser.parse_args()
    if get_settings().app_env == "production" and not args.allow_production:
        parser.error("Use prffs-migrate-db for the first deployment; CSV imports replace historical data")
    init_db()
    with SessionLocal() as session:
        result = import_local_history(session, Path(ROOT_DIR), reset=args.reset)
    print(result)


if __name__ == "__main__":
    main()
