# Event-Daten fuer "Die Tor-Fakten zur WM"

## Ziel

Der Bereich braucht pro Spiel strukturierte Eventdaten, damit Tor-Minuten, Torschuetzen, Startelf, Wechsel, Spielerfenster und Hydration-Break-Muster belastbar ausgewertet werden koennen.

## Empfohlene Quellen

1. FIFA Match Centre
Primärquelle fuer:
- offizielles Endergebnis
- Torschuetzen
- Tor-Minuten inkl. Nachspielzeit
- Startaufstellungen beider Teams
- Einwechslungen und Auswechslungen
- Karten
- Hydration-Break-Hinweise, wenn im Match Centre als Event oder Match Note ausgewiesen

2. ESPN Match Pages
Sekundärquelle und derzeit technischer Fetch-Pfad fuer:
- unabhaengige Verifikation von Scorern und Minuten
- Startelf und Wechsel
- Plausibilitaetscheck bei spaet nachgezogenen offiziellen Details
- strukturierte Rueckbefuellung aus `site.api.espn.com` fuer einen grossen Teil der absolvierten Spiele

3. AP Match Reports
Sekundärquelle fuer:
- finale Ergebnisverifikation
- Torschuetzen und zentrale Spielszenen
- redaktionellen Cross-Check, falls strukturierte Daten fehlen

## Dateiziel im Projekt

Die taegliche Refresh-Kette importiert automatisch diese Dateien, sobald sie vorhanden sind:

```text
data/players.csv
data/match_team_sheets.csv
data/match_player_appearances.csv
data/match_events.csv
```

## Minimale Feldabdeckung

### `data/players.csv`
- `team_iso3`
- `player_name`
- optional: `preferred_name`, `shirt_number`, `position_group`, `is_goalkeeper`

### `data/match_team_sheets.csv`
- `match_id`
- `team_iso3`
- optional: `formation`, `coach_name`, `captain_player_name`, `hydration_break_planned`, `notes`

### `data/match_player_appearances.csv`
- `match_id`
- `team_iso3`
- `player_name`
- `appearance_role`
- optional: `shirt_number`, `position_label`, `lineup_slot`, `minute_in`, `minute_out`, `minutes_played`

### `data/match_events.csv`
- `match_id`
- `event_type`
- `minute`
- optional: `stoppage_minute`, `period`, `team_iso3`, `beneficiary_team_iso3`, `player_name`, `related_player_name`, `scoreboard_team_a`, `scoreboard_team_b`, `notes`

## Was daraus im Frontend entsteht

- Tore nach 15-Minuten-Fenstern
- Teams mit den meisten Toren je Zeitfenster
- Teams mit den meisten Gegentoren je Zeitfenster
- Fruehstarter
- Schlussphasen- und Crunchtime-Tore
- Tortrends erste Halbzeit vs. zweite Halbzeit
- Spielerfenster, sobald Torschuetzen je Event gepflegt sind
- Hydration-Break-Auswertung, sobald Break-Marker gepflegt sind

## Betriebsregel

Solange fuer ein beendetes Spiel keine Eventdaten vorliegen, zeigt der Bereich die Coverage offen an, statt Scheingenauigkeit zu erzeugen. Wetter bleibt ein Kontextsignal; Ist-Wetter bleibt offen, bis Open-Meteo Messdaten liefert.

## Stand 2026-06-24

Der automatisierte ESPN-Backfill deckt derzeit 37 von 48 absolvierten Spielen strukturiert ab. Fuer 11 Spiele weichen lokaler Spielplan und ESPN-Turnierfeed voneinander ab; diese Partien muessen bis auf Weiteres aus einer zweiten Quelle nachgezogen oder gegen FIFA Match Centre gegengeprueft werden.
