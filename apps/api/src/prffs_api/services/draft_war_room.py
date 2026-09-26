from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher

import requests
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import DraftPick
from .current_season import owner_name


AUCTION_BUDGET = 200
ROSTER_SIZE = 15
CORE_SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "D/ST": 1, "HC": 1}
FLEX_POSITIONS = {"RB", "WR", "TE"}


def live_draft_payload(session: Session, year: int = 2026, my_team_id: int = 1, poll_espn: bool = True) -> dict:
    settings = get_settings()
    poll_status = {"ok": False, "source": "local", "message": "ESPN polling skipped", "espn_pick_count": None, "new_picks": 0}
    teams = _current_teams(year)
    if poll_espn:
        poll_status = _sync_espn_draft(session, year, teams)

    picks = session.scalars(
        select(DraftPick)
        .where(DraftPick.league_id == settings.league_id, DraftPick.year == year)
        .order_by(DraftPick.position_drafted)
    ).all()
    team_rows = _team_summaries(teams, picks, my_team_id)
    my_team = next((team for team in team_rows if team["team_id"] == my_team_id), team_rows[0] if team_rows else None)
    position_market = _position_market(session, year, picks)
    return {
        "league_id": settings.league_id,
        "year": year,
        "auction_budget": AUCTION_BUDGET,
        "roster_size": ROSTER_SIZE,
        "poll_status": poll_status,
        "last_checked_at": datetime.utcnow().isoformat(),
        "draft": {
            "picks": len(picks),
            "target_picks": len(teams) * ROSTER_SIZE if teams else 0,
            "complete": bool(teams) and len(picks) >= len(teams) * ROSTER_SIZE,
        },
        "my_team": my_team,
        "advice": _advice(my_team, position_market, picks),
        "teams": team_rows,
        "recent_picks": [_pick_row(pick) for pick in picks[-18:]][::-1],
        "position_market": position_market,
    }


def add_manual_pick(session: Session, payload: dict, year: int = 2026) -> dict:
    settings = get_settings()
    teams = _current_teams(year)
    team = _match_team(teams, payload.get("owner") or payload.get("team_name") or "")
    position_drafted = int(payload.get("position_drafted") or 0)
    if position_drafted <= 0:
        position_drafted = int(
            session.scalar(
                select(func.max(DraftPick.position_drafted)).where(DraftPick.league_id == settings.league_id, DraftPick.year == year)
            )
            or 0
        ) + 1
    pick = _upsert_pick(
        session,
        year=year,
        position_drafted=position_drafted,
        team_id=int(team["team_id"] if team else payload.get("team_id") or 0),
        owner=str(team["owner"] if team else payload.get("owner") or "Unknown"),
        team_name=str(team["team_name"] if team else payload.get("team_name") or payload.get("owner") or "Unknown"),
        division=team.get("division") if team else None,
        player_id=payload.get("player_id"),
        player_name=str(payload.get("player_name") or "").strip(),
        position=(str(payload.get("position") or "").strip().upper() or None),
        pro_team=(str(payload.get("pro_team") or "").strip().upper() or None),
        bid_amount=float(payload.get("bid_amount") or 0),
        round_drafted=int(payload.get("round_drafted") or 0),
        round_pick=int(payload.get("round_pick") or 0),
        source="manual-live",
    )
    session.commit()
    return _pick_row(pick)


