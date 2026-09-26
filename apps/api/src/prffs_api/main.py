import math
from contextlib import asynccontextmanager
from pathlib import Path

from pydantic import BaseModel, Field
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import ROOT_DIR, get_settings
from .auth import require_admin
from .database import get_session, init_db
from .models import ChatMessage, DraftPick, LineupEntry, MediaAsset, PollOption, PollVote, ScoreSnapshot, Season, SidePointAward, WeeklyTeamResult
from .services.current_season import current_season_payload, ensure_default_polls
from .services.draft_war_room import add_manual_pick, live_draft_payload
from .services.importer import import_local_history
from .services.matchup_experiences import (
    admin_context_payload,
    matchup_briefs,
    save_admin_context,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_runtime(require_admin=True)
    if settings.initialize_database_on_startup:
        init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessageIn(BaseModel):
    author: str = Field(min_length=1, max_length=80)
    body: str = Field(min_length=1, max_length=1000)


class PollVoteIn(BaseModel):
    voter: str = Field(min_length=1, max_length=80)
    option_id: int


class ContextBlockIn(BaseModel):
    public_notes: str = ""
    background_notes: str = ""
    off_limits: str = ""


class LeagueContextIn(ContextBlockIn):
    tone_guide: str = ""


class OwnerContextIn(ContextBlockIn):
    owner: str
    nickname: str = ""
    roast_level: str = "medium"
    political_affiliation: str = "unassigned"
    veto_hunter: str = "unknown"
    rival_owner: str = ""


class MatchupContextIn(ContextBlockIn):
    matchup_id: int


class AdminContextIn(BaseModel):
    league_context: LeagueContextIn
    weekly_context: ContextBlockIn
    owner_contexts: list[OwnerContextIn] = []
    matchup_contexts: list[MatchupContextIn] = []


class ManualDraftPickIn(BaseModel):
    player_name: str = Field(min_length=1, max_length=120)
    owner: str = Field(min_length=1, max_length=120)
    bid_amount: float = Field(ge=0, le=200)
    position: str = Field(default="", max_length=16)
    pro_team: str = Field(default="", max_length=16)
    team_id: int | None = None
    player_id: int | None = None
    position_drafted: int | None = None
    round_drafted: int | None = None
    round_pick: int | None = None


@app.get("/health")
def health(session: Session = Depends(get_session)) -> dict:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"ok": True, "app": settings.app_name}


@app.get("/api/admin/session", dependencies=[Depends(require_admin)])
def admin_session() -> dict:
    return {"ok": True}


@app.get("/api/constitution/pdf")
def constitution_pdf() -> FileResponse:
    path = ROOT_DIR / "Constitution.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Constitution PDF not found")
    return FileResponse(path, media_type="application/pdf", headers={"Content-Disposition": 'inline; filename="Pork_Rub_Constitution.pdf"'})


@app.post("/api/admin/import-local", dependencies=[Depends(require_admin)])
def import_local(
    reset: bool = False,
    session: Session = Depends(get_session),
) -> dict:
    if settings.app_env == "production":
        raise HTTPException(status_code=403, detail="Local imports are disabled in production")
    return import_local_history(session, ROOT_DIR, reset=reset)


@app.get("/api/admin/context", dependencies=[Depends(require_admin)])
def admin_context(year: int = 2026, week: int = 1, session: Session = Depends(get_session)) -> dict:
    return admin_context_payload(session, year, week)


@app.post("/api/admin/context", dependencies=[Depends(require_admin)])
def update_admin_context(payload: AdminContextIn, year: int = 2026, week: int = 1, session: Session = Depends(get_session)) -> dict:
    return save_admin_context(session, year, week, payload.model_dump())


@app.get("/api/admin/matchup-briefs", dependencies=[Depends(require_admin)])
def admin_matchup_briefs(year: int = 2026, week: int = 1, session: Session = Depends(get_session)) -> list[dict]:
    try:
        return matchup_briefs(session, year, week)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/seasons")
def seasons(session: Session = Depends(get_session)) -> list[dict]:
    rows = session.scalars(select(Season).order_by(Season.year)).all()
    return [{"league_id": row.league_id, "year": row.year, "source": row.source} for row in rows]


