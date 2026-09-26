from __future__ import annotations

import ast
import csv
import re
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import DraftPick, LineupEntry, MediaAsset, Season, SidePointAward, TeamSeason, WeeklyTeamResult
from .media import discover_media
from .side_points import calculate_side_points

TEAM_STATS_RE = re.compile(r"(?P<league>\d+)_(?P<year>20\d{2})_team_stats\.csv$")
DRAFT_STATS_RE = re.compile(r"(?P<league>\d+)_(?P<year>20\d{2})_?draft_stats\.csv$")
LINEUP_SLOTS = ["QB", "RB1", "RB2", "WR1", "WR2", "TE", "RB/WR/TE", "D/ST", "HC"]
DRAFT_REQUIRED_COLUMNS = {"team ID", "Owner", "Player Name", "Position Drafted", "bid_amount"}


def _safe_int(value: str | None, default: int = 0) -> int:
    try:
        return int(float(value or default))
    except ValueError:
        return default


def _safe_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except ValueError:
        return default


def _parse_lineup(value: str | None) -> tuple[str, str | None, float]:
    if not value:
        return ("empty", None, 0.0)
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return (value, None, 0.0)
    if not isinstance(parsed, list) or len(parsed) < 3:
        return ("empty", None, 0.0)
    return (str(parsed[0]), str(parsed[1]) if parsed[1] else None, _safe_float(str(parsed[2])))


def _source_priority(path: Path) -> tuple[int, str]:
    parts = set(path.parts)
    if "archive" in parts or "bac" in parts or "2021_1" in parts:
        return (99, str(path))
    if "2023" in parts:
        return (0, str(path))
    year = path.name.split("_")[1]
    if year in parts:
        return (1, str(path))
    return (10, str(path))


def find_team_stat_sources(root: Path, league_id: int | None = None) -> list[Path]:
    selected: dict[tuple[int, int], Path] = {}
    for path in root.rglob("*_team_stats.csv"):
        match = TEAM_STATS_RE.match(path.name)
        if not match:
            continue
        source_league_id = int(match.group("league"))
        if league_id and source_league_id != league_id:
            continue
        key = (source_league_id, int(match.group("year")))
        current = selected.get(key)
        if current is None or _source_priority(path) < _source_priority(current):
            selected[key] = path
    return sorted(selected.values(), key=lambda item: (TEAM_STATS_RE.match(item.name).group("year"), str(item)))


def find_draft_sources(root: Path, league_id: int | None = None) -> list[Path]:
    selected: dict[tuple[int, int], Path] = {}
    for path in root.rglob("*draft_stats.csv"):
        match = DRAFT_STATS_RE.match(path.name)
        if not match:
            continue
        source_league_id = int(match.group("league"))
        if league_id and source_league_id != league_id:
            continue
        if not _looks_like_draft_csv(path):
            continue
        key = (source_league_id, int(match.group("year")))
        current = selected.get(key)
        if current is None or _draft_source_priority(path) < _draft_source_priority(current):
            selected[key] = path
    return sorted(selected.values(), key=lambda item: (DRAFT_STATS_RE.match(item.name).group("year"), str(item)))


def import_local_history(session: Session, root: Path, reset: bool = False, league_id: int | None = None) -> dict:
    league_id = league_id or get_settings().league_id
    if reset:
        for model in [DraftPick, SidePointAward, LineupEntry, WeeklyTeamResult, TeamSeason, Season, MediaAsset]:
            session.execute(delete(model))
        session.commit()

    imported_files = []
    for source in find_team_stat_sources(root, league_id=league_id):
        match = TEAM_STATS_RE.match(source.name)
        if not match:
            continue
        league_id = int(match.group("league"))
        year = int(match.group("year"))
        _import_team_stats_file(session, source, league_id, year)
        imported_files.append(str(source.relative_to(root)))

    imported_drafts = []
    for source in find_draft_sources(root, league_id=league_id):
        match = DRAFT_STATS_RE.match(source.name)
        if not match:
            continue
        _import_draft_file(session, source, int(match.group("league")), int(match.group("year")))
        imported_drafts.append(str(source.relative_to(root)))

    _import_media(session, root)
    session.commit()
    return {
        "imported_files": imported_files,
        "imported_drafts": imported_drafts,
        "count": len(imported_files),
        "draft_count": len(imported_drafts),
    }


