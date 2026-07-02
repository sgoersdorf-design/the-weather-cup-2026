# Production Setup

## 1. Dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 2. Supabase/PostgreSQL

In `.env`:

```bash
DATABASE_URL=postgresql://postgres:PASSWORD@HOST:5432/postgres?sslmode=require
NEXT_PUBLIC_SUPABASE_URL=https://PROJECT_REF.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

Dann:

```bash
.venv/bin/python -m python.pipelines.db_setup
```

Ohne `DATABASE_URL` kann das Schema nicht ausgefuehrt werden.
Eine ausfuehrliche Anleitung fuer Supabase-Erstnutzer liegt in `docs/supabase_step_by_step.md`.

## 3. Echte Basisdaten abrufen

```bash
.venv/bin/python -m python.pipelines.fetch_openfootball_schedule --output data/full_schedule_openfootball.csv
.venv/bin/python -m python.pipelines.fetch_restcountries_teams --output data/full_teams_restcountries.csv
.venv/bin/python -m python.pipelines.generate_weather_profiles_from_teams --teams data/full_teams_restcountries.csv --output data/full_team_weather_profiles.csv
.venv/bin/python -m python.pipelines.fetch_open_meteo_csv --schedule data/full_schedule_openfootball.csv --venues data/sample_venues.csv --output data/live_weather_forecast_full.csv
```

## 4. Import-Reihenfolge

```bash
.venv/bin/python -m python.pipelines.import_data_sources --file data/data_sources_catalog.csv
.venv/bin/python -m python.pipelines.import_teams --file data/full_teams_restcountries.csv
.venv/bin/python -m python.pipelines.import_venues --file data/sample_venues.csv
.venv/bin/python -m python.pipelines.import_schedule --file data/full_schedule_openfootball.csv
.venv/bin/python -m python.pipelines.import_weather_profiles --file data/full_team_weather_profiles.csv
.venv/bin/python -m python.pipelines.import_weather_forecast --file data/live_weather_forecast_full.csv
.venv/bin/python -m python.pipelines.import_results --file data/full_schedule_openfootball.csv
```

Sportmetriken:

```bash
.venv/bin/python -m python.pipelines.import_sport_metrics --file data/sport_metrics_template.csv
```

Ersetze `sport_metrics_template.csv` durch eine Datei aus einem lizenzierten Anbieter.

## 5. Quellenstatus

- OpenFootball: CC0/Public Domain, guter Schedule-Feed.
- Open-Meteo: CC BY 4.0, Attribution erforderlich.
- REST Countries: oeffentliche API fuer Laenderstammdaten.
- FIFA: offizielle Referenz fuer Plausibilisierung, nicht als ungepruefte Scraping-Quelle.
- Sportmetriken: lizenzierten Anbieter/API-Key erforderlich.
