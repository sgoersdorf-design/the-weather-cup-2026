# Daten aktualisieren

Diese Anleitung beschreibt, wie die Website-Daten manuell, halbautomatisch oder automatisch alle 24 Stunden aktualisiert werden.

## Was wird aktualisiert?

Der Refresh-Lauf führt diese Schritte aus:

1. Spielplan/Ergebnisfeed aus OpenFootball aktualisieren.
2. DNS-Erreichbarkeit für GitHub, Open-Meteo, ESPN und Supabase vorab prüfen.
3. Wetter-Forecasts aus Open-Meteo für alle Matches im Forecast-Fenster abrufen. Ist der Standard-Endpunkt vorübergehend nicht erreichbar, verwendet die Pipeline automatisch den offiziellen Ensemble-Endpunkt und kennzeichnet diese Datensätze als Fallback.
4. Venue-/Stadiondaten aus `data/sample_venues.csv` in Supabase aktualisieren.
5. Spielplan, Ergebnisse, Werbung und Forecasts in Supabase importieren.
6. Reise-, Zeitzonen-, Höhen- und Fan-Proximity-Metriken neu berechnen.
7. Weather-Fit-Metriken und Weather-Fit-Texte neu generieren.
8. MVP-Prognosen und Match-Preview-Texte neu generieren.
9. Website-Datenexport `website/mvp/data.js` neu schreiben.
10. Standalone-Datei `website/mvp/wm-2026-weather-fit-mvp.html` neu bauen.
11. Upload-Datei `website/deploy/index.html` neu bauen.
12. Lokale Validierung, Build-Sanity-Check und Supabase-Status ausgeben.

Noch nicht automatisch enthalten sind lizenzierte Sportdaten, solange kein Anbieter/API-Key eingerichtet ist. Sobald ein erlaubter Ergebnis- oder Sportdatenanbieter vorhanden ist, wird er in diesen Refresh-Lauf eingebunden.

## Manuell aktualisieren

Im Projektordner:

```bash
.venv/bin/python -m python.pipelines.refresh_mvp_data
```

Oder per Doppelklick auf:

```text
/Users/steffengorsdorf/Documents/WM Projekt/scripts/refresh_mvp.command
```

Wenn du nur testen willst, welche Schritte laufen würden:

```bash
.venv/bin/python -m python.pipelines.refresh_mvp_data --dry-run
```

Wenn du externe Abrufe überspringen und nur aus vorhandenen CSV-/DB-Daten neu rechnen willst:

```bash
.venv/bin/python -m python.pipelines.refresh_mvp_data --skip-schedule-fetch --skip-weather-fetch
```

## Halbautomatisch aktualisieren

Halbautomatisch heißt: Du startest den Lauf selbst, aber alle Import-, Rechen-, Text-, Export- und HTML-Schritte laufen danach ohne weitere Eingriffe.

Empfohlener Befehl für einen schnellen sicheren Lauf ohne externe Abrufe:

```bash
.venv/bin/python -m python.pipelines.refresh_mvp_data --skip-schedule-fetch --skip-weather-fetch
```

Empfohlener Befehl für einen kompletten Lauf mit Abruf neuer Wetterdaten:

```bash
.venv/bin/python -m python.pipelines.refresh_mvp_data
```

Nach erfolgreichem Lauf:

- `website/mvp/data.js` enthält den aktuellen Datenstand.
- `website/mvp/wm-2026-weather-fit-mvp.html` ist die herunterladbare Einzeldatei.
- `website/deploy/index.html` ist die uploadfertige Startdatei für das Hosting.
- Browser neu laden.

## Täglich um 06:00 Uhr automatisch aktualisieren

macOS kann den Refresh mit `launchd` automatisch ausführen.

1. Öffne den Finder.
2. Gehe zu deinem Projektordner:

```text
/Users/steffengorsdorf/Documents/WM Projekt
```

3. Kopiere diese Datei:

```text
automation/com.wmprojekt.refresh-mvp.plist
```

4. Füge sie hier ein:

```text
/Users/steffengorsdorf/Library/LaunchAgents/
```

5. Öffne das Terminal und lade den Job:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.wmprojekt.refresh-mvp.plist
```

6. Zum sofortigen Testlauf:

```bash
launchctl kickstart gui/$(id -u)/com.wmprojekt.refresh-mvp
```

Die Logs liegen danach hier:

```text
/Users/steffengorsdorf/Documents/WM Projekt/logs/refresh_mvp.out.log
/Users/steffengorsdorf/Documents/WM Projekt/logs/refresh_mvp.err.log
```

Der Refresh ist inzwischen robuster gegenüber typischen Infrastrukturproblemen:

- Netzwerk-Schritte haben feste Timeouts statt endlos zu hängen.
- DNS-/Hostfehler werden vorab sichtbar gemacht.
- Ein optionaler Event-DB-Import wird bei Supabase-DNS-Problemen sauber übersprungen, damit Export und HTML-Build trotzdem fertig werden.
- Der lokale Browser-Check prüft die in die Standalone-Datei eingebetteten Daten und die Schedule-UX-Elemente direkt im Build.

## Automatik wieder deaktivieren

```bash
launchctl bootout gui/$(id -u)/com.wmprojekt.refresh-mvp
```

## Was sieht man danach auf der Website?

Nach jedem erfolgreichen Refresh sind `website/mvp/data.js` und `website/mvp/wm-2026-weather-fit-mvp.html` neu geschrieben. Wenn der lokale Server läuft, reicht ein Reload im Browser. Bei der lokalen Datei-Ansicht ebenfalls einfach die Seite neu laden.

Der Bereich `Turnierstand & Tabellen` nutzt denselben Datenstand:

- `Stand`: aktuelle Gruppentabellen aus echten Ergebnisfeldern.
- `Partien`: Analyse pro Partie.
- `Spieltage`: Aggregate pro Matchday.
- `Phasen`: Aggregate pro Turnierphase.
- `Report`: Kennzahlen, die später in den Abschlussreport einfließen.

## Live-Check nach jedem größeren Update

Diese Punkte sollten vor Veröffentlichung geprüft werden:

- Matchday lädt mit korrekter Anzahl an Partien.
- Wetterkarte zeigt Pins und Partien.
- Klick aus Wetterkarte auf `Im Matchday öffnen` springt zur richtigen Partie.
- Matchdetails zeigen Anstoßzeit in Nutzerzeit und Ortszeit.
- Stadionsektion zeigt Kapazität, Dach, Klimatisierung, Wetterschutz, Höhe und Venue-Hinweise.
- Werbeflächen sind sichtbar und klar als `Anzeige` markiert.
- Smartphone-Ansicht hat keinen horizontalen Scrollbalken.
- `python -m python.pipelines.validate_local` liefert `status: ok`.

## Produktive Restpunkte

Technisch kann die Website mit dem aktuellen Stand live betrieben werden. Für einen öffentlichen Produktivbetrieb bleiben diese externen Punkte zu klären:

- lizenzierter Ergebnis-/Sportdatenfeed für Ranking, Form, Ergebnisse und spätere K.-o.-Partien
- rechtliche Prüfung von Werbeausspielung, Tracking-Pixeln und Datenschutz/Consent
- redaktionelle Prüfung der Venue-Kapazitäten und Dach-/Klimatisierungslogik vor Veröffentlichung
- Hosting-Ziel festlegen, z.B. statische Website, Supabase Edge/Storage oder Next.js/Vercel
