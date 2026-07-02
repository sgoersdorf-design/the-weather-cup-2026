# WM 2026 Context Lab

Automatisiertes, zweisprachiges MVP für datenjournalistische WM-2026-Match-Kontexte. Das System importiert strukturierte Daten, berechnet transparente Kontextindikatoren und erzeugt deutsche sowie englische Website- und Social-Texte ohne manuelle Recherche im laufenden Betrieb.

## MVP-Scope

- Spielplan, Teams und Venues aus CSV/JSON oder lizenzierter API importieren
- Wetterhistorie, Forecast und Ist-Wetter über Open-Meteo verarbeiten
- Weather Fit pro Team berechnen: Wer kommt mit der konkreten Wettersituation voraussichtlich besser klar?
- Reise-, Erholungs-, Zeitzonen-, Höhen- und Fan-Proximity-Indikatoren berechnen
- Basic Team Strength aus strukturierten Sportdaten integrieren
- Transparente Prognose mit Unsicherheitsgrad erzeugen
- Match Cards, Social-Templates und Post-Match-Updates zweisprachig generieren
- Website-Datenvertrag für Next.js/Supabase bereitstellen

## Ausgeschlossen

- FIFA-, Team-, Verbands-, Club- oder Sponsorenlogos
- manuell recherchierte Stadionbeschreibungen
- Diaspora-Schaetzungen und Fan-Stimmungsprognosen
- Trainingscamp-, Verletzungs-, Sperren- und Startelfdaten im MVP
- tiefe Taktik, xG, Pressing- oder Passnetzwerkmodelle
- Wettmodell-Wording oder sichere Ergebnisversprechen

## Struktur

