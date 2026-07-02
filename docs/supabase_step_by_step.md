# Supabase Schritt-fuer-Schritt-Anleitung

Diese Anleitung erklaert, wofuer Supabase in diesem MVP gebraucht wird und wie du das Projekt ohne Programmierkenntnisse startklar machst.

## 1. Wofuer ist Supabase?

Supabase ist fuer dieses Projekt unsere zentrale Datenbank. Dort liegen spaeter:

- Teams, Spielorte und Spielplan
- Wetter-Forecasts und spaetere Ist-Wetterdaten
- Weather-Fit-Werte pro Team und Partie
- Pre-Match-Texte fuer Website und Social Media
- Post-Match-Auswertungen pro Partie, Spieltag, Turnierphase und Turnier

Ohne Supabase koennen wir lokal mit CSV-Dateien testen. Fuer ein echtes Website-MVP brauchen wir aber eine Datenbank, damit die Website, die Import-Skripte und die Reports auf dieselben Daten zugreifen.

## 2. Was bedeuten deine Supabase-Daten?

Du hast diese Werte geliefert:

- Project URL: `https://srcwznnkbhrtstqbkijx.supabase.co`
- Publishable Key: beginnt mit `sb_publishable_...`
- Direct Connection String: `postgresql://postgres:[YOUR-PASSWORD]@db.srcwznnkbhrtstqbkijx.supabase.co:5432/postgres`
- Project Ref: `srcwznnkbhrtstqbkijx`

Die Bedeutung:

- `Project URL`: Adresse deines Supabase-Projekts. Die Website nutzt sie, um Supabase zu erreichen.
- `Publishable Key`: oeffentlicher Frontend-Schluessel. Er darf in einer Website verwendet werden, solange Supabase-Rechte sauber ueber Row Level Security/Policies geregelt sind.
- `DATABASE_URL`: private Datenbankverbindung fuer unsere Backend-/Import-Skripte. Damit erstellen wir Tabellen und importieren Daten.
- `Project Ref`: technische Projekt-ID fuer Supabase CLI und Projektverknuepfung.

Wichtig: Der Publishable Key reicht nicht aus, um Tabellen anzulegen oder CSV-Daten per Python in die Datenbank zu importieren. Dafuer brauchen wir das echte Datenbank-Passwort in der `DATABASE_URL`.

## 3. Was ist schon vorbereitet?

Ich habe lokal diese Datei angelegt:

```text
/Users/steffengorsdorf/Documents/WM Projekt/.env
```

Darin stehen deine Supabase-Projektwerte bereits drin. Nur das Datenbank-Passwort fehlt noch:

```bash
DATABASE_URL=postgresql://postgres:REPLACE_WITH_DATABASE_PASSWORD@db.srcwznnkbhrtstqbkijx.supabase.co:5432/postgres?sslmode=require
```

Die Datei `.env` wird von Git ignoriert. Sie ist fuer lokale Zugangsdaten gedacht und soll nicht veroeffentlicht werden.

## 4. Datenbank-Passwort in Supabase finden oder neu setzen

