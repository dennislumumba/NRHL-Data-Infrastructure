from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from app.deps import get_current_tenant, get_db
from app.schemas.league import FinanceDashboardSummary, MatchYieldRead
from models import FinancialOperation, Match, Tenant

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/matches/{match_id}/yield", response_model=MatchYieldRead, summary="Get economist audit for a match")
def get_match_yield(
    match_id: UUID,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
) -> MatchYieldRead:
    row = db.execute(
        select(FinancialOperation, Match)
        .join(Match, Match.id == FinancialOperation.match_id)
        .where(FinancialOperation.match_id == match_id, FinancialOperation.tenant_id == tenant.id)
    ).first()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial operation not found for match.")

    financial, match = row
    return MatchYieldRead(
        match_id=match.id,
        match_code=match.match_code,
        currency_code=financial.currency_code,
        captured_match_hours=financial.captured_match_hours,
        total_revenue_kes=financial.total_revenue_kes,
        total_cost_kes=financial.total_cost_kes,
        net_yield_kes=financial.net_yield_kes,
        yield_per_hour_kes=financial.yield_per_hour_kes,
        target_efficiency_kes_per_hour=financial.target_efficiency_kes_per_hour,
        meets_efficiency_target=financial.meets_efficiency_target,
    )


@router.get("/dashboard/summary", response_model=FinanceDashboardSummary, summary="Summarize match-day economics")
def finance_summary(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
) -> FinanceDashboardSummary:
    metrics = db.execute(
        select(
            func.count(FinancialOperation.id),
            func.coalesce(func.sum(FinancialOperation.total_revenue_kes), 0),
            func.coalesce(func.sum(FinancialOperation.total_cost_kes), 0),
            func.coalesce(func.avg(FinancialOperation.yield_per_hour_kes), 0),
            func.coalesce(func.sum(cast(FinancialOperation.meets_efficiency_target, Integer)), 0),
        ).where(FinancialOperation.tenant_id == tenant.id)
    ).one()

    total_matches, total_revenue, total_cost, avg_yield_per_hour, matches_above_target = metrics
    total_matches = int(total_matches or 0)
    matches_above_target = int(matches_above_target or 0)

    return FinanceDashboardSummary(
        total_financially_tracked_matches=total_matches,
        total_revenue_kes=Decimal(total_revenue),
        total_cost_kes=Decimal(total_cost),
        total_net_yield_kes=Decimal(total_revenue) - Decimal(total_cost),
        average_yield_per_hour_kes=Decimal(avg_yield_per_hour),
        matches_above_efficiency_target=matches_above_target,
    )
