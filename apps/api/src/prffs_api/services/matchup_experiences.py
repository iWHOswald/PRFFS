from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import (
    DraftPick,
    LeagueContext,
    MatchupContext,
    OwnerContext,
    WeeklyContext,
    WeeklyTeamResult,
)
from .current_season import current_season_payload


DEFAULT_TONE = (
    "Sharp, funny, league-specific, and direct. Avoid generic sports cliches, fake broadcast hype, "
    "and corny rivalry language. Use stats as receipts, but let human context shape the voice."
)


def admin_context_payload(session: Session, year: int, week: int) -> dict:
    settings = get_settings()
    current = current_season_payload(session, year)
    league_context = _league_context(session, settings.league_id, year)
    weekly_context = _weekly_context(session, settings.league_id, year, week)
    owner_contexts = {
        row.owner: row
        for row in session.scalars(
            select(OwnerContext).where(OwnerContext.league_id == settings.league_id, OwnerContext.year == year)
        ).all()
    }
    matchup_contexts = {
        row.matchup_id: row
        for row in session.scalars(
            select(MatchupContext).where(
                MatchupContext.league_id == settings.league_id,
                MatchupContext.year == year,
                MatchupContext.week == week,
            )
        ).all()
    }

    return {
        "year": year,
        "week": week,
        "league_context": _league_context_row(league_context),
        "weekly_context": _weekly_context_row(weekly_context),
        "owner_contexts": [
            _owner_context_row(owner_contexts.get(team["owner"]), team)
            for team in sorted(current["teams"], key=lambda item: item["owner"])
        ],
        "matchup_contexts": [
            _matchup_context_row(matchup_contexts.get(matchup["matchup_id"]), matchup)
            for matchup in _week_matchups(current, week)
        ],
    }


def save_admin_context(session: Session, year: int, week: int, payload: dict) -> dict:
    settings = get_settings()
    league_payload = payload.get("league_context") or {}
    league_context = _league_context(session, settings.league_id, year)
    league_context.tone_guide = _clean_text(league_payload.get("tone_guide")) or DEFAULT_TONE
    league_context.public_notes = _clean_text(league_payload.get("public_notes"))
    league_context.background_notes = _clean_text(league_payload.get("background_notes"))
    league_context.off_limits = _clean_text(league_payload.get("off_limits"))

    weekly_payload = payload.get("weekly_context") or {}
    weekly_context = _weekly_context(session, settings.league_id, year, week)
    weekly_context.public_notes = _clean_text(weekly_payload.get("public_notes"))
    weekly_context.background_notes = _clean_text(weekly_payload.get("background_notes"))
    weekly_context.off_limits = _clean_text(weekly_payload.get("off_limits"))

    for row in payload.get("owner_contexts") or []:
        owner = _clean_text(row.get("owner"))
        if not owner:
            continue
        context = _owner_context(session, settings.league_id, year, owner)
        context.nickname = _clean_text(row.get("nickname"))
        context.roast_level = _clean_text(row.get("roast_level")) or "medium"
        context.political_affiliation = _clean_text(row.get("political_affiliation")) or "unassigned"
        context.veto_hunter = _clean_text(row.get("veto_hunter")) or "unknown"
        context.rival_owner = _clean_text(row.get("rival_owner"))
        context.public_notes = _clean_text(row.get("public_notes"))
        context.background_notes = _clean_text(row.get("background_notes"))
        context.off_limits = _clean_text(row.get("off_limits"))

    for row in payload.get("matchup_contexts") or []:
        matchup_id = row.get("matchup_id")
        if matchup_id is None:
            continue
        context = _matchup_context(session, settings.league_id, year, week, int(matchup_id))
        context.public_notes = _clean_text(row.get("public_notes"))
        context.background_notes = _clean_text(row.get("background_notes"))
        context.off_limits = _clean_text(row.get("off_limits"))

    session.commit()
    return admin_context_payload(session, year, week)


def matchup_briefs(session: Session, year: int, week: int) -> list[dict]:
    current = current_season_payload(session, year)
    return [matchup_brief(session, year, week, matchup["matchup_id"]) for matchup in _week_matchups(current, week)]


def matchup_brief(session: Session, year: int, week: int, matchup_id: int) -> dict:
    current = current_season_payload(session, year)
    matchups = _week_matchups(current, week)
    matchup = next((item for item in matchups if item["matchup_id"] == matchup_id), None)
    if not matchup:
        raise ValueError("Matchup not found")

    home = matchup.get("home") or {}
    away = matchup.get("away") or {}
    home_summary = _historical_owner_summary(session, home.get("owner"), year)
    away_summary = _historical_owner_summary(session, away.get("owner"), year)
    home_draft = _draft_highlights(session, home.get("owner"), year - 1)
    away_draft = _draft_highlights(session, away.get("owner"), year - 1)

    return {
        "year": year,
        "week": week,
        "matchup_id": matchup_id,
        "label": _matchup_label(matchup),
        "home": home,
        "away": away,
        "score": {"home": matchup.get("home_score", 0), "away": matchup.get("away_score", 0)},
        "signals": {
            "combined_previous_average": round(home_summary["average"] + away_summary["average"], 2),
            "combined_high_score": round(home_summary["high_score"] + away_summary["high_score"], 2),
            "same_division": bool(home.get("division") and home.get("division") == away.get("division")),
        },
        "history": {
            "home": home_summary,
            "away": away_summary,
        },
        "draft": {
            "home": home_draft,
            "away": away_draft,
        },
    }


