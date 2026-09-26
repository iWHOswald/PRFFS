from __future__ import annotations

from collections import defaultdict
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import DraftPick, LineupEntry, Season, SidePointAward, TeamSeason, WeeklyTeamResult
from .side_points import calculate_side_points


STARTER_BASE_SLOTS = {"QB", "TE", "RB/WR/TE", "D/ST", "HC", "K"}
COUNTED_SLOTS = {"RB", "WR", "BE", "IR"}


def import_espn_season(session: Session, year: int, include_playoffs: bool = False) -> dict:
    from espn_api.football import League

    settings = get_settings()
    league = League(
        league_id=settings.league_id,
        year=year,
        espn_s2=settings.espn_s2,
        swid=settings.espn_swid,
    )
    end_week = int(league.finalScoringPeriod if include_playoffs else league.settings.reg_season_count)

    _delete_existing(session, settings.league_id, year)
    session.add(Season(league_id=settings.league_id, year=year, source="espn-api"))

    for team in league.teams:
        session.add(
            TeamSeason(
                league_id=settings.league_id,
                year=year,
                team_id=int(team.team_id),
                owner=_owner_name(team),
                team_name=str(team.team_name),
                division=getattr(team, "division_name", None),
            )
        )

    cumulative_points: defaultdict[int, float] = defaultdict(float)
    wins: defaultdict[int, int] = defaultdict(int)
    losses: defaultdict[int, int] = defaultdict(int)
    ties: defaultdict[int, int] = defaultdict(int)
    imported_weeks = 0
    imported_teams = 0

    player_team_cache = {}
    for week in range(1, end_week + 1):
        is_playoff = week > int(league.settings.reg_season_count)
        season_phase = "playoff" if is_playoff else "regular"
        weekly_rows: list[dict] = []
        lineup_points: dict[tuple[int, str], float] = {}
        try:
            boxes = league.box_scores(week, player_team_cache=player_team_cache)
            weekly_rows = _add_box_score_week(
                session,
                settings.league_id,
                year,
                week,
                boxes,
                wins,
                losses,
                ties,
                cumulative_points,
                is_playoff,
                season_phase,
                lineup_points,
            )
        except Exception as exc:
            if "before 2019" not in str(exc):
                raise
            weekly_rows = _add_scoreboard_week(
                session,
                settings.league_id,
                year,
                week,
                league.scoreboard(week),
                wins,
                losses,
                ties,
                cumulative_points,
                is_playoff,
                season_phase,
            )

        for award in calculate_side_points(weekly_rows, lineup_points):
            session.add(
                SidePointAward(
                    league_id=settings.league_id,
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
        imported_weeks += 1
        imported_teams += len(weekly_rows)

    session.commit()
    return {"year": year, "weeks": imported_weeks, "team_weeks": imported_teams, "source": "espn-api"}


def _add_box_score_week(
    session: Session,
    league_id: int,
    year: int,
    week: int,
    boxes: list,
    wins: defaultdict[int, int],
    losses: defaultdict[int, int],
    ties: defaultdict[int, int],
    cumulative_points: defaultdict[int, float],
    is_playoff: bool,
    season_phase: str,
    lineup_points: dict[tuple[int, str], float],
) -> list[dict]:
    weekly_rows: list[dict] = []
    for matchup_id, box in enumerate(boxes):
        sides = [
            ("home", box.home_team, float(box.home_score), float(box.away_score)),
            ("away", box.away_team, float(box.away_score), float(box.home_score)),
        ]
        for side, team, score, opponent_score in sides:
            if team is None:
                continue
            owner, team_id = _add_weekly_team_result(
                session,
                league_id,
                year,
                week,
                matchup_id,
                side,
                team,
                score,
                opponent_score,
                wins,
                losses,
                ties,
                cumulative_points,
                is_playoff,
                season_phase,
            )
            plus_minus = score - opponent_score
            weekly_rows.append(
                {
                    "team_id": team_id,
                    "owner": owner,
                    "weekly_points": round(score, 2),
                    "plus_minus": round(plus_minus, 2),
                }
            )
            lineup = box.home_lineup if side == "home" else box.away_lineup
            for entry in _lineup_entries(league_id, year, week, team_id, owner, lineup):
                session.add(entry)
                if entry.slot_key in {"QB", "RB1", "RB2", "WR1", "WR2", "TE", "D/ST", "HC"}:
                    lineup_points[(team_id, entry.slot_key)] = entry.points
    return weekly_rows


def _add_scoreboard_week(
    session: Session,
    league_id: int,
    year: int,
    week: int,
    scoreboard: list,
    wins: defaultdict[int, int],
    losses: defaultdict[int, int],
    ties: defaultdict[int, int],
    cumulative_points: defaultdict[int, float],
    is_playoff: bool,
    season_phase: str,
) -> list[dict]:
    weekly_rows: list[dict] = []
    for matchup_id, matchup in enumerate(scoreboard):
        home_team = getattr(matchup, "home_team", None)
        away_team = getattr(matchup, "away_team", None)
        home_score = float(getattr(matchup, "home_score", 0) or 0)
        away_score = float(getattr(matchup, "away_score", 0) or 0)
        sides = [
            ("home", home_team, home_score, away_score),
            ("away", away_team, away_score, home_score),
        ]
        for side, team, score, opponent_score in sides:
            if team is None:
                continue
            owner, team_id = _add_weekly_team_result(
                session,
                league_id,
                year,
                week,
                matchup_id,
                side,
                team,
                score,
                opponent_score,
                wins,
                losses,
                ties,
                cumulative_points,
                is_playoff,
                season_phase,
            )
            weekly_rows.append(
                {
                    "team_id": team_id,
                    "owner": owner,
                    "weekly_points": round(score, 2),
                    "plus_minus": round(score - opponent_score, 2),
                }
            )
    return weekly_rows


def _add_weekly_team_result(
    session: Session,
    league_id: int,
    year: int,
    week: int,
    matchup_id: int,
    side: str,
    team,
    score: float,
    opponent_score: float,
    wins: defaultdict[int, int],
    losses: defaultdict[int, int],
    ties: defaultdict[int, int],
    cumulative_points: defaultdict[int, float],
    is_playoff: bool,
    season_phase: str,
) -> tuple[str, int]:
    team_id = int(team.team_id)
    if score > opponent_score:
        wins[team_id] += 1
    elif score < opponent_score:
        losses[team_id] += 1
    else:
        ties[team_id] += 1
    cumulative_points[team_id] += score
    plus_minus = score - opponent_score
    owner = _owner_name(team)

    session.add(
        WeeklyTeamResult(
            league_id=league_id,
            year=year,
            week=week,
            team_id=team_id,
            matchup_id=matchup_id,
            owner=owner,
            team_name=str(team.team_name),
            home_away=side.title(),
            division=getattr(team, "division_name", None),
            wins=wins[team_id],
            losses=losses[team_id],
            ties=ties[team_id],
            record_label=f"({wins[team_id]}-{losses[team_id]}-{ties[team_id]})",
            total_points_season=float(getattr(team, "points_for", 0) or 0),
            cumulative_points=round(cumulative_points[team_id], 2),
            weekly_points=round(score, 2),
            plus_minus=round(plus_minus, 2),
            is_playoff=is_playoff,
            season_phase=season_phase,
        )
    )
    return owner, team_id


def import_espn_draft(session: Session, year: int) -> dict:
    from espn_api.football import League

    settings = get_settings()
    league = League(
        league_id=settings.league_id,
        year=year,
        espn_s2=settings.espn_s2,
        swid=settings.espn_swid,
    )
    session.execute(delete(DraftPick).where(DraftPick.league_id == settings.league_id, DraftPick.year == year))
    if year < 2019:
        for position_drafted, pick in enumerate(league.draft, start=1):
            team = pick.team
            bid_amount = float(getattr(pick, "bid_amount", 0) or 0)
            session.add(
                DraftPick(
                    league_id=settings.league_id,
                    year=year,
                    team_id=int(team.team_id),
                    owner=_owner_name(team),
                    division=getattr(team, "division_name", None),
                    player_id=int(pick.playerId),
                    player_name=str(pick.playerName),
                    pro_team=None,
                    position=None,
                    total_points=0,
                    round_drafted=int(pick.round_num),
                    round_pick=int(pick.round_pick),
                    position_drafted=position_drafted,
                    bid_amount=bid_amount,
                    dollar_value=None,
                    source="espn-api-draft-board",
                )
            )
        session.commit()
        return {"year": year, "draft_picks": len(league.draft), "source": "espn-api-draft-board"}

    player_cache = {}
    for position_drafted, pick in enumerate(league.draft, start=1):
        team = pick.team
        player = player_cache.get(pick.playerId)
        if player is None:
            try:
                player = league.player_info(playerId=pick.playerId)
            except Exception:
                player = None
            player_cache[pick.playerId] = player
        total_points = float(getattr(player, "total_points", 0) or 0)
        bid_amount = float(getattr(pick, "bid_amount", 0) or 0)
        session.add(
            DraftPick(
                league_id=settings.league_id,
                year=year,
                team_id=int(team.team_id),
                owner=_owner_name(team),
                division=getattr(team, "division_name", None),
                player_id=int(pick.playerId),
                player_name=str(pick.playerName),
                pro_team=str(getattr(player, "proTeam", "") or "") or None,
                position=str(getattr(player, "position", "") or "") or None,
                total_points=round(total_points, 2),
                round_drafted=int(pick.round_num),
                round_pick=int(pick.round_pick),
                position_drafted=position_drafted,
                bid_amount=bid_amount,
                dollar_value=round(total_points / bid_amount, 2) if bid_amount else None,
                source="espn-api",
            )
        )
    session.commit()
    return {"year": year, "draft_picks": len(league.draft), "source": "espn-api"}


def _delete_existing(session: Session, league_id: int, year: int) -> None:
    for model in [SidePointAward, LineupEntry, WeeklyTeamResult, TeamSeason, Season]:
        session.execute(delete(model).where(model.league_id == league_id, model.year == year))


def _owner_name(team) -> str:
    owner = getattr(team, "owner", None)
    if owner:
        return str(owner)
    owners = getattr(team, "owners", None) or []
    if owners:
        primary = owners[0]
        first = primary.get("firstName") or ""
        last = primary.get("lastName") or ""
        full_name = f"{first} {last}".strip()
        if full_name:
            return full_name
        if primary.get("displayName"):
            return str(primary["displayName"])
    return str(getattr(team, "team_name", "Unknown"))


def _lineup_entries(league_id: int, year: int, week: int, team_id: int, owner: str, lineup: list) -> list[LineupEntry]:
    counters: defaultdict[str, int] = defaultdict(int)
    entries: list[LineupEntry] = []
    for player in lineup:
        raw_slot = str(getattr(player, "slot_position", "") or "")
        if raw_slot in {"IR"}:
            continue
        slot_key = _slot_key(raw_slot, counters)
        if not slot_key:
            continue
        entries.append(
            LineupEntry(
                league_id=league_id,
                year=year,
                week=week,
                team_id=team_id,
                owner=owner,
                slot_key=slot_key,
                player_name=str(getattr(player, "name", "empty") or "empty"),
                player_position=str(getattr(player, "position", "") or raw_slot or ""),
                points=float(getattr(player, "points", 0) or 0),
            )
        )
    return entries


def _slot_key(raw_slot: str, counters: defaultdict[str, int]) -> str | None:
    if raw_slot in STARTER_BASE_SLOTS:
        return raw_slot
    if raw_slot in {"RB", "WR", "BE"}:
        counters[raw_slot] += 1
        return f"{raw_slot}{counters[raw_slot]}"
    return raw_slot or None
