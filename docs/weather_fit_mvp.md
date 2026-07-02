# Weather Fit MVP

## Produktfrage

Vor einem Spieltag sollen User auf Website und Social Media schnell sehen:

> Welches Team kommt mit der konkreten Wettersituation voraussichtlich besser klar?

Nach dem Spiel sollen Auswertungen pro Partie, Spieltag, Turnierphase und Gesamtturnier zeigen:

- Wie stark war die Wetterbelastung laut Forecast?
- Wie stark war sie im Ist-Wetter?
- Welches Team hatte den Forecast Weather Fit Edge?
- Hat das Team mit Weather Fit Edge gewonnen, nicht gewonnen oder gab es ein Remis?
- Wo gab es hohe Forecast-vs-Actual-Abweichungen?

## MVP-Bausteine

- `team_weather_profiles`: strukturierte Referenz- und Toleranzprofile pro Team
- `weather_matchup_metrics`: Weather Fit pro Match/Team fuer Forecast oder Actual Weather
- `analysis_reports`: speicherbare Reports fuer Match, Matchday, Phase und Tournament
- `python.pipelines.weather_matchup`: Pre-Match Website-/SoMe-Ausgabe
- `python.pipelines.weather_reports`: Post-Match Analyse und Markdown/JSON Report

## Lokale Demo

```bash
python -m python.pipelines.weather_matchup
python -m python.pipelines.weather_reports --format markdown --output reports/weather_mvp_report.md
```

## Redaktionelle Leitplanken

- Weather Fit ist kein Performance- oder Wettmodell.
- Ergebnisvergleiche sind deskriptiv, keine Ursachenbeweise.
- Wenn Forecast und Actual stark auseinanderliegen, muss das im Nachgang sichtbar sein.
- Bei niedriger Datenqualitaet wird Unsicherheit explizit genannt.
