from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_current_tenant, get_db
from app.schemas.league import TeamRead
from models import Conference, RegionalNode, Team, Tenant, Venue

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamRead], summary="List teams for a tenant")
def list_teams(
    conference_id: UUID | None = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[TeamRead]:
    query = (
        select(Team)
        .where(Team.tenant_id == tenant.id)
        .options(selectinload(Team.conference), selectinload(Team.regional_node), selectinload(Team.home_venue))
        .order_by(Team.name)
    )
    if conference_id:
        query = query.where(Team.conference_id == conference_id)

    teams = db.scalars(query).all()
    return [
        TeamRead(
            id=team.id,
            name=team.name,
            slug=team.slug,
            short_name=team.short_name,
            conference_name=team.conference.name if team.conference else None,
            regional_node_name=team.regional_node.name if team.regional_node else None,
            home_venue_name=team.home_venue.name if team.home_venue else None,
            ownership_model=team.ownership_model,
            primary_color=team.primary_color,
            secondary_color=team.secondary_color,
        )
        for team in teams
    ]
