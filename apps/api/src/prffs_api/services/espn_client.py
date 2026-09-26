from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..config import get_settings
from .current_season import owner_name


@dataclass(frozen=True)
class FantasyScore:
    matchup_id: int
    team_id: int
    owner: str
    team_name: str
    score: float
    projected_score: float | None
    captured_at: datetime


class EspnFantasyClient:
    def __init__(self, league_id: int | None = None, year: int | None = None):
        settings = get_settings()
        self.league_id = league_id or settings.league_id
        self.year = year or datetime.utcnow().year
        self.espn_s2 = settings.espn_s2
        self.swid = settings.espn_swid
        self._league = None

    def league(self):
        if self._league is None:
            from espn_api.football import League

            self._league = League(
                league_id=self.league_id,
                year=self.year,
                espn_s2=self.espn_s2,
                swid=self.swid,
            )
        return self._league

    def refresh(self) -> None:
        league = self.league()
        if hasattr(league, "refresh"):
            league.refresh()
        else:
            self._league = None

    def current_week(self) -> int:
        return int(self.league().current_week)

    def live_scores(self, week: int | None = None) -> list[FantasyScore]:
        league = self.league()
        week = week or self.current_week()
        captured_at = datetime.utcnow()
        scores: list[FantasyScore] = []
        for matchup_id, box in enumerate(league.box_scores(week)):
            for side in ("home", "away"):
                team = getattr(box, f"{side}_team")
                if not team:
                    continue
                scores.append(
                    FantasyScore(
                        matchup_id=matchup_id,
                        team_id=int(team.team_id),
                        owner=owner_name(team),
                        team_name=str(team.team_name),
                        score=float(getattr(box, f"{side}_score")),
                        projected_score=float(getattr(box, f"{side}_projected", 0) or 0),
                        captured_at=captured_at,
                    )
                )
        return scores
