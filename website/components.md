# Components

## TeamBadge

Props:

```ts
type TeamBadgeProps = {
  iso2: string
  iso3: string
  name: string
  flagEmoji?: string
  locale: 'de' | 'en'
}
```

## MatchCard

Zeigt Datum, Venue, beide Teams, Kernindikatoren, Prognose und Unsicherheit. Fehlende Felder werden nicht versteckt, sondern als `Daten folgen` oder `Data pending` angezeigt.

## WeatherPanel

Zeigt Forecast, Historical oder Actual Weather mit `dataQualityScore`.

## WeatherFitPanel

Zeigt die Kernfrage des Produkts: Welches Team passt besser zur aktuellen Wettersituation? Enthalten sind Weather Fit Score fuer beide Teams, Edge, Edge Gap, Unsicherheit und ein kurzer Disclaimer.

## TravelPanel

Zeigt Distanz, geschaetzte Reisezeit, Resttage und `travelRecoveryScore`.

## TimezonePanel

Zeigt Referenz-Zeitzone, Venue-Zeitzone, gefuehlte Anstosszeit und `circadianLoadScore`.

## AltitudePanel

Zeigt Venue-Hoehe, Hoehenwechsel und `altitudeLoadScore`.

## FanProximityPanel

Zeigt Naeheindikator, Hauptstadt-Venue-Distanz und Host-Country-Status. Kein Diaspora- oder Stimmungslabel.

## PredictionPanel

Zeigt Ergebniskategorie, Wahrscheinlichkeiten, groessten Kontextfaktor und Unsicherheitsgrad. Immer mit Disclaimer.

## VenueMap

MapLibre oder Leaflet. Marker nur fuer Venues, keine Logo-Assets.

## RankingTable

Listet Teams mit Basic Team Strength, Kontext-Edges und Datenqualitaet.

## DisclaimerBox

Zeigt lokalisierten Standard-Disclaimer aus `content/disclaimer_texts.json`.

## ReportView

Zeigt Post-Match-Auswertungen pro Partie, Spieltag, Turnierphase und Gesamtturnier. Ergebnisvergleiche werden deskriptiv dargestellt und duerfen nicht als Wetterkausalitaet formuliert werden.
