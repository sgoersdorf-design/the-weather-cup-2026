-- WM 2026 Context Lab - PostgreSQL / Supabase MVP Schema
-- Teams are represented with country names, ISO codes and flag emoji only.
-- No FIFA, association, club, team or sponsor logos are stored.

create extension if not exists "uuid-ossp";

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists data_sources (
  id uuid primary key default uuid_generate_v4(),
  source_name text not null unique,
  source_type text not null,
  source_url text,
  license_status text,
  usage_notes text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists teams (
  id uuid primary key default uuid_generate_v4(),
  name_de text not null,
  name_en text not null,
  iso2 char(2) not null unique,
  iso3 char(3) not null unique,
  flag_emoji text,
  confederation text,
  continent text,
  capital_city text,
  capital_latitude numeric(9,6),
  capital_longitude numeric(9,6),
  reference_timezone text,
  reference_timezone_method text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint teams_latitude_check check (capital_latitude is null or capital_latitude between -90 and 90),
  constraint teams_longitude_check check (capital_longitude is null or capital_longitude between -180 and 180)
);

create table if not exists venues (
  id uuid primary key default uuid_generate_v4(),
  stadium_name text not null,
  host_city text not null,
  host_country text not null,
  latitude numeric(9,6) not null,
  longitude numeric(9,6) not null,
  elevation_m numeric(8,2),
  timezone text not null,
  stadium_type_basic text not null default 'unknown',
  stadium_capacity integer,
  roof_available_boolean boolean not null default false,
  roof_type text,
  climate_control_available boolean not null default false,
  weather_protection_level integer,
  climate_control_note_de text,
  pitch_surface_note_de text,
  venue_weather_note_de text,
  capacity_source_note text,
  coordinate_precision text,
  coordinate_accuracy_m numeric(8,2),
  google_place_id text,
  maps_url text,
  coordinate_verified_at timestamptz,
  data_source_name text,
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (stadium_name, host_city),
  constraint venues_latitude_check check (latitude between -90 and 90),
  constraint venues_longitude_check check (longitude between -180 and 180),
  constraint venues_stadium_type_check check (stadium_type_basic in ('indoor', 'outdoor', 'retractable_roof', 'unknown')),
  constraint venues_quality_check check (data_quality_score between 0 and 100)
);

alter table if exists venues add column if not exists coordinate_accuracy_m numeric(8,2);
alter table if exists venues add column if not exists google_place_id text;
alter table if exists venues add column if not exists maps_url text;
alter table if exists venues add column if not exists coordinate_verified_at timestamptz;
alter table if exists venues add column if not exists roof_type text;
alter table if exists venues add column if not exists climate_control_available boolean not null default false;
alter table if exists venues add column if not exists weather_protection_level integer;
alter table if exists venues add column if not exists climate_control_note_de text;
alter table if exists venues add column if not exists pitch_surface_note_de text;
alter table if exists venues add column if not exists venue_weather_note_de text;
alter table if exists venues add column if not exists capacity_source_note text;

create table if not exists matches (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null unique,
  tournament_stage text,
  group_name text,
  matchday integer,
  matchday_label text,
  calendar_day integer,
  calendar_day_label text,
  date_utc timestamptz,
  local_date date,
  local_time time,
  local_timezone text,
  team_a_id uuid references teams(id),
  team_b_id uuid references teams(id),
  venue_id uuid references venues(id),
  result_team_a integer,
  result_team_b integer,
  match_status text not null default 'scheduled',
  data_source_name text,
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint matches_status_check check (match_status in ('scheduled', 'live', 'finished', 'postponed', 'cancelled', 'unknown')),
  constraint matches_quality_check check (data_quality_score between 0 and 100)
);

alter table if exists matches add column if not exists matchday_label text;
alter table if exists matches add column if not exists calendar_day integer;
alter table if exists matches add column if not exists calendar_day_label text;

create table if not exists players (
  id uuid primary key default uuid_generate_v4(),
  team_id uuid not null references teams(id) on delete cascade,
  player_name text not null,
  preferred_name text,
  shirt_number integer,
  position_group text,
  date_of_birth date,
  is_goalkeeper boolean not null default false,
  is_active boolean not null default true,
  data_source_name text,
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (team_id, player_name),
  constraint players_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists match_team_sheets (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  team_id uuid not null references teams(id) on delete cascade,
  formation text,
  coach_name text,
  captain_player_id uuid references players(id) on delete set null,
  hydration_break_planned boolean,
  notes text,
  data_source_name text,
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (match_id, team_id),
  constraint match_team_sheets_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists match_player_appearances (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  team_id uuid not null references teams(id) on delete cascade,
  player_id uuid not null references players(id) on delete cascade,
  appearance_role text not null default 'bench',
  shirt_number integer,
  position_label text,
  lineup_slot text,
  minute_in integer,
  minute_out integer,
  minutes_played integer,
  is_captain boolean not null default false,
  is_goalkeeper boolean not null default false,
  data_source_name text,
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (match_id, team_id, player_id),
  constraint match_player_appearances_role_check check (appearance_role in ('starter', 'bench', 'unused')),
  constraint match_player_appearances_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists match_events (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  source_row_key text unique,
  team_id uuid references teams(id) on delete set null,
  beneficiary_team_id uuid references teams(id) on delete set null,
  player_id uuid references players(id) on delete set null,
  related_player_id uuid references players(id) on delete set null,
  event_type text not null,
  minute integer not null,
  stoppage_minute integer,
  period text not null default 'unknown',
  scoreboard_team_a integer,
  scoreboard_team_b integer,
  notes text,
  data_source_name text,
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint match_events_type_check check (
    event_type in (
      'goal', 'own_goal', 'penalty_goal', 'missed_penalty',
      'yellow_card', 'red_card', 'sub_in', 'sub_out',
      'hydration_break_start', 'hydration_break_end', 'var_overturn', 'other'
    )
  ),
  constraint match_events_period_check check (period in ('1H', '2H', 'ET1', 'ET2', 'PEN', 'unknown')),
  constraint match_events_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists weather_historical (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  historical_avg_temp numeric(6,2),
  historical_min_temp numeric(6,2),
  historical_max_temp numeric(6,2),
  historical_precipitation numeric(8,2),
  historical_humidity numeric(6,2),
  historical_wind_speed numeric(6,2),
  historical_heat_index numeric(6,2),
  historical_weather_years_count integer,
  historical_data_source text,
  last_updated_at timestamptz not null default now(),
  data_quality_score numeric(5,2) not null default 0,
  unique (match_id),
  constraint weather_historical_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists weather_forecast (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  forecast_temp numeric(6,2),
  forecast_min_temp numeric(6,2),
  forecast_max_temp numeric(6,2),
  forecast_precipitation_probability numeric(6,2),
  forecast_humidity numeric(6,2),
  forecast_wind_speed numeric(6,2),
  forecast_heat_index numeric(6,2),
  forecast_weather_code integer,
  forecast_last_updated timestamptz not null default now(),
  forecast_data_source text,
  data_quality_score numeric(5,2) not null default 0,
  unique (match_id),
  constraint weather_forecast_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists weather_actual (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  actual_temp numeric(6,2),
  actual_humidity numeric(6,2),
  actual_precipitation numeric(8,2),
  actual_wind_speed numeric(6,2),
  actual_heat_index numeric(6,2),
  actual_weather_code integer,
  actual_data_source text,
  actual_weather_last_updated timestamptz not null default now(),
  data_quality_score numeric(5,2) not null default 0,
  unique (match_id),
  constraint weather_actual_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists team_weather_profiles (
  id uuid primary key default uuid_generate_v4(),
  team_id uuid not null references teams(id) on delete cascade,
  reference_temp_c numeric(6,2),
  reference_humidity numeric(6,2),
  heat_tolerance_score numeric(5,2) not null default 50,
  humidity_tolerance_score numeric(5,2) not null default 50,
  rain_tolerance_score numeric(5,2) not null default 50,
  wind_tolerance_score numeric(5,2) not null default 50,
  profile_method text not null default 'structured_reference',
  data_source_name text,
  is_active boolean not null default true,
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (team_id, profile_method),
  constraint team_weather_profiles_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists weather_matchup_metrics (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  team_id uuid not null references teams(id) on delete cascade,
  source_weather_type text not null default 'forecast',
  weather_temp_c numeric(6,2),
  weather_humidity numeric(6,2),
  weather_wind_speed numeric(6,2),
  precipitation_probability numeric(6,2),
  weather_load_score numeric(5,2),
  weather_familiarity_score numeric(5,2),
  weather_tolerance_score numeric(5,2),
  effective_weather_load_score numeric(5,2),
  weather_fit_score numeric(5,2),
  weather_fit_label text,
  edge_team_role text,
  edge_gap numeric(5,2),
  explanation_de text,
  explanation_en text,
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (match_id, team_id, source_weather_type),
  constraint weather_matchup_source_check check (source_weather_type in ('forecast', 'actual', 'historical')),
  constraint weather_matchup_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists travel_metrics (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  team_id uuid not null references teams(id) on delete cascade,
  previous_match_id text,
  previous_host_city text,
  previous_latitude numeric(9,6),
  previous_longitude numeric(9,6),
  current_host_city text,
  current_latitude numeric(9,6),
  current_longitude numeric(9,6),
  distance_from_previous_venue_km numeric(9,2),
  estimated_travel_time_hours numeric(8,2),
  rest_days_since_previous_match numeric(6,2),
  hours_since_previous_kickoff numeric(8,2),
  net_recovery_hours_after_estimated_travel numeric(8,2),
  cumulative_travel_distance_km numeric(10,2),
  cumulative_timezone_shift numeric(8,2),
  cumulative_recovery_load numeric(8,2),
  travel_recovery_score numeric(5,2),
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (match_id, team_id),
  constraint travel_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists timezone_metrics (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  team_id uuid not null references teams(id) on delete cascade,
  team_reference_timezone text,
  previous_match_timezone text,
  current_match_timezone text,
  timezone_shift_from_previous_match numeric(6,2),
  timezone_shift_from_reference numeric(6,2),
  local_kickoff_time time,
  perceived_kickoff_time_reference time,
  days_since_timezone_shift numeric(6,2),
  circadian_load_score numeric(5,2),
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (match_id, team_id),
  constraint timezone_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists altitude_metrics (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  team_id uuid not null references teams(id) on delete cascade,
  current_venue_elevation_m numeric(8,2),
  previous_venue_elevation_m numeric(8,2),
  elevation_change_from_previous_match_m numeric(8,2),
  venue_altitude_factor numeric(5,2),
  altitude_load_score numeric(5,2),
  data_quality_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (match_id, team_id),
  constraint altitude_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists sport_metrics (
  id uuid primary key default uuid_generate_v4(),
  team_id uuid not null references teams(id) on delete cascade,
  fifa_ranking_position integer,
  fifa_ranking_points numeric(8,2),
  elo_rating numeric(8,2),
  recent_matches_played integer,
  recent_wins integer,
  recent_draws integer,
  recent_losses integer,
  recent_goals_for integer,
  recent_goals_against integer,
  basic_form_score numeric(5,2),
  team_strength_score numeric(5,2),
  data_source_name text,
  last_updated_at timestamptz not null default now(),
  data_quality_score numeric(5,2) not null default 0,
  constraint sport_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists squad_age_metrics (
  id uuid primary key default uuid_generate_v4(),
  team_id uuid not null references teams(id) on delete cascade,
  squad_average_age numeric(5,2),
  squad_median_age numeric(5,2),
  share_players_over_30 numeric(5,2),
  share_players_under_24 numeric(5,2),
  squad_age_data_source text,
  squad_age_last_updated timestamptz,
  squad_age_resilience_score numeric(5,2),
  is_active_in_model boolean not null default false,
  data_quality_score numeric(5,2) not null default 0,
  constraint squad_age_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists fan_proximity_metrics (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  team_id uuid not null references teams(id) on delete cascade,
  host_country_team_boolean boolean not null default false,
  host_region_proximity_score numeric(5,2),
  distance_team_capital_to_venue_km numeric(9,2),
  distance_team_country_centroid_to_venue_km numeric(9,2),
  same_continent_boolean boolean not null default false,
  official_host_advantage_boolean boolean not null default false,
  fan_proximity_score numeric(5,2),
  data_quality_score numeric(5,2) not null default 0,
  unique (match_id, team_id),
  constraint fan_proximity_quality_check check (data_quality_score between 0 and 100)
);

create table if not exists predictions (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  predicted_result_category text not null default 'unknown',
  probability_team_a_win numeric(5,2),
  probability_draw numeric(5,2),
  probability_team_b_win numeric(5,2),
  main_context_advantage text,
  biggest_load_factor text,
  uncertainty_level text not null default 'unknown',
  explanation_de text,
  explanation_en text,
  social_hook_de text,
  social_hook_en text,
  website_teaser_de text,
  website_teaser_en text,
  model_version text not null default 'mvp_0_1',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (match_id),
  constraint predictions_category_check check (predicted_result_category in ('team_a_win', 'draw', 'team_b_win', 'unknown')),
  constraint predictions_uncertainty_check check (uncertainty_level in ('low', 'medium', 'high', 'unknown'))
);

create table if not exists generated_texts (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  language text not null,
  content_type text not null,
  headline text,
  subheadline text,
  teaser text,
  body text,
  social_hook text,
  generated_from_data_hash text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint generated_texts_language_check check (language in ('de', 'en')),
  unique (match_id, language, content_type)
);

create table if not exists post_match_evaluations (
  id uuid primary key default uuid_generate_v4(),
  match_id text not null references matches(match_id) on delete cascade,
  prediction_correct_boolean boolean,
  prediction_vs_reality_de text,
  prediction_vs_reality_en text,
  weather_check_de text,
  weather_check_en text,
  model_learning_note_de text,
  model_learning_note_en text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (match_id)
);

create table if not exists analysis_reports (
  id uuid primary key default uuid_generate_v4(),
  scope_type text not null,
  scope_key text not null,
  language text not null,
  title text,
  summary text,
  body text,
  metrics_json jsonb,
  generated_from_data_hash text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint analysis_reports_scope_check check (scope_type in ('match', 'matchday', 'phase', 'tournament')),
  constraint analysis_reports_language_check check (language in ('de', 'en')),
  unique (scope_type, scope_key, language)
);

create table if not exists ad_partners (
  id uuid primary key default uuid_generate_v4(),
  partner_key text not null unique,
  partner_name text not null,
  contact_email text,
  partner_type text not null default 'direct',
  status text not null default 'active',
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ad_partners_status_check check (status in ('active', 'paused', 'archived')),
  constraint ad_partners_type_check check (partner_type in ('direct', 'agency', 'network', 'internal'))
);

create table if not exists ad_campaigns (
  id uuid primary key default uuid_generate_v4(),
  campaign_key text not null unique,
  partner_id uuid references ad_partners(id) on delete set null,
  campaign_name text not null,
  booking_status text not null default 'draft',
  starts_at timestamptz,
  ends_at timestamptz,
  priority integer not null default 50,
  targeting_json jsonb,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ad_campaigns_status_check check (booking_status in ('draft', 'ready', 'active', 'paused', 'ended', 'archived'))
);

create table if not exists ad_creatives (
  id uuid primary key default uuid_generate_v4(),
  creative_key text not null unique,
  campaign_id uuid references ad_campaigns(id) on delete cascade,
  creative_name text not null,
  creative_type text not null default 'html',
  label text not null default 'Anzeige',
  headline text,
  body text,
  call_to_action text,
  image_url text,
  click_url text,
  tracking_pixel_url text,
  alt_text text,
  background_color text,
  text_color text,
  width integer,
  height integer,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ad_creatives_type_check check (creative_type in ('html', 'image', 'native', 'network_tag'))
);

create table if not exists ad_slots (
  id uuid primary key default uuid_generate_v4(),
  slot_key text not null unique,
  section_key text not null,
  placement_key text not null,
  display_name text not null,
  allowed_sizes text,
  max_width integer,
  min_height integer,
  device_targeting text not null default 'all',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ad_slots_device_check check (device_targeting in ('all', 'mobile', 'desktop'))
);

create table if not exists ad_placements (
  id uuid primary key default uuid_generate_v4(),
  slot_id uuid not null references ad_slots(id) on delete cascade,
  creative_id uuid not null references ad_creatives(id) on delete cascade,
  starts_at timestamptz,
  ends_at timestamptz,
  priority integer not null default 50,
  weight integer not null default 100,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (slot_id, creative_id)
);

create table if not exists import_logs (
  id uuid primary key default uuid_generate_v4(),
  import_type text not null,
  source_file text,
  rows_processed integer not null default 0,
  rows_inserted integer not null default 0,
  rows_updated integer not null default 0,
  rows_failed integer not null default 0,
  status text not null default 'completed',
  error_message text,
  created_at timestamptz not null default now()
);

create index if not exists idx_matches_date_utc on matches(date_utc);
create index if not exists idx_matches_teams on matches(team_a_id, team_b_id);
create index if not exists idx_matches_venue on matches(venue_id);
create index if not exists idx_players_team on players(team_id);
create index if not exists idx_match_team_sheets_match on match_team_sheets(match_id);
create index if not exists idx_match_team_sheets_team on match_team_sheets(team_id);
create index if not exists idx_match_player_appearances_match on match_player_appearances(match_id);
create index if not exists idx_match_player_appearances_team on match_player_appearances(team_id);
create index if not exists idx_match_player_appearances_player on match_player_appearances(player_id);
create index if not exists idx_match_events_match on match_events(match_id);
create index if not exists idx_match_events_team on match_events(team_id);
create index if not exists idx_match_events_beneficiary_team on match_events(beneficiary_team_id);
create index if not exists idx_match_events_player on match_events(player_id);
create index if not exists idx_match_events_type on match_events(event_type);
create index if not exists idx_travel_team on travel_metrics(team_id);
create index if not exists idx_timezone_team on timezone_metrics(team_id);
create index if not exists idx_altitude_team on altitude_metrics(team_id);
create index if not exists idx_fan_team on fan_proximity_metrics(team_id);
create index if not exists idx_sport_team on sport_metrics(team_id);
create index if not exists idx_team_weather_profiles_team on team_weather_profiles(team_id);
create index if not exists idx_weather_matchup_match on weather_matchup_metrics(match_id);
create index if not exists idx_weather_matchup_team on weather_matchup_metrics(team_id);
create index if not exists idx_analysis_reports_scope on analysis_reports(scope_type, scope_key);
create index if not exists idx_generated_texts_match on generated_texts(match_id);
create index if not exists idx_ad_campaigns_partner on ad_campaigns(partner_id);
create index if not exists idx_ad_creatives_campaign on ad_creatives(campaign_id);
create index if not exists idx_ad_placements_slot on ad_placements(slot_id);
create index if not exists idx_ad_placements_creative on ad_placements(creative_id);

drop trigger if exists set_data_sources_updated_at on data_sources;
create trigger set_data_sources_updated_at before update on data_sources for each row execute function set_updated_at();

drop trigger if exists set_teams_updated_at on teams;
create trigger set_teams_updated_at before update on teams for each row execute function set_updated_at();

drop trigger if exists set_venues_updated_at on venues;
create trigger set_venues_updated_at before update on venues for each row execute function set_updated_at();

drop trigger if exists set_matches_updated_at on matches;
create trigger set_matches_updated_at before update on matches for each row execute function set_updated_at();

drop trigger if exists set_players_updated_at on players;
create trigger set_players_updated_at before update on players for each row execute function set_updated_at();

drop trigger if exists set_match_team_sheets_updated_at on match_team_sheets;
create trigger set_match_team_sheets_updated_at before update on match_team_sheets for each row execute function set_updated_at();

drop trigger if exists set_match_player_appearances_updated_at on match_player_appearances;
create trigger set_match_player_appearances_updated_at before update on match_player_appearances for each row execute function set_updated_at();

drop trigger if exists set_match_events_updated_at on match_events;
create trigger set_match_events_updated_at before update on match_events for each row execute function set_updated_at();

drop trigger if exists set_travel_metrics_updated_at on travel_metrics;
create trigger set_travel_metrics_updated_at before update on travel_metrics for each row execute function set_updated_at();

drop trigger if exists set_timezone_metrics_updated_at on timezone_metrics;
create trigger set_timezone_metrics_updated_at before update on timezone_metrics for each row execute function set_updated_at();

drop trigger if exists set_altitude_metrics_updated_at on altitude_metrics;
create trigger set_altitude_metrics_updated_at before update on altitude_metrics for each row execute function set_updated_at();

drop trigger if exists set_predictions_updated_at on predictions;
create trigger set_predictions_updated_at before update on predictions for each row execute function set_updated_at();

drop trigger if exists set_generated_texts_updated_at on generated_texts;
create trigger set_generated_texts_updated_at before update on generated_texts for each row execute function set_updated_at();

drop trigger if exists set_post_match_evaluations_updated_at on post_match_evaluations;
create trigger set_post_match_evaluations_updated_at before update on post_match_evaluations for each row execute function set_updated_at();

drop trigger if exists set_team_weather_profiles_updated_at on team_weather_profiles;
create trigger set_team_weather_profiles_updated_at before update on team_weather_profiles for each row execute function set_updated_at();

drop trigger if exists set_weather_matchup_metrics_updated_at on weather_matchup_metrics;
create trigger set_weather_matchup_metrics_updated_at before update on weather_matchup_metrics for each row execute function set_updated_at();

drop trigger if exists set_analysis_reports_updated_at on analysis_reports;
create trigger set_analysis_reports_updated_at before update on analysis_reports for each row execute function set_updated_at();

drop trigger if exists set_ad_partners_updated_at on ad_partners;
create trigger set_ad_partners_updated_at before update on ad_partners for each row execute function set_updated_at();

drop trigger if exists set_ad_campaigns_updated_at on ad_campaigns;
create trigger set_ad_campaigns_updated_at before update on ad_campaigns for each row execute function set_updated_at();

drop trigger if exists set_ad_creatives_updated_at on ad_creatives;
create trigger set_ad_creatives_updated_at before update on ad_creatives for each row execute function set_updated_at();

drop trigger if exists set_ad_slots_updated_at on ad_slots;
create trigger set_ad_slots_updated_at before update on ad_slots for each row execute function set_updated_at();

drop trigger if exists set_ad_placements_updated_at on ad_placements;
create trigger set_ad_placements_updated_at before update on ad_placements for each row execute function set_updated_at();

-- Supabase security baseline:
-- Enable and force RLS on every public table.
-- Only expose explicitly website-safe tables as read-only to anon/authenticated roles.
do $$
declare
  table_name text;
  protected_tables text[] := array[
    'data_sources',
    'teams',
    'venues',
    'matches',
    'players',
    'match_team_sheets',
    'match_player_appearances',
    'match_events',
    'weather_historical',
    'weather_forecast',
    'weather_actual',
    'team_weather_profiles',
    'weather_matchup_metrics',
    'travel_metrics',
    'timezone_metrics',
    'altitude_metrics',
    'sport_metrics',
    'squad_age_metrics',
    'fan_proximity_metrics',
    'predictions',
    'generated_texts',
    'post_match_evaluations',
    'analysis_reports',
    'ad_partners',
    'ad_campaigns',
    'ad_creatives',
    'ad_slots',
    'ad_placements',
    'import_logs'
  ];
  public_read_tables text[] := array[
    'data_sources',
    'teams',
    'venues',
    'matches',
    'weather_forecast',
    'weather_actual',
    'team_weather_profiles',
    'weather_matchup_metrics',
    'travel_metrics',
    'timezone_metrics',
    'altitude_metrics',
    'sport_metrics',
    'fan_proximity_metrics',
    'predictions',
    'generated_texts',
    'analysis_reports',
    'ad_partners',
    'ad_campaigns',
    'ad_creatives',
    'ad_slots',
    'ad_placements'
  ];
begin
  foreach table_name in array protected_tables loop
    execute format('alter table public.%I enable row level security', table_name);
    execute format('alter table public.%I force row level security', table_name);
    execute format('drop policy if exists %I_public_read on public.%I', table_name, table_name);
  end loop;

  foreach table_name in array public_read_tables loop
    execute format(
      'create policy %I_public_read on public.%I for select to anon, authenticated using (true)',
      table_name,
      table_name
    );
  end loop;
end
$$;
