# Current Tournament Snapshot

Recherche-Stand: 2026-06-07.

## Turnierrahmen

- Zeitraum: 11. Juni bis 19. Juli 2026.
- Format: 48 Teams, 104 Spiele, 12 Gruppen mit je vier Teams.
- Gastgeber: Kanada, Mexiko und USA.
- Group Stage: 11. bis 27. Juni 2026.
- Round of 32: 28. Juni bis 3. Juli 2026.
- Round of 16: 4. bis 7. Juli 2026.
- Quarter-finals: 9. bis 11. Juli 2026.
- Semi-finals: 14. bis 15. Juli 2026.
- Third-place play-off: 18. Juli 2026.
- Final: 19. Juli 2026.

## Host Cities

Die 16 Host Cities sind Atlanta, Boston, Dallas, Guadalajara, Houston, Kansas City, Los Angeles, Mexico City, Miami, Monterrey, New York/New Jersey, Philadelphia, San Francisco Bay Area, Seattle, Toronto und Vancouver.

Die Venue-Stammdaten liegen in `data/sample_venues.csv`. Die Datei nutzt event-neutrale Venue-Namen wie `Mexico City Stadium`, `Dallas Stadium` und `New York New Jersey Stadium`, damit keine Sponsor-/Markenlogos oder Sponsoridentitaeten in der Darstellung erforderlich sind.

## Gruppen

Die aktuelle Gruppenuebersicht liegt als strukturierte CSV in `data/world_cup_2026_groups.csv`.

Wichtig: `team_code` ist als Wettbewerbs-/Teamcode zu verstehen. Fuer die meisten Teams entspricht er ISO3. Fuer England und Scotland werden Fussball-Teamcodes verwendet, weil sie keine eigenstaendigen ISO-3166-Laendercodes als Nationalteam darstellen.

## Nutzung im MVP

- `data/world_cup_2026_groups.csv` ist ein Recherche-Snapshot, nicht der produktive Importpfad fuer Team-Stammdaten.
- `data/sample_teams.csv` bleibt klein, damit lokale Tests schnell und uebersichtlich laufen.
- Ein produktiver Import sollte Gruppen- und Teamdaten aus einer erlaubten, versionierten Quelle uebernehmen und den Snapshot nur als Plausibilitaetsreferenz verwenden.

## Quellen

- FIFA Host-City- und Spielplanseiten: `https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026`
- FIFA Media Release zum aktualisierten 104-Spiele-Spielplan: `https://inside.fifa.com/organisation/media-releases/updated-world-cup-2026-match-schedule-venues-kick-off-times-104-matches`
- FourFourTwo Gruppen-/Fixture-Uebersicht, zuletzt aktualisiert am 26. Mai 2026: `https://www.fourfourtwo.com/features/fifa-world-cup-2026-dates-fixtures-stadiums-tickets-and-everything-you-need-to-know`
