from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Poll, PollOption, PollVote, WeeklyTeamResult


def owner_name(team) -> str:
    owner = getattr(team, "owner", None)
    if owner:
        return str(owner)
    owners = getattr(team, "owners", None) or []
    if owners:
        primary = owners[0]
        full_name = f"{primary.get('firstName') or ''} {primary.get('lastName') or ''}".strip()
        return full_name or str(primary.get("displayName") or getattr(team, "team_name", "Unknown"))
    return str(getattr(team, "team_name", "Unknown"))


def current_season_payload(session: Session, year: int | None = None) -> dict:
    from espn_api.football import League

    settings = get_settings()
    year = year or datetime.now().year
    league = League(league_id=settings.league_id, year=year, espn_s2=settings.espn_s2, swid=settings.espn_swid)
    current_week = int(getattr(league, "current_week", 0) or 0)
    display_week = max(1, current_week)
    draft_picks = len(getattr(league, "draft", []) or [])
    phase = "pre_draft" if draft_picks == 0 else "preseason" if current_week == 0 else "in_season"
    teams = [_team_row(team) for team in league.teams]
    matchups = _matchup_rows(league, display_week)
    return {
        "league_id": settings.league_id,
        "year": year,
        "league_name": league.settings.name,
        "phase": phase,
        "current_week": current_week,
        "display_week": display_week,
        "nfl_week": int(getattr(league, "nfl_week", 0) or 0),
        "regular_season_weeks": int(getattr(league.settings, "reg_season_count", 0) or 0),
        "final_scoring_period": int(getattr(league, "finalScoringPeriod", 0) or 0),
        "draft": {
            "completed": draft_picks > 0,
            "picks": draft_picks,
            "teams": len(teams),
        },
        "teams": teams,
        "matchups": matchups,
        "gotw": _gotw_candidates(session, year, display_week, matchups),
        "polls": poll_payloads(session, settings.league_id, year),
    }


def ensure_default_polls(session: Session, league_id: int, year: int, matchups: list[dict]) -> None:
    _dedupe_active_polls(session, league_id, year)

    week = int(matchups[0]["week"]) if matchups else 1
    gotw_question = f"Week {week} Game of the Week?"
    gotw_labels = [_matchup_label(matchup) for matchup in matchups]
    gotw_labels = [label for label in gotw_labels if label][:6]

    _archive_stale_gotw_polls(session, league_id, year, gotw_question)
    if gotw_labels:
        _ensure_poll(session, league_id, year, gotw_question, gotw_labels, sync_options=True)
    _ensure_poll(
        session,
        league_id,
        year,
        "Draft night headline?",
        ["Chaos pick", "Massive overpay", "Perfect value", "Trade rumor"],
    )
    session.commit()


def _dedupe_active_polls(session: Session, league_id: int, year: int) -> None:
    polls = session.scalars(
        select(Poll).where(Poll.league_id == league_id, Poll.year == year, Poll.status == "active").order_by(Poll.created_at, Poll.id)
    ).all()
    seen = set()
    duplicate_ids = []
    for poll in polls:
        if poll.question in seen:
            duplicate_ids.append(poll.id)
        else:
            seen.add(poll.question)
    if not duplicate_ids:
        return
    session.execute(delete(PollVote).where(PollVote.poll_id.in_(duplicate_ids)))
    session.execute(delete(PollOption).where(PollOption.poll_id.in_(duplicate_ids)))
    session.execute(delete(Poll).where(Poll.id.in_(duplicate_ids)))
    session.commit()


def poll_payloads(session: Session, league_id: int, year: int) -> list[dict]:
    polls = session.scalars(
        select(Poll).where(Poll.league_id == league_id, Poll.year == year, Poll.status == "active").order_by(Poll.created_at)
    ).all()
    payloads = []
    for poll in polls:
        options = session.scalars(select(PollOption).where(PollOption.poll_id == poll.id).order_by(PollOption.sort_order)).all()
        vote_counts = dict(
            session.execute(
                select(PollVote.option_id, func.count(PollVote.id)).where(PollVote.poll_id == poll.id).group_by(PollVote.option_id)
            ).all()
        )
        total_votes = sum(vote_counts.values())
        payloads.append(
            {
                "id": poll.id,
                "question": poll.question,
                "total_votes": total_votes,
                "options": [
                    {
                        "id": option.id,
                        "label": option.label,
                        "votes": int(vote_counts.get(option.id, 0)),
                    }
                    for option in options
                ],
            }
        )
    return payloads


