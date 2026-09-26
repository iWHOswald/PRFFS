from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("league_id", "year", name="uq_season"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    source: Mapped[str] = mapped_column(String(255), default="local")
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TeamSeason(Base):
    __tablename__ = "team_seasons"
    __table_args__ = (UniqueConstraint("league_id", "year", "team_id", name="uq_team_season"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    team_id: Mapped[int] = mapped_column(Integer, index=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    team_name: Mapped[str] = mapped_column(String(255))
    division: Mapped[str | None] = mapped_column(String(255), nullable=True)


class WeeklyTeamResult(Base):
    __tablename__ = "weekly_team_results"
    __table_args__ = (
        UniqueConstraint("league_id", "year", "week", "team_id", name="uq_weekly_team_result"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    team_id: Mapped[int] = mapped_column(Integer, index=True)
    matchup_id: Mapped[int] = mapped_column(Integer, index=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    team_name: Mapped[str] = mapped_column(String(255))
    home_away: Mapped[str] = mapped_column(String(16))
    division: Mapped[str | None] = mapped_column(String(255), nullable=True)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    ties: Mapped[int] = mapped_column(Integer, default=0)
    record_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_points_season: Mapped[float] = mapped_column(Float, default=0)
    cumulative_points: Mapped[float] = mapped_column(Float, default=0)
    weekly_points: Mapped[float] = mapped_column(Float, default=0)
    plus_minus: Mapped[float] = mapped_column(Float, default=0)
    is_playoff: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    season_phase: Mapped[str] = mapped_column(String(32), default="regular", index=True)


class LineupEntry(Base):
    __tablename__ = "lineup_entries"
    __table_args__ = (
        UniqueConstraint("league_id", "year", "week", "team_id", "slot_key", name="uq_lineup_entry"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    team_id: Mapped[int] = mapped_column(Integer, index=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    slot_key: Mapped[str] = mapped_column(String(32), index=True)
    player_name: Mapped[str] = mapped_column(String(255))
    player_position: Mapped[str | None] = mapped_column(String(32), nullable=True)
    points: Mapped[float] = mapped_column(Float, default=0)


class SidePointAward(Base):
    __tablename__ = "side_point_awards"
    __table_args__ = (
        UniqueConstraint("league_id", "year", "week", "team_id", "category", name="uq_side_point_award"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    team_id: Mapped[int] = mapped_column(Integer, index=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(128), index=True)
    points: Mapped[float] = mapped_column(Float)
    metric_name: Mapped[str] = mapped_column(String(128))
    metric_value: Mapped[float] = mapped_column(Float, default=0)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)


class ScoreSnapshot(Base):
    __tablename__ = "score_snapshots"
    __table_args__ = (
        UniqueConstraint("league_id", "year", "week", "team_id", "captured_at", name="uq_score_snapshot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    team_id: Mapped[int] = mapped_column(Integer, index=True)
    matchup_id: Mapped[int] = mapped_column(Integer, index=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    team_name: Mapped[str] = mapped_column(String(255))
    score: Mapped[float] = mapped_column(Float, default=0)
    projected_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = (UniqueConstraint("path", name="uq_media_asset_path"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(32), index=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    week: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DraftPick(Base):
    __tablename__ = "draft_picks"
    __table_args__ = (
        UniqueConstraint("league_id", "year", "position_drafted", name="uq_draft_pick_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    team_id: Mapped[int] = mapped_column(Integer, index=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    division: Mapped[str | None] = mapped_column(String(255), nullable=True)
    player_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    player_name: Mapped[str] = mapped_column(String(255), index=True)
    pro_team: Mapped[str | None] = mapped_column(String(32), nullable=True)
    position: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    total_points: Mapped[float] = mapped_column(Float, default=0)
    round_drafted: Mapped[int] = mapped_column(Integer, default=0)
    round_pick: Mapped[int] = mapped_column(Integer, default=0)
    position_drafted: Mapped[int] = mapped_column(Integer, index=True)
    bid_amount: Mapped[float] = mapped_column(Float, default=0)
    dollar_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(128), default="local")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    author: Mapped[str] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Poll(Base):
    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    question: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class PollOption(Base):
    __tablename__ = "poll_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[int] = mapped_column(Integer, index=True)
    label: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class PollVote(Base):
    __tablename__ = "poll_votes"
    __table_args__ = (UniqueConstraint("poll_id", "voter", name="uq_poll_vote_voter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[int] = mapped_column(Integer, index=True)
    option_id: Mapped[int] = mapped_column(Integer, index=True)
    voter: Mapped[str] = mapped_column(String(80), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class LeagueContext(Base):
    __tablename__ = "league_contexts"
    __table_args__ = (UniqueConstraint("league_id", "year", name="uq_league_context"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    tone_guide: Mapped[str] = mapped_column(Text, default="")
    public_notes: Mapped[str] = mapped_column(Text, default="")
    background_notes: Mapped[str] = mapped_column(Text, default="")
    off_limits: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OwnerContext(Base):
    __tablename__ = "owner_contexts"
    __table_args__ = (UniqueConstraint("league_id", "year", "owner", name="uq_owner_context"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    nickname: Mapped[str] = mapped_column(String(255), default="")
    roast_level: Mapped[str] = mapped_column(String(32), default="medium")
    political_affiliation: Mapped[str] = mapped_column(String(64), default="unassigned")
    veto_hunter: Mapped[str] = mapped_column(String(32), default="unknown")
    rival_owner: Mapped[str] = mapped_column(String(255), default="")
    public_notes: Mapped[str] = mapped_column(Text, default="")
    background_notes: Mapped[str] = mapped_column(Text, default="")
    off_limits: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WeeklyContext(Base):
    __tablename__ = "weekly_contexts"
    __table_args__ = (UniqueConstraint("league_id", "year", "week", name="uq_weekly_context"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    public_notes: Mapped[str] = mapped_column(Text, default="")
    background_notes: Mapped[str] = mapped_column(Text, default="")
    off_limits: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MatchupContext(Base):
    __tablename__ = "matchup_contexts"
    __table_args__ = (UniqueConstraint("league_id", "year", "week", "matchup_id", name="uq_matchup_context"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    matchup_id: Mapped[int] = mapped_column(Integer, index=True)
    public_notes: Mapped[str] = mapped_column(Text, default="")
    background_notes: Mapped[str] = mapped_column(Text, default="")
    off_limits: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
