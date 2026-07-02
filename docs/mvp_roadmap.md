# MVP Roadmap

## Phase 1 - Data Foundation

- Datenmodell finalisieren
- Supabase/PostgreSQL aufsetzen
- `sql/001_schema.sql` ausfuehren
- Datenquellenkatalog importieren
- CSV-Templates und Sample-Daten importieren
- Datenquellen und Lizenzrisiken dokumentieren

## Phase 2 - Automated Metrics

- Wetterpipeline fuer Forecast, Historical und Actual laufen lassen
- Weather Fit pro Team und Match berechnen
- Travel Metrics berechnen
- Timezone Metrics berechnen
- Altitude Metrics berechnen
- Fan Proximity Metrics berechnen
- Basic Team Strength aus lizenzierter Quelle laden

## Phase 3 - Predictions and Texts

- Prognosepipeline fuer alle Matches ausfuehren
- DE/EN Match-Card-Texte generieren
- Pre-Match Weather-Fit Website- und Social-Texte generieren
- Social Templates erzeugen
- Post-Match-Update und Prognose-vs.-Realitaet-Vergleich schreiben
- Weather-Fit-Reports pro Match, Spieltag, Phase und Turnier erstellen

## Phase 4 - Website MVP

- Next.js-Prototyp mit TypeScript und Supabase anbinden
- `/de` und `/en` Routen umsetzen
- Match Cards und Match Detail bauen
- Venue Map integrieren
- Methodikseite mit Disclaimer veroeffentlichen

## Phase 5 - Production Readiness

- Vollstaendige lizenzierte Sportdatenquelle entscheiden
- Spielplan/Ergebnisupdates automatisieren
- Open-Meteo Attribution im Frontend einbauen
- Monitoring fuer Importfehler und Datenqualitaet
- Score-Gewichte transparent kalibrieren
