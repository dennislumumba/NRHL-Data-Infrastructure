from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.deps import get_current_tenant, get_db
from app.schemas.league import PlayerRead
from models import Player, PlayerPosition, RosterAssignment, Team, Tenant

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[PlayerRead], summary="List players with roster context")
def list_players(
    team_id: UUID | None = None,
    season_id: UUID | None = None,
    position: PlayerPosition | None = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[PlayerRead]:
    query: Select = (
        select(Player, RosterAssignment, Team)
        .join(RosterAssignment, RosterAssignment.player_id == Player.id)
        .join(Team, Team.id == RosterAssignment.team_id)
        .where(Player.tenant_id == tenant.id, RosterAssignment.tenant_id == tenant.id, Team.tenant_id == tenant.id)
        .order_by(Team.name, Player.last_name, Player.first_name)
    )

    if team_id:
        query = query.where(RosterAssignment.team_id == team_id)
    if season_id:
        query = query.where(RosterAssignment.season_id == season_id)
    if position:
        query = query.where(Player.primary_position == position)

    rows = db.execute(query).all()
    return [
        PlayerRead(
            id=player.id,
            display_name=player.display_name,
            first_name=player.first_name,
            last_name=player.last_name,
            performance_id=player.performance_id,
            athlete_id=player.athlete_id,
            primary_position=player.primary_position,
            team_id=team.id,
            team_name=team.name,
            jersey_number=roster.jersey_number,
            roster_status=roster.roster_status,
        )
        for player, roster, team in rows
    ]
