from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import finance, health, matches, players, teams

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(teams.router)
api_router.include_router(players.router)
api_router.include_router(matches.router)
api_router.include_router(finance.router)
