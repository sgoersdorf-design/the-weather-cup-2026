# Werbeflächen-Leitfaden

Dieser MVP unterstützt native Werbeflächen, die über CSV, Supabase/PostgreSQL und den Website-Export gesteuert werden. Ziel: Dienstleister, Sponsoren oder Medienpartner können Kampagnen vorbereitet einreichen, ohne dass jedes Mal Layout-Code geändert werden muss.

## Aktueller Darstellungsstatus

Die Werbeflächen sind derzeit in der öffentlichen Website ausgeblendet. Inventar, Datenmodell, Import-Pipeline, vorbereitete Slots und Rendering-Code bleiben vollständig erhalten.

Die Anzeige wird nur aktiviert, wenn mindestens eine dieser Konfigurationen ausdrücklich `true` liefert:

- `window.WM_ADS_ENABLED = true` vor dem Laden von `app.js`
- `metadata.ads_enabled = true` im Website-Export

Ohne diese Freigabe werden keine Werbemittel gerendert und keine Bild- oder Tracking-Ressourcen der Kampagnen geladen. Nach einer Aktivierung gelten weiterhin die vorhandenen Kampagnenregeln, Laufzeiten, Gerätefilter und Prioritäten.

## 1. Verfügbare Slots

| Slot Key | Bereich | Platzierung | Zweck |
| --- | --- | --- | --- |
| `matchday_top` | Matchday | oben | breiter Tages-/Sponsorenbanner |
| `matchday_inline` | Matchday | zwischen Überblick und Matchliste | native Kontextfläche |
| `map_sidebar` | Wetterkarte | in der Detailspalte | Anbieter für Wetter, Travel, Mobility oder Sportdaten |
| `tables_top` | Tabellen | oben | Report-, B2B- oder Datenpartner |

Alle Slots werden im Frontend automatisch als `Anzeige` markiert.

## 2. Kampagnen vorbereiten

Die einfache MVP-Pflege läuft über `data/ad_inventory.csv`. Pro Zeile wird eine aktive Platzierung beschrieben.

Wichtige Felder:

| Feld | Bedeutung |
| --- | --- |
| `slot_key` | muss zu einem verfügbaren Slot passen |
| `partner_key`, `partner_name` | eindeutiger Dienstleister oder Partner |
| `campaign_key`, `campaign_name` | Kampagne |
| `creative_key`, `creative_name` | konkretes Werbemittel |
| `creative_type` | im MVP bevorzugt `native`; möglich sind `image`, `html`, `network_tag` |
| `label` | in der Regel `Anzeige` |
| `headline`, `body`, `call_to_action` | sichtbarer Inhalt |
| `click_url` | Zielseite, nur `https://` oder `http://` |
| `tracking_pixel_url` | optional, erst nach Datenschutz-/Consent-Prüfung nutzen |
| `background_color`, `text_color` | einfache Gestaltung |
| `starts_at`, `ends_at` | Laufzeit als ISO-Zeit |
| `priority`, `weight` | Auswahlreihenfolge, falls mehrere Kampagnen pro Slot aktiv sind |
| `device_targeting` | `all`, `mobile` oder `desktop` |
| `is_active` | `true` oder `false` |

## 3. Import und Website aktualisieren

Nach Änderung der CSV werden die Daten importiert und der Website-Export neu gebaut:

```bash
python -m python.pipelines.import_ads --file data/ad_inventory.csv
python -m python.pipelines.export_website_mvp
```

Für den kompletten Tageslauf ist `python -m python.pipelines.refresh_mvp_data` vorgesehen. Dieser Lauf importiert auch `data/ad_inventory.csv`.

## 4. Qualitätscheck vor Veröffentlichung

Vor Live-Schaltung prüfen:

- Ist der Partner vertraglich freigegeben?
- Ist die Ziel-URL korrekt und erreichbar?
- Ist die Anzeige klar als Anzeige erkennbar?
- Passt die Kampagne zum Umfeld Sport/Wetter/Datenjournalismus?
- Gibt es keine Logos oder Marken, für die keine Nutzungsrechte vorliegen?
- Sind Tracking-Pixel und Drittanbieter-Scripte rechtlich geprüft?
- Funktioniert die Anzeige auf Smartphone und Desktop ohne Layout-Überlauf?

## 5. Späterer Ad-Server-Betrieb

Für einen professionellen Werbebetrieb kann später Google Ad Manager mit Google Publisher Tag integriert werden. Laut offizieller Google-Dokumentation werden dafür `gpt.js`, definierte Ad Slots, passende `<div>`-Container und fertige Line Items in Google Ad Manager benötigt.

Für den MVP bleibt native Werbung die bessere Startlösung, weil sie:

- ohne externes Werbe-Script funktioniert
- schneller lädt
- einfacher in Supabase kontrollierbar ist
- weniger Datenschutz- und Consent-Komplexität erzeugt
- auf Smartphone stabiler ist

## 6. Empfohlener Prozess für Dienstleister

1. Dienstleister liefert Text, Ziel-URL, Laufzeit, Wunsch-Slot und optional Bild/Tracking.
2. Du prüfst, ob Inhalt und Rechte passen.
3. Die Kampagne wird als neue Zeile in `data/ad_inventory.csv` angelegt.
4. Import ausführen.
5. Website-Export ausführen.
6. Mobile und Desktop kurz prüfen.
7. Bei Ende der Kampagne `is_active=false` setzen oder `ends_at` auslaufen lassen.

Hinweis: Dieser Leitfaden ersetzt keine Rechtsberatung. Vor produktiver Ausspielung mit Tracking, Profiling, Ad-Netzwerken oder Drittanbieter-Scripten sollten Datenschutz, Consent-Banner und Verträge geprüft werden.