@app.get("/api/weekly-results")
def weekly_results(
    year: int | None = None,
    week: int | None = None,
    team_id: int | None = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    stmt = select(WeeklyTeamResult)
    if year:
        stmt = stmt.where(WeeklyTeamResult.year == year)
    if week:
        stmt = stmt.where(WeeklyTeamResult.week == week)
    if team_id:
        stmt = stmt.where(WeeklyTeamResult.team_id == team_id)
    stmt = stmt.order_by(WeeklyTeamResult.year, WeeklyTeamResult.week, desc(WeeklyTeamResult.weekly_points))
    rows = session.scalars(stmt.limit(500)).all()
    return [
        {
            "league_id": row.league_id,
            "year": row.year,
            "week": row.week,
            "team_id": row.team_id,
            "owner": row.owner,
            "team_name": row.team_name,
            "matchup_id": row.matchup_id,
            "weekly_points": row.weekly_points,
            "cumulative_points": row.cumulative_points,
            "plus_minus": row.plus_minus,
            "record": row.record_label,
        }
        for row in rows
    ]


@app.get("/api/records")
def records(session: Session = Depends(get_session)) -> dict:
    most_points = session.scalars(
        select(WeeklyTeamResult).order_by(desc(WeeklyTeamResult.weekly_points)).limit(10)
    ).all()
    largest_margin = session.scalars(
        select(WeeklyTeamResult).order_by(desc(WeeklyTeamResult.plus_minus)).limit(10)
    ).all()
    side_totals = session.execute(
        select(SidePointAward.owner, func.sum(SidePointAward.points).label("points"))
        .group_by(SidePointAward.owner)
        .order_by(desc("points"))
        .limit(12)
    ).all()
    return {
        "most_points": [_record_row(row) for row in most_points],
        "largest_margin": [_record_row(row) for row in largest_margin],
        "side_point_totals": [{"owner": owner, "points": round(points or 0, 2)} for owner, points in side_totals],
    }


@app.get("/api/side-points")
def side_points(
    year: int | None = None,
    week: int | None = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    stmt = select(SidePointAward)
    if year:
        stmt = stmt.where(SidePointAward.year == year)
    if week:
        stmt = stmt.where(SidePointAward.week == week)
    stmt = stmt.order_by(SidePointAward.year, SidePointAward.week, SidePointAward.category)
    rows = session.scalars(stmt.limit(1000)).all()
    return [
        {
            "year": row.year,
            "week": row.week,
            "team_id": row.team_id,
            "owner": row.owner,
            "category": row.category,
            "points": row.points,
            "metric_name": row.metric_name,
            "metric_value": row.metric_value,
        }
        for row in rows
    ]


@app.get("/api/media")
def media_assets(
    year: int | None = None,
    media_type: str | None = Query(default=None, alias="type"),
    session: Session = Depends(get_session),
) -> list[dict]:
    stmt = select(MediaAsset)
    if year:
        stmt = stmt.where(MediaAsset.year == year)
    if media_type:
        stmt = stmt.where(MediaAsset.media_type == media_type)
    rows = session.scalars(stmt.order_by(desc(MediaAsset.year), MediaAsset.title).limit(500)).all()
    return [
        {
            "id": row.id,
            "path": row.path,
            "url": f"/media/{row.path}",
            "title": row.title,
            "type": row.media_type,
            "year": row.year,
            "week": row.week,
            "category": row.category,
        }
        for row in rows
    ]


@app.get("/api/draft/picks")
def draft_picks(
    year: int | None = None,
    owner: str | None = None,
    position: str | None = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    stmt = select(DraftPick)
    if year:
        stmt = stmt.where(DraftPick.year == year)
    if owner:
        stmt = stmt.where(DraftPick.owner == owner)
    if position:
        stmt = stmt.where(DraftPick.position == position)
    rows = session.scalars(stmt.order_by(DraftPick.year.desc(), DraftPick.position_drafted).limit(1000)).all()
    return [_draft_row(row) for row in rows]


@app.get("/api/draft/summary")
def draft_summary(year: int | None = None, session: Session = Depends(get_session)) -> dict:
    all_picks = session.scalars(select(DraftPick)).all()
    regular_rows = session.scalars(select(WeeklyTeamResult).where(WeeklyTeamResult.is_playoff == False)).all()  # noqa: E712
    years = sorted({pick.year for pick in all_picks})
    if year is None and years:
        year = years[-1]

    stmt = select(DraftPick)
    if year:
        stmt = stmt.where(DraftPick.year == year)
    picks = session.scalars(stmt).all()
    by_owner: dict[str, dict] = {}
    by_position: dict[str, dict] = {}
    for pick in picks:
        owner = by_owner.setdefault(
            pick.owner,
            {"owner": pick.owner, "spent": 0.0, "points": 0.0, "picks": 0, "value": 0.0},
        )
        owner["spent"] += pick.bid_amount
        owner["points"] += pick.total_points
        owner["picks"] += 1

        pos = pick.position or "UNK"
        position_bucket = by_position.setdefault(
            pos,
            {"position": pos, "spent": 0.0, "points": 0.0, "picks": 0, "value": 0.0},
        )
        position_bucket["spent"] += pick.bid_amount
        position_bucket["points"] += pick.total_points
        position_bucket["picks"] += 1

    for bucket in list(by_owner.values()) + list(by_position.values()):
        bucket["spent"] = round(bucket["spent"], 2)
        bucket["points"] = round(bucket["points"], 2)
        bucket["value"] = round(bucket["points"] / bucket["spent"], 2) if bucket["spent"] else 0

    top_values = sorted(
        [pick for pick in picks if pick.bid_amount > 0],
        key=lambda pick: pick.dollar_value or 0,
        reverse=True,
    )[:20]
    biggest_buys = sorted(picks, key=lambda pick: pick.bid_amount, reverse=True)[:20]
    projected_values = _draft_projected_values(picks, all_picks, year)
    strategy_profiles = _draft_strategy_profiles(picks)
    strategy_history = _draft_strategy_history(all_picks, picks)
    strategy_outcomes = _draft_strategy_outcomes(strategy_history, regular_rows)
    return {
        "years": years,
        "by_owner": sorted(by_owner.values(), key=lambda item: item["spent"], reverse=True),
        "by_position": sorted(by_position.values(), key=lambda item: item["spent"], reverse=True),
        "top_values": [_draft_row(pick) for pick in top_values],
        "biggest_buys": [_draft_row(pick) for pick in biggest_buys],
        "projected_best_values": projected_values[:20],
        "strategy_profiles": strategy_profiles,
        "strategy_history": strategy_history,
        "strategy_outcomes": strategy_outcomes,
        "spender_pca": _draft_spender_pca(picks),
    }


@app.get("/api/draft/live")
def draft_live(
    year: int = 2026,
    my_team_id: int = 1,
    poll_espn: bool = False,
    x_admin_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> dict:
    if poll_espn:
        require_admin(x_admin_token)
    return live_draft_payload(session, year=year, my_team_id=my_team_id, poll_espn=poll_espn)


@app.post("/api/draft/live/manual", dependencies=[Depends(require_admin)])
def create_manual_draft_pick(
    payload: ManualDraftPickIn,
    year: int = 2026,
    session: Session = Depends(get_session),
) -> dict:
    return add_manual_pick(session, payload.model_dump(), year=year)


@app.get("/api/history/summary")
def history_summary(session: Session = Depends(get_session)) -> dict:
    games = session.scalars(select(WeeklyTeamResult)).all()
    draft_picks = session.scalars(select(DraftPick)).all()
    side_awards = session.scalars(select(SidePointAward)).all()
    lineups = session.scalars(select(LineupEntry)).all()
    seasons = sorted({row.year for row in games})
    draft_years = sorted({row.year for row in draft_picks})
    playoff_games = [row for row in games if row.is_playoff]
    regular_games = [row for row in games if not row.is_playoff]

    regular_seasons = _season_totals(regular_games)
    all_game_owner_totals = _owner_game_totals(games)
    playoff_owner_totals = _owner_game_totals(playoff_games)
    side_totals = _side_totals(side_awards)
    game_lookup = {(row.year, row.week, row.team_id): row for row in games}
    player_records = _player_records(lineups)
    bench_records = _bench_records(lineups, game_lookup)
    playoff_justice = _playoff_justice(regular_games, playoff_games)

    return {
        "overview": {
            "season_years": seasons,
            "draft_years": draft_years,
            "team_week_rows": len(games),
            "regular_team_week_rows": len(regular_games),
            "playoff_team_week_rows": len(playoff_games),
            "draft_picks": len(draft_picks),
        },
        "game_records": {
            "highest_scores": [_record_row(row) for row in sorted(games, key=lambda row: row.weekly_points, reverse=True)[:10]],
            "lowest_scores": [_record_row(row) for row in sorted(games, key=lambda row: row.weekly_points)[:10]],
            "largest_margins": [_record_row(row) for row in sorted(games, key=lambda row: row.plus_minus, reverse=True)[:10]],
            "worst_losses": [_record_row(row) for row in sorted(games, key=lambda row: row.plus_minus)[:10]],
            "best_regular_seasons": regular_seasons[:10],
            "worst_regular_seasons": list(reversed(regular_seasons[-10:])),
            "owner_totals": all_game_owner_totals[:12],
        },
        "playoff_records": {
            "highest_scores": [_record_row(row) for row in sorted(playoff_games, key=lambda row: row.weekly_points, reverse=True)[:10]],
            "lowest_scores": [_record_row(row) for row in sorted(playoff_games, key=lambda row: row.weekly_points)[:10]],
            "largest_margins": [_record_row(row) for row in sorted(playoff_games, key=lambda row: row.plus_minus, reverse=True)[:10]],
            "owner_totals": playoff_owner_totals[:12],
        },
        "division_records": {
            "owner_totals": _division_owner_totals(games),
            "season_totals": _division_season_totals(regular_games),
        },
        "playoff_justice": playoff_justice,
        "player_records": player_records,
        "blunder_records": {
            "bench_blunders": bench_records[:20],
            "costly_bench_blunders": [row for row in bench_records if row["would_cover_loss"]][:20],
        },
        "side_point_records": {
            "owner_totals": side_totals[:12],
        },
        "draft_records": {
            "biggest_buys": [_draft_row(row) for row in sorted(draft_picks, key=lambda row: row.bid_amount, reverse=True)[:10]],
            "best_values": [
                _draft_row(row)
                for row in sorted(
                    [pick for pick in draft_picks if pick.dollar_value is not None and pick.bid_amount > 0],
                    key=lambda row: row.dollar_value or 0,
                    reverse=True,
                )[:10]
            ],
            "most_points": [_draft_row(row) for row in sorted(draft_picks, key=lambda row: row.total_points, reverse=True)[:10]],
            "owner_value": _draft_owner_totals(draft_picks)[:12],
        },
    }


@app.get("/api/current-season")
def current_season(year: int | None = None, session: Session = Depends(get_session)) -> dict:
    payload = current_season_payload(session, year)
    ensure_default_polls(
        session,
        payload["league_id"],
        payload["year"],
        payload["matchups"],
    )
    return current_season_payload(session, year)


@app.get("/api/current-season/chat")
def current_season_chat(year: int | None = None, limit: int = 50, session: Session = Depends(get_session)) -> list[dict]:
    year = year or 2026
    rows = session.scalars(
        select(ChatMessage)
        .where(ChatMessage.league_id == settings.league_id, ChatMessage.year == year)
        .order_by(ChatMessage.created_at.desc())
        .limit(min(limit, 100))
    ).all()
    return [
        {
            "id": row.id,
            "author": row.author,
            "body": row.body,
            "created_at": row.created_at.isoformat(),
        }
        for row in reversed(rows)
    ]


@app.post("/api/current-season/chat")
def create_current_season_chat(message: ChatMessageIn, year: int | None = None, session: Session = Depends(get_session)) -> dict:
    year = year or 2026
    row = ChatMessage(
        league_id=settings.league_id,
        year=year,
        author=message.author.strip(),
        body=message.body.strip(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return {"id": row.id, "author": row.author, "body": row.body, "created_at": row.created_at.isoformat()}


@app.post("/api/current-season/polls/{poll_id}/vote")
def vote_current_season_poll(poll_id: int, vote: PollVoteIn, session: Session = Depends(get_session)) -> dict:
    option = session.scalar(select(PollOption).where(PollOption.id == vote.option_id, PollOption.poll_id == poll_id))
    if not option:
        raise HTTPException(status_code=404, detail="Poll option not found")
    existing = session.scalar(select(PollVote).where(PollVote.poll_id == poll_id, PollVote.voter == vote.voter.strip()))
    if existing:
        existing.option_id = vote.option_id
    else:
        session.add(PollVote(poll_id=poll_id, option_id=vote.option_id, voter=vote.voter.strip()))
    session.commit()
    return {"ok": True}


@app.get("/api/live/snapshots")
def live_snapshots(
    year: int,
    week: int,
    session: Session = Depends(get_session),
) -> list[dict]:
    rows = session.scalars(
        select(ScoreSnapshot)
        .where(ScoreSnapshot.year == year, ScoreSnapshot.week == week)
        .order_by(ScoreSnapshot.captured_at)
        .limit(5000)
    ).all()
    return [
        {
            "captured_at": row.captured_at.isoformat(),
            "team_id": row.team_id,
            "matchup_id": row.matchup_id,
            "owner": row.owner,
            "team_name": row.team_name,
            "score": row.score,
            "projected_score": row.projected_score,
        }
        for row in rows
    ]


def _record_row(row: WeeklyTeamResult) -> dict:
    return {
        "year": row.year,
        "week": row.week,
        "season_phase": row.season_phase,
        "is_playoff": row.is_playoff,
        "team_id": row.team_id,
        "owner": row.owner,
        "team_name": row.team_name,
        "weekly_points": row.weekly_points,
        "plus_minus": row.plus_minus,
        "record": row.record_label,
    }


def _draft_row(row: DraftPick) -> dict:
    return {
        "year": row.year,
        "team_id": row.team_id,
        "owner": row.owner,
        "division": row.division,
        "player_id": row.player_id,
        "player_name": row.player_name,
        "pro_team": row.pro_team,
        "position": row.position,
        "total_points": row.total_points,
        "round_drafted": row.round_drafted,
        "round_pick": row.round_pick,
        "position_drafted": row.position_drafted,
        "bid_amount": row.bid_amount,
        "dollar_value": row.dollar_value,
        "source": row.source,
    }


def _draft_projected_values(picks: list[DraftPick], all_picks: list[DraftPick], selected_year: int | None) -> list[dict]:
    history = [pick for pick in all_picks if pick.total_points > 0 and pick.bid_amount > 0 and (selected_year is None or pick.year != selected_year)]
    fallback_points = sum(pick.total_points for pick in history) / len(history) if history else 0

    by_position: dict[str, list[DraftPick]] = {}
    by_position_tier: dict[tuple[str, str], list[DraftPick]] = {}
    for pick in history:
        position = pick.position or "UNK"
        by_position.setdefault(position, []).append(pick)
        by_position_tier.setdefault((position, _bid_tier(pick.bid_amount)), []).append(pick)

    rows: list[dict] = []
    for pick in picks:
        if pick.bid_amount <= 0:
            continue
        position = pick.position or "UNK"
        tier_rows = by_position_tier.get((position, _bid_tier(pick.bid_amount)), [])
        position_rows = by_position.get(position, [])
        source_rows = tier_rows if len(tier_rows) >= 4 else position_rows
        projected_points = sum(row.total_points for row in source_rows) / len(source_rows) if source_rows else fallback_points
        projected_value = projected_points / pick.bid_amount if pick.bid_amount else 0
        rows.append(
            {
                **_draft_row(pick),
                "projected_points": round(projected_points, 2),
                "projected_value": round(projected_value, 2),
                "projection_basis": f"{position} {_bid_tier(pick.bid_amount)}" if len(tier_rows) >= 4 else f"{position} historical average",
            }
        )
    return sorted(rows, key=lambda row: row["projected_value"], reverse=True)


def _bid_tier(bid: float) -> str:
    if bid >= 50:
        return "$50+"
    if bid >= 31:
        return "$31-49"
    if bid >= 16:
        return "$16-30"
    if bid >= 6:
        return "$6-15"
    return "$1-5"


def _draft_spender_pca(picks: list[DraftPick]) -> list[dict]:
    profiles = _draft_strategy_profiles(picks)
    if len(profiles) < 2:
        return [
            {
                "owner": item["owner"],
                "pc1": 0.0,
                "pc2": 0.0,
                "spent": round(item["spent"], 2),
                "picks": item["picks"],
                "label": item["owner"].split(" ")[0],
                "strategy_type": item["strategy_type"],
            }
            for item in profiles
        ]

    feature_names = ["top_heavy_score", "patience_score", "balance_score", "rb_share", "wr_share", "qb_share", "te_share", "one_dollar_share", "avg_bid"]
    matrix: list[list[float]] = []
    for item in profiles:
        matrix.append([float(item[name]) for name in feature_names])

    means = [sum(row[col] for row in matrix) / len(matrix) for col in range(len(feature_names))]
    centered = [[value - means[col] for col, value in enumerate(row)] for row in matrix]
    deviations = [_stddev([row[col] for row in centered]) or 1 for col in range(len(feature_names))]
    scaled = [[value / deviations[col] for col, value in enumerate(row)] for row in centered]

    covariance = _covariance_matrix(scaled)
    pc1 = _principal_vector(covariance)
    covariance_2 = _deflate(covariance, pc1)
    pc2 = _principal_vector(covariance_2)

    rows = []
    for item, vector in zip(profiles, scaled):
        x = sum(value * weight for value, weight in zip(vector, pc1))
        y = sum(value * weight for value, weight in zip(vector, pc2))
        rows.append(
            {
                "owner": item["owner"],
                "pc1": round(x, 3),
                "pc2": round(y, 3),
                "spent": round(item["spent"], 2),
                "picks": item["picks"],
                "label": item["owner"].split(" ")[0],
                "strategy_type": item["strategy_type"],
            }
        )
    return rows


def _draft_strategy_history(all_picks: list[DraftPick], selected_picks: list[DraftPick]) -> list[dict]:
    selected_owners = {pick.owner for pick in selected_picks}
    if not selected_owners:
        return []
    rows: list[dict] = []
    for year in sorted({pick.year for pick in all_picks}):
        year_picks = [pick for pick in all_picks if pick.year == year and pick.owner in selected_owners]
        rows.extend(_draft_strategy_profiles(year_picks))
    return sorted(rows, key=lambda row: (row["owner"], row["year"]))


def _draft_strategy_outcomes(strategy_rows: list[dict], regular_rows: list[WeeklyTeamResult]) -> dict:
    by_year: dict[int, list[WeeklyTeamResult]] = {}
    for row in regular_rows:
        by_year.setdefault(row.year, []).append(row)

    outcomes: dict[tuple[str, int], dict] = {}
    for year, rows in by_year.items():
        for summary in _regular_team_summaries(rows):
            if summary["games"] < 8 or summary["points"] <= 0:
                continue
            outcomes[(summary["owner"], year)] = {
                "team_name": summary["team_name"],
                "wins": summary["wins"],
                "losses": summary["losses"],
                "ties": summary["ties"],
                "win_pct": summary["win_pct"],
                "regular_points": summary["points"],
                "average": summary["average"],
                "points_rank": summary["points_rank"],
                "record_rank": summary["record_rank"],
            }

    rows = []
    for profile in strategy_rows:
        outcome = outcomes.get((profile["owner"], profile["year"]))
        rows.append({**profile, **(outcome or {})})

    completed = [row for row in rows if row.get("regular_points") is not None]
    metrics = ["top_heavy_score", "patience_score", "balance_score", "top3_share", "one_dollar_share", "late_spend_share", "rb_share", "wr_share"]
    targets = ["regular_points", "average", "win_pct", "points_rank", "record_rank"]
    correlations = []
    for metric in metrics:
        for target in targets:
            value = _pearson([float(row[metric]) for row in completed], [float(row[target]) for row in completed])
            correlations.append(
                {
                    "metric": metric,
                    "target": target,
                    "correlation": round(value, 3),
                    "n": len(completed),
                    "direction": "lower is better" if target.endswith("_rank") else "higher is better",
                }
            )

    by_type: dict[str, dict] = {}
    for row in completed:
        item = by_type.setdefault(
            row["strategy_type"],
            {"strategy_type": row["strategy_type"], "seasons": 0, "avg_points": 0.0, "avg_win_pct": 0.0, "avg_points_rank": 0.0, "avg_record_rank": 0.0},
        )
        item["seasons"] += 1
        item["avg_points"] += row["regular_points"]
        item["avg_win_pct"] += row["win_pct"]
        item["avg_points_rank"] += row["points_rank"]
        item["avg_record_rank"] += row["record_rank"]
    for item in by_type.values():
        seasons = item["seasons"] or 1
        item["avg_points"] = round(item["avg_points"] / seasons, 2)
        item["avg_win_pct"] = round(item["avg_win_pct"] / seasons, 3)
        item["avg_points_rank"] = round(item["avg_points_rank"] / seasons, 2)
        item["avg_record_rank"] = round(item["avg_record_rank"] / seasons, 2)

    return {
        "rows": sorted(rows, key=lambda row: (row["owner"], row["year"])),
        "completed_rows": sorted(completed, key=lambda row: (row["owner"], row["year"])),
        "correlations": sorted(correlations, key=lambda row: abs(row["correlation"]), reverse=True),
        "by_type": sorted(by_type.values(), key=lambda row: row["avg_points_rank"]),
    }


def _draft_strategy_profiles(picks: list[DraftPick]) -> list[dict]:
    by_owner_year: dict[tuple[str, int], list[DraftPick]] = {}
    for pick in picks:
        by_owner_year.setdefault((pick.owner, pick.year), []).append(pick)

    profiles = []
    for (owner, year), owner_picks in by_owner_year.items():
        bids = sorted([float(pick.bid_amount or 0) for pick in owner_picks], reverse=True)
        spent = sum(bids)
        picks_count = len(owner_picks)
        if not spent or not bids:
            continue
        top1_share = bids[0] / spent
        top2_share = sum(bids[:2]) / spent
        top3_share = sum(bids[:3]) / spent
        one_dollar_count = sum(1 for bid in bids if bid <= 1)
        high_bid_count = sum(1 for bid in bids if bid >= 30)
        mid_bid_count = sum(1 for bid in bids if 6 <= bid < 30)
        plus_10_count = sum(1 for bid in bids if bid >= 10)
        weighted_pick = sum((pick.position_drafted or 0) * float(pick.bid_amount or 0) for pick in owner_picks) / spent
        late_spend_share = sum(float(pick.bid_amount or 0) for pick in owner_picks if (pick.position_drafted or 0) >= 90) / spent
        first_big_pick = min([pick.position_drafted for pick in owner_picks if pick.bid_amount >= 30] or [0])
        position_spend = _position_spend(owner_picks)
        gini = _gini(bids)
        avg_bid = spent / picks_count
        median_bid = _median(bids)
        profile = {
            "year": year,
            "owner": owner,
            "label": owner.split(" ")[0],
            "spent": round(spent, 2),
            "picks": picks_count,
            "avg_bid": round(avg_bid, 2),
            "median_bid": round(median_bid, 2),
            "top1_share": round(top1_share, 3),
            "top2_share": round(top2_share, 3),
            "top3_share": round(top3_share, 3),
            "gini": round(gini, 3),
            "one_dollar_count": one_dollar_count,
            "one_dollar_share": round(one_dollar_count / picks_count, 3),
            "high_bid_count": high_bid_count,
            "high_bid_share": round(high_bid_count / picks_count, 3),
            "mid_bid_count": mid_bid_count,
            "plus_10_count": plus_10_count,
            "weighted_pick": round(weighted_pick, 2),
            "late_spend_share": round(late_spend_share, 3),
            "first_big_pick": first_big_pick,
            "qb_share": round(position_spend.get("QB", 0) / spent, 3),
            "rb_share": round(position_spend.get("RB", 0) / spent, 3),
            "wr_share": round(position_spend.get("WR", 0) / spent, 3),
            "te_share": round(position_spend.get("TE", 0) / spent, 3),
            "top_heavy_score": 0.0,
            "patience_score": 0.0,
            "balance_score": 0.0,
        }
        profiles.append(profile)
    _score_strategy_profiles(profiles)
    return sorted(profiles, key=lambda item: (-item["top_heavy_score"], -item["spent"]))


def _score_strategy_profiles(profiles: list[dict]) -> None:
    def norm(key: str, invert: bool = False) -> list[float]:
        values = [float(profile[key]) for profile in profiles]
        low = min(values) if values else 0
        high = max(values) if values else 0
        scores = []
        for profile in profiles:
            value = 50.0 if high == low else ((float(profile[key]) - low) / (high - low)) * 100
            scores.append(100 - value if invert else value)
        return scores

    top3 = norm("top3_share")
    gini = norm("gini")
    high_bid = norm("high_bid_share")
    one_dollar = norm("one_dollar_share")
    weighted_pick = norm("weighted_pick")
    late_spend = norm("late_spend_share")
    mid_bid = norm("mid_bid_count")
    plus_10 = norm("plus_10_count")
    balanced_gini = norm("gini", invert=True)
    fewer_one_dollar = norm("one_dollar_share", invert=True)

    for index, profile in enumerate(profiles):
        profile["top_heavy_score"] = round(_clamp100(top3[index] * 0.42 + gini[index] * 0.3 + high_bid[index] * 0.16 + one_dollar[index] * 0.12), 1)
        profile["patience_score"] = round(_clamp100(weighted_pick[index] * 0.66 + late_spend[index] * 0.34), 1)
        profile["balance_score"] = round(_clamp100(balanced_gini[index] * 0.42 + mid_bid[index] * 0.25 + plus_10[index] * 0.18 + fewer_one_dollar[index] * 0.15), 1)
        profile["strategy_type"] = _strategy_type(profile)


def _position_spend(picks: list[DraftPick]) -> dict[str, float]:
    aliases = {"D/ST": "DST", "D": "DST", "DEF": "DST"}
    totals: dict[str, float] = {}
    for pick in picks:
        position = aliases.get((pick.position or "UNK").upper(), (pick.position or "UNK").upper())
        totals[position] = totals.get(position, 0.0) + float(pick.bid_amount or 0)
    return totals


def _strategy_type(profile: dict) -> str:
    top_heavy = profile["top_heavy_score"]
    patience = profile["patience_score"]
    balance = profile["balance_score"]
    if top_heavy >= 72 and balance < 56:
        return "Boom or Bust"
    if patience >= 58 and balance >= 54:
        return "Wait and See"
    if balance >= 68 and top_heavy < 68:
        return "Balanced Builder"
    if profile["rb_share"] >= 0.44:
        return "RB Aggressor"
    if profile["wr_share"] >= 0.48:
        return "WR Heavy"
    if top_heavy >= 62:
        return "Star Lean"
    return "Hybrid"


def _gini(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    total = sum(sorted_values)
    if total == 0:
        return 0.0
    n = len(sorted_values)
    weighted = sum((index + 1) * value for index, value in enumerate(sorted_values))
    return (2 * weighted) / (n * total) - (n + 1) / n


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, value))


def _stddev(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 3 or len(xs) != len(ys):
        return 0.0
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_denominator = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    if not x_denominator or not y_denominator:
        return 0.0
    return numerator / (x_denominator * y_denominator)


def _covariance_matrix(rows: list[list[float]]) -> list[list[float]]:
    if not rows:
        return []
    cols = len(rows[0])
    denominator = max(1, len(rows) - 1)
    return [[sum(row[i] * row[j] for row in rows) / denominator for j in range(cols)] for i in range(cols)]


def _principal_vector(matrix: list[list[float]], iterations: int = 60) -> list[float]:
    if not matrix:
        return []
    vector = [1 / math.sqrt(len(matrix)) for _ in matrix]
    for _ in range(iterations):
        next_vector = [sum(row[col] * vector[col] for col in range(len(vector))) for row in matrix]
        length = math.sqrt(sum(value * value for value in next_vector))
        if length == 0:
            return vector
        vector = [value / length for value in next_vector]
    return vector


def _deflate(matrix: list[list[float]], vector: list[float]) -> list[list[float]]:
    if not matrix or not vector:
        return matrix
    eigenvalue = sum(vector[i] * sum(matrix[i][j] * vector[j] for j in range(len(vector))) for i in range(len(vector)))
    return [[matrix[i][j] - eigenvalue * vector[i] * vector[j] for j in range(len(vector))] for i in range(len(vector))]


def _season_totals(rows: list[WeeklyTeamResult]) -> list[dict]:
    totals: dict[tuple[int, int], dict] = {}
    for row in rows:
        key = (row.year, row.team_id)
        item = totals.setdefault(
            key,
            {
                "year": row.year,
                "team_id": row.team_id,
                "owner": row.owner,
                "team_name": row.team_name,
                "points": 0.0,
                "games": 0,
                "average": 0.0,
                "wins": row.wins,
                "losses": row.losses,
                "ties": row.ties,
            },
        )
        item["points"] += row.weekly_points
        item["games"] += 1
        item["wins"] = max(item["wins"], row.wins)
        item["losses"] = max(item["losses"], row.losses)
        item["ties"] = max(item["ties"], row.ties)
    for item in totals.values():
        item["points"] = round(item["points"], 2)
        item["average"] = round(item["points"] / item["games"], 2) if item["games"] else 0
    return sorted(totals.values(), key=lambda item: item["points"], reverse=True)


def _owner_game_totals(rows: list[WeeklyTeamResult]) -> list[dict]:
    totals: dict[str, dict] = {}
    for row in rows:
        item = totals.setdefault(row.owner, {"owner": row.owner, "points": 0.0, "games": 0, "average": 0.0, "high_score": 0.0})
        item["points"] += row.weekly_points
        item["games"] += 1
        item["high_score"] = max(item["high_score"], row.weekly_points)
    for item in totals.values():
        item["points"] = round(item["points"], 2)
        item["average"] = round(item["points"] / item["games"], 2) if item["games"] else 0
    return sorted(totals.values(), key=lambda item: item["points"], reverse=True)


def _side_totals(rows: list[SidePointAward]) -> list[dict]:
    totals: dict[str, dict] = {}
    for row in rows:
        item = totals.setdefault(row.owner, {"owner": row.owner, "points": 0.0, "awards": 0})
        item["points"] += row.points
        item["awards"] += 1
    for item in totals.values():
        item["points"] = round(item["points"], 2)
    return sorted(totals.values(), key=lambda item: item["points"], reverse=True)


def _draft_owner_totals(rows: list[DraftPick]) -> list[dict]:
    totals: dict[str, dict] = {}
    for row in rows:
        item = totals.setdefault(row.owner, {"owner": row.owner, "spent": 0.0, "points": 0.0, "picks": 0, "value": 0.0})
        item["spent"] += row.bid_amount
        item["points"] += row.total_points
        item["picks"] += 1
    for item in totals.values():
        item["spent"] = round(item["spent"], 2)
        item["points"] = round(item["points"], 2)
        item["value"] = round(item["points"] / item["spent"], 2) if item["spent"] else 0
    return sorted(totals.values(), key=lambda item: item["value"], reverse=True)


def _division_owner_totals(rows: list[WeeklyTeamResult]) -> list[dict]:
    totals: dict[tuple[str, str], dict] = {}
    for row in rows:
        division = row.division or "Unknown"
        key = (division, row.owner)
        item = totals.setdefault(
            key,
            {"division": division, "owner": row.owner, "points": 0.0, "games": 0, "average": 0.0, "high_score": 0.0},
        )
        item["points"] += row.weekly_points
        item["games"] += 1
        item["high_score"] = max(item["high_score"], row.weekly_points)
    for item in totals.values():
        item["points"] = round(item["points"], 2)
        item["average"] = round(item["points"] / item["games"], 2) if item["games"] else 0
    return sorted(totals.values(), key=lambda item: (item["division"], -item["points"]))


def _division_season_totals(rows: list[WeeklyTeamResult]) -> list[dict]:
    totals: dict[tuple[str, int, int], dict] = {}
    for row in rows:
        division = row.division or "Unknown"
        key = (division, row.year, row.team_id)
        item = totals.setdefault(
            key,
            {"division": division, "year": row.year, "team_id": row.team_id, "owner": row.owner, "team_name": row.team_name, "points": 0.0, "games": 0, "average": 0.0},
        )
        item["points"] += row.weekly_points
        item["games"] += 1
    for item in totals.values():
        item["points"] = round(item["points"], 2)
        item["average"] = round(item["points"] / item["games"], 2) if item["games"] else 0
    return sorted(totals.values(), key=lambda item: (item["division"], -item["points"]))


def _playoff_justice(regular_rows: list[WeeklyTeamResult], playoff_rows: list[WeeklyTeamResult]) -> dict:
    by_year: dict[int, list[WeeklyTeamResult]] = {}
    playoff_by_year: dict[int, list[WeeklyTeamResult]] = {}
    for row in regular_rows:
        by_year.setdefault(row.year, []).append(row)
    for row in playoff_rows:
        playoff_by_year.setdefault(row.year, []).append(row)

    seasons = []
    all_snubs = []
    all_beneficiaries = []
    for year in sorted(by_year):
        summaries = _regular_team_summaries(by_year[year])
        if not summaries:
            continue
        actual_ids = _actual_playoff_team_ids(playoff_by_year.get(year, []), summaries)
        playoff_slots = len(actual_ids) or min(6, len(summaries))
        if not actual_ids:
            actual_ids = {row["team_id"] for row in _league_rule_qualifiers(summaries, playoff_slots)}

        points_only = sorted(summaries, key=_points_rank_key)[:playoff_slots]
        record_only = sorted(summaries, key=_record_rank_key)[:playoff_slots]
        division_winners = _division_winners(summaries)
        actual = sorted([row for row in summaries if row["team_id"] in actual_ids], key=_record_rank_key)
        points_ids = {row["team_id"] for row in points_only}
        record_ids = {row["team_id"] for row in record_only}
        division_winner_ids = {row["team_id"] for row in division_winners}
        point_snubs = sorted([row for row in points_only if row["team_id"] not in actual_ids], key=_points_rank_key)
        point_beneficiaries = sorted([row for row in actual if row["team_id"] not in points_ids], key=_points_rank_key, reverse=True)
        record_snubs = sorted([row for row in record_only if row["team_id"] not in actual_ids], key=_record_rank_key)
        beneficiaries = _beneficiary_rows(point_beneficiaries, point_snubs, points_ids, division_winner_ids)
        snubs = _snub_rows(point_snubs, point_beneficiaries, actual_ids, division_winner_ids)

        season = {
            "year": year,
            "playoff_slots": playoff_slots,
            "teams": [
                _playoff_team_row(row, actual_ids, points_ids, record_ids, division_winner_ids)
                for row in sorted(summaries, key=_points_rank_key)
            ],
            "actual_playoff_teams": [_playoff_team_row(row, actual_ids, points_ids, record_ids, division_winner_ids) for row in actual],
            "points_only_playoff_teams": [_playoff_team_row(row, actual_ids, points_ids, record_ids, division_winner_ids) for row in points_only],
            "record_only_playoff_teams": [_playoff_team_row(row, actual_ids, points_ids, record_ids, division_winner_ids) for row in record_only],
            "division_winners": [_playoff_team_row(row, actual_ids, points_ids, record_ids, division_winner_ids) for row in division_winners],
            "snubs": snubs,
            "beneficiaries": beneficiaries,
            "record_snubs": [
                _playoff_team_row(row, actual_ids, points_ids, record_ids, division_winner_ids) for row in record_snubs
            ],
        }
        seasons.append(season)
        all_snubs.extend({**row, "year": year} for row in snubs)
        all_beneficiaries.extend({**row, "year": year} for row in beneficiaries)

    return {
        "seasons": seasons,
        "biggest_snubs": sorted(all_snubs, key=lambda row: row["points_gap"], reverse=True)[:10],
        "biggest_beneficiaries": sorted(all_beneficiaries, key=lambda row: row["points_gap"], reverse=True)[:10],
    }


def _regular_team_summaries(rows: list[WeeklyTeamResult]) -> list[dict]:
    totals: dict[int, dict] = {}
    for row in rows:
        item = totals.setdefault(
            row.team_id,
            {
                "year": row.year,
                "team_id": row.team_id,
                "owner": row.owner,
                "team_name": row.team_name,
                "division": row.division or "Unknown",
                "points": 0.0,
                "games": 0,
                "wins": row.wins,
                "losses": row.losses,
                "ties": row.ties,
                "points_rank": 0,
                "record_rank": 0,
            },
        )
        item["points"] += row.weekly_points
        item["games"] += 1
        item["wins"] = max(item["wins"], row.wins)
        item["losses"] = max(item["losses"], row.losses)
        item["ties"] = max(item["ties"], row.ties)
    summaries = list(totals.values())
    for item in summaries:
        item["points"] = round(item["points"], 2)
        item["average"] = round(item["points"] / item["games"], 2) if item["games"] else 0
        item["win_pct"] = round((item["wins"] + item["ties"] * 0.5) / item["games"], 4) if item["games"] else 0
    for rank, item in enumerate(sorted(summaries, key=_points_rank_key), start=1):
        item["points_rank"] = rank
    for rank, item in enumerate(sorted(summaries, key=_record_rank_key), start=1):
        item["record_rank"] = rank
    return summaries


def _actual_playoff_team_ids(playoff_rows: list[WeeklyTeamResult], summaries: list[dict]) -> set[int]:
    if not playoff_rows:
        return set()
    first_week = min(row.week for row in playoff_rows)
    first_week_rows = [row for row in playoff_rows if row.week == first_week]
    playoff_slots = min(6, len(summaries))
    actual_ids: list[int] = []
    side_order = {"Home": 0, "Away": 1}
    for row in sorted(first_week_rows, key=lambda item: (item.matchup_id, side_order.get(item.home_away, 2), item.team_id)):
        if row.team_id not in actual_ids:
            actual_ids.append(row.team_id)
        if len(actual_ids) >= playoff_slots:
            break
    return set(actual_ids)


def _division_winners(summaries: list[dict]) -> list[dict]:
    by_division: dict[str, list[dict]] = {}
    for row in summaries:
        by_division.setdefault(row["division"], []).append(row)
    return [sorted(rows, key=_record_rank_key)[0] for division, rows in sorted(by_division.items()) if rows]


def _league_rule_qualifiers(summaries: list[dict], playoff_slots: int) -> list[dict]:
    division_winners = _division_winners(summaries)
    winner_ids = {row["team_id"] for row in division_winners}
    wildcards = [row for row in sorted(summaries, key=_record_rank_key) if row["team_id"] not in winner_ids]
    return sorted(division_winners, key=_record_rank_key) + wildcards[: max(0, playoff_slots - len(division_winners))]


def _beneficiary_rows(beneficiaries: list[dict], snubs: list[dict], points_ids: set[int], division_winner_ids: set[int]) -> list[dict]:
    rows = []
    for index, beneficiary in enumerate(beneficiaries):
        snub = snubs[index] if index < len(snubs) else None
        rows.append(
            {
                **_playoff_team_row(beneficiary, {beneficiary["team_id"]}, points_ids, set(), division_winner_ids),
                "replaced_owner": snub["owner"] if snub else None,
                "replaced_team_name": snub["team_name"] if snub else None,
                "points_gap": round((snub["points"] - beneficiary["points"]) if snub else 0, 2),
                "label": "Division Auto-Bid" if beneficiary["team_id"] in division_winner_ids else "Record Wildcard",
            }
        )
    return rows


def _snub_rows(snubs: list[dict], beneficiaries: list[dict], actual_ids: set[int], division_winner_ids: set[int]) -> list[dict]:
    rows = []
    for index, snub in enumerate(snubs):
        beneficiary = beneficiaries[index] if index < len(beneficiaries) else None
        rows.append(
            {
                **_playoff_team_row(snub, actual_ids, {snub["team_id"]}, set(), division_winner_ids),
                "replaced_by_owner": beneficiary["owner"] if beneficiary else None,
                "replaced_by_team_name": beneficiary["team_name"] if beneficiary else None,
                "points_gap": round((snub["points"] - beneficiary["points"]) if beneficiary else 0, 2),
                "label": "Robbed By Geography",
            }
        )
    return rows


def _playoff_team_row(row: dict, actual_ids: set[int], points_ids: set[int], record_ids: set[int], division_winner_ids: set[int]) -> dict:
    team_id = row["team_id"]
    made_actual = team_id in actual_ids
    made_points = team_id in points_ids
    made_record = team_id in record_ids
    is_division_winner = team_id in division_winner_ids
    if made_actual and is_division_winner:
        qualification_type = "division_winner"
    elif made_actual:
        qualification_type = "wildcard"
    elif made_points and not made_actual:
        qualification_type = "points_snub"
    else:
        qualification_type = "missed"
    return {
        "year": row["year"],
        "team_id": team_id,
        "owner": row["owner"],
        "team_name": row["team_name"],
        "division": row["division"],
        "wins": row["wins"],
        "losses": row["losses"],
        "ties": row["ties"],
        "regular_points": row["points"],
        "average": row["average"],
        "points_rank": row["points_rank"],
        "record_rank": row["record_rank"],
        "made_actual_playoffs": made_actual,
        "made_points_playoffs": made_points,
        "made_record_playoffs": made_record,
        "division_winner": is_division_winner,
        "qualification_type": qualification_type,
    }


def _points_rank_key(row: dict) -> tuple:
    return (-row["points"], -row["wins"], row["losses"], -row["ties"], row["owner"])


def _record_rank_key(row: dict) -> tuple:
    return (-row["wins"], row["losses"], -row["ties"], -row["points"], row["owner"])


def _player_records(rows: list[LineupEntry]) -> dict:
    real_rows = [row for row in rows if row.player_name and row.player_name.lower() != "empty"]
    starter_rows = [row for row in real_rows if not row.slot_key.startswith("BE")]
    player_totals: dict[tuple[str, str], dict] = {}
    for row in starter_rows:
        key = (row.player_name, row.player_position or row.slot_key)
        item = player_totals.setdefault(
            key,
            {"player_name": row.player_name, "position": row.player_position or row.slot_key, "points": 0.0, "starts": 0, "average": 0.0, "high_score": 0.0},
        )
        item["points"] += row.points
        item["starts"] += 1
        item["high_score"] = max(item["high_score"], row.points)
    for item in player_totals.values():
        item["points"] = round(item["points"], 2)
        item["average"] = round(item["points"] / item["starts"], 2) if item["starts"] else 0

    return {
        "best_player_games": [_lineup_row(row) for row in sorted(starter_rows, key=lambda row: row.points, reverse=True)[:20]],
        "worst_starter_games": [_lineup_row(row) for row in sorted(starter_rows, key=lambda row: row.points)[:20]],
        "best_player_totals": sorted(player_totals.values(), key=lambda item: item["points"], reverse=True)[:20],
        "best_player_averages": sorted([item for item in player_totals.values() if item["starts"] >= 5], key=lambda item: item["average"], reverse=True)[:20],
    }


def _bench_records(rows: list[LineupEntry], game_lookup: dict[tuple[int, int, int], WeeklyTeamResult]) -> list[dict]:
    bench_rows = [row for row in rows if row.slot_key.startswith("BE") and row.player_name and row.player_name.lower() != "empty"]
    records = []
    for row in bench_rows:
        game = game_lookup.get((row.year, row.week, row.team_id))
        if not game:
            continue
        loss_margin = abs(game.plus_minus) if game.plus_minus < 0 else None
        records.append(
            {
                **_lineup_row(row),
                "team_score": game.weekly_points,
                "plus_minus": game.plus_minus,
                "loss_margin": loss_margin,
                "would_cover_loss": bool(loss_margin is not None and row.points > loss_margin),
                "season_phase": game.season_phase,
            }
        )
    return sorted(records, key=lambda item: (item["would_cover_loss"], item["points"]), reverse=True)


def _lineup_row(row: LineupEntry) -> dict:
    return {
        "year": row.year,
        "week": row.week,
        "team_id": row.team_id,
        "owner": row.owner,
        "slot_key": row.slot_key,
        "player_name": row.player_name,
        "position": row.player_position,
        "points": round(row.points, 2),
    }


media_dir = Path(settings.media_root)


@app.get("/media/{asset_path:path}")
def serve_media(asset_path: str, session: Session = Depends(get_session)):
    asset = session.scalar(select(MediaAsset).where(MediaAsset.path == asset_path))
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found")
    path = (media_dir / asset.path).resolve()
    if not path.is_file() or media_dir.resolve() not in path.parents:
        raise HTTPException(status_code=404, detail="Media asset not found")
    return FileResponse(path)
