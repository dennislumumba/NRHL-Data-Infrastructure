# NRHL Backend Platform

The hard truth: if NRHL is serious about becoming a multi-node sports institution, this cannot behave like a hobby league CRUD app. It must operate like a **tenant-aware sports operating system** with a clean data contract into Athlytica, a defensible migration story, and APIs that can scale from Nairobi to additional league nodes.

This repository delivers that foundation:

- **PostgreSQL + SQLAlchemy 2.0** data model
- **Alembic** migration scaffolding with an initial schema revision
- **FastAPI** production-grade starter with multi-tenant request resolution
- **Athlytica bridge** via `players.athlete_id` and `players.performance_id`
- **Economist audit layer** for match-day ROI and KES 5,000/hr efficiency tracking
- **Seed data** for a realistic 4-team Nairobi launch footprint

---

## Why this architecture matters

NRHL is not just scheduling matches. It is running a vertically integrated development system across competition, coaching, identity, venue economics, and player intelligence.

This backend is designed to support:

- conference-based league operations today
- regional expansion tomorrow
- player lifecycle tracking across seasons
- analytics-grade event and stat collection
- venue and match profitability analysis by node

If you cannot answer **which node produces the highest player development return per shilling**, you are not managing a system. You are guessing.

---

## Core platform capabilities

### 1. Multi-tenancy
Every operational table is tenant-scoped with `tenant_id`. That means NRHL Nairobi can run today while preserving a clean path to future markets without schema duplication.

### 2. Athlytica bridge
The `players` table includes:

- `athlete_id` for the Athlytica core engine UUID bridge
- `performance_id` for the operational performance identity surfaced in league workflows

This makes the backend a **league intelligence layer**, not an isolated app.

### 3. Competition engine
The schema supports:

- seasons
- conferences
- regional nodes
- venues
- teams and ownership
- rosters
- regular season fixtures
- tournament brackets and rounds

### 4. Match intelligence
Two layers are modeled:

- `player_match_stats` for aggregate reporting
- `match_events` for future event-driven analytics and film breakdown workflows

### 5. Economist audit
The `financial_operations` table tracks match-day revenue and cost composition, then computes:

- total revenue
- total cost
- net yield
- yield per hour
- target achievement against **KES 5,000/hour**

That means facility overhead, staffing, officiating, and sponsorship can be evaluated against actual node performance.

---

## Project structure

```text
nrhl_backend/
├── app/
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── finance.py
│   │       ├── health.py
│   │       ├── matches.py
│   │       ├── players.py
│   │       └── teams.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── schemas/
│   │   └── league.py
│   ├── db.py
│   ├── deps.py
│   └── main.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 20260408_0001_initial_nrhl_schema.py
├── alembic.ini
├── models.py
├── schema.sql
├── seed_data.py
├── render_schema.py
├── requirements.txt
└── .env.example
```

---

## Quick start

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Update `DATABASE_URL` if needed.

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Load sample data

```bash
python seed_data.py
```

### 5. Start the API

```bash
uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/healthz`

---

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `APP_NAME` | Service name | `NRHL Backend API` |
| `ENVIRONMENT` | App environment | `development` |
| `DATABASE_URL` | PostgreSQL SQLAlchemy URL | `postgresql+psycopg://postgres:postgres@localhost:5432/nrhl` |
| `DEFAULT_TENANT_SLUG` | Default tenant fallback | `nrhl-nairobi` |
| `API_V1_PREFIX` | Versioned API prefix | `/api/v1` |
| `ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000,http://127.0.0.1:3000` |
| `SQL_ECHO` | SQL debug logging | `false` |

---

## API starter endpoints

### Health
- `GET /healthz`
- `GET /api/v1/health`

### Teams
- `GET /api/v1/teams`
- Filter by `conference_id`

### Players
- `GET /api/v1/players`
- Filter by `team_id`, `season_id`, `position`

### Matches
- `GET /api/v1/matches`
- Filter by `season_id`, `competition_id`, `status`, `from_date`, `to_date`

### Finance
- `GET /api/v1/finance/matches/{match_id}/yield`
- `GET /api/v1/finance/dashboard/summary`

### Multi-tenant header
Use:

```http
X-Tenant-Slug: nrhl-nairobi
```

If omitted, the API falls back to `DEFAULT_TENANT_SLUG`.

---

## Alembic migration strategy

The initial revision bootstraps the database from the canonical `schema.sql` export. That gives you two leverage points:

1. a **human-readable SQL artifact** for review and DBA scrutiny
2. a **repeatable migration entrypoint** for deployment pipelines

For subsequent changes, use:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## ERD for GitHub / documentation

```mermaid
erDiagram
    TENANTS ||--o{ ORGANIZATIONS : contains
    TENANTS ||--o{ SEASONS : contains
    SEASONS ||--o{ CONFERENCES : defines
    CONFERENCES ||--o{ REGIONAL_NODES : maps
    REGIONAL_NODES ||--o{ VENUES : hosts
    CONFERENCES ||--o{ TEAMS : groups
    TEAMS ||--o{ TEAM_OWNERSHIPS : owned_by
    PLAYERS ||--o{ ROSTER_ASSIGNMENTS : assigned_to
    TEAMS ||--o{ ROSTER_ASSIGNMENTS : carries
    SEASONS ||--o{ COMPETITIONS : runs
    COMPETITIONS ||--o{ TOURNAMENT_BRACKETS : structures
    TOURNAMENT_BRACKETS ||--o{ BRACKET_ROUNDS : contains
    BRACKET_ROUNDS ||--o{ MATCHES : sequences
    MATCHES ||--o{ PLAYER_MATCH_STATS : aggregates
    MATCHES ||--o{ MATCH_EVENTS : records
    MATCHES ||--|| FINANCIAL_OPERATIONS : monetizes
```

---

## Economist audit for the README narrative

Use this language in your portfolio and stakeholder docs:

> The NRHL backend is designed to optimize resource allocation across league nodes by linking match scheduling, venue overhead, player output, and financial yield in one operational model. By measuring match-day revenue against facility, officiating, staffing, and medical costs, the platform makes node-level ROI auditable and comparable.

That is the difference between running events and running an institution.

---

## Recommended next moves

If you want this to stop being a strong prototype and become real infrastructure, do these next:

1. Add Alembic follow-up revisions for audit logging and authentication tables.
2. Introduce row-level security in PostgreSQL for tenant isolation.
3. Add test coverage for tenant resolution, schedule queries, and finance rollups.
4. Stand up CI for linting, migrations, and smoke tests.
5. Add async ingestion pipelines for Athlytica sync and match event imports.

---

## Final standard

Your standard is no longer “does it work?”

Your standard is: **can this backend survive growth, scrutiny, and operator complexity without a rewrite?**
