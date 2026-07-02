# Data Sources Audit

Recherche-Stand: 2026-06-07.

## Empfohlene MVP-Quellen

| Bereich | Quelle | Status | Lizenz-/Risiko-Hinweis | MVP-Entscheidung |
| --- | --- | --- | --- | --- |
| Host Cities, Venue-Namen, Matchrahmen | FIFA public tournament pages | oeffentliche Referenz | Nicht ungeprueft massenhaft scrapen oder als eigene offizielle Datenbank republishen | Als Referenz dokumentieren, strukturierte Daten per CSV oder lizenzierter API importieren |
| Vollstaendiger Spielplan | OpenFootball `worldcup.json` | CC0/Public Domain | Inoffizielle Quelle, gegen FIFA plausibilisieren | Aktiv als maschinenlesbarer Schedule-Feed |
| Wetter Forecast | Open-Meteo Forecast API | gut geeignet | CC BY 4.0 Attribution, Rate Limits beachten | Aktiv im MVP |
| Historisches/Ist-Wetter | Open-Meteo Archive API | gut geeignet | CC BY 4.0 Attribution, Modell-/Reanalysecharakter transparent nennen | Aktiv im MVP |
| Laenderdaten | REST Countries API oder eigenes ISO-Mapping | geeignet | Verfuegbarkeit und Rate Limits pruefen | ISO, Namen, Hauptstaedte, Zeitzonen als CSV seedbar |
| Spielplan | FIFA public page, lizenzierte Sportdaten-API oder validierte CSV | kritisch | Vollstaendige Fixture-Replikation rechtlich pruefen | CSV/API-Import, keine ungepruefte Weiterverwertung |
| Sportdaten | lizenzierte Sportdaten-API oder strukturierte Datei | kritisch | Ranking, Form, Ergebnisse und Squad-Daten brauchen klare Lizenz/API-Key | Importadapter vorhanden, produktiv nur mit Vertrag/API-Key |
| Squad Age | lizenzierte Squad-Daten oder deaktiviert | kritisch | Kaderdaten koennen kurzfristig wechseln | `is_active_in_model=false`, bis Quelle geklaert |
| Fan-Proximity | Hauptstadt-/Kontinentdistanz aus strukturierten Stammdaten | geeignet | Kein Diaspora- oder Stimmungsschluss | Aktiv als Naeheindikator, kein Fanvorteil |

## Recherchierte Referenzen

- FIFA bestaetigt 16 Host Cities in Kanada, Mexiko und den USA.
- FIFA beschreibt den aktualisierten Spielplan mit 104 Matches und konkreten Kick-off-Zeiten.
- Open-Meteo bietet Forecast und historische Wetterdaten ohne API-Key, mit CC-BY-Attribution.
- REST Countries stellt ISO- und Laenderdaten ueber `v3.1` bereit.

## Daten im Projekt

- `data/full_schedule_openfootball.csv` enthaelt 104 Matches aus OpenFootball CC0.
- `data/full_teams_restcountries.csv` enthaelt 48 Team-Stammdaten aus REST Countries plus Teamcode-Overrides fuer England/Scotland.
- `data/live_weather_forecast.csv` enthaelt echte Open-Meteo-Forecasts im aktuellen Forecast-Horizont.
- `data/sample_venues.csv` sammelt die 16 Host-Venue-Referenzen mit Koordinaten, Zeitzonen, Hoehen und groben Kapazitaeten.
- `data/sample_schedule.csv` enthaelt einen kleinen recherchierten Fixture-Ausschnitt fuer lokale Tests.
- `data/world_cup_2026_groups.csv` enthaelt einen aktuellen Gruppen-Snapshot als Recherche- und Plausibilitaetsdatei.
- `data/data_sources_catalog.csv` haelt Quellen, URL, Lizenzstatus und Nutzungshinweise fest.

## Fallbacks

- Wetter fehlt: Score wird nicht erfunden, `data_quality_score` sinkt.
- Teamstaerke fehlt: neutraler Score 50.
- Squad Age fehlt: optionaler Score bleibt inaktiv.
- Vollstaendiger Spielplan fehlt: Website zeigt `Daten folgen` statt Annahmen.

## Offene Entscheidungen

- Welche lizenzierte Quelle liefert den finalen Vollspielplan, Ergebnisse und Sportdaten?
- Soll REST Countries live genutzt oder als versioniertes CSV-Mapping eingefroren werden?
- Welche Attribution soll im Frontend fuer Open-Meteo sichtbar sein?
- Welcher kommerzielle Sportdatenanbieter liefert FIFA-Ranking, Formkurve, Resultate und ggf. Elo im erlaubten Lizenzrahmen?
