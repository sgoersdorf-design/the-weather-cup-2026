# Spieltagslogik

Der MVP trennt zwei Begriffe, die im Spielplan leicht verwechselt werden:

## Gruppenspieltag

`matchday` meint den sportlichen Gruppenspieltag.

- `1` = 1. Gruppenspieltag: erste Partie-Runde aller Gruppen
- `2` = 2. Gruppenspieltag: zweite Partie-Runde aller Gruppen
- `3` = 3. Gruppenspieltag: dritte Partie-Runde aller Gruppen

Bei 48 Teams und 12 Gruppen umfasst jeder Gruppenspieltag 24 Partien. Der `1. Gruppenspieltag` laeuft im deutschen Anzeigeformat vom 11.06.2026 bis 18.06.2026.

Diese Logik wird fuer Website-Navigation, Matchday-Check, Wetterkarte und Spieltagsanalysen genutzt.

## Turniertag

`calendar_day` meint den operativen Turniertag beziehungsweise Tagesblock aus dem Spielplan-Feed.

Dieser Wert wird fuer Forecast-Abdeckung, taegliche Datenaktualisierung und operative Monitoring-Ansichten genutzt. Ein Turniertag ist nicht automatisch dasselbe wie ein Gruppenspieltag.

## Zeitdarstellung

Die Website zeigt Anstosszeiten in `Europe/Berlin`, damit sie zur deutschen Nutzung und zu deutschen Spielplanseiten passen. Die Host-Zeit bleibt im Matchdetail sichtbar.

## Importregel

Der OpenFootball-Fetcher berechnet den Gruppenspieltag aus der Reihenfolge der Partien innerhalb jeder Gruppe:

- Spiele 1 und 2 einer Gruppe: `1. Gruppenspieltag`
- Spiele 3 und 4 einer Gruppe: `2. Gruppenspieltag`
- Spiele 5 und 6 einer Gruppe: `3. Gruppenspieltag`

Die bisherige Tagesnummer aus dem Feed bleibt als `calendar_day` erhalten.
