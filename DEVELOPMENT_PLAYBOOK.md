# Development Playbook

Wiederverwendbare Entwicklungsregeln, abgeleitet aus dem WM-Projekt. Diese Datei gehoert zu Beginn jedes neuen Projekts in den Projektkontext. Sie ist bewusst technologieoffen; projektbezogene Entscheidungen werden in einem eigenen Abschnitt konkretisiert.

## 1. Vor dem ersten Code

### Do

- Ein klares Ergebnis definieren: Zielgruppe, Kernnutzen, nicht verhandelbare Qualitätskriterien und expliziter Nicht-Scope.
- Eine kanonische Quelle der Wahrheit festlegen: genau ein Repository, ein Standard-Branch, ein Deploy-Ziel und ein Ort fuer produktive Daten.
- Pfade relativ zum Repository ableiten. Falls ein absoluter Pfad unvermeidbar ist, ihn zentral dokumentieren und in Skripten validieren.
- Datenvertrag, Datenquellen, Lizenzstatus, Aktualisierungsrhythmus und Verantwortlichkeit vor UI-Implementierung festlegen.
- Unbekanntes als unbekannt modellieren: `null`, Status, Quelle, Abrufzeit, Datenqualität und Unsicherheit sind Produktdaten, keine Nebensachen.
- Akzeptanzkriterien so formulieren, dass sie automatisch oder mit einem klaren manuellen Check pruefbar sind.

### Don't

- Nicht parallel in mehreren lokalen Kopien entwickeln oder Builds aus einem alten Arbeitsordner erzeugen.
- Keine Features auf impliziten Annahmen aufbauen, wenn Quelle, Lizenz oder fachliche Definition noch offen sind.
- Kein "wir raeumen die Datenqualitaet spaeter auf". Das wird fast immer zu falschen Auswertungen und schwer nachvollziehbaren UI-Zustaenden.
- Nicht mit Design oder Modelllogik beginnen, bevor klar ist, welche Daten verlässlich vorliegen und welche nicht.

## 2. Architektur und Daten

### Do

- Rohdaten, berechnete Kennzahlen, redaktionelle Texte und Frontend-Export sauber trennen.
- Jede Importstrecke idempotent bauen: eindeutige Schluessel, Upserts, Validierung vor dem Schreiben und nachvollziehbare Importprotokolle.
- Einen versionierten Datenvertrag zwischen Backend/Pipeline und Frontend pflegen. Änderungen daran wie API-Änderungen behandeln.
- Für jede Kennzahl Richtung, Einheit, Formel, Grenzen und Fehlverhalten dokumentieren. Beispiel: Ist ein hoher Score gut oder schlecht?
- Lokale CSV-/JSON-Fallbacks so auslegen, dass die vollständigere, validierte Quelle einer unvollständigen Datenbankansicht vorgezogen wird.
- Datenquellen mit URL, Lizenz, zulässiger Nutzung, Abrufzeit und Qualität katalogisieren.
- Bei externen Daten mindestens eine Primär- oder autoritative Quelle und, bei kritischen Ergebnissen, einen unabhängigen Cross-Check nutzen.

### Don't

- Keine stillen Defaultwerte erfinden, die wie echte Messwerte aussehen. Neutrale Werte dürfen nur klar markierte Modell-Fallbacks sein.
- Datenbank und Export nicht unabhängig fortschreiben lassen, ohne Coverage und Zeitstempel gegeneinander zu prüfen.
- Keine automatischen Überschreibungen, wenn Schlüssel, Match-Zuordnung oder Entität nicht eindeutig ist.
- Keine Analyse auf Coverage-Lücken hochrechnen oder als vollständige Rangliste ausgeben.

## 3. Fachlichkeit, Texte und Darstellung

### Do

