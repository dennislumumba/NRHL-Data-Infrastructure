from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class for NRHL/Athlytica operational schema."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )


class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )


class TenantScopedMixin:
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )


class ConferenceSide(str, enum.Enum):
    WESTERN = "western"
    EASTERN = "eastern"
    CENTRAL = "central"
    NORTHERN = "northern"
    SOUTHERN = "southern"
    OPEN = "open"


class OrganizationType(str, enum.Enum):
    LEAGUE = "league"
    TEAM_OPERATOR = "team_operator"
    FACILITY = "facility"
    PARTNER = "partner"
    SCHOOL = "school"
    SPONSOR = "sponsor"


class CompetitionType(str, enum.Enum):
    REGULAR_SEASON = "regular_season"
    PLAYOFFS = "playoffs"
    TOURNAMENT = "tournament"
    SHOWCASE = "showcase"


class BracketFormat(str, enum.Enum):
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    ROUND_ROBIN = "round_robin"
    LADDER = "ladder"


class MatchStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINAL = "final"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    FORFEIT = "forfeit"


class MatchFormat(str, enum.Enum):
    LEAGUE = "league"
    GROUP_STAGE = "group_stage"
    KNOCKOUT = "knockout"
    FRIENDLY = "friendly"


class RosterStatus(str, enum.Enum):
    ACTIVE = "active"
    RESERVE = "reserve"
    INJURED = "injured"
    SUSPENDED = "suspended"
    RELEASED = "released"


class PlayerPosition(str, enum.Enum):
    GOALIE = "goalie"
    DEFENDER = "defender"
    CENTER = "center"
    WING = "wing"
    UTILITY = "utility"


class EventType(str, enum.Enum):
    GOAL = "goal"
    PENALTY = "penalty"
    SHOT = "shot"
    FACEOFF = "faceoff"
    SAVE = "save"
    SHIFT = "shift"
    NOTE = "note"


class PenaltyType(str, enum.Enum):
    MINOR = "minor"
    MAJOR = "major"
    MISCONDUCT = "misconduct"
    MATCH = "match"
    BENCH = "bench"


class FinancialOperationType(str, enum.Enum):
    MATCH_DAY = "match_day"
    FACILITY = "facility"
    SPONSORSHIP = "sponsorship"
    OFFICIATING = "officiating"
    MEDICAL = "medical"
    OTHER = "other"