1. Oeffne [supabase.com](https://supabase.com/) und logge dich ein.
2. Oeffne dein Projekt mit der Ref `srcwznnkbhrtstqbkijx`.
3. Klicke oben oder links im Projekt auf `Connect`, falls sichtbar.
4. Suche den Bereich fuer `Connection string` oder `Direct connection`.
5. Supabase zeigt dort den Connection String mit `[YOUR-PASSWORD]`.
6. Wenn du das Datenbank-Passwort noch kennst, verwende es.
7. Wenn du es nicht kennst, gehe in die Project Settings/Database Settings und setze das Datenbank-Passwort neu.

Nach dem Aendern oder Zuruecksetzen kann es kurz dauern, bis Supabase die neue Verbindung annimmt.

## 5. Passwort in `.env` einsetzen

1. Oeffne im Projektordner die Datei `.env`.
2. Suche diese Stelle:

```text
REPLACE_WITH_DATABASE_PASSWORD
```

3. Ersetze nur diesen Platzhalter durch dein echtes Datenbank-Passwort.
4. Lasse den Rest der Zeile unveraendert.
5. Speichere die Datei.

Beispiel:

```bash
DATABASE_URL=postgresql://postgres:DEIN_PASSWORT@db.srcwznnkbhrtstqbkijx.supabase.co:5432/postgres?sslmode=require
```

Falls dein Passwort Sonderzeichen wie `@`, `/`, `#`, `?`, `%` oder Leerzeichen enthaelt, muss es in der URL kodiert werden. Am einfachsten ist dann: Passwort hier nicht oeffentlich posten, sondern mir sagen, dass Sonderzeichen enthalten sind; ich kann dir dann erklaeren, wie du es lokal sicher einsetzt.

## 6. Verbindung testen

Wenn das Passwort eingetragen ist, fuehre ich oder du diesen Befehl im Projektordner aus:

```bash
.venv/bin/python -m python.db
```

Erwartete gute Meldung:

```text
Database connection ok: True
```

Wenn stattdessen eine Fehlermeldung kommt, sind die haeufigsten Ursachen:

- Passwort ist falsch oder noch der Platzhalter.
- Projekt ist pausiert oder noch nicht voll gestartet.
- Netzwerk kann die direkte Verbindung nicht erreichen.
- Passwort enthaelt Sonderzeichen und ist in der URL nicht kodiert.

## 7. Schema ausfuehren

Wenn die Verbindung funktioniert, legen wir die Tabellen an:

```bash
.venv/bin/python -m python.pipelines.db_setup
```

Das fuehrt die Datei aus:

```text
/Users/steffengorsdorf/Documents/WM Projekt/sql/001_schema.sql
```

Danach existieren in Supabase die Tabellen fuer Teams, Matches, Wetter, Scores, Prognosen, Texte und Post-Match-Auswertungen.

## 8. Basisdaten importieren

Nach dem Schema kommen die Daten in dieser Reihenfolge:

```bash
.venv/bin/python -m python.pipelines.import_data_sources --file data/data_sources_catalog.csv
.venv/bin/python -m python.pipelines.import_teams --file data/full_teams_restcountries.csv
.venv/bin/python -m python.pipelines.import_venues --file data/sample_venues.csv
.venv/bin/python -m python.pipelines.import_schedule --file data/full_schedule_openfootball.csv
.venv/bin/python -m python.pipelines.import_weather_profiles --file data/full_team_weather_profiles.csv
.venv/bin/python -m python.pipelines.import_weather_forecast --file data/live_weather_forecast_full.csv
.venv/bin/python -m python.pipelines.import_results --file data/full_schedule_openfootball.csv
```

Sportdaten werden erst importiert, wenn eine lizenzierte Quelle oder ein API-Key vorhanden ist:

```bash
.venv/bin/python -m python.pipelines.import_sport_metrics --file data/sport_metrics_template.csv
```

## 9. Weather-Fit-Auswertungen erzeugen

Wenn Daten importiert sind, koennen wir Pre-Match- und Reportdaten erzeugen:

```bash
.venv/bin/python -m python.pipelines.generate_predictions
.venv/bin/python -m python.pipelines.generate_texts
.venv/bin/python -m python.pipelines.weather_reports --format markdown --output reports/weather_mvp_report.md
```

Damit entsteht die Grundlage fuer:

- Website Match Cards
- Social-Media-Posts vor einem Spieltag
- Nachtraegliche Analyse pro Partie
- Tages-/Spieltag-Report
- Turnierphasen- und Abschlussreport

## 10. Was ist mit der Supabase CLI?

Die von Supabase vorgeschlagenen CLI-Befehle sind nuetzlich, aber fuer unseren ersten Datenbankstart nicht zwingend noetig:

```bash
supabase login
supabase init
supabase link --project-ref srcwznnkbhrtstqbkijx
```

Aktuell ist die Supabase CLI auf deinem Rechner in diesem Projektkontext nicht installiert. Das ist kein Blocker, weil wir das Schema und die Imports ueber `DATABASE_URL` ausfuehren koennen.

Die CLI wird spaeter sinnvoll, wenn wir:

- Datenbankmigrationen professionell versionieren
- lokale Supabase-Umgebungen starten
- Remote- und lokale Datenbank vergleichen
- TypeScript-Typen fuer die Website generieren

## 11. Wenn die direkte Verbindung nicht klappt

Supabase bietet mehrere Verbindungstypen. Die direkte Verbindung nutzt Port `5432`. Manche Netzwerke haben Probleme mit direkter IPv6-Verbindung. Dann nimm in Supabase unter `Connect` statt `Direct connection` den `Session pooler` oder `Transaction pooler` und ersetze die komplette `DATABASE_URL` in `.env`.

Fuer unsere Setup-Skripte ist wichtig:

- Die URL muss mit `postgresql://` oder `postgres://` beginnen.
- Sie muss das echte Passwort enthalten.
- Sie sollte am Ende `?sslmode=require` haben, falls Supabase es nicht automatisch anzeigt.

## 12. Sicherheitsregeln

- Nie einen `service_role` Key oder `sb_secret_...` Key in die Website einbauen.
- Nie `.env` in Git committen.
- Datenbank-Passwort nicht in oeffentlichen Chats, Issues oder Dokumenten speichern.
- Der Publishable Key ist fuer Browser-Apps gedacht, ersetzt aber keine Datenbankrechte.
- Spaeter fuer Website-Zugriff Row Level Security und Policies sauber setzen.

## 13. Offizielle Supabase-Referenzen

- Datenbankuebersicht: https://supabase.com/docs/guides/database/overview
- Datenbank verbinden: https://supabase.com/docs/guides/database/connecting-to-postgres
- API Keys verstehen: https://supabase.com/docs/guides/getting-started/api-keys
- Supabase CLI: https://supabase.com/docs/guides/cli/getting-started
