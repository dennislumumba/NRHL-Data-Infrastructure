-- NRHL PostgreSQL schema export
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE organization_type_enum AS ENUM ('LEAGUE', 'TEAM_OPERATOR', 'FACILITY', 'PARTNER', 'SCHOOL', 'SPONSOR');

CREATE TYPE conference_side_enum AS ENUM ('WESTERN', 'EASTERN', 'CENTRAL', 'NORTHERN', 'SOUTHERN', 'OPEN');

CREATE TYPE owner_type_enum AS ENUM ('PERSON', 'ORGANIZATION', 'INVESTOR_GROUP');

CREATE TYPE player_position_enum AS ENUM ('GOALIE', 'DEFENDER', 'CENTER', 'WING', 'UTILITY');

CREATE TYPE roster_status_enum AS ENUM ('ACTIVE', 'RESERVE', 'INJURED', 'SUSPENDED', 'RELEASED');

CREATE TYPE competition_type_enum AS ENUM ('REGULAR_SEASON', 'PLAYOFFS', 'TOURNAMENT', 'SHOWCASE');

CREATE TYPE bracket_format_enum AS ENUM ('SINGLE_ELIMINATION', 'DOUBLE_ELIMINATION', 'ROUND_ROBIN', 'LADDER');

CREATE TYPE match_status_enum AS ENUM ('DRAFT', 'SCHEDULED', 'LIVE', 'FINAL', 'POSTPONED', 'CANCELLED', 'FORFEIT');

CREATE TYPE match_format_enum AS ENUM ('LEAGUE', 'GROUP_STAGE', 'KNOCKOUT', 'FRIENDLY');

CREATE TYPE event_type_enum AS ENUM ('GOAL', 'PENALTY', 'SHOT', 'FACEOFF', 'SAVE', 'SHIFT', 'NOTE');

CREATE TYPE penalty_type_enum AS ENUM ('MINOR', 'MAJOR', 'MISCONDUCT', 'MATCH', 'BENCH');

CREATE TYPE financial_operation_type_enum AS ENUM ('MATCH_DAY', 'FACILITY', 'SPONSORSHIP', 'OFFICIATING', 'MEDICAL', 'OTHER');


CREATE TABLE tenants (
	slug VARCHAR(80) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	city VARCHAR(80) NOT NULL, 
	country_code VARCHAR(2) DEFAULT 'KE' NOT NULL, 
	timezone_name VARCHAR(64) DEFAULT 'Africa/Nairobi' NOT NULL, 
	is_active BOOLEAN DEFAULT true NOT NULL, 
	settings JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (slug)
);


