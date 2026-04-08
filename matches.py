from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, aliased

from app.deps import get_current_tenant, get_db
from app.schemas.league import MatchRead
from models import Match, MatchStatus, Team, Tenant, Venue

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchRead], summary="List matches for a tenant")
def list_matches(
    season_id: UUID | None = None,
    competition_id: UUID | None = None,
    status: MatchStatus | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[MatchRead]:
    home_team = aliased(Team)
    away_team = aliased(Team)

    query: Select = (
        select(Match, home_team, away_team, Venue)
        .join(home_team, home_team.id == Match.home_team_id)
        .join(away_team, away_team.id == Match.away_team_id)
        .outerjoin(Venue, Venue.id == Match.venue_id)
        .where(Match.tenant_id == tenant.id)
        .order_by(Match.scheduled_start)
    )

    if season_id:
        query = query.where(Match.season_id == season_id)
    if competition_id:
        query = query.where(Match.competition_id == competition_id)
    if status:
        query = query.where(Match.status == status)
    if from_date:
        query = query.where(Match.scheduled_start >= from_date)
    if to_date:
        query = query.where(Match.scheduled_start <= to_date)

    rows = db.execute(query).all()
    return [
        MatchRead(
            id=match.id,
            match_code=match.match_code,
            scheduled_start=match.scheduled_start,
            status=match.status,
            match_format=match.match_format,
            home_team_name=home.name,
            away_team_name=away.name,
            venue_name=venue.name if venue else None,
            home_score=match.home_score,
            away_score=match.away_score,
            round_label=match.round_label,
        )
        for match, home, away, venue in rows
    ]
