from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_session
from models import Tenant


def get_db() -> Generator[Session, None, None]:
    db = get_session()
    try:
        yield db
    finally:
        db.close()


DBSession = Depends(get_db)


def get_current_tenant(
    db: Session = DBSession,
    x_tenant_slug: str | None = Header(default=None, alias="X-Tenant-Slug"),
) -> Tenant:
    settings = get_settings()
    tenant_slug = x_tenant_slug or settings.default_tenant_slug

    tenant = db.scalar(select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active.is_(True)))
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_slug}' was not found or is inactive.",
        )
    return tenant


CurrentTenant = Depends(get_current_tenant)