def _sync_espn_draft(session: Session, year: int, teams: list[dict]) -> dict:
    from espn_api.football import League

    settings = get_settings()
    low_level = _draft_detail_view(year)
    try:
        league = League(league_id=settings.league_id, year=year, espn_s2=settings.espn_s2, swid=settings.espn_swid)
        draft = list(getattr(league, "draft", []) or [])
    except Exception as exc:
        if not low_level["ok"]:
            return {"ok": False, "source": "espn", "message": str(exc), "espn_pick_count": None, "new_picks": 0}
        league = None
        draft = []

    player_cache = {}
    existing_count = int(
        session.scalar(select(func.count(DraftPick.id)).where(DraftPick.league_id == settings.league_id, DraftPick.year == year)) or 0
    )
    completed_low_level = low_level.get("completed_picks", []) if low_level["ok"] else []
    for raw_pick in completed_low_level:
        player_id = int(raw_pick.get("playerId") or 0) or None
        player = _player_info(league, player_cache, player_id)
        team_id = int(raw_pick.get("teamId") or 0)
        matched = next((team for team in teams if int(team["team_id"]) == team_id), None)
        _upsert_pick(
            session,
            year=year,
            position_drafted=int(raw_pick.get("overallPickNumber") or raw_pick.get("id") or 0),
            team_id=team_id,
            owner=str(matched.get("owner") if matched else f"Team {team_id}"),
            team_name=str(matched.get("team_name") if matched else f"Team {team_id}"),
            division=matched.get("division") if matched else None,
            player_id=player_id,
            player_name=str(getattr(player, "name", "") or getattr(player, "playerName", "") or raw_pick.get("playerName") or f"Player {player_id}"),
            position=str(getattr(player, "position", "") or raw_pick.get("position") or "").upper() or None,
            pro_team=str(getattr(player, "proTeam", "") or raw_pick.get("proTeam") or "").upper() or None,
            bid_amount=float(raw_pick.get("bidAmount") or 0),
            round_drafted=int(raw_pick.get("roundId") or 0),
            round_pick=int(raw_pick.get("roundPickNumber") or 0),
            source="espn-draft-detail",
        )

    for position_drafted, pick in enumerate(draft, start=1):
        team = getattr(pick, "team", None)
        if not team:
            continue
        player_id = int(getattr(pick, "playerId", 0) or 0) or None
        player = _player_info(league, player_cache, player_id)
        matched = _match_team(teams, owner_name(team))
        team_id = int(getattr(team, "team_id", 0) or (matched.get("team_id", 0) if matched else 0))
        team_name = str(getattr(team, "team_name", "") or (matched.get("team_name", "") if matched else ""))
        _upsert_pick(
            session,
            year=year,
            position_drafted=position_drafted,
            team_id=team_id,
            owner=owner_name(team),
            team_name=team_name,
            division=getattr(team, "division_name", None) or (matched.get("division") if matched else None),
            player_id=player_id,
            player_name=str(getattr(pick, "playerName", "") or "Unknown"),
            position=str(getattr(player, "position", "") or "").upper() or None,
            pro_team=str(getattr(player, "proTeam", "") or "").upper() or None,
            bid_amount=float(getattr(pick, "bid_amount", 0) or 0),
            round_drafted=int(getattr(pick, "round_num", 0) or 0),
            round_pick=int(getattr(pick, "round_pick", 0) or 0),
            source="espn-live",
        )
    session.commit()
    current_count = int(
        session.scalar(select(func.count(DraftPick.id)).where(DraftPick.league_id == settings.league_id, DraftPick.year == year)) or 0
    )
    completed_count = max(len(draft), len(completed_low_level))
    if low_level["ok"] and low_level.get("in_progress") and completed_count == 0:
        message = "ESPN draft room is visible and in progress, but completed pick details are still hidden. Use manual entry until picks populate."
    elif low_level["ok"] and completed_count == 0:
        message = "ESPN draft board has no completed picks visible yet. Use manual entry if players are being sold in the room."
    elif completed_count:
        message = "ESPN completed picks synced."
    else:
        message = "ESPN draft board currently has 0 picks. Keep manual entry ready until the room starts publishing."
    return {
        "ok": True,
        "source": "espn",
        "message": message,
        "espn_pick_count": completed_count,
        "new_picks": max(0, current_count - existing_count),
        "in_progress": bool(low_level.get("in_progress")) if low_level["ok"] else None,
        "drafted": bool(low_level.get("drafted")) if low_level["ok"] else None,
        "draft_slots": int(low_level.get("draft_slots") or 0) if low_level["ok"] else None,
    }


def _draft_detail_view(year: int) -> dict:
    settings = get_settings()
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{settings.league_id}"
    try:
        response = requests.get(
            url,
            params={"view": "mDraftDetail"},
            cookies={"espn_s2": settings.espn_s2 or "", "SWID": settings.espn_swid or ""},
            timeout=10,
        )
        response.raise_for_status()
        detail = response.json().get("draftDetail", {})
    except Exception as exc:
        return {"ok": False, "message": str(exc), "completed_picks": []}
    picks = detail.get("picks", []) or []
    completed = [
        pick
        for pick in picks
        if int(pick.get("playerId") or -1) > 0 and int(pick.get("teamId") or -1) > 0 and float(pick.get("bidAmount") or 0) > 0
    ]
    return {
        "ok": True,
        "drafted": bool(detail.get("drafted")),
        "in_progress": bool(detail.get("inProgress")),
        "draft_slots": len(picks),
        "completed_picks": completed,
    }