CREATE TABLE organizations (
	code VARCHAR(32) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	organization_type organization_type_enum NOT NULL, 
	parent_organization_id UUID, 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_organizations_tenant_code UNIQUE (tenant_id, code), 
	FOREIGN KEY(parent_organization_id) REFERENCES organizations (id) ON DELETE SET NULL, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_organizations_tenant_id ON organizations (tenant_id);


CREATE TABLE players (
	first_name VARCHAR(80) NOT NULL, 
	last_name VARCHAR(80) NOT NULL, 
	display_name VARCHAR(160) NOT NULL, 
	date_of_birth DATE, 
	gender VARCHAR(32), 
	handedness VARCHAR(16), 
	primary_position player_position_enum NOT NULL, 
	secondary_position player_position_enum, 
	jersey_preference INTEGER, 
	athlete_id UUID, 
	performance_id VARCHAR(64) NOT NULL, 
	national_id_ref VARCHAR(64), 
	guardian_name VARCHAR(160), 
	guardian_phone VARCHAR(32), 
	medical_notes TEXT, 
	profile_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	is_active BOOLEAN DEFAULT true NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_players_tenant_performance_id UNIQUE (tenant_id, performance_id), 
	CONSTRAINT uq_players_tenant_athlete_id UNIQUE (tenant_id, athlete_id), 
	CONSTRAINT ck_players_jersey_preference CHECK (jersey_preference IS NULL OR jersey_preference BETWEEN 0 AND 99), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_players_tenant_performance_id ON players USING btree (tenant_id, performance_id);

CREATE INDEX ix_players_athlete_id ON players (athlete_id);

CREATE INDEX ix_players_tenant_athlete_id ON players USING btree (tenant_id, athlete_id);

CREATE INDEX ix_players_tenant_id ON players (tenant_id);

CREATE INDEX ix_players_performance_id ON players (performance_id);


CREATE TABLE seasons (
	organization_id UUID NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	slug VARCHAR(80) NOT NULL, 
	year INTEGER NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	is_active BOOLEAN DEFAULT false NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_seasons_tenant_slug UNIQUE (tenant_id, slug), 
	CONSTRAINT ck_seasons_date_window CHECK (end_date >= start_date), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_seasons_tenant_id ON seasons (tenant_id);


CREATE TABLE conferences (
	season_id UUID NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	code VARCHAR(24) NOT NULL, 
	side conference_side_enum NOT NULL, 
	rank_order INTEGER DEFAULT 1 NOT NULL, 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_conferences_season_code UNIQUE (season_id, code), 
	FOREIGN KEY(season_id) REFERENCES seasons (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_conferences_tenant_id ON conferences (tenant_id);


CREATE TABLE competitions (
	season_id UUID NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	slug VARCHAR(80) NOT NULL, 
	competition_type competition_type_enum NOT NULL, 
	description TEXT, 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_competitions_season_slug UNIQUE (season_id, slug), 
	FOREIGN KEY(season_id) REFERENCES seasons (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_competitions_tenant_id ON competitions (tenant_id);


CREATE TABLE regional_nodes (
	conference_id UUID NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	county VARCHAR(120) DEFAULT 'Nairobi County' NOT NULL, 
	sub_county VARCHAR(120), 
	neighbourhood VARCHAR(120), 
	latitude NUMERIC(9, 6), 
	longitude NUMERIC(9, 6), 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_regional_nodes_conf_name UNIQUE (tenant_id, conference_id, name), 
	FOREIGN KEY(conference_id) REFERENCES conferences (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_regional_nodes_tenant_id ON regional_nodes (tenant_id);


CREATE TABLE tournament_brackets (
	competition_id UUID NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	bracket_format bracket_format_enum NOT NULL, 
	bronze_match_enabled BOOLEAN DEFAULT false NOT NULL, 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(competition_id) REFERENCES competitions (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_tournament_brackets_tenant_id ON tournament_brackets (tenant_id);


CREATE TABLE venues (
	operator_organization_id UUID, 
	regional_node_id UUID, 
	name VARCHAR(160) NOT NULL, 
	address_line VARCHAR(255), 
	hourly_cost_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	capacity INTEGER, 
	indoor BOOLEAN DEFAULT false NOT NULL, 
	surface_type VARCHAR(80), 
	is_active BOOLEAN DEFAULT true NOT NULL, 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_venues_tenant_name UNIQUE (tenant_id, name), 
	CONSTRAINT ck_venues_hourly_cost_non_negative CHECK (hourly_cost_kes >= 0), 
	FOREIGN KEY(operator_organization_id) REFERENCES organizations (id) ON DELETE SET NULL, 
	FOREIGN KEY(regional_node_id) REFERENCES regional_nodes (id) ON DELETE SET NULL, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_venues_tenant_id ON venues (tenant_id);


CREATE TABLE bracket_rounds (
	bracket_id UUID NOT NULL, 
	round_number INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_bracket_round_number UNIQUE (bracket_id, round_number), 
	FOREIGN KEY(bracket_id) REFERENCES tournament_brackets (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_bracket_rounds_tenant_id ON bracket_rounds (tenant_id);


CREATE TABLE teams (
	operator_organization_id UUID, 
	conference_id UUID, 
	regional_node_id UUID, 
	home_venue_id UUID, 
	name VARCHAR(160) NOT NULL, 
	slug VARCHAR(80) NOT NULL, 
	short_name VARCHAR(48) NOT NULL, 
	primary_color VARCHAR(7), 
	secondary_color VARCHAR(7), 
	founded_on DATE, 
	ownership_model VARCHAR(80), 
	is_active BOOLEAN DEFAULT true NOT NULL, 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_teams_tenant_slug UNIQUE (tenant_id, slug), 
	CONSTRAINT uq_teams_tenant_name UNIQUE (tenant_id, name), 
	FOREIGN KEY(operator_organization_id) REFERENCES organizations (id) ON DELETE SET NULL, 
	FOREIGN KEY(conference_id) REFERENCES conferences (id) ON DELETE SET NULL, 
	FOREIGN KEY(regional_node_id) REFERENCES regional_nodes (id) ON DELETE SET NULL, 
	FOREIGN KEY(home_venue_id) REFERENCES venues (id) ON DELETE SET NULL, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_teams_tenant_id ON teams (tenant_id);


CREATE TABLE team_ownerships (
	team_id UUID NOT NULL, 
	owner_type owner_type_enum NOT NULL, 
	owner_name VARCHAR(160) NOT NULL, 
	owner_organization_id UUID, 
	stake_percentage NUMERIC(5, 2) DEFAULT 100.00 NOT NULL, 
	start_date DATE, 
	end_date DATE, 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_team_ownership_stake_pct CHECK (stake_percentage >= 0 AND stake_percentage <= 100), 
	FOREIGN KEY(team_id) REFERENCES teams (id) ON DELETE CASCADE, 
	FOREIGN KEY(owner_organization_id) REFERENCES organizations (id) ON DELETE SET NULL, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_team_ownerships_tenant_id ON team_ownerships (tenant_id);


CREATE TABLE roster_assignments (
	season_id UUID NOT NULL, 
	team_id UUID NOT NULL, 
	player_id UUID NOT NULL, 
	jersey_number INTEGER NOT NULL, 
	roster_status roster_status_enum DEFAULT 'ACTIVE' NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE, 
	notes TEXT, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_roster_season_team_player UNIQUE (season_id, team_id, player_id), 
	CONSTRAINT uq_roster_season_team_jersey UNIQUE (season_id, team_id, jersey_number), 
	CONSTRAINT ck_roster_jersey_number CHECK (jersey_number BETWEEN 0 AND 99), 
	FOREIGN KEY(season_id) REFERENCES seasons (id) ON DELETE CASCADE, 
	FOREIGN KEY(team_id) REFERENCES teams (id) ON DELETE CASCADE, 
	FOREIGN KEY(player_id) REFERENCES players (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_roster_assignments_tenant_id ON roster_assignments (tenant_id);


CREATE TABLE matches (
	competition_id UUID NOT NULL, 
	bracket_round_id UUID, 
	venue_id UUID, 
	home_team_id UUID NOT NULL, 
	away_team_id UUID NOT NULL, 
	winner_team_id UUID, 
	season_id UUID NOT NULL, 
	external_match_ref VARCHAR(64), 
	match_code VARCHAR(32) NOT NULL, 
	scheduled_start TIMESTAMP WITH TIME ZONE NOT NULL, 
	scheduled_end TIMESTAMP WITH TIME ZONE, 
	actual_start TIMESTAMP WITH TIME ZONE, 
	actual_end TIMESTAMP WITH TIME ZONE, 
	status match_status_enum DEFAULT 'SCHEDULED' NOT NULL, 
	match_format match_format_enum DEFAULT 'LEAGUE' NOT NULL, 
	round_label VARCHAR(64), 
	sequence_in_round INTEGER, 
	home_score INTEGER DEFAULT 0 NOT NULL, 
	away_score INTEGER DEFAULT 0 NOT NULL, 
	overtime_required BOOLEAN DEFAULT false NOT NULL, 
	shootout_required BOOLEAN DEFAULT false NOT NULL, 
	notes TEXT, 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_matches_distinct_teams CHECK (home_team_id <> away_team_id), 
	FOREIGN KEY(competition_id) REFERENCES competitions (id) ON DELETE CASCADE, 
	FOREIGN KEY(bracket_round_id) REFERENCES bracket_rounds (id) ON DELETE SET NULL, 
	FOREIGN KEY(venue_id) REFERENCES venues (id) ON DELETE SET NULL, 
	FOREIGN KEY(home_team_id) REFERENCES teams (id) ON DELETE RESTRICT, 
	FOREIGN KEY(away_team_id) REFERENCES teams (id) ON DELETE RESTRICT, 
	FOREIGN KEY(winner_team_id) REFERENCES teams (id) ON DELETE SET NULL, 
	FOREIGN KEY(season_id) REFERENCES seasons (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_matches_tenant_scheduled_start ON matches USING btree (tenant_id, scheduled_start);

CREATE INDEX ix_matches_tenant_id ON matches (tenant_id);

CREATE INDEX ix_matches_scheduled_start_brin ON matches USING brin (scheduled_start);


CREATE TABLE player_match_stats (
	match_id UUID NOT NULL, 
	player_id UUID NOT NULL, 
	team_id UUID NOT NULL, 
	goals INTEGER DEFAULT 0 NOT NULL, 
	assists INTEGER DEFAULT 0 NOT NULL, 
	points INTEGER DEFAULT 0 NOT NULL, 
	shots_on_goal INTEGER DEFAULT 0 NOT NULL, 
	penalties INTEGER DEFAULT 0 NOT NULL, 
	penalty_minutes INTEGER DEFAULT 0 NOT NULL, 
	time_on_floor_seconds INTEGER DEFAULT 0 NOT NULL, 
	plus_minus INTEGER DEFAULT 0 NOT NULL, 
	save_percentage NUMERIC(5, 4), 
	stat_context JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_player_match_stats_match_player UNIQUE (match_id, player_id), 
	CONSTRAINT ck_player_match_stats_non_negative CHECK (goals >= 0 AND assists >= 0 AND penalties >= 0 AND penalty_minutes >= 0), 
	CONSTRAINT ck_player_match_stats_tof_non_negative CHECK (time_on_floor_seconds >= 0), 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE, 
	FOREIGN KEY(player_id) REFERENCES players (id) ON DELETE CASCADE, 
	FOREIGN KEY(team_id) REFERENCES teams (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_player_match_stats_player_match ON player_match_stats USING btree (player_id, match_id);

CREATE INDEX ix_player_match_stats_tenant_id ON player_match_stats (tenant_id);


CREATE TABLE match_events (
	match_id UUID NOT NULL, 
	team_id UUID, 
	primary_player_id UUID, 
	secondary_player_id UUID, 
	tertiary_player_id UUID, 
	event_type event_type_enum NOT NULL, 
	penalty_type penalty_type_enum, 
	period_number INTEGER DEFAULT 1 NOT NULL, 
	event_second INTEGER DEFAULT 0 NOT NULL, 
	description TEXT, 
	penalty_minutes INTEGER, 
	event_payload JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE, 
	FOREIGN KEY(team_id) REFERENCES teams (id) ON DELETE SET NULL, 
	FOREIGN KEY(primary_player_id) REFERENCES players (id) ON DELETE SET NULL, 
	FOREIGN KEY(secondary_player_id) REFERENCES players (id) ON DELETE SET NULL, 
	FOREIGN KEY(tertiary_player_id) REFERENCES players (id) ON DELETE SET NULL, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_match_events_tenant_id ON match_events (tenant_id);

CREATE INDEX ix_match_events_match_period_time ON match_events USING btree (match_id, period_number, event_second);


CREATE TABLE financial_operations (
	match_id UUID NOT NULL, 
	operation_type financial_operation_type_enum DEFAULT 'MATCH_DAY' NOT NULL, 
	currency_code VARCHAR(3) DEFAULT 'KES' NOT NULL, 
	captured_match_hours NUMERIC(8, 2) DEFAULT 1.00 NOT NULL, 
	target_efficiency_kes_per_hour NUMERIC(12, 2) DEFAULT 5000.00 NOT NULL, 
	ticket_revenue_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	sponsorship_revenue_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	concession_revenue_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	broadcast_revenue_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	other_revenue_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	facility_cost_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	officiating_cost_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	staffing_cost_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	medical_cost_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	security_cost_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	other_cost_kes NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	total_revenue_kes NUMERIC(12, 2) GENERATED ALWAYS AS (COALESCE(ticket_revenue_kes, 0) + COALESCE(sponsorship_revenue_kes, 0) + COALESCE(concession_revenue_kes, 0) + COALESCE(broadcast_revenue_kes, 0) + COALESCE(other_revenue_kes, 0)) STORED NOT NULL, 
	total_cost_kes NUMERIC(12, 2) GENERATED ALWAYS AS (COALESCE(facility_cost_kes, 0) + COALESCE(officiating_cost_kes, 0) + COALESCE(staffing_cost_kes, 0) + COALESCE(medical_cost_kes, 0) + COALESCE(security_cost_kes, 0) + COALESCE(other_cost_kes, 0)) STORED NOT NULL, 
	net_yield_kes NUMERIC(12, 2) GENERATED ALWAYS AS ((COALESCE(ticket_revenue_kes, 0) + COALESCE(sponsorship_revenue_kes, 0) + COALESCE(concession_revenue_kes, 0) + COALESCE(broadcast_revenue_kes, 0) + COALESCE(other_revenue_kes, 0)) - (COALESCE(facility_cost_kes, 0) + COALESCE(officiating_cost_kes, 0) + COALESCE(staffing_cost_kes, 0) + COALESCE(medical_cost_kes, 0) + COALESCE(security_cost_kes, 0) + COALESCE(other_cost_kes, 0))) STORED NOT NULL, 
	yield_per_hour_kes NUMERIC(12, 2) GENERATED ALWAYS AS (CASE WHEN captured_match_hours > 0 THEN (((COALESCE(ticket_revenue_kes, 0) + COALESCE(sponsorship_revenue_kes, 0) + COALESCE(concession_revenue_kes, 0) + COALESCE(broadcast_revenue_kes, 0) + COALESCE(other_revenue_kes, 0)) - (COALESCE(facility_cost_kes, 0) + COALESCE(officiating_cost_kes, 0) + COALESCE(staffing_cost_kes, 0) + COALESCE(medical_cost_kes, 0) + COALESCE(security_cost_kes, 0) + COALESCE(other_cost_kes, 0))) / captured_match_hours) ELSE 0 END) STORED NOT NULL, 
	meets_efficiency_target BOOLEAN GENERATED ALWAYS AS (CASE WHEN captured_match_hours > 0 THEN ((((COALESCE(ticket_revenue_kes, 0) + COALESCE(sponsorship_revenue_kes, 0) + COALESCE(concession_revenue_kes, 0) + COALESCE(broadcast_revenue_kes, 0) + COALESCE(other_revenue_kes, 0)) - (COALESCE(facility_cost_kes, 0) + COALESCE(officiating_cost_kes, 0) + COALESCE(staffing_cost_kes, 0) + COALESCE(medical_cost_kes, 0) + COALESCE(security_cost_kes, 0) + COALESCE(other_cost_kes, 0))) / captured_match_hours) >= target_efficiency_kes_per_hour) ELSE false END) STORED NOT NULL, 
	notes TEXT, 
	metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	tenant_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_financial_operations_match_id UNIQUE (match_id), 
	CONSTRAINT ck_financial_ops_match_hours_non_negative CHECK (captured_match_hours >= 0), 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_financial_operations_tenant_id ON financial_operations (tenant_id);
