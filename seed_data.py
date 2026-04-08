from __future__ import annotations

import os
import uuid
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, sessionmaker

from models import (
    Base,
    BracketFormat,
    BracketRound,
    Competition,
    CompetitionType,
    Conference,
    ConferenceSide,
    FinancialOperation,
    FinancialOperationType,
    Match,
    MatchFormat,
    MatchStatus,
    Organization,
    OrganizationType,
    OwnerType,
    Player,
    PlayerMatchStat,
    PlayerPosition,
    RegionalNode,
    RosterAssignment,
    RosterStatus,
    Season,
    Team,
    TeamOwnership,
    Tenant,
    TournamentBracket,
    Venue,
    build_engine,
)

TZ = ZoneInfo("Africa/Nairobi")
NAMESPACE = uuid.UUID("b2e2fb14-b8e8-4ab4-988c-ae2246b82ff3")


def uid(key: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, key)


def dt(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=TZ)


def seed_sample_data(session: Session) -> None:
    tenant = session.get(Tenant, uid("tenant:nairobi"))
    if tenant:
        return

    tenant = Tenant(
        id=uid("tenant:nairobi"),
        slug="nrhl-nairobi",
        name="Nairobi Roller Hockey League",
        city="Nairobi",
        country_code="KE",
        timezone_name="Africa/Nairobi",
        settings={"multi_tenant_mode": "row_level", "analytics_bridge": "athlytica"},
    )
    session.add(tenant)

    league_org = Organization(
        id=uid("org:nrhl"),
        tenant_id=tenant.id,
        code="NRHL",
        name="Nairobi Roller Hockey League",
        organization_type=OrganizationType.LEAGUE,
        metadata_json={"founder": "Dennis Lumumba", "stack": "Athlytica Performance Intelligence OS"},
    )
    west_operator = Organization(
        id=uid("org:west-operator"),
        tenant_id=tenant.id,
        code="NRHL-WEST-OPS",
        name="NRHL West Operations",
        organization_type=OrganizationType.TEAM_OPERATOR,
    )
    east_operator = Organization(
        id=uid("org:east-operator"),
        tenant_id=tenant.id,
        code="NRHL-EAST-OPS",
        name="NRHL East Operations",
        organization_type=OrganizationType.TEAM_OPERATOR,
    )
    session.add_all([league_org, west_operator, east_operator])

    season = Season(
        id=uid("season:2026-s1"),
        tenant_id=tenant.id,
        organization_id=league_org.id,
        name="Season 1 2026",
        slug="season-1-2026",
        year=2026,
        start_date=date(2026, 5, 2),
        end_date=date(2026, 8, 29),
        is_active=True,
    )
    session.add(season)

    western = Conference(
        id=uid("conf:western"),
        tenant_id=tenant.id,
        season_id=season.id,
        name="Western Conference",
        code="WEST",
        side=ConferenceSide.WESTERN,
        rank_order=1,
        metadata_json={"legacy_expansion_mode": ["summit", "ridge", "plateau"]},
    )
    eastern = Conference(
        id=uid("conf:eastern"),
        tenant_id=tenant.id,
        season_id=season.id,
        name="Eastern Conference",
        code="EAST",
        side=ConferenceSide.EASTERN,
        rank_order=2,
        metadata_json={"legacy_expansion_mode": ["savannah"]},
    )
    session.add_all([western, eastern])

    nodes = {
        "westlands": RegionalNode(
            id=uid("node:westlands"),
            tenant_id=tenant.id,
            conference_id=western.id,
            name="Westlands Node",
            sub_county="Westlands",
            neighbourhood="Westlands",
            latitude=Decimal("-1.267600"),
            longitude=Decimal("36.810800"),
        ),
        "karen": RegionalNode(
            id=uid("node:karen"),
            tenant_id=tenant.id,
            conference_id=western.id,
            name="Karen Node",
            sub_county="Lang'ata",
            neighbourhood="Karen",
            latitude=Decimal("-1.319500"),
            longitude=Decimal("36.707300"),
        ),
        "embakasi": RegionalNode(
            id=uid("node:embakasi"),
            tenant_id=tenant.id,
            conference_id=eastern.id,
            name="Embakasi Node",
            sub_county="Embakasi",
            neighbourhood="Embakasi",
            latitude=Decimal("-1.315100"),
            longitude=Decimal("36.891100"),
        ),
        "kasarani": RegionalNode(
            id=uid("node:kasarani"),
            tenant_id=tenant.id,
            conference_id=eastern.id,
            name="Kasarani Node",
            sub_county="Kasarani",
            neighbourhood="Kasarani",
            latitude=Decimal("-1.228000"),
            longitude=Decimal("36.899200"),
        ),
    }
    session.add_all(nodes.values())

    venues = {
        "braeburn": Venue(
            id=uid("venue:braeburn"),
            tenant_id=tenant.id,
            operator_organization_id=league_org.id,
            regional_node_id=nodes["westlands"].id,
            name="Braeburn School Rink",
            address_line="Gitanga Road, Nairobi",
            hourly_cost_kes=Decimal("5200.00"),
            capacity=220,
            indoor=True,
            surface_type="sport-court",
        ),
        "karen_prep": Venue(
            id=uid("venue:karen-prep"),
            tenant_id=tenant.id,
            operator_organization_id=league_org.id,
            regional_node_id=nodes["karen"].id,
            name="Karen Prep Arena",
            address_line="Karen Road, Nairobi",
            hourly_cost_kes=Decimal("4800.00"),
            capacity=260,
            indoor=False,
            surface_type="sealed-concrete",
        ),
        "embakasi_msc": Venue(
            id=uid("venue:embakasi-msc"),
            tenant_id=tenant.id,
            operator_organization_id=league_org.id,
            regional_node_id=nodes["embakasi"].id,
            name="Embakasi MSC Court",
            address_line="Embakasi MSC, Nairobi",
            hourly_cost_kes=Decimal("3900.00"),
            capacity=300,
            indoor=False,
            surface_type="sport-tile",
        ),
        "kasarani_annex": Venue(
            id=uid("venue:kasarani-annex"),
            tenant_id=tenant.id,
            operator_organization_id=league_org.id,
            regional_node_id=nodes["kasarani"].id,
            name="Kasarani Annex Rink",
            address_line="Moi International Sports Centre Annex, Nairobi",
            hourly_cost_kes=Decimal("4100.00"),
            capacity=350,
            indoor=True,
            surface_type="sport-court",
        ),
    }
    session.add_all(venues.values())

    teams = {
        "westlands_wolves": Team(
            id=uid("team:westlands-wolves"),
            tenant_id=tenant.id,
            operator_organization_id=west_operator.id,
            conference_id=western.id,
            regional_node_id=nodes["westlands"].id,
            home_venue_id=venues["braeburn"].id,
            name="Westlands Wolves",
            slug="westlands-wolves",
            short_name="WLV",
            primary_color="#0B1F3A",
            secondary_color="#D4AF37",
            founded_on=date(2026, 1, 10),
            ownership_model="league-operated franchise",
        ),
        "karen_ridgebacks": Team(
            id=uid("team:karen-ridgebacks"),
            tenant_id=tenant.id,
            operator_organization_id=west_operator.id,
            conference_id=western.id,
            regional_node_id=nodes["karen"].id,
            home_venue_id=venues["karen_prep"].id,
            name="Karen Ridgebacks",
            slug="karen-ridgebacks",
            short_name="KRB",
            primary_color="#1D6B38",
            secondary_color="#F5E6A8",
            founded_on=date(2026, 1, 10),
            ownership_model="community-backed franchise",
        ),
        "embakasi_predators": Team(
            id=uid("team:embakasi-predators"),
            tenant_id=tenant.id,
            operator_organization_id=east_operator.id,
            conference_id=eastern.id,
            regional_node_id=nodes["embakasi"].id,
            home_venue_id=venues["embakasi_msc"].id,
            name="Embakasi Predators",
            slug="embakasi-predators",
            short_name="EMP",
            primary_color="#7A0019",
            secondary_color="#F7B32B",
            founded_on=date(2026, 1, 10),
            ownership_model="league-operated franchise",
        ),
        "kasarani_cyclones": Team(
            id=uid("team:kasarani-cyclones"),
            tenant_id=tenant.id,
            operator_organization_id=east_operator.id,
            conference_id=eastern.id,
            regional_node_id=nodes["kasarani"].id,
            home_venue_id=venues["kasarani_annex"].id,
            name="Kasarani Cyclones",
            slug="kasarani-cyclones",
            short_name="KCY",
            primary_color="#123C69",
            secondary_color="#EAEAEA",
            founded_on=date(2026, 1, 10),
            ownership_model="private operator",
        ),
    }
    session.add_all(teams.values())

    ownerships = [
        TeamOwnership(
            id=uid("ownership:westlands"),
            tenant_id=tenant.id,
            team_id=teams["westlands_wolves"].id,
            owner_type=OwnerType.ORGANIZATION,
            owner_name="NRHL West Operations",
            owner_organization_id=west_operator.id,
            stake_percentage=Decimal("100.00"),
            start_date=date(2026, 1, 10),
        ),
        TeamOwnership(
            id=uid("ownership:karen"),
            tenant_id=tenant.id,
            team_id=teams["karen_ridgebacks"].id,
            owner_type=OwnerType.INVESTOR_GROUP,
            owner_name="Karen Hockey Growth Syndicate",
            stake_percentage=Decimal("100.00"),
            start_date=date(2026, 1, 10),
            metadata_json={"lead_governor": "Dennis Lumumba"},
        ),
        TeamOwnership(
            id=uid("ownership:embakasi"),
            tenant_id=tenant.id,
            team_id=teams["embakasi_predators"].id,
            owner_type=OwnerType.ORGANIZATION,
            owner_name="NRHL East Operations",
            owner_organization_id=east_operator.id,
            stake_percentage=Decimal("100.00"),
            start_date=date(2026, 1, 10),
        ),
        TeamOwnership(
            id=uid("ownership:kasarani"),
            tenant_id=tenant.id,
            team_id=teams["kasarani_cyclones"].id,
            owner_type=OwnerType.PERSON,
            owner_name="Amina Wanjiku",
            stake_percentage=Decimal("100.00"),
            start_date=date(2026, 1, 10),
        ),
    ]
    session.add_all(ownerships)

    team_players = {
        "westlands_wolves": [
            ("Ethan", "Mwangi", PlayerPosition.CENTER, 9),
            ("Noah", "Kiptoo", PlayerPosition.WING, 17),
            ("Liam", "Odhiambo", PlayerPosition.DEFENDER, 4),
            ("Jayden", "Gikonyo", PlayerPosition.WING, 12),
            ("Zane", "Muriuki", PlayerPosition.DEFENDER, 22),
            ("Ryan", "Mbae", PlayerPosition.GOALIE, 1),
        ],
        "karen_ridgebacks": [
            ("Milan", "Njoroge", PlayerPosition.CENTER, 10),
            ("Tobias", "Maina", PlayerPosition.WING, 11),
            ("Kian", "Otieno", PlayerPosition.DEFENDER, 5),
            ("Ari", "Muthoni", PlayerPosition.WING, 15),
            ("Leo", "Karanja", PlayerPosition.DEFENDER, 24),
            ("Daniel", "Kibet", PlayerPosition.GOALIE, 30),
        ],
        "embakasi_predators": [
            ("Samuel", "Mutua", PlayerPosition.CENTER, 13),
            ("Brian", "Musyoka", PlayerPosition.WING, 18),
            ("Kevin", "Munyao", PlayerPosition.DEFENDER, 6),
            ("Ian", "Mworia", PlayerPosition.WING, 19),
            ("Brandon", "Kivuva", PlayerPosition.DEFENDER, 23),
            ("Elvis", "Makau", PlayerPosition.GOALIE, 31),
        ],
        "kasarani_cyclones": [
            ("Aiden", "Kamau", PlayerPosition.CENTER, 14),
            ("Tyler", "Wekesa", PlayerPosition.WING, 20),
            ("Caleb", "Wanjala", PlayerPosition.DEFENDER, 7),
            ("Nathan", "Mungai", PlayerPosition.WING, 16),
            ("Joel", "Nyabuto", PlayerPosition.DEFENDER, 26),
            ("Mark", "Owino", PlayerPosition.GOALIE, 33),
        ],
    }

    player_counter = 1
    players = []
    rosters = []
    for team_key, roster in team_players.items():
        for first_name, last_name, position, jersey in roster:
            player_id = uid(f"player:{team_key}:{jersey}")
            performance_id = f"ATH-NRHL-2026-{player_counter:04d}"
            athlete_id = uid(f"athlete-core:{performance_id}")
            player = Player(
                id=player_id,
                tenant_id=tenant.id,
                first_name=first_name,
                last_name=last_name,
                display_name=f"{first_name} {last_name}",
                date_of_birth=date(2012, (player_counter % 12) + 1, min((player_counter * 2) % 28 + 1, 28)),
                gender="M",
                handedness="right" if player_counter % 3 else "left",
                primary_position=position,
                jersey_preference=jersey,
                athlete_id=athlete_id,
                performance_id=performance_id,
                guardian_name=f"Guardian {last_name}",
                guardian_phone=f"+254700{player_counter:04d}",
                profile_json={"tier": "champion", "athlytica_sync": True},
            )
            players.append(player)
            rosters.append(
                RosterAssignment(
                    id=uid(f"roster:{team_key}:{jersey}"),
                    tenant_id=tenant.id,
                    season_id=season.id,
                    team_id=teams[team_key].id,
                    player_id=player.id,
                    jersey_number=jersey,
                    roster_status=RosterStatus.ACTIVE,
                    start_date=season.start_date,
                )
            )
            player_counter += 1
    session.add_all(players)
    session.add_all(rosters)

    regular_season = Competition(
        id=uid("competition:regular-season"),
        tenant_id=tenant.id,
        season_id=season.id,
        name="NRHL Season 1 Regular Season",
        slug="nrhl-s1-regular-season",
        competition_type=CompetitionType.REGULAR_SEASON,
        description="Cross-conference foundational schedule for Nairobi launch season.",
    )
    championship = Competition(
        id=uid("competition:championship"),
        tenant_id=tenant.id,
        season_id=season.id,
        name="NRHL East-West Championship",
        slug="nrhl-east-west-championship",
        competition_type=CompetitionType.TOURNAMENT,
        description="Conference winners advance to a single-match final.",
    )
    session.add_all([regular_season, championship])

    bracket = TournamentBracket(
        id=uid("bracket:championship"),
        tenant_id=tenant.id,
        competition_id=championship.id,
        name="East-West Championship Bracket",
        bracket_format=BracketFormat.SINGLE_ELIMINATION,
    )
    final_round = BracketRound(
        id=uid("round:final"),
        tenant_id=tenant.id,
        bracket_id=bracket.id,
        round_number=1,
        name="Grand Final",
    )
    session.add_all([bracket, final_round])

    matches = [
        Match(
            id=uid("match:001"),
            tenant_id=tenant.id,
            competition_id=regular_season.id,
            season_id=season.id,
            venue_id=venues["braeburn"].id,
            home_team_id=teams["westlands_wolves"].id,
            away_team_id=teams["embakasi_predators"].id,
            match_code="NRHL-001",
            scheduled_start=dt(2026, 5, 9, 9, 0),
            scheduled_end=dt(2026, 5, 9, 10, 30),
            actual_start=dt(2026, 5, 9, 9, 5),
            actual_end=dt(2026, 5, 9, 10, 27),
            status=MatchStatus.FINAL,
            match_format=MatchFormat.LEAGUE,
            round_label="Week 1",
            home_score=4,
            away_score=2,
            winner_team_id=teams["westlands_wolves"].id,
        ),
        Match(
            id=uid("match:002"),
            tenant_id=tenant.id,
            competition_id=regular_season.id,
            season_id=season.id,
            venue_id=venues["karen_prep"].id,
            home_team_id=teams["karen_ridgebacks"].id,
            away_team_id=teams["kasarani_cyclones"].id,
            match_code="NRHL-002",
            scheduled_start=dt(2026, 5, 9, 11, 0),
            scheduled_end=dt(2026, 5, 9, 12, 30),
            actual_start=dt(2026, 5, 9, 11, 2),
            actual_end=dt(2026, 5, 9, 12, 26),
            status=MatchStatus.FINAL,
            match_format=MatchFormat.LEAGUE,
            round_label="Week 1",
            home_score=3,
            away_score=3,
            overtime_required=True,
            shootout_required=True,
            winner_team_id=teams["karen_ridgebacks"].id,
            notes="Karen wins shootout 2-1.",
        ),
        Match(
            id=uid("match:003"),
            tenant_id=tenant.id,
            competition_id=regular_season.id,
            season_id=season.id,
            venue_id=venues["embakasi_msc"].id,
            home_team_id=teams["embakasi_predators"].id,
            away_team_id=teams["karen_ridgebacks"].id,
            match_code="NRHL-003",
            scheduled_start=dt(2026, 5, 16, 10, 0),
            scheduled_end=dt(2026, 5, 16, 11, 30),
            status=MatchStatus.SCHEDULED,
            match_format=MatchFormat.LEAGUE,
            round_label="Week 2",
        ),
        Match(
            id=uid("match:004"),
            tenant_id=tenant.id,
            competition_id=regular_season.id,
            season_id=season.id,
            venue_id=venues["kasarani_annex"].id,
            home_team_id=teams["kasarani_cyclones"].id,
            away_team_id=teams["westlands_wolves"].id,
            match_code="NRHL-004",
            scheduled_start=dt(2026, 5, 16, 12, 0),
            scheduled_end=dt(2026, 5, 16, 13, 30),
            status=MatchStatus.SCHEDULED,
            match_format=MatchFormat.LEAGUE,
            round_label="Week 2",
        ),
        Match(
            id=uid("match:005"),
            tenant_id=tenant.id,
            competition_id=championship.id,
            bracket_round_id=final_round.id,
            season_id=season.id,
            venue_id=venues["karen_prep"].id,
            home_team_id=teams["westlands_wolves"].id,
            away_team_id=teams["karen_ridgebacks"].id,
            match_code="NRHL-FINAL-01",
            scheduled_start=dt(2026, 8, 29, 14, 0),
            scheduled_end=dt(2026, 8, 29, 16, 0),
            status=MatchStatus.SCHEDULED,
            match_format=MatchFormat.KNOCKOUT,
            round_label="Grand Final",
            sequence_in_round=1,
            notes="Placeholder final seeded with projected Western finalists for demo purposes.",
        ),
    ]
    session.add_all(matches)

    stat_rows = [
        ("match:001", "westlands_wolves", 9, 2, 1, 0, 0, 1260),
        ("match:001", "westlands_wolves", 17, 1, 1, 0, 0, 1185),
        ("match:001", "westlands_wolves", 4, 0, 1, 1, 2, 1210),
        ("match:001", "embakasi_predators", 13, 1, 0, 0, 0, 1245),
        ("match:001", "embakasi_predators", 18, 1, 0, 1, 2, 1170),
        ("match:001", "embakasi_predators", 6, 0, 1, 0, 0, 1225),
        ("match:002", "karen_ridgebacks", 10, 1, 1, 0, 0, 1320),
        ("match:002", "karen_ridgebacks", 11, 1, 0, 0, 0, 1190),
        ("match:002", "karen_ridgebacks", 5, 0, 1, 1, 2, 1280),
        ("match:002", "kasarani_cyclones", 14, 2, 0, 0, 0, 1305),
        ("match:002", "kasarani_cyclones", 20, 1, 1, 1, 2, 1215),
        ("match:002", "kasarani_cyclones", 7, 0, 1, 0, 0, 1270),
    ]

    player_by_team_jersey = {}
    for roster in rosters:
        player_by_team_jersey[(roster.team_id, roster.jersey_number)] = roster.player_id

    stats = []
    for match_key, team_key, jersey, goals, assists, penalties, pim, tof in stat_rows:
        team_id = teams[team_key].id
        player_id = player_by_team_jersey[(team_id, jersey)]
        stats.append(
            PlayerMatchStat(
                id=uid(f"stat:{match_key}:{team_id}:{jersey}"),
                tenant_id=tenant.id,
                match_id=uid(match_key),
                player_id=player_id,
                team_id=team_id,
                goals=goals,
                assists=assists,
                points=goals + assists,
                shots_on_goal=max(goals + assists + 1, 1),
                penalties=penalties,
                penalty_minutes=pim,
                time_on_floor_seconds=tof,
                plus_minus=goals - penalties,
                stat_context={"source": "seed_data", "verified": True},
            )
        )
    session.add_all(stats)

    financials = [
        FinancialOperation(
            id=uid("finance:001"),
            tenant_id=tenant.id,
            match_id=uid("match:001"),
            operation_type=FinancialOperationType.MATCH_DAY,
            captured_match_hours=Decimal("1.50"),
            ticket_revenue_kes=Decimal("14500.00"),
            sponsorship_revenue_kes=Decimal("3500.00"),
            concession_revenue_kes=Decimal("2200.00"),
            facility_cost_kes=Decimal("5200.00"),
            officiating_cost_kes=Decimal("2500.00"),
            staffing_cost_kes=Decimal("1800.00"),
            medical_cost_kes=Decimal("700.00"),
            security_cost_kes=Decimal("600.00"),
            notes="Net yield comfortably above KES 5,000/hr target.",
        ),
        FinancialOperation(
            id=uid("finance:002"),
            tenant_id=tenant.id,
            match_id=uid("match:002"),
            operation_type=FinancialOperationType.MATCH_DAY,
            captured_match_hours=Decimal("1.40"),
            ticket_revenue_kes=Decimal("12600.00"),
            sponsorship_revenue_kes=Decimal("2800.00"),
            concession_revenue_kes=Decimal("1600.00"),
            facility_cost_kes=Decimal("4800.00"),
            officiating_cost_kes=Decimal("2500.00"),
            staffing_cost_kes=Decimal("1500.00"),
            medical_cost_kes=Decimal("650.00"),
            security_cost_kes=Decimal("500.00"),
            notes="Close benchmark case useful for efficiency analysis.",
        ),
    ]
    session.add_all(financials)

    session.commit()


def main() -> None:
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/nrhl")
    engine = build_engine(db_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        seed_sample_data(session)
    print("NRHL seed data loaded successfully.")


if __name__ == "__main__":
    main()