def _ensure_poll(session: Session, league_id: int, year: int, question: str, labels: list[str], sync_options: bool = False) -> None:
    poll = session.scalar(
        select(Poll).where(Poll.league_id == league_id, Poll.year == year, Poll.question == question, Poll.status == "active")
    )
    if not poll:
        poll = Poll(league_id=league_id, year=year, question=question, status="active")
        session.add(poll)
        session.flush()

    if sync_options:
        _sync_poll_options(session, poll.id, labels)
        return

    existing_options = session.scalars(select(PollOption).where(PollOption.poll_id == poll.id)).all()
    if existing_options:
        return
    for index, label in enumerate(labels):
        session.add(PollOption(poll_id=poll.id, label=label, sort_order=index))


def _sync_poll_options(session: Session, poll_id: int, labels: list[str]) -> None:
    options = session.scalars(select(PollOption).where(PollOption.poll_id == poll_id)).all()
    options_by_label = {option.label: option for option in options}
    labels_by_order = dict.fromkeys(labels)

    for option in options:
        if option.label not in labels_by_order:
            session.execute(delete(PollVote).where(PollVote.option_id == option.id))
            session.execute(delete(PollOption).where(PollOption.id == option.id))

    for index, label in enumerate(labels):
        option = options_by_label.get(label)
        if option:
            option.sort_order = index
        else:
            session.add(PollOption(poll_id=poll_id, label=label, sort_order=index))


def _archive_stale_gotw_polls(session: Session, league_id: int, year: int, current_question: str) -> None:
    polls = session.scalars(
        select(Poll).where(Poll.league_id == league_id, Poll.year == year, Poll.status == "active")
    ).all()
    for poll in polls:
        is_gotw = poll.question == "Game of the Week?" or poll.question.endswith(" Game of the Week?")
        if is_gotw and poll.question != current_question:
            poll.status = "archived"


def _matchup_label(matchup: dict) -> str:
    home = matchup.get("home") or {}
    away = matchup.get("away") or {}
    home_name = home.get("team_name") or home.get("owner")
    away_name = away.get("team_name") or away.get("owner")
    if not home_name or not away_name:
        return ""
    return f"{home_name} vs {away_name}"


def _team_row(team) -> dict:
    return {
        "team_id": int(team.team_id),
        "owner": owner_name(team),
        "team_name": str(team.team_name),
        "division": getattr(team, "division_name", None),
        "wins": int(getattr(team, "wins", 0) or 0),
        "losses": int(getattr(team, "losses", 0) or 0),
        "ties": int(getattr(team, "ties", 0) or 0),
        "points_for": float(getattr(team, "points_for", 0) or 0),
    }


def _matchup_rows(league, week: int) -> list[dict]:
    try:
        scoreboard = league.scoreboard(week)
    except Exception:
        return []
    rows = []
    for index, matchup in enumerate(scoreboard):
        home = getattr(matchup, "home_team", None)
        away = getattr(matchup, "away_team", None)
        rows.append(
            {
                "matchup_id": index,
                "week": week,
                "home": _team_row(home) if home else None,
                "away": _team_row(away) if away else None,
                "home_score": float(getattr(matchup, "home_score", 0) or 0),
                "away_score": float(getattr(matchup, "away_score", 0) or 0),
            }
        )
    return rows


def _gotw_candidates(session: Session, year: int, week: int, matchups: list[dict]) -> list[dict]:
    previous_year = year - 1
    previous_rows = session.scalars(select(WeeklyTeamResult).where(WeeklyTeamResult.year == previous_year, WeeklyTeamResult.is_playoff == False)).all()
    strength = {}
    for row in previous_rows:
        item = strength.setdefault(row.team_id, {"points": 0.0, "wins": 0, "games": 0})
        item["points"] += row.weekly_points
        item["wins"] = max(item["wins"], row.wins)
        item["games"] += 1
    candidates = []
    for matchup in matchups:
        home = matchup.get("home") or {}
        away = matchup.get("away") or {}
        home_strength = strength.get(home.get("team_id"), {})
        away_strength = strength.get(away.get("team_id"), {})
        score = float(home_strength.get("points", 0)) + float(away_strength.get("points", 0))
        same_division = home.get("division") and home.get("division") == away.get("division")
        if same_division:
            score += 100
        candidates.append(
            {
                **matchup,
                "gotw_score": round(score, 2),
                "reason": "Division heat" if same_division else "Highest combined 2025 scoring profile",
            }
        )
    return sorted(candidates, key=lambda item: item["gotw_score"], reverse=True)[:3]
