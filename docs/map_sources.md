# Kartenquellen

Die lokale Wetterkarte nutzt eine offlinefähige SVG-Vektorkarte. Grundlage sind gefilterte GeoJSON-Grenzen für Kanada, die USA und Mexiko.

## Quelle

- Natural Earth / world.geo.json
- Projekt: https://github.com/johan/world.geo.json
- Natural Earth Terms: https://www.naturalearthdata.com/about/terms-of-use/

Natural Earth stellt Raster- und Vektordaten als Public Domain bereit. Die Website braucht dadurch keinen externen Kartenanbieter, keine Tile-API und keinen API-Key.

## Warum SVG statt Map Tiles?

- Offline/lokal lauffähig
- Keine laufenden Kartenkosten
- Keine Abhängigkeit von Google/Mapbox/OSM-Tiles im MVP
- Präzise genug für den Spielort- und Wettervergleich
- Venue-Pins bleiben exakt über Latitude/Longitude positioniert
- Schnelle Darstellung auf Smartphones, weil keine externen Kartentiles geladen werden

## Genauigkeit der Spielorte

Die Pins werden aus den Venue-Koordinaten in `data/sample_venues.csv` gesetzt. Der MVP nutzt Stadionkoordinaten mit zusätzlichem Feld `coordinate_accuracy_m`, damit die UI transparent anzeigen kann, wie genau der Pin im Datenbestand bewertet ist.

Für die präzise Detailansicht ist eine Google-Maps-Verknüpfung sinnvoll. Im MVP wird dafür Google Maps URLs genutzt:

- kein API-Key notwendig
- funktioniert als externer Absprung auf Desktop und Smartphone
- koordinatenbasierte Suche (`lat,lon`) vermeidet Namensverwechslungen
- Google Place IDs können später ergänzt werden, wenn die Stadionorte einmal sauber auditiert wurden

Nicht sinnvoll für den ersten MVP ist eine voll eingebettete Google-Karte mit eigener Tile-Darstellung. Dafür wären API-Key, Billing, Consent-/Datenschutzprüfung und ein robuster Fallback nötig.

## Nächster Genauigkeitsschritt

Für eine Production-Version sollte eine Venue-Audit-Tabelle gepflegt werden:

- offizieller Host-Venue-Name
- Stadionzentrum als Latitude/Longitude
- `coordinate_accuracy_m`
- `google_place_id`, sofern aus einer erlaubten Google-Places-/Geocoding-Abfrage bestätigt
- Quellenstatus und Prüfdatum
- Hinweis, ob der Name wegen Sponsoring-/Lizenzrechten generisch ausgespielt wird

Für eine spätere Production-Version kann dieselbe Datenlogik in MapLibre GL oder Leaflet überführt werden, falls Zoom, Pan, Basemap-Layer oder detaillierte Stadt-/Straßenebenen gebraucht werden.