def _league_context(session: Session, league_id: int, year: int) -> LeagueContext:
    row = session.scalar(select(LeagueContext).where(LeagueContext.league_id == league_id, LeagueContext.year == year))
    if row:
        return row
    row = LeagueContext(league_id=league_id, year=year, tone_guide=DEFAULT_TONE)
    session.add(row)
    session.flush()
    return row


def _owner_context(session: Session, league_id: int, year: int, owner: str) -> OwnerContext:
    row = session.scalar(
        select(OwnerContext).where(OwnerContext.league_id == league_id, OwnerContext.year == year, OwnerContext.owner == owner)
    )
    if row:
        return row
    row = OwnerContext(league_id=league_id, year=year, owner=owner)
    session.add(row)
    session.flush()
    return row


def _weekly_context(session: Session, league_id: int, year: int, week: int) -> WeeklyContext:
    row = session.scalar(
        select(WeeklyContext).where(WeeklyContext.league_id == league_id, WeeklyContext.year == year, WeeklyContext.week == week)
    )
    if row:
        return row
    row = WeeklyContext(league_id=league_id, year=year, week=week)
    session.add(row)
    session.flush()
    return row


def _matchup_context(session: Session, league_id: int, year: int, week: int, matchup_id: int) -> MatchupContext:
    row = session.scalar(
        select(MatchupContext).where(
            MatchupContext.league_id == league_id,
            MatchupContext.year == year,
            MatchupContext.week == week,
            MatchupContext.matchup_id == matchup_id,
        )
    )
    if row:
        return row
    row = MatchupContext(league_id=league_id, year=year, week=week, matchup_id=matchup_id)
    session.add(row)
    session.flush()
    return row


def _league_context_row(row: LeagueContext) -> dict:
    return {
        "tone_guide": row.tone_guide or DEFAULT_TONE,
        "public_notes": row.public_notes or "",
        "background_notes": row.background_notes or "",
        "off_limits": row.off_limits or "",
    }


def _owner_context_row(row: OwnerContext | None, team: dict) -> dict:
    return {
        "owner": team.get("owner") or (row.owner if row else ""),
        "team_name": team.get("team_name", ""),
        "nickname": row.nickname if row else "",
        "roast_level": row.roast_level if row else "medium",
        "political_affiliation": row.political_affiliation if row else "unassigned",
        "veto_hunter": row.veto_hunter if row else "unknown",
        "rival_owner": row.rival_owner if row else "",
        "public_notes": row.public_notes if row else "",
        "background_notes": row.background_notes if row else "",
        "off_limits": row.off_limits if row else "",
    }


def _weekly_context_row(row: WeeklyContext) -> dict:
    return {
        "public_notes": row.public_notes or "",
        "background_notes": row.background_notes or "",
        "off_limits": row.off_limits or "",
    }


def _matchup_context_row(row: MatchupContext | None, matchup: dict) -> dict:
    return {
        "matchup_id": matchup.get("matchup_id", row.matchup_id if row else 0),
        "label": matchup.get("label") or _matchup_label(matchup),
        "public_notes": row.public_notes if row else "",
        "background_notes": row.background_notes if row else "",
        "off_limits": row.off_limits if row else "",
    }


def _week_matchups(current: dict, week: int) -> list[dict]:
    if week == current["display_week"]:
        return current["matchups"]
    from espn_api.football import League

    settings = get_settings()
    league = League(league_id=settings.league_id, year=current["year"], espn_s2=settings.espn_s2, swid=settings.espn_swid)
    from .current_season import _matchup_rows

    return _matchup_rows(league, week)


def _historical_owner_summary(session: Session, owner: str | None, year: int) -> dict:
    if not owner:
        return {"owner": "", "games": 0, "wins": 0, "losses": 0, "ties": 0, "points": 0.0, "average": 0.0, "high_score": 0.0}
    rows = session.scalars(
        select(WeeklyTeamResult).where(
            WeeklyTeamResult.owner == owner,
            WeeklyTeamResult.year < year,
            WeeklyTeamResult.is_playoff == False,
        )
    ).all()
    games = len(rows)
    points = sum(row.weekly_points for row in rows)
    wins = sum(1 for row in rows if row.plus_minus > 0)
    losses = sum(1 for row in rows if row.plus_minus < 0)
    ties = games - wins - losses
    high_score = max((row.weekly_points for row in rows), default=0.0)
    return {
        "owner": owner,
        "games": games,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "points": round(points, 2),
        "average": round(points / games, 2) if games else 0.0,
        "high_score": round(high_score, 2),
    }


def _draft_highlights(session: Session, owner: str | None, year: int) -> list[dict]:
    if not owner:
        return []
    rows = session.scalars(
        select(DraftPick)
        .where(DraftPick.owner == owner, DraftPick.year == year)
        .order_by(desc(DraftPick.bid_amount), DraftPick.position_drafted)
        .limit(3)
    ).all()
    return [
        {
            "player_name": row.player_name,
            "position": row.position,
            "pro_team": row.pro_team,
            "bid_amount": row.bid_amount,
            "total_points": row.total_points,
        }
        for row in rows
    ]


def _matchup_label(matchup: dict) -> str:
    home = matchup.get("home") or {}
    away = matchup.get("away") or {}
    home_name = home.get("team_name") or home.get("owner") or "TBD"
    away_name = away.get("team_name") or away.get("owner") or "TBD"
    return f"{home_name} vs {away_name}"


def _clean_text(value) -> str:
    return str(value or "").strip()
