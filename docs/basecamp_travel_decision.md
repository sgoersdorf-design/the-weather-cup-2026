# Basislager und Reisekontext

Stand: 2026-06-09

## Entscheidung fuer den MVP

Der sichtbare Website-MVP weist keinen Reisekontext aus.

Grund: Im aktuellen Datenbestand sind keine belastbaren Team-Basislager mit Koordinaten, Ankunftslogik und Spielort-Routen hinterlegt. Damit sind fuer `0 von 48` Mannschaften vollstaendige Anreiserouten aus Basislager und Spielort bekannt.

## Was vorhanden ist

- Spielorte mit Koordinaten
- Spielplan mit Spielort und Anstosszeit
- technische Travel-Metriken zwischen aufeinanderfolgenden Spielorten

Diese Travel-Metriken sind fuer interne Modelltests nutzbar, ersetzen aber keine echte Route aus Team-Basislager, Hotel/Trainingssite und Spielort.

## Was fuer eine sichtbare Reisekomponente fehlen wuerde

- bestaetigtes Team-Basislager je Mannschaft
- Koordinaten von Hotel oder Trainingssite
- Regeln, ob Teams vor jedem Spiel vom Basislager, vom vorherigen Spielort oder aus einem Zwischenquartier reisen
- Zeitpunkte fuer Anreise, Abreise und Regeneration
- Quellen- und Lizenzstatus fuer diese Informationen

Erst wenn diese Daten fuer alle oder klar markierte Teilmengen belastbar vorliegen, sollte Reisekontext wieder sichtbar in Match Cards, Social Texten und Analysen auftauchen.