def _player_info(league, player_cache: dict, player_id: int | None):
    if not league or not player_id:
        return None
    player = player_cache.get(player_id)
    if player is not None:
        return player
    try:
        player = league.player_info(playerId=player_id)
    except Exception:
        player = None
    player_cache[player_id] = player
    return player


def _upsert_pick(
    session: Session,
    *,
    year: int,
    position_drafted: int,
    team_id: int,
    owner: str,
    team_name: str,
    division: str | None,
    player_id: int | None,
    player_name: str,
    position: str | None,
    pro_team: str | None,
    bid_amount: float,
    round_drafted: int,
    round_pick: int,
    source: str,
) -> DraftPick:
    settings = get_settings()
    pick = session.scalar(
        select(DraftPick).where(
            DraftPick.league_id == settings.league_id,
            DraftPick.year == year,
            DraftPick.position_drafted == position_drafted,
        )
    )
    if not pick:
        pick = DraftPick(league_id=settings.league_id, year=year, position_drafted=position_drafted)
        session.add(pick)
    pick.team_id = team_id
    pick.owner = owner
    pick.division = division
    pick.player_id = player_id
    pick.player_name = player_name
    pick.pro_team = pro_team
    pick.position = position
    pick.total_points = 0
    pick.round_drafted = round_drafted
    pick.round_pick = round_pick
    pick.bid_amount = round(bid_amount, 2)
    pick.dollar_value = None
    pick.source = source
    # DraftPick does not store team_name, so keep owner/team mapping in response summaries.
    return pick


def _current_teams(year: int) -> list[dict]:
    from espn_api.football import League

    settings = get_settings()
    league = League(league_id=settings.league_id, year=year, espn_s2=settings.espn_s2, swid=settings.espn_swid)
    return [
        {
            "team_id": int(team.team_id),
            "owner": owner_name(team),
            "team_name": str(team.team_name),
            "division": getattr(team, "division_name", None),
        }
        for team in league.teams
    ]


def _team_summaries(teams: list[dict], picks: list[DraftPick], my_team_id: int) -> list[dict]:
    picks_by_team: dict[int, list[DraftPick]] = {}
    for pick in picks:
        picks_by_team.setdefault(pick.team_id, []).append(pick)
    rows = []
    for team in teams:
        team_picks = picks_by_team.get(int(team["team_id"]), [])
        spent = round(sum(pick.bid_amount for pick in team_picks), 2)
        picks_count = len(team_picks)
        remaining_slots = max(0, ROSTER_SIZE - picks_count)
        budget_left = round(AUCTION_BUDGET - spent, 2)
        max_bid = max(0, budget_left - max(0, remaining_slots - 1))
        position_counts = _position_counts(team_picks)
        rows.append(
            {
                **team,
                "is_me": int(team["team_id"]) == my_team_id,
                "spent": spent,
                "budget_left": budget_left,
                "picks": picks_count,
                "remaining_slots": remaining_slots,
                "max_bid": round(max_bid, 2),
                "avg_spend_per_pick": round(spent / picks_count, 1) if picks_count else 0,
                "positions": position_counts,
                "needs": _needs(position_counts, remaining_slots),
                "roster": [_pick_row(pick) for pick in team_picks],
            }
        )
    return sorted(rows, key=lambda row: (not row["is_me"], row["budget_left"]), reverse=False)


