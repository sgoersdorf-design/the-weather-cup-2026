# Methodik: Spielort-Reiseranking

Das Ranking beschreibt die Reisebelastung der Teams in der Gruppenphase ausschließlich anhand der zeitlich aufeinanderfolgenden Spielorte.

## Enthalten

- Drei Gruppenspiele pro Team
- Stadionkoordinaten jedes Spiels
- Luftlinie zwischen Spiel 1 und Spiel 2
- Luftlinie zwischen Spiel 2 und Spiel 3
- Summe beider Teilstrecken
- Anzahl verschiedener Städte und Arenen
- Anzahl der Ortswechsel
- Wiederholte Nutzung desselben Stadions

## Nicht enthalten

- Basislager oder Teamhotel
- Anreise zum ersten Spiel
- Abreise nach dem dritten Spiel
- Flughäfen, Transfers und Straßenstrecken
- Tatsächliche Flugrouten oder Zwischenstopps
- Individuelle Reiseplanung der Verbände

## Distanzberechnung

Die Entfernung wird als Großkreisdistanz zwischen zwei Stadionkoordinaten auf einer Erde mit einem mittleren Radius von 6.371 Kilometern berechnet. Die Darstellung wird auf volle Kilometer gerundet.

Dadurch ist das Ranking zwischen allen Teams konsistent vergleichbar, aber keine Rekonstruktion der real zurückgelegten Strecke.