def _import_team_stats_file(session: Session, source: Path, league_id: int, year: int) -> None:
    session.execute(delete(SidePointAward).where(SidePointAward.league_id == league_id, SidePointAward.year == year))
    session.execute(delete(LineupEntry).where(LineupEntry.league_id == league_id, LineupEntry.year == year))
    session.execute(delete(WeeklyTeamResult).where(WeeklyTeamResult.league_id == league_id, WeeklyTeamResult.year == year))
    session.execute(delete(TeamSeason).where(TeamSeason.league_id == league_id, TeamSeason.year == year))
    session.execute(delete(Season).where(Season.league_id == league_id, Season.year == year))

    session.add(Season(league_id=league_id, year=year, source=str(source)))
    weekly_rows: dict[int, list[dict]] = {}
    lineup_points: dict[tuple[int, int, str], float] = {}
    teams_seen: set[int] = set()

    with source.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            team_id = _safe_int(row.get("Team ID"))
            week = _safe_int(row.get("Week"))
            if not team_id or not week:
                continue
            owner = (row.get("Owner") or "").strip()
            team_name = (row.get("Team Name") or "").strip()
            division = (row.get("Division") or "").strip() or None
            if team_id not in teams_seen:
                session.add(
                    TeamSeason(
                        league_id=league_id,
                        year=year,
                        team_id=team_id,
                        owner=owner,
                        team_name=team_name,
                        division=division,
                    )
                )
                teams_seen.add(team_id)

            result = WeeklyTeamResult(
                league_id=league_id,
                year=year,
                week=week,
                team_id=team_id,
                matchup_id=_safe_int(row.get("Matchup_ID")),
                owner=owner,
                team_name=team_name,
                home_away=(row.get("Home/Away") or "").strip(),
                division=division,
                wins=_safe_int(row.get("Wins")),
                losses=_safe_int(row.get("Losses")),
                ties=_safe_int(row.get("Ties")),
                record_label=(row.get("Record (season)") or "").strip(),
                total_points_season=_safe_float(row.get("Total pts (season)")),
                cumulative_points=_safe_float(row.get("Cumulative points")),
                weekly_points=_safe_float(row.get("Points for (week)")),
                plus_minus=_safe_float(row.get("Plus/Minus")),
                is_playoff=False,
                season_phase="regular",
            )
            session.add(result)
            weekly_rows.setdefault(week, []).append(
                {
                    "team_id": team_id,
                    "owner": owner,
                    "weekly_points": result.weekly_points,
                    "plus_minus": result.plus_minus,
                }
            )

            for slot in LINEUP_SLOTS:
                player_name, player_position, points = _parse_lineup(row.get(slot))
                session.add(
                    LineupEntry(
                        league_id=league_id,
                        year=year,
                        week=week,
                        team_id=team_id,
                        owner=owner,
                        slot_key=slot,
                        player_name=player_name,
                        player_position=player_position,
                        points=points,
                    )
                )
                lineup_points[(week, team_id, slot)] = points

    for week, rows in weekly_rows.items():
        week_lineup = {
            (team_id, slot): points
            for (lineup_week, team_id, slot), points in lineup_points.items()
            if lineup_week == week
        }
        for award in calculate_side_points(rows, week_lineup):
            session.add(
                SidePointAward(
                    league_id=league_id,
                    year=year,
                    week=week,
                    team_id=award.team_id,
                    owner=award.owner,
                    category=award.category,
                    points=award.points,
                    metric_name=award.metric_name,
                    metric_value=award.metric_value,
                    detail=award.detail,
                )
            )


def _import_media(session: Session, root: Path) -> None:
    for item in discover_media(root):
        existing = session.scalar(select(MediaAsset).where(MediaAsset.path == item["path"]))
        if existing:
            for key, value in item.items():
                setattr(existing, key, value)
        else:
            session.add(MediaAsset(**item))


def _draft_source_priority(path: Path) -> tuple[int, str]:
    parts = set(path.parts)
    if "archive" in parts or "bac" in parts or "2021_1" in parts:
        return (99, str(path))
    if "2023" in parts:
        return (0, str(path))
    if "draft" in parts:
        return (1, str(path))
    year = DRAFT_STATS_RE.match(path.name).group("year") if DRAFT_STATS_RE.match(path.name) else ""
    if year in parts:
        return (2, str(path))
    return (10, str(path))


def _looks_like_draft_csv(path: Path) -> bool:
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            header = set(next(csv.reader(handle)))
    except (OSError, StopIteration):
        return False
    return DRAFT_REQUIRED_COLUMNS.issubset(header)


def _import_draft_file(session: Session, source: Path, league_id: int, year: int) -> None:
    session.execute(delete(DraftPick).where(DraftPick.league_id == league_id, DraftPick.year == year))
    with source.open(newline="", encoding="utf-8-sig") as handle:
        for fallback_position, row in enumerate(csv.DictReader(handle), start=1):
            player_name = (row.get("Player Name") or "").strip()
            if not player_name:
                continue
            bid_amount = _safe_float(row.get("bid_amount"))
            total_points = _safe_float(row.get("Total Points"))
            dollar_value = _safe_float(row.get("Dollar value")) if bid_amount else None
            session.add(
                DraftPick(
                    league_id=league_id,
                    year=year,
                    team_id=_safe_int(row.get("team ID")),
                    owner=(row.get("Owner") or "").strip(),
                    division=(row.get("Division") or "").strip() or None,
                    player_id=_safe_int(row.get("Player ID")) or None,
                    player_name=player_name,
                    pro_team=(row.get("Pro Team") or "").strip() or None,
                    position=(row.get("Position") or "").strip() or None,
                    total_points=total_points,
                    round_drafted=_safe_int(row.get("Round Drafted")),
                    round_pick=_safe_int(row.get("round_pick")),
                    position_drafted=_safe_int(row.get("Position Drafted"), fallback_position),
                    bid_amount=bid_amount,
                    dollar_value=dollar_value,
                    source=str(source),
                )
            )
