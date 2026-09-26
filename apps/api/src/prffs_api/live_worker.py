from __future__ import annotations

import time

from sqlalchemy import select

from .config import get_settings
from .database import SessionLocal, init_db
from .models import ScoreSnapshot
from .services.espn_client import EspnFantasyClient


def poll_once(year: int | None = None, week: int | None = None) -> int:
    settings = get_settings()
    client = EspnFantasyClient(league_id=settings.league_id, year=year)
    week = week or client.current_week()
    scores = client.live_scores(week)
    inserted = 0
    with SessionLocal() as session:
        for score in scores:
            latest = session.scalar(
                select(ScoreSnapshot)
                .where(
                    ScoreSnapshot.league_id == settings.league_id,
                    ScoreSnapshot.year == client.year,
                    ScoreSnapshot.week == week,
                    ScoreSnapshot.team_id == score.team_id,
                )
                .order_by(ScoreSnapshot.captured_at.desc())
                .limit(1)
            )
            if latest and latest.score == score.score and latest.projected_score == score.projected_score:
                continue
            session.add(
                ScoreSnapshot(
                    league_id=settings.league_id,
                    year=client.year,
                    week=week,
                    team_id=score.team_id,
                    matchup_id=score.matchup_id,
                    owner=score.owner,
                    team_name=score.team_name,
                    score=score.score,
                    projected_score=score.projected_score,
                    captured_at=score.captured_at,
                )
            )
            inserted += 1
        session.commit()
    return inserted


def main() -> None:
    settings = get_settings()
    settings.validate_runtime()
    if settings.initialize_database_on_startup:
        init_db()
    while True:
        try:
            inserted = poll_once()
            print(f"live poll inserted={inserted}")
        except Exception as exc:
            print(f"live poll failed: {exc}")
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
