import argparse

from .database import SessionLocal, init_db
from .services.espn_importer import import_espn_draft, import_espn_season


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch ESPN fantasy seasons into the PRFFS database.")
    parser.add_argument("years", nargs="+", type=int)
    parser.add_argument("--include-playoffs", action="store_true")
    parser.add_argument("--draft-only", action="store_true")
    parser.add_argument("--season-only", action="store_true")
    args = parser.parse_args()

    init_db()
    with SessionLocal() as session:
        for year in args.years:
            if not args.draft_only:
                result = import_espn_season(session, year, include_playoffs=args.include_playoffs)
                print(result)
            if not args.season_only:
                print(import_espn_draft(session, year))


if __name__ == "__main__":
    main()