- Fakten, Beobachtung, Korrelation, Modellindikator und Kausalbehauptung sprachlich strikt trennen.
- Für DE/EN oder weitere Sprachen eine fachlich gleichwertige, nicht nur wörtliche Ausgabe erzeugen und prüfen.
- Für unvollständige Daten eine ehrliche UI vorsehen: Coverage, "noch nicht verfügbar", Quellenhinweis und Unsicherheitslabel.
- Kontextsignale als Kontext beschreiben, nicht als Ergebnisursachen oder sichere Vorhersagen.
- In der UI immer die Datenreife neben dem Ergebnis sichtbar machen, besonders bei Rankings, Statistiken und Reports.

### Don't

- Keine Wett-, Orakel- oder Überkausalitäts-Sprache verwenden, wenn das Modell nur einen Kontextindikator liefert.
- Keine neuen redaktionellen Fakten manuell in generierte Texte mischen, wenn sie nicht im strukturierten Datenbestand stehen.
- Keine scheinpräzisen Diagramme oder KPIs zeigen, wenn Nenner, Zeitraum oder Coverage fehlen.

## 4. Automatisierung und Betrieb

### Do

- Einen vollständigen, wiederholbaren Refresh als Orchestrator anbieten: Fetch, Import, Berechnung, Text, Export, Build, Validierung, Publish und Live-Prüfung.
- Pro Schritt Timeouts, strukturierte Fehler, begrenzte Retries und sichtbare Fortschrittsmeldungen implementieren.
- Nichtkritische externe Ausfälle sauber degradieren; kritische Abweichungen von Publish- oder Datenintegrität müssen den Lauf fehlschlagen lassen.
- Gleichzeitige Läufe mit einem Lock verhindern und Logs, letzter Lauf, Fehlerartefakte sowie Benachrichtigungen bereitstellen.
- Automationen mit explizitem Lebenszyklus bauen: Startbedingung, Frequenz, Ende, Abschaltkommando und verifizierbarer Status.
- Nach fachlichen Endpunkten, z. B. Turnierende oder Kampagnenende, Job deaktivieren, Plan aus der Konfiguration entfernen und den tatsächlichen Scheduler-Status prüfen.

### Don't

- Nicht allein darauf vertrauen, dass eine einmal entladene Automation dauerhaft beendet bleibt. Scheduler, CI, Cron und externe Trigger separat prüfen.
- Kein automatisches Pushen, wenn der Refresh nur teilweise erfolgreich war oder Artefakte nicht konsistent validiert sind.
- Keine stillen Fehler. Ein Lauf ohne Ergebnis oder mit veraltetem Deploy muss eindeutig sichtbar fehlschlagen.
- Keine ungebremsten Retries oder Jobs ohne Lock: Sie erzeugen doppelte Importe, Konflikte und unnötige Kosten.

## 5. Testen und Release

### Do

- Lokal mindestens drei Ebenen pruefen: Daten-/Schema-Validierung, erzeugte Artefakte und produktnahe Browser-/Interaktionschecks.
- Für statische Exporte Daten eingebettet prüfen: Payload vorhanden, Zeitstempel vorhanden, zentrale UI-Zustände vorhanden, keine versehentlichen externen Laufzeitabhängigkeiten.
- Den Release erst als erfolgreich markieren, wenn die Live-Seite denselben oder einen neueren Exportzeitpunkt und dieselben zentralen Stats wie der lokale Publish-Stand liefert.
- Deploy-Verifikation cache-busted abrufen und innerhalb eines begrenzten Zeitfensters pollen.
- Bei jeder Veröffentlichung festhalten: Commit, lokaler Exportzeitpunkt, Live-Exportzeitpunkt, Daten-Coverage und offene Einschränkungen.

### Don't

- "Build erfolgreich" nicht mit "veröffentlicht und korrekt" verwechseln.
- Keine Live-Prüfung nur anhand des HTTP-Status durchführen; den fachlichen Payload vergleichen.
- Nicht nur Happy Paths testen. Fehlende Daten, alte Exporte, leere Events, Zeitüberschreitungen und mobile Darstellung gehören in die Release-Prüfung.