```text
sql/                 PostgreSQL/Supabase-Schema
python/config.py     zentrale Konfiguration
python/db.py         SQLAlchemy Engine und Connection-Test
python/scoring/      transparente Score-Funktionen
python/pipelines/    CSV-Importe, Wetter, Kontext, Prognosen, Texte
python/utils/        Geo-, Zeitzonen- und Qualitätshelfer
data/                Templates, Sample-Daten, Quellenkatalog
content/             DE/EN Match-, Social- und Disclaimer-Templates
website/             Next.js-Konzept und Datenvertrag
docs/                Datenquellen, Methodik, Redaktion, Roadmap
prompts/             Entwicklungs-Prompts
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

In `.env` wird für Datenbankfunktionen `DATABASE_URL` gesetzt. Open-Meteo braucht für den MVP keinen API-Key; Attribution und Lizenzhinweise bleiben erforderlich.

Supabase-Erstsetup ohne Entwicklerkenntnisse: `docs/supabase_step_by_step.md`.

## Datenimport

Templates:

- `data/teams_template.csv`
- `data/venues_template.csv`
- `data/schedule_template.csv`
- `data/players_template.csv`
- `data/match_team_sheets_template.csv`
- `data/match_player_appearances_template.csv`
- `data/match_events_template.csv`

Samples:

- `data/sample_teams.csv`
- `data/sample_venues.csv` mit allen 16 Host-Venue-Referenzen
- `data/sample_schedule.csv` mit kleinem recherchiertem Fixture-Ausschnitt
- `data/sample_team_weather_profiles.csv` mit MVP-Wetterprofilen
- `data/full_team_weather_profiles.csv` mit 48 transparent heuristischen Weather-Fit-Profilen
- `data/sample_weather_forecast.csv`, `data/sample_weather_actual.csv` und `data/sample_results.csv` für Pre-/Post-Match-Tests
- `data/ad_inventory.csv` mit nativen Werbeflächen und Demo-Platzierungen
- `data/full_schedule_openfootball.csv` mit 104 Matches aus OpenFootball CC0
- `data/full_teams_restcountries.csv` mit 48 Team-Stammdaten aus REST Countries plus Teamcode-Overrides
- `data/live_weather_forecast_full.csv` mit echten Open-Meteo-Forecasts für Matches im Forecast-Horizont
- `data/world_cup_2026_groups.csv` als aktueller Gruppen-Snapshot
- `data/data_sources_catalog.csv` mit Quellen und Lizenznotizen

Importbefehle:

```bash
python -m python.pipelines.import_data_sources --file data/data_sources_catalog.csv
python -m python.pipelines.import_teams --file data/sample_teams.csv
python -m python.pipelines.import_venues --file data/sample_venues.csv
python -m python.pipelines.import_schedule --file data/sample_schedule.csv
python -m python.pipelines.import_weather_profiles --file data/sample_team_weather_profiles.csv
python -m python.pipelines.import_weather_forecast --file data/live_weather_forecast_full.csv
python -m python.pipelines.import_results --file data/full_schedule_openfootball.csv
python -m python.pipelines.import_sport_metrics --file data/sport_metrics_template.csv
python -m python.pipelines.import_match_event_data --players data/players_template.csv --team-sheets data/match_team_sheets_template.csv --appearances data/match_player_appearances_template.csv --events data/match_events_template.csv --dry-run
```

Ohne `DATABASE_URL` geben die Skripte eine verständliche Setup-Meldung aus.

## Wetterpipeline

```bash
python -m python.pipelines.weather_open_meteo --match-id M001
```

Die Pipeline nutzt Open-Meteo Forecast für nahe Zukunft und Archive für historische bzw. nachträgliche Ist-Werte. Nicht verfügbare Wetterdaten senken `data_quality_score`, statt die gesamte Pipeline abzubrechen.

## Score-Berechnung

```bash
python -m python.scoring.scores
```

Das Modul berechnet u.a. Weather Load, Weather Familiarity, Travel Recovery, Circadian Load, Venue Altitude, Venue Type, Fan Proximity, Basic Team Strength und Unsicherheit.

## Kontextmetriken

```bash
python -m python.pipelines.context_metrics
python -m python.pipelines.context_metrics --all
```

Ohne DB liest der erste Befehl die Sample-CSV-Dateien und zeigt Beispielmetriken. Mit DB schreibt `--all` Reise-, Zeitzonen-, Höhen- und Fan-Proximity-Metriken für alle Matches mit feststehenden Teams.

## Lokale Validierung

```bash
python -m python.pipelines.validate_local
```

Der Befehl prüft CSVs, JSON-Templates, Sample-Kontextmetriken, Sample-Prognose und Sample-Texte ohne Datenbank, Netzwerk oder Drittanbieterpakete.

## Weather Fit MVP

Echte Datenpfade:

```bash
python -m python.pipelines.fetch_openfootball_schedule --output data/full_schedule_openfootball.csv
python -m python.pipelines.fetch_restcountries_teams --output data/full_teams_restcountries.csv
python -m python.pipelines.generate_weather_profiles_from_teams --teams data/full_teams_restcountries.csv --output data/full_team_weather_profiles.csv
python -m python.pipelines.fetch_open_meteo_csv --schedule data/full_schedule_openfootball.csv --venues data/sample_venues.csv --output data/live_weather_forecast_full.csv
```

Pre-Match:

```bash
python -m python.pipelines.weather_matchup
python -m python.pipelines.weather_matchup --all
```

Der erste Befehl berechnet lokale Sample-Matches. Mit DB schreibt `--all` den Weather Fit beider Teams, den Weather-Fit-Vorteil, Website-Teaser und Social Hooks für alle Matches mit Forecastdaten.

Post-Match:

```bash
python -m python.pipelines.weather_reports --format markdown --output reports/weather_mvp_report.md
```

Der Report aggregiert pro Partie, Spieltag, Turnierphase und Gesamtturnier. Er vergleicht Forecast Weather Fit, Ist-Wetter und Ergebnis nur als Kontextauswertung, nicht als Ursachenbeweis.

## Datenbank-Setup

```bash
python -m python.pipelines.db_setup --dry-run
python -m python.pipelines.db_setup
python -m python.pipelines.db_status
```

Der zweite Befehl benötigt `DATABASE_URL` in `.env` oder der Shell. Ohne Supabase/PostgreSQL-URL kann das Schema nicht real ausgeführt werden.

## Daten aktualisieren

```bash
python -m python.pipelines.refresh_mvp_data
```

Eine Anleitung für manuelle und 24h-Aktualisierung liegt in `docs/refresh_operations.md`.
Der Orchestrator führt vorab einen DNS-Check aus, nutzt Step-Timeouts und überspringt den optionalen Event-DB-Import sauber, falls Supabase per DNS gerade nicht erreichbar ist.
Kartenquellen und Lizenznotizen liegen in `docs/map_sources.md`.
Die Trennung zwischen Gruppenspieltag und Turniertag ist in `docs/matchday_logic.md` dokumentiert.
Die Entscheidung, Reisekontext ohne bestätigte Team-Basislager nicht sichtbar auszuspielen, liegt in `docs/basecamp_travel_decision.md`.
Der Leitfaden für Werbeflächen, Dienstleister und Kampagnenpflege liegt in `docs/ad_operations_guide.md`. Die öffentliche Darstellung ist derzeit per Feature-Schalter deaktiviert; Datenmodell und Aktivierungsweg bleiben vorbereitet.

## Netlify-Deploy

Für Git-basierte Netlify-Deploys ist die Publish-Konfiguration im Repo hinterlegt:

- `netlify.toml` setzt `website/deploy` als Publish-Verzeichnis
- ein Build-Command ist nicht erforderlich, wenn `website/deploy/index.html` lokal vor dem Push erzeugt wird

Empfohlener Ablauf:

1. `python -m python.pipelines.refresh_mvp_data`
2. Änderungen committen und nach `main` pushen
3. Netlify veröffentlicht den neuen Stand automatisch

## Sportdaten

Echte Ranking-, Form- und Elo-Daten brauchen eine lizenzierte Quelle oder einen API-Key. Der MVP enthält dafür `data/sport_metrics_template.csv` und `python.pipelines.import_sport_metrics`. Ohne Lizenzdaten bleiben Team-Strength-Werte neutral oder inaktiv.

Ergebnisse können mit `python.pipelines.import_results` aus einem result-ready Schedule/Feed aktualisiert werden. Der OpenFootball-Feed enthält vor Turnierstart leere Ergebnisfelder und später nutzbare Result-Felder, falls die Quelle aktualisiert wird.

## Textgenerierung

```bash
python -m python.pipelines.generate_texts
python -m python.pipelines.generate_predictions
python -m python.pipelines.generate_predictions --all
python -m python.pipelines.generate_texts --all
```

Die Textgenerierung ist bewusst templatebasiert. Es wird keine externe LLM-API benötigt.

## Post-Match-Update

```bash
python -m python.pipelines.post_match_update --match-id M001 --result-a 2 --result-b 1 --evaluate --regenerate-content
```

Der Post-Match-Pfad vergleicht Prognose und Ergebnis, prüft Forecast gegen Ist-Wetter und erzeugt zweisprachige Updates.

Für detaillierte Post-Match-Ereignisse stehen nun optionale Tabellen und CSV-Templates für Spieler, Team Sheets, Aufstellungen/Bank und Match-Events bereit. Damit können später Torschützen, Torzeiten, Wechsel, Hydration-Break-Marker und spielerbezogene Auswertungen sauber importiert werden.

Aus Event-CSV-Dateien lassen sich Timing- und Spielerstatistiken lokal auswerten:

```bash
python -m python.pipelines.event_tournament_stats --events data/match_events_template.csv --schedule data/full_schedule_openfootball.csv
```

Ohne echte Eventzeilen liefert der Befehl nur eine leere Struktur. Mit gepflegten Eventdaten sind damit u.a. 15-Minuten-Segmente, Frühstarter, Schlussphasen, Gegentorfenster und erste Spielerlevel-Auswertungen möglich.

Für die tägliche Aktualisierung erzeugt `python -m python.pipelines.refresh_mvp_data` jetzt zusätzlich diese Event-Dateien und nutzt sie direkt für den Website-Export:

```text
data/players.csv
data/match_team_sheets.csv
data/match_player_appearances.csv
data/match_events.csv
```

Empfohlene Quellen für diese vier Dateien:

1. FIFA Match Centre als Primärquelle für offizielle Torschützen, Torzeiten, Startelf, Bank, Wechsel und Hydration-Break-Marker.
2. ESPN- oder AP-Matchseiten als journalistische Zweitquelle zur Verifikation, wenn offizielle Ergebnis- oder Eventangaben verspätet sichtbar werden.

Die Feldlogik und das tägliche Betriebsmodell für Eventdaten sind in `docs/event_data_sources.md` beschrieben.

Optional kann der langsame Datenbank-Import der Eventdateien explizit zugeschaltet werden:

```bash
python -m python.pipelines.refresh_mvp_data --with-event-db-import
python -m python.pipelines.import_match_event_data --players data/players.csv --team-sheets data/match_team_sheets.csv --appearances data/match_player_appearances.csv --events data/match_events.csv
```

Der Website-Export verwendet Eventdaten bereits ohne DB-Import, solange `data/match_events.csv` und `data/match_player_appearances.csv` lokal vorliegen.

## Website-Konzept

Die Dateien unter `website/` beschreiben Next.js, TypeScript, Supabase, i18n, Karten- und Chart-Komponenten sowie JSON-Datenverträge für Match Cards, Rankings, Venues und Methodikseiten.

## Disclaimer

Das WM 2026 Context Lab bewertet Wetter-, Reise-, Höhen-, Zeitzonen- und Standortfaktoren als datenjournalistische Kontextindikatoren. Die Werte sind keine medizinischen Leistungsnachweise, keine Wettprognosen und kein Beweis dafür, dass ein einzelner Faktor ein Spielergebnis verursacht.

## Nächste Schritte

1. Supabase-Passwort in `.env` einsetzen und `sql/001_schema.sql` ausführen.
2. Vollständigen Spielplan aus erlaubter Quelle als CSV/API importieren.
3. Sportdatenanbieter für Ranking, Form, Ergebnisse und Squad-Age lizenzieren.
4. Wetter- und Kontextmetriken für alle Matches laufen lassen.
5. Next.js-Prototyp gegen Supabase-Datenvertrag bauen.
