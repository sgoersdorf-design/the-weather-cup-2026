# Scoring Methodology

Alle Scores laufen von 0 bis 100. Die Richtung ist pro Score explizit definiert.

## Wetter

`weather_load_score`: hoeher bedeutet staerkere Wetterbelastung. Hitze, hohe Luftfeuchtigkeit, starker Wind und Niederschlagswahrscheinlichkeit erhoehen den Wert.

`weather_familiarity_score`: hoeher bedeutet, dass Venue-Bedingungen der Referenzumgebung eines Teams aehnlicher sind.

`weather_tolerance_score`: hoeher bedeutet, dass das Teamprofil fuer die konkret relevanten Wetterarten guenstiger bewertet wird. Bei Hitze zaehlt Heat Tolerance staerker, bei hoher Luftfeuchtigkeit Humidity Tolerance, bei Regen Rain Tolerance und bei Wind Wind Tolerance.

`weather_fit_score`: hoeher bedeutet, dass ein Team im MVP besser zur konkreten Wettersituation passt. Der Score kombiniert Familiarity, relevante Toleranz und effektive Wetterbelastung.

`calculate_heat_index`: berechnet einen Naeherungswert fuer gefuehlte Waerme. Bei milden Bedingungen wird die Temperatur direkt zurueckgegeben.

## Reise und Erholung

`travel_recovery_score`: hoeher bedeutet guenstigere Erholung. Distanz, kurze Pausen, Zeitzonenwechsel und kumulative Distanz senken den Score.

`estimate_travel_time_hours`: `distance_km / 750 + 3`.

## Zeitzone

`circadian_load_score`: hoeher bedeutet staerkere moegliche Biorhythmusbelastung. Zeitzonenverschiebung, nicht adaptierte Tage und gefuehlt fruehe/spaete Anstosszeiten erhoehen den Wert.

## Hoehe

`venue_altitude_factor`: hoeher bedeutet staerkere Hoehenlage des Venues.

`altitude_load_score`: kombiniert Hoehenlage und Hoehenwechsel gegenueber dem vorherigen Spiel.

## Venue Type

`venue_type_factor`: hoeher bedeutet potenziell stabilere Bedingungen. Indoor und retractable roof werden hoeher bewertet als outdoor.

## Fan Proximity

`fan_proximity_score`: hoeher bedeutet groessere strukturelle Naehe. Gastgeberstatus, gleicher Kontinent und Distanz zur Hauptstadt werden beruecksichtigt. Der Score ist kein Diaspora-, Stimmungs- oder echter Fanvorteils-Score.

## Basic Team Strength

`basic_team_strength_score`: nutzt, falls vorhanden, FIFA-Rankingposition, Rankingpunkte, Elo-Rating und Basic Form Score. Fehlende Werte werden nicht erfunden; bei komplett fehlenden Daten ist der neutrale Wert 50.

## Unsicherheit

`uncertainty_score`: hoeher bedeutet groessere Unsicherheit. Niedrige Datenqualitaet und fehlende Pflichtfelder erhoehen den Wert.

Labels:

- `low`: unter 35
- `medium`: 35 bis unter 70
- `high`: ab 70

## Prognose

`predict_match` kombiniert:

- Basic Team Strength
- Weather Familiarity
- Weather Load als Belastung
- Travel Recovery
- Circadian Load als Belastung
- Altitude Load als Belastung
- Venue Type
- Squad Age, falls aktiv
- Fan Proximity

Die Ausgabe ist ein transparenter MVP-Indikator mit:

- predicted_result_category
- probability_team_a_win
- probability_draw
- probability_team_b_win
- main_context_advantage
- biggest_load_factor
- uncertainty_level

## Disclaimer

Die Prognose ist kein Wettmodell. Wetter, Reise, Hoehe, Zeitzonen und Standortnaehe sind Kontextindikatoren und keine alleinigen Ergebnisursachen.

## Post-Match Weather Fit

Nach dem Spiel vergleicht der MVP:

- Forecast Weather Fit vor dem Spiel
- Actual Weather Fit aus Ist-Wetter
- Forecast-vs-Actual-Delta fuer Temperatur und Luftfeuchtigkeit
- Ergebnis-Kategorie als deskriptive Einordnung

Die Aggregation pro Partie, Spieltag, Turnierphase und Turnier zaehlt, ob das Team mit Forecast Weather Fit Edge gewonnen hat, nicht gewonnen hat oder ob ein Remis folgte. Diese Kennzahl ist deskriptiv und darf nicht als Kausalitaet formuliert werden.