def _position_counts(picks: list[DraftPick]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for pick in picks:
        pos = _normalize_position(pick.position)
        counts[pos] = counts.get(pos, 0) + 1
    return counts


def _needs(counts: dict[str, int], remaining_slots: int) -> list[str]:
    needs = []
    required_slots = 0
    for pos, target in CORE_SLOTS.items():
        key = pos
        current = counts.get(key, 0)
        if current < target:
            missing = target - current
            required_slots += missing
            needs.append(f"{key} x{missing}")
    if not any(counts.get(pos, 0) > CORE_SLOTS.get(pos, 0) for pos in FLEX_POSITIONS) and remaining_slots > required_slots:
        needs.append("FLEX")
        required_slots += 1
    if remaining_slots > required_slots:
        needs.append(f"Bench x{remaining_slots - required_slots}")
    return needs


def _position_market(session: Session, year: int, picks: list[DraftPick]) -> list[dict]:
    current: dict[str, dict] = {}
    for pick in picks:
        pos = _normalize_position(pick.position)
        item = current.setdefault(pos, {"position": pos, "picks": 0, "spent": 0.0, "high_bid": 0.0})
        item["picks"] += 1
        item["spent"] += pick.bid_amount
        item["high_bid"] = max(item["high_bid"], pick.bid_amount)

    historical = dict(
        session.execute(
            select(DraftPick.position, func.avg(DraftPick.bid_amount))
            .where(DraftPick.year.in_([year - 1, year - 2, year - 3]), DraftPick.bid_amount > 0)
            .group_by(DraftPick.position)
        ).all()
    )
    rows = []
    for pos, item in current.items():
        hist = float(historical.get(pos, 0) or 0)
        avg = item["spent"] / item["picks"] if item["picks"] else 0
        rows.append(
            {
                "position": pos,
                "picks": item["picks"],
                "average_bid": round(avg, 1),
                "historical_average_bid": round(hist, 1),
                "inflation": round(avg - hist, 1) if hist else 0,
                "high_bid": round(item["high_bid"], 1),
            }
        )
    return sorted(rows, key=lambda row: row["picks"], reverse=True)


def _advice(my_team: dict | None, position_market: list[dict], picks: list[DraftPick]) -> dict:
    if not my_team:
        return {"headline": "No team context yet.", "bullets": []}
    bullets = [
        f"Budget left ${my_team['budget_left']:.0f}; max legal bid ${my_team['max_bid']:.0f} after reserving $1 per empty slot.",
        f"Open slots: {my_team['remaining_slots']}; needs: {', '.join(my_team['needs']) if my_team['needs'] else 'depth and upside only'}.",
    ]
    if my_team["picks"] == 0:
        headline = "Stay flexible early. You can still bid on any elite player, but avoid setting the market unless it is a clear top-tier target."
    elif my_team["budget_left"] > 150 and my_team["remaining_slots"] <= 12:
        headline = "You have room to attack. Push on scarce elite RB/WR profiles and do not get trapped waiting forever."
    elif my_team["budget_left"] < my_team["remaining_slots"] + 25:
        headline = "Shift into value mode. Preserve nominations and hunt underpriced starters or high-upside bench pieces."
    else:
        headline = "Balanced position. Be aggressive only where it fills a real need or beats the current market."
    latest = picks[-1] if picks else None
    if latest:
        pos = _normalize_position(latest.position)
        market = next((row for row in position_market if row["position"] == pos), None)
        if market and market["historical_average_bid"]:
            delta = latest.bid_amount - market["historical_average_bid"]
            label = "above" if delta > 0 else "below"
            bullets.append(f"Last pick: {latest.player_name} at ${latest.bid_amount:.0f}, ${abs(delta):.0f} {label} recent {pos} average.")
        else:
            bullets.append(f"Last pick: {latest.player_name} to {latest.owner} for ${latest.bid_amount:.0f}.")
    return {"headline": headline, "bullets": bullets}


def _pick_row(pick: DraftPick) -> dict:
    return {
        "year": pick.year,
        "team_id": pick.team_id,
        "owner": pick.owner,
        "division": pick.division,
        "player_id": pick.player_id,
        "player_name": pick.player_name,
        "pro_team": pick.pro_team,
        "position": pick.position,
        "total_points": pick.total_points,
        "round_drafted": pick.round_drafted,
        "round_pick": pick.round_pick,
        "position_drafted": pick.position_drafted,
        "bid_amount": pick.bid_amount,
        "dollar_value": pick.dollar_value,
        "source": pick.source,
    }


def _match_team(teams: list[dict], query: str) -> dict | None:
    query = query.strip().lower()
    if not query:
        return None
    best = None
    best_score = 0.0
    for team in teams:
        labels = [str(team.get("owner", "")), str(team.get("team_name", ""))]
        for label in labels:
            raw = label.lower()
            score = 1.0 if query in raw or raw in query else SequenceMatcher(None, query, raw).ratio()
            if score > best_score:
                best = team
                best_score = score
    return best if best_score >= 0.45 else None


def _normalize_position(position: str | None) -> str:
    pos = (position or "UNK").upper()
    if pos in {"DST", "DEF"}:
        return "D/ST"
    return pos