## 6. Git und Zusammenarbeit

### Do

- Kleine, fachlich zusammenhängende Commits erstellen und vor dem Push den Arbeitsbaum prüfen.
- Generierte Artefakte nur dann versionieren, wenn sie bewusst Teil des Deploy-Vertrags sind.
- Änderungen an Datenmodell, Pipeline, Export und UI zusammen denken; bei Änderungen am Vertrag alle Verbraucher aktualisieren.
- Dokumentation neben der Implementierung aktualisieren, besonders bei Betrieb, Datenquellen und Release-Ablauf.

### Don't

- Keine fremden oder unklaren lokalen Änderungen überschreiben oder zurücksetzen.
- Keine Geheimnisse, personenbezogenen Daten oder produktiven Zugangsdaten committen.
- Kein Commit-Spam durch periodische Jobs, wenn sich nur ein Zeitstempel ändert und kein fachlicher Datengewinn entstanden ist. Zeitgesteuerte Exporte brauchen eine inhaltliche Änderungsprüfung oder einen bewusst getrennten Audit-Mechanismus.

## Projektstart-Checkliste

Vor der Implementierung muessen diese Punkte beantwortet sein:

- Was ist das messbare Nutzerergebnis und was gehoert ausdrücklich nicht dazu?
- Welches Repository, welcher Branch und welches Deploy-Ziel sind verbindlich?
- Welche Daten sind autoritativ, welche nur Fallback und welche dürfen nicht verwendet werden?
- Wie werden Quelle, Zeitpunkt, Lizenz, Qualität und Unsicherheit im Datenmodell transportiert?
- Welche Berechnungen sind transparent genug, um sie fachlich und redaktionell zu erklären?
- Was passiert bei fehlenden, widersprüchlichen oder verspäteten Daten?
- Wie sieht der komplette Refresh- und Releasepfad aus, einschließlich Rollback oder Fehleralarm?
- Woran erkennt ein automatischer Check, dass die Live-Seite wirklich den lokalen Publish-Stand zeigt?
- Welche Automation wird wann und wie nachweisbar abgeschaltet?

## Startkontext fuer ein neues Projekt

> Arbeite ausschließlich im kanonischen Repository. Definiere vor Implementierung Datenvertrag, Quellen-/Lizenzstatus, Qualitäts- und Unsicherheitsfelder sowie Akzeptanzkriterien. Baue jede Datenstrecke idempotent und reproduzierbar. Behandle fehlende Daten sichtbar statt sie zu schätzen. Der Release ist erst abgeschlossen, wenn lokale Validierung, Artefaktprüfung, Browsercheck und ein fachlicher Live-/Publish-Abgleich erfolgreich sind. Automationen benötigen Lock, Timeout, begrenzte Retries, Fehleralarm, dokumentierte Endbedingung und verifizierbare Deaktivierung.

## Konkrete Lehren aus diesem Projekt

- Ein einzelner kanonischer Pfad verhindert, dass ein korrekter Build aus der falschen Arbeitskopie veröffentlicht wird.
- Event- und Ergebnisdaten brauchen Coverage-Metriken; nur dann bleiben Tor- und Ranking-Statistiken bei lückenhaften Feeds redlich.
- Ist-Daten und Forecast-Daten sind unterschiedliche Zustände. Forecast darf Ist-Wetter nicht ersetzen.
- Eine Datenbank kann hinter lokalen, geprüften Event-Dateien zurückliegen. Der Export muss die bessere Coverage aktiv wählen und das kennzeichnen.
- Der Exportzeitpunkt ist ein praktikabler End-to-End-Vertrag zwischen Pipeline und Live-Website, wenn er zusätzlich mit zentralen Kennzahlen abgeglichen wird.
- Eine entfernte Zeitplanung in einer Konfigurationsdatei beweist nicht, dass kein anderer Trigger mehr läuft. Scheduler-Status und Commit-/Deploy-Historie gehören zur Abschlussprüfung.