class OwnerType(str, enum.Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    INVESTOR_GROUP = "investor_group"


class Tenant(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, server_default=text("'KE'"))
    timezone_name: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'Africa/Nairobi'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    organizations: Mapped[list[Organization]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    seasons: Mapped[list[Season]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class Organization(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_organizations_tenant_code"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    organization_type: Mapped[OrganizationType] = mapped_column(
        SAEnum(OrganizationType, name="organization_type_enum"), nullable=False
    )
    parent_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    tenant: Mapped[Tenant] = relationship(back_populates="organizations")
    parent_organization: Mapped[Organization | None] = relationship(remote_side="Organization.id")
    teams: Mapped[list[Team]] = relationship(back_populates="operator_organization")


class Season(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_seasons_tenant_slug"),
        CheckConstraint("end_date >= start_date", name="ck_seasons_date_window"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    organization: Mapped[Organization] = relationship()
    tenant: Mapped[Tenant] = relationship(back_populates="seasons")
    conferences: Mapped[list[Conference]] = relationship(back_populates="season", cascade="all, delete-orphan")
    rosters: Mapped[list[RosterAssignment]] = relationship(back_populates="season")
    competitions: Mapped[list[Competition]] = relationship(back_populates="season")


class Conference(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "conferences"
    __table_args__ = (
        UniqueConstraint("season_id", "code", name="uq_conferences_season_code"),
    )

    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(24), nullable=False)
    side: Mapped[ConferenceSide] = mapped_column(
        SAEnum(ConferenceSide, name="conference_side_enum"), nullable=False
    )
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    season: Mapped[Season] = relationship(back_populates="conferences")
    regional_nodes: Mapped[list[RegionalNode]] = relationship(back_populates="conference")
    teams: Mapped[list[Team]] = relationship(back_populates="conference")


class RegionalNode(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "regional_nodes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "conference_id", "name", name="uq_regional_nodes_conf_name"),
    )

    conference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conferences.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    county: Mapped[str] = mapped_column(String(120), nullable=False, server_default=text("'Nairobi County'"))
    sub_county: Mapped[str | None] = mapped_column(String(120))
    neighbourhood: Mapped[str | None] = mapped_column(String(120))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    conference: Mapped[Conference] = relationship(back_populates="regional_nodes")
    venues: Mapped[list[Venue]] = relationship(back_populates="regional_node")
    teams: Mapped[list[Team]] = relationship(back_populates="regional_node")


class Venue(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "venues"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_venues_tenant_name"),
        CheckConstraint("hourly_cost_kes >= 0", name="ck_venues_hourly_cost_non_negative"),
    )

    operator_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    regional_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regional_nodes.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    address_line: Mapped[str | None] = mapped_column(String(255))
    hourly_cost_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    capacity: Mapped[int | None] = mapped_column(Integer)
    indoor: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    surface_type: Mapped[str | None] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    regional_node: Mapped[RegionalNode | None] = relationship(back_populates="venues")
    matches: Mapped[list[Match]] = relationship(back_populates="venue")


class Team(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_teams_tenant_slug"),
        UniqueConstraint("tenant_id", "name", name="uq_teams_tenant_name"),
    )

    operator_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    conference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conferences.id", ondelete="SET NULL")
    )
    regional_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regional_nodes.id", ondelete="SET NULL")
    )
    home_venue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("venues.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    short_name: Mapped[str] = mapped_column(String(48), nullable=False)
    primary_color: Mapped[str | None] = mapped_column(String(7))
    secondary_color: Mapped[str | None] = mapped_column(String(7))
    founded_on: Mapped[date | None] = mapped_column(Date)
    ownership_model: Mapped[str | None] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    operator_organization: Mapped[Organization | None] = relationship(back_populates="teams")
    conference: Mapped[Conference | None] = relationship(back_populates="teams")
    regional_node: Mapped[RegionalNode | None] = relationship(back_populates="teams")
    home_venue: Mapped[Venue | None] = relationship(foreign_keys=[home_venue_id])
    owners: Mapped[list[TeamOwnership]] = relationship(back_populates="team", cascade="all, delete-orphan")
    roster_assignments: Mapped[list[RosterAssignment]] = relationship(back_populates="team")


class TeamOwnership(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "team_ownerships"
    __table_args__ = (
        CheckConstraint("stake_percentage >= 0 AND stake_percentage <= 100", name="ck_team_ownership_stake_pct"),
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    owner_type: Mapped[OwnerType] = mapped_column(SAEnum(OwnerType, name="owner_type_enum"), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(160), nullable=False)
    owner_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    stake_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default=text("100.00"))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    team: Mapped[Team] = relationship(back_populates="owners")


class Player(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("tenant_id", "performance_id", name="uq_players_tenant_performance_id"),
        UniqueConstraint("tenant_id", "athlete_id", name="uq_players_tenant_athlete_id"),
        CheckConstraint("jersey_preference IS NULL OR jersey_preference BETWEEN 0 AND 99", name="ck_players_jersey_preference"),
        Index("ix_players_tenant_performance_id", "tenant_id", "performance_id", postgresql_using="btree"),
        Index("ix_players_tenant_athlete_id", "tenant_id", "athlete_id", postgresql_using="btree"),
    )

    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(32))
    handedness: Mapped[str | None] = mapped_column(String(16))
    primary_position: Mapped[PlayerPosition] = mapped_column(
        SAEnum(PlayerPosition, name="player_position_enum"), nullable=False
    )
    secondary_position: Mapped[PlayerPosition | None] = mapped_column(
        SAEnum(PlayerPosition, name="player_position_enum", create_type=False)
    )
    jersey_preference: Mapped[int | None] = mapped_column(Integer)
    athlete_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    performance_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    national_id_ref: Mapped[str | None] = mapped_column(String(64))
    guardian_name: Mapped[str | None] = mapped_column(String(160))
    guardian_phone: Mapped[str | None] = mapped_column(String(32))
    medical_notes: Mapped[str | None] = mapped_column(Text)
    profile_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    roster_assignments: Mapped[list[RosterAssignment]] = relationship(back_populates="player")
    match_stats: Mapped[list[PlayerMatchStat]] = relationship(back_populates="player")


class RosterAssignment(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "roster_assignments"
    __table_args__ = (
        UniqueConstraint("season_id", "team_id", "player_id", name="uq_roster_season_team_player"),
        UniqueConstraint("season_id", "team_id", "jersey_number", name="uq_roster_season_team_jersey"),
        CheckConstraint("jersey_number BETWEEN 0 AND 99", name="ck_roster_jersey_number"),
    )

    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    jersey_number: Mapped[int] = mapped_column(Integer, nullable=False)
    roster_status: Mapped[RosterStatus] = mapped_column(
        SAEnum(RosterStatus, name="roster_status_enum"), nullable=False, server_default=text("'ACTIVE'"),
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    season: Mapped[Season] = relationship(back_populates="rosters")
    team: Mapped[Team] = relationship(back_populates="roster_assignments")
    player: Mapped[Player] = relationship(back_populates="roster_assignments")


class Competition(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "competitions"
    __table_args__ = (
        UniqueConstraint("season_id", "slug", name="uq_competitions_season_slug"),
    )

    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    competition_type: Mapped[CompetitionType] = mapped_column(
        SAEnum(CompetitionType, name="competition_type_enum"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    season: Mapped[Season] = relationship(back_populates="competitions")
    brackets: Mapped[list[TournamentBracket]] = relationship(back_populates="competition")
    matches: Mapped[list[Match]] = relationship(back_populates="competition")


class TournamentBracket(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "tournament_brackets"

    competition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    bracket_format: Mapped[BracketFormat] = mapped_column(
        SAEnum(BracketFormat, name="bracket_format_enum"), nullable=False
    )
    bronze_match_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    competition: Mapped[Competition] = relationship(back_populates="brackets")
    rounds: Mapped[list[BracketRound]] = relationship(back_populates="bracket", cascade="all, delete-orphan")


class BracketRound(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "bracket_rounds"
    __table_args__ = (
        UniqueConstraint("bracket_id", "round_number", name="uq_bracket_round_number"),
    )

    bracket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tournament_brackets.id", ondelete="CASCADE"), nullable=False
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    bracket: Mapped[TournamentBracket] = relationship(back_populates="rounds")
    matches: Mapped[list[Match]] = relationship(back_populates="bracket_round")


class Match(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="ck_matches_distinct_teams"),
        Index("ix_matches_tenant_scheduled_start", "tenant_id", "scheduled_start", postgresql_using="btree"),
        Index("ix_matches_scheduled_start_brin", "scheduled_start", postgresql_using="brin"),
    )

    competition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False
    )
    bracket_round_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bracket_rounds.id", ondelete="SET NULL")
    )
    venue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("venues.id", ondelete="SET NULL")
    )
    home_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    away_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    winner_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL")
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    external_match_ref: Mapped[str | None] = mapped_column(String(64))
    match_code: Mapped[str] = mapped_column(String(32), nullable=False)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[MatchStatus] = mapped_column(
        SAEnum(MatchStatus, name="match_status_enum"), nullable=False, server_default=text("'SCHEDULED'"),
    )
    match_format: Mapped[MatchFormat] = mapped_column(
        SAEnum(MatchFormat, name="match_format_enum"), nullable=False, server_default=text("'LEAGUE'"),
    )
    round_label: Mapped[str | None] = mapped_column(String(64))
    sequence_in_round: Mapped[int | None] = mapped_column(Integer)
    home_score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    away_score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    overtime_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    shootout_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    competition: Mapped[Competition] = relationship(back_populates="matches")
    bracket_round: Mapped[BracketRound | None] = relationship(back_populates="matches")
    venue: Mapped[Venue | None] = relationship(back_populates="matches")
    home_team: Mapped[Team] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(foreign_keys=[away_team_id])
    winner_team: Mapped[Team | None] = relationship(foreign_keys=[winner_team_id])
    player_stats: Mapped[list[PlayerMatchStat]] = relationship(back_populates="match", cascade="all, delete-orphan")
    events: Mapped[list[MatchEvent]] = relationship(back_populates="match", cascade="all, delete-orphan")
    financial_operation: Mapped[FinancialOperation | None] = relationship(back_populates="match", uselist=False)


class PlayerMatchStat(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "player_match_stats"
    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_player_match_stats_match_player"),
        CheckConstraint("goals >= 0 AND assists >= 0 AND penalties >= 0 AND penalty_minutes >= 0", name="ck_player_match_stats_non_negative"),
        CheckConstraint("time_on_floor_seconds >= 0", name="ck_player_match_stats_tof_non_negative"),
        Index("ix_player_match_stats_player_match", "player_id", "match_id", postgresql_using="btree"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    goals: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    assists: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        server_onupdate=text("(goals + assists)"),
    )
    shots_on_goal: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    penalties: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    penalty_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    time_on_floor_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    plus_minus: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    save_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    stat_context: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    match: Mapped[Match] = relationship(back_populates="player_stats")
    player: Mapped[Player] = relationship(back_populates="match_stats")
    team: Mapped[Team] = relationship()


class MatchEvent(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "match_events"
    __table_args__ = (
        Index("ix_match_events_match_period_time", "match_id", "period_number", "event_second", postgresql_using="btree"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL")
    )
    primary_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL")
    )
    secondary_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL")
    )
    tertiary_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL")
    )
    event_type: Mapped[EventType] = mapped_column(SAEnum(EventType, name="event_type_enum"), nullable=False)
    penalty_type: Mapped[PenaltyType | None] = mapped_column(
        SAEnum(PenaltyType, name="penalty_type_enum")
    )
    period_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    event_second: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    description: Mapped[str | None] = mapped_column(Text)
    penalty_minutes: Mapped[int | None] = mapped_column(Integer)
    event_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    match: Mapped[Match] = relationship(back_populates="events")


class FinancialOperation(UUIDPKMixin, TenantScopedMixin, TimestampMixin, Base):
    __tablename__ = "financial_operations"
    __table_args__ = (
        UniqueConstraint("match_id", name="uq_financial_operations_match_id"),
        CheckConstraint("captured_match_hours >= 0", name="ck_financial_ops_match_hours_non_negative"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    operation_type: Mapped[FinancialOperationType] = mapped_column(
        SAEnum(FinancialOperationType, name="financial_operation_type_enum"),
        nullable=False,
        server_default=text("'MATCH_DAY'"),
    )
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'KES'"))
    captured_match_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, server_default=text("1.00"))
    target_efficiency_kes_per_hour: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("5000.00")
    )
    ticket_revenue_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    sponsorship_revenue_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    concession_revenue_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    broadcast_revenue_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    other_revenue_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    facility_cost_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    officiating_cost_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    staffing_cost_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    medical_cost_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    security_cost_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    other_cost_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    total_revenue_kes: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        Computed(
            "COALESCE(ticket_revenue_kes, 0) + COALESCE(sponsorship_revenue_kes, 0) + COALESCE(concession_revenue_kes, 0) + COALESCE(broadcast_revenue_kes, 0) + COALESCE(other_revenue_kes, 0)",
            persisted=True,
        ),
        nullable=False,
    )
    total_cost_kes: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        Computed(
            "COALESCE(facility_cost_kes, 0) + COALESCE(officiating_cost_kes, 0) + COALESCE(staffing_cost_kes, 0) + COALESCE(medical_cost_kes, 0) + COALESCE(security_cost_kes, 0) + COALESCE(other_cost_kes, 0)",
            persisted=True,
        ),
        nullable=False,
    )
    net_yield_kes: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        Computed(
            "(COALESCE(ticket_revenue_kes, 0) + COALESCE(sponsorship_revenue_kes, 0) + COALESCE(concession_revenue_kes, 0) + COALESCE(broadcast_revenue_kes, 0) + COALESCE(other_revenue_kes, 0)) - (COALESCE(facility_cost_kes, 0) + COALESCE(officiating_cost_kes, 0) + COALESCE(staffing_cost_kes, 0) + COALESCE(medical_cost_kes, 0) + COALESCE(security_cost_kes, 0) + COALESCE(other_cost_kes, 0))",
            persisted=True,
        ),
        nullable=False,
    )
    yield_per_hour_kes: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        Computed(
            "CASE WHEN captured_match_hours > 0 THEN (((COALESCE(ticket_revenue_kes, 0) + COALESCE(sponsorship_revenue_kes, 0) + COALESCE(concession_revenue_kes, 0) + COALESCE(broadcast_revenue_kes, 0) + COALESCE(other_revenue_kes, 0)) - (COALESCE(facility_cost_kes, 0) + COALESCE(officiating_cost_kes, 0) + COALESCE(staffing_cost_kes, 0) + COALESCE(medical_cost_kes, 0) + COALESCE(security_cost_kes, 0) + COALESCE(other_cost_kes, 0))) / captured_match_hours) ELSE 0 END",
            persisted=True,
        ),
        nullable=False,
    )
    meets_efficiency_target: Mapped[bool] = mapped_column(
        Boolean,
        Computed(
            "CASE WHEN captured_match_hours > 0 THEN ((((COALESCE(ticket_revenue_kes, 0) + COALESCE(sponsorship_revenue_kes, 0) + COALESCE(concession_revenue_kes, 0) + COALESCE(broadcast_revenue_kes, 0) + COALESCE(other_revenue_kes, 0)) - (COALESCE(facility_cost_kes, 0) + COALESCE(officiating_cost_kes, 0) + COALESCE(staffing_cost_kes, 0) + COALESCE(medical_cost_kes, 0) + COALESCE(security_cost_kes, 0) + COALESCE(other_cost_kes, 0))) / captured_match_hours) >= target_efficiency_kes_per_hour) ELSE false END",
            persisted=True,
        ),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    match: Mapped[Match] = relationship(back_populates="financial_operation")


# PostgreSQL-friendly helper for local development/tests.
def build_engine(db_url: str):
    from sqlalchemy import create_engine

    return create_engine(db_url, future=True)
