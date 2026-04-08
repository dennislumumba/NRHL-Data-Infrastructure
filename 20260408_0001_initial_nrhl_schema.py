"""initial NRHL schema

Revision ID: 20260408_0001
Revises: None
Create Date: 2026-04-08 00:00:00
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260408_0001"
down_revision = None
branch_labels = None
depends_on = None

ENUM_TYPES = [
    "financial_operation_type_enum",
    "penalty_type_enum",
    "event_type_enum",
    "match_format_enum",
    "match_status_enum",
    "bracket_format_enum",
    "competition_type_enum",
    "roster_status_enum",
    "player_position_enum",
    "owner_type_enum",
    "conference_side_enum",
    "organization_type_enum",
]

TABLES_IN_DROP_ORDER = [
    "financial_operations",
    "match_events",
    "player_match_stats",
    "matches",
    "bracket_rounds",
    "tournament_brackets",
    "roster_assignments",
    "team_ownerships",
    "teams",
    "venues",
    "regional_nodes",
    "conferences",
    "competitions",
    "seasons",
    "players",
    "organizations",
    "tenants",
]


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schema.sql"


def _iter_statements(schema_text: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []

    for line in schema_text.splitlines():
        stripped = line.strip()
        if not stripped:
            if buffer:
                buffer.append(line)
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(buffer).strip().rstrip(";")
            if statement:
                statements.append(statement)
            buffer = []

    if buffer:
        statement = "\n".join(buffer).strip().rstrip(";")
        if statement:
            statements.append(statement)

    return statements


def upgrade() -> None:
    connection = op.get_bind()
    schema_sql = _schema_path().read_text(encoding="utf-8")
    for statement in _iter_statements(schema_sql):
        connection.exec_driver_sql(statement)


def downgrade() -> None:
    connection = op.get_bind()
    for table_name in TABLES_IN_DROP_ORDER:
        connection.exec_driver_sql(f"DROP TABLE IF EXISTS {table_name} CASCADE")
    for enum_name in ENUM_TYPES:
        connection.exec_driver_sql(f"DROP TYPE IF EXISTS {enum_name} CASCADE")
