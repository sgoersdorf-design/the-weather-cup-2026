# Website MVP

Die Website ist als Next.js-App mit TypeScript, Supabase und zweisprachigem Routing geplant. Dieses Verzeichnis enthaelt die Umsetzungsgrundlage, noch keine vollstaendige App.

## Ziele

- Match Schedule fuer `/de` und `/en`
- Match Cards mit Wetter, Reise, Zeitzone, Hoehe, Fan Proximity und Prognose
- Venue- und Team-Listen
- Ranking-/Methodikseiten
- klare Disclaimer und Datenqualitaetszustand

## Stack

- Next.js App Router
- TypeScript
- Supabase Client
- `next-intl` oder vergleichbares i18n-System
- MapLibre oder Leaflet fuer Karten
- Recharts oder ECharts fuer einfache Score-Visualisierungen

## UX-Regeln

- keine Logos
- Teamdarstellung nur Flagge, ISO3 und lokalisierter Laendername
- Missing Data sichtbar als "Daten folgen" / "Data pending"
- jede Prognose zeigt Unsicherheit und Disclaimer
