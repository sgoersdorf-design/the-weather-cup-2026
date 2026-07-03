const source = window.WM_MVP_DATA || { metadata: {}, matches: [] };
const hostMap = window.WM_HOST_GEOJSON || { features: [] };
const ads = Array.isArray(source.ads) ? source.ads : [];
const ADS_ENABLED = window.WM_ADS_ENABLED === true || source.metadata?.ads_enabled === true;
const state = {
  lang: "de",
  activeSection: "home",
  mode: "all",
  scheduleView: "smart",
  query: "",
  matchday: "all",
  group: "all",
  selectedId: null,
  analysisMode: "standings",
  travelSort: "distance_desc",
  mapMatchday: "all",
  favoritesMatchday: "all",
  selectedVenueKey: null,
  mapSelectedMatchId: null,
  mapView: "venues",
  mapSheetOpen: false,
  knockoutStage: null,
  selectedScorer: "Lionel Messi",
};

const els = {
  status: document.querySelector("#exportStatus"),
  homeDashboard: document.querySelector("#homeDashboard"),
  heroSignal: document.querySelector("#heroSignal"),
  heroTodayCta: document.querySelector("#heroTodayCta"),
  heroMapCta: document.querySelector("#heroMapCta"),
  metricMatches: document.querySelector("#metricMatches"),
  metricForecasts: document.querySelector("#metricForecasts"),
  metricEdges: document.querySelector("#metricEdges"),
  metricTexts: document.querySelector("#metricTexts"),
  coverageBars: document.querySelector("#coverageBars"),
  scheduleJumpbar: document.querySelector("#scheduleJumpbar"),
  scheduleToolbarStatus: document.querySelector("#scheduleToolbarStatus"),
  search: document.querySelector("#searchInput"),
  modeButtons: [...document.querySelectorAll(".segment")],
  matchdayFilter: document.querySelector("#matchdayFilter"),
  matchdaySummary: document.querySelector("#matchdaySummary"),
  groupFilter: document.querySelector("#groupFilter"),
  list: document.querySelector("#matchList"),
  detail: document.querySelector("#matchDetail"),
  analysisButtons: [...document.querySelectorAll(".analysis-tab")],
  analysisContent: document.querySelector("#analysisContent"),
  analysisEyebrow: document.querySelector("#analysisEyebrow"),
  analysisTitle: document.querySelector("#analysisTitle"),
  analysisTabs: document.querySelector("#analysisTabs"),
  travelContent: document.querySelector("#travelContent"),
  mapMatchdayFilter: document.querySelector("#mapMatchdayFilter"),
  mapCanvas: document.querySelector("#weatherMapCanvas"),
  mapDetail: document.querySelector("#weatherMapDetail"),
  venueHighlights: document.querySelector("#venueHighlights"),
  mapViewButtons: [...document.querySelectorAll(".map-view-toggle")],
  favoritesMatchdayFilter: document.querySelector("#favoritesMatchdayFilter"),
  favoritesSummary: document.querySelector("#favoritesSummary"),
  favoritesList: document.querySelector("#weatherFavorites"),
  navButtons: [...document.querySelectorAll(".app-nav-item")],
  sections: [...document.querySelectorAll(".app-section")],
  adSlots: [...document.querySelectorAll("[data-ad-slot]")],
  languageToggle: document.querySelector("#languageToggle"),
  backToTop: document.querySelector("#backToTop"),
  predictionDialog: document.querySelector("#predictionDialog"),
  predictionDialogContent: document.querySelector("#predictionDialogContent"),
  legalLinks: [...document.querySelectorAll("[data-legal-target]")],
};

const I18N = {
  de: {
    siteEyebrow: "WM 2026 Context Lab",
    heroClaim: "Der tägliche Blick auf den Wetter-Faktor bei der WM.",
    siteSubline: "Wetter, Reisen, Höhe und Zeitzonen für jedes Spiel — datenbasiert, zweisprachig, ohne Ergebnisgarantie.",
    heroTodayCta: "Heutige Spiele ansehen",
    heroMapCta: "Wetterkarte öffnen",
    statusLoading: "Datenstand wird geladen",
    navToday: "Heute",
    navStats: "Stats",
    navSchedule: "Spielplan",
    navMatchday: "Spieltag",
    navFavorites: "Wetterfavoriten",
    navMap: "Wetterkarte",
    navTravel: "Reiseranking",
    navTables: "Tabellen",
    navFaq: "FAQ",
    todayContext: "Der WM-Tag",
    todayNoMatches: "Heute stehen keine Spiele an. Hier sind die nächsten Partien mit den auffälligsten Kontextsignalen.",
    liveMatches: "Live-Spiele",
    todayMatches: "Spiele heute",
    nextMatch: "Nächstes Spiel",
    highestLoad: "Höchster Weather Load",
    biggestEdge: "Größter Wettervorteil",
    highestTravel: "Größte Reisedistanz",
    highestAltitude: "Höchster Höhenfaktor",
    nextUp: "Als Nächstes",
    nextUpIntro: "Die unmittelbar nächsten Partien mit ihrem stärksten Kontextsignal.",
    topContextMatch: "Wetterspiel des Tages",
    upcomingMatches: "Weitere kommende Spiele",
    allUpcoming: "Zum vollständigen Spielplan",
    realityCheck: "Reality Check",
    realityCheckIntro: "Was Prognose und Wettervorteil vor dem Spiel zeigten — und wie die Partie endete.",
    noFinishedMatches: "Sobald Spiele beendet sind, erscheinen hier Ergebnis und Kontextabgleich.",
    favoritesPreview: "Wetterfavoriten im Blick",
    travelPreview: "Reisebelastung im Blick",
    venuePreview: "Härteste Spielorte",
    tablePreview: "Aktueller Tabellenblick",
    methodologyEyebrow: "Methodik in Kürze",
    methodologyTitle: "Was ist ein Wettervorteil?",
    methodologyBody: "Ein Kontextwert, der Wetterfit und Spielbedingungen vergleicht. Keine Ergebnisgarantie. Kein Wettmodell.",
    viewAll: "Alle ansehen",
    openFaq: "Methodik & FAQ öffnen",
    statusLive: "Live",
    statusToday: "Heute",
    statusUpcoming: "Kommend",
    statusFinished: "Beendet",
    liveContext: "Live-Kontext ansehen",
    viewGame: "Spiel ansehen",
    submitTip: "Tipp abgeben",
    viewTip: "Tipp auswerten",
    topContextSignal: "Wetter-Schlüsselfaktor",
    weatherShort: "Wetter",
    travelShort: "Reise",
    predictionShort: "Prognose",
    distancePreviousVenue: "seit vorherigem Spielort",
    noPreviousTravel: "Erstes Gruppenspiel",
    dataConfidence: "Datenlage",
    confidenceStable: "stabil",
    confidenceMedium: "mittel",
    confidenceLimited: "begrenzt",
    matchDetails: "Spieldetails",
    detailOverview: "Überblick",
    detailWeather: "Wetter",
    detailContext: "Weitere Bedingungen",
    detailVenue: "Stadion",
    detailPrediction: "Prognose & Methodik",
    forecastWeather: "Wetterprognose",
    historicalWeather: "Historischer Vergleich",
    historicalWeatherPending: "Historische Vergleichswerte werden ergänzt, sobald eine belastbare Referenzreihe vorliegt.",
    actualWeatherPending: "Ist-Wetter wird nach Spielende automatisch ergänzt, sobald die Daten verfügbar sind.",
    actualWeatherLabel: "Ist-Wetter",
    travelDistance: "Reisedistanz",
    recoveryTime: "Erholungszeit",
    timezoneLoad: "Zeitzonenfaktor",
    altitudeLoad: "Höhenfaktor",
    fanProximity: "Standortnähe",
    teamStrength: "Basis-Teamstärke",
    modelMethodNote: "Alle Werte sind Kontextindikatoren. Sie erklären Bedingungen, nicht das Ergebnis, und sind kein Wettmodell.",
    forecastHelpfulEmpty: "Forecast noch nicht aktiv. Historische Wetterdaten, Spielort und Reiseindikatoren sind bereits verfügbar.",
    weatherCoverageTitle: "Wetterstatus",
    weatherCoverageAvailable: "Bereits verfügbar",
    weatherCoverageForecastSoon: "Forecast startet automatisch näher am Anpfiff.",
    weatherCoverageActualSoon: "Ist-Wetter folgt nach Spielende, sobald Messdaten vorliegen.",
    weatherCoverageHistoricalSoon: "Historische Vergleichswerte werden ergänzt, sobald genug Referenzspiele vorliegen.",
    predictionDialogTitle: "Dein Tipp",
    predictionQuestion: "Wie endet die Partie?",
    contextQuestion: "Spielt der Kontext sichtbar eine Rolle?",
    contextMatters: "Ja, sichtbar",
    contextLow: "Eher kaum",
    teamAWins: "Team A gewinnt",
    drawPick: "Unentschieden",
    teamBWins: "Team B gewinnt",
    predictionStored: "Dein Tipp ist auf diesem Gerät gespeichert.",
    predictionConfirm: "Tipp speichern",
    predictionUpdate: "Tipp aktualisieren",
    predictionChooseBoth: "Bitte wähle ein Ergebnis und die Rolle des Kontexts aus.",
    predictionSavedStrong: "Tipp erfolgreich gespeichert",
    predictionCorrect: "Dein Ergebnistipp war richtig.",
    predictionWrong: "Dein Ergebnistipp war nicht richtig.",
    predictionPending: "Auswertung folgt nach Spielende.",
    localOnlyNote: "Ohne Login. Speicherung nur lokal in diesem Browser.",
    close: "Schließen",
    tipScore: "Tippbilanz",
    personalTipBalance: "Deine Tippbilanz",
    noPersonalTips: "Noch keine abgeschlossenen Tipps auf diesem Gerät.",
    correctTips: "richtige Tipps",
    forecastVsActual: "Forecast vs. Ist-Wetter",
    forecastVsActualPending: "Ist-Wetter noch nicht verfügbar",
    forecastVsResult: "Prognose vs. Ergebnis",
    predictionMatched: "Prognose traf zu",
    predictionMissed: "Prognose wich ab",
    contextNotGuarantee: "Kontextdaten zeigen Bedingungen, aber keine Ergebnisgarantie.",
    mapViewVenues: "Spielorte",
    mapViewMap: "Karte",
    hardestVenues: "Härteste Spielorte heute",
    closeVenue: "Detail schließen",
    contextOutlook: "Context Outlook",
    nextGroupMatch: "Nächstes Gruppenspiel",
    bestGroupFit: "Bester Weather Fit",
    groupTravelLoad: "Größte Reisebelastung",
    groupWeatherLoad: "Höchster Weather Load",
    faq9Q: "Wie funktioniert die Tippfunktion?",
    faq9A: "Deine Tipps werden ausschließlich lokal in diesem Browser gespeichert. Es gibt kein Konto, keine Übertragung personenbezogener Daten und kein verpflichtendes Tracking. Du kannst die lokalen Tipps jederzeit über deine Browserdaten löschen.",
    searchPlaceholder: "Team, Gruppe, Ort, Match-ID",
    modeAll: "Alle",
    modeEdge: "Wettervorteil",
    scheduleSmart: "Relevant jetzt",
    scheduleFull: "Komplette Timeline",
    jumpCurrent: "Zur aktuellen Partie",
    jumpLive: "Live",
    jumpToday: "Heute",
    jumpNext: "Nächstes Spiel",
    jumpRecent: "Zuletzt gespielt",
    jumpStart: "Turnierstart",
    jumpOpenHistory: "Frühere Spieltage anzeigen",
    jumpCloseHistory: "Frühere Spieltage ausblenden",
    scheduleFocusToday: "Spielplan startet jetzt bei den heutigen Spielen.",
    scheduleFocusLive: "Spielplan startet jetzt bei den Live-Spielen.",
    scheduleFocusNext: "Spielplan startet jetzt beim nächsten Spiel.",
    scheduleFocusRecent: "Spielplan startet jetzt beim zuletzt gespielten Match.",
    scheduleFocusStart: "Komplette Timeline ab Turnierbeginn.",
    scheduleFocusFiltered: "Filter aktiv. Die Relevanznavigation bleibt als Schnellzugriff sichtbar.",
    scheduleHistoryCollapsed: "Frühere Turniertage sind eingeklappt, damit du schneller beim aktuellen Kontext landest.",
    scheduleHistorySummary: "Frühere Turniertage",
    scheduleHistoryCount: "historische Matches",
    metricMatches: "Gruppenspiele",
    metricForecasts: "mit Forecast",
    metricEdges: "Wettervorteile",
    metricTexts: "Social Hooks",
    forecastBandTitle: "Forecast-Abdeckung nach Turniertag",
    mapEyebrow: "Wetterkarte",
    mapTitle: "Spielorte & Bedingungen",
    mapAria: "Interaktive Wetterkarte",
    mapSelectAria: "Gruppenspieltag für Wetterkarte",
    mapCanvasAria: "Wetterkarte der Spielorte",
    mapDetailAria: "Wetterkarte Detail",
    legendLow: "niedrig",
    legendMedium: "mittel",
    legendHigh: "hoch",
    legendPending: "Forecast offen",
    tablesEyebrow: "Turnierdaten",
    tablesTitle: "Turnierstand & Tabellen",
    standingsKnockoutTitle: "KO-Baum",
    standingsKnockoutIntro: "Die KO-Runde folgt dem festen FIFA-Matchpfad. Offene Slots bleiben als Sieger- oder Verliererpfad sichtbar, bis ein Match entschieden ist.",
    standingsKnockoutMobileIntro: "Auf Mobilgeräten wird jeweils eine KO-Runde fokussiert angezeigt. Wechsle oben zwischen den Runden.",
    standingsGroupsTitle: "Gruppenstände",
    standingsGroupsIntro: "Alle zwölf Gruppen bleiben separat lesbar. Die KO-Runde steht darüber als eigener Bracket-Bereich.",
    standingsBestThirdTitle: "Beste Gruppendritte",
    standingsBestThirdIntro: "2026 ziehen zusätzlich die acht besten Gruppendritten in die KO-Runde ein. Die markierten Teams liegen aktuell auf Kurs.",
    standingsQualified: "auf KO-Kurs",
    standingsBubbleHint: "Zum Abschnitt springen",
    standingsBracketOpen: "Im Spielplan öffnen",
    standingsBracketSwipe: "Horizontal wischen für den kompletten Bracket-Pfad.",
    standingsBracketPending: "Pfadslot offen",
    standingsBracketWinnerOf: "Sieger",
    standingsBracketLoserOf: "Verlierer",
    standingsBracketFrom: "aus",
    standingsBracketThirdPlace: "Spiel um Platz 3",
    standingsBracketCurrent: "Aktuell im Fokus",
    standingsBracketFinished: "abgeschlossen",
    standingsBracketScheduled: "offen",
    tabStandings: "Stand",
    tabStats: "Stats",
    tabMatches: "Partien",
    tabMatchdays: "Spieltage",
    tabPhases: "Phasen",
    tabTravel: "Reisen",
    tabReport: "Report",
    statsTitle: "Die Tor-Fakten zur WM",
    statsIntro: "Diese Übersicht bündelt Tore, Gegentore und Timing-Muster aus dem aktuellen Turnierbild. Eventdaten werden separat ausgewiesen, damit Coverage und Lücken sichtbar bleiben.",
    statsMatchesFinished: "Beendete Spiele",
    statsTotalGoals: "Tore gesamt",
    statsGoalsPerMatch: "Tore pro Spiel",
    statsBtts: "Beide Teams trafen",
    statsTopAttack: "Stärkste Offensiven",
    statsTopDefense: "Anfälligste Defensiven",
    statsGoalDiff: "Beste Tordifferenz",
    statsCleanSheets: "Weiße Westen",
    statsBlanked: "Ohne eigenes Tor",
    statsGoalsFor: "Tore",
    statsGoalsAgainst: "Gegentore",
    statsGoalDifference: "Differenz",
    statsCleanSheetShort: "Zu null",
    statsBlankShort: "Ohne Tor",
    statsPerMatch: "pro Spiel",
    statsWeatherOverlay: "Wetter-Overlay",
    statsWeatherOverlayIntro: "Deskriptiver Kontext, kein Wirkungsnachweis. Solange Messdaten zum Ist-Wetter fehlen, basiert die Einordnung auf Forecast- und Weather-Fit-Werten.",
    statsLoadBuckets: "Tore nach Belastungsniveau",
    statsLoadLow: "Niedrige Belastung",
    statsLoadMedium: "Mittlere Belastung",
    statsLoadHigh: "Hohe Belastung",
    statsEdgePerformance: "Klare Wetterkante",
    statsEdgeWins: "Wetterseite gewann",
    statsEdgeDraws: "Wetterkante endete remis",
    statsEdgeLosses: "Wetterseite gewann nicht",
    statsEdgeWinRate: "Trefferquote Wetterkante",
    statsActualWeatherPending: "Noch keine belastbaren Messdaten zum Ist-Wetter. Deshalb bleiben alle Wetteraussagen vorläufig.",
    statsNoSignal: "Noch keine belastbaren Stats vorhanden.",
    statsEventCoverageTitle: "Event-Coverage",
    statsEventCoverageIntro: "Wie viele beendete Spiele bereits mit Tor-Events, Startelf, Wechseln und Hydration-Markern im Datenbestand stecken.",
    statsEventFactsTitle: "Tor-Muster aus Eventdaten",
    statsEventCoverageCompact: "Datenabdeckung",
    statsEventMatchesCovered: "Spiele mit Tor-Events",
    statsEventLineupsCovered: "Spiele mit kompletter Startelf",
    statsEventSubsCovered: "Spiele mit Wechsel-Events",
    statsEventHydrationCovered: "Spiele mit Hydration-Markern",
    statsEventMatchesCoveredShort: "Tore",
    statsEventLineupsCoveredShort: "Startelf",
    statsEventSubsCoveredShort: "Wechsel",
    statsEventHydrationCoveredShort: "Hydration",
    statsEventLastUpdate: "Letztes Event-Update",
    statsTopScorersTitle: "Gesamttorschuetzenliste",
    statsTopScorersIntro: "Oben steht immer die aktuelle Spitze. Fuer die komplette Rangliste kannst du direkt im Modul weiter scrollen.",
    statsTopScorersGoals: "Tore",
    statsTopScorersPrime: "Staerkstes Fenster",
    statsTopScorersEmpty: "Noch keine belastbare Torschuetzenliste im Datenstand.",
    statsGoalMinutePatterns: "Tor-Minuten",
    statsGoalWindows: "Teams treffen am häufigsten hier",
    statsConcedingWindows: "Teams kassieren am häufigsten hier",
    statsEarlyStarters: "Frühstarter",
    statsCrunchtimeScorers: "Schlussphase & Crunchtime",
    statsFirstHalfScorers: "Meiste Tore in Halbzeit eins",
    statsSecondHalfScorers: "Meiste Tore in Halbzeit zwei",
    statsFirstHalfConceders: "Meiste Gegentore in Halbzeit eins",
    statsSecondHalfConceders: "Meiste Gegentore in Halbzeit zwei",
    statsPlayerWindows: "Spieler mit klaren Zeitfenstern",
    statsPlayerGraphicTitle: "Wann treffen die WM-Stars am Liebsten?",
    statsPlayerGraphicIntro: "Wähle einen Torschützen und sieh, in welchen Zeitfenstern seine WM-Tore fallen.",
    statsPlayerSelectLabel: "Torschütze auswählen",
    statsPlayerTotalGoals: "WM-Tore",
    statsPlayerPrimeWindow: "Lieblingsfenster",
    statsPlayerNoGoals: "Noch keine Torschützen mit belastbaren Eventdaten verfügbar.",
    statsDedication: "Für die Data-Crunch-Legende Hannes: der Mann, der Excel-Tabellen noch aus Holz schnitzen konnte.",
    statsHydrationWindow: "Tore nach Hydration-Breaks",
    statsCoverageOpen: "Coverage offen",
    statsNeedsEventData: "Für volle Tor-Fakten fehlen noch Eventdaten pro Partie.",
    statsNoHydrationSignals: "Noch keine belastbaren Hydration-Signale im Datenstand.",
    statsDataGapTitle: "Noch nicht möglich mit dem aktuellen Bestand",
    statsDataGapBody: "15-Minuten-Segmente, Frühstarter, Schlussphasen, Hydration-Breaks, Torschützen, Startaufstellungen, Wechsel und Spieler-Rankings brauchen Eventdaten pro Spiel.",
    travelEyebrow: "Gruppenphase · Spielort-Routing",
    travelTitle: "Reisedistanzen der Teams",
    travelIntro: "Verglichen wird ausschließlich die Luftlinie zwischen den drei aufeinanderfolgenden Spielorten. Basislager, Hotels und reale Flug- oder Straßenrouten sind nicht enthalten.",
    travelSortAria: "Reiseranking sortieren",
    travelSortDistanceDesc: "Längste Distanz",
    travelSortDistanceAsc: "Kürzeste Distanz",
    travelSortCities: "Meiste verschiedene Orte",
    travelSortRepeats: "Häufigste Ortswiederholung",
    travelSortLoad: "Höchste kumulierte Belastung",
    travelLongest: "Längste Route",
    travelShortest: "Kürzeste Route",
    travelThreeCities: "Drei verschiedene Orte",
    travelRepeatVenue: "Mit Wiederholungsort",
    travelTeams: "Teams",
    travelDistance: "Gesamtdistanz",
    travelCities: "Orte",
    travelVenues: "Arenen",
    travelChanges: "Ortswechsel",
    travelRoute: "Die Spielorte des Teams",
    travelSameVenue: "Spiele am selben Ort",
    travelNoRepeat: "Kein Spielort doppelt",
    travelRankNotice: "Rang nach gewählter Sortierung",
    travelMethodNote: "Berechnung als Großkreis-Luftlinie von Stadion zu Stadion. Die Werte sind gerundet und beschreiben keine tatsächliche Anreise.",
    travelNoData: "Keine vollständigen Spielortdaten für die Gruppenphase vorhanden.",
    faq1Q: "Was zeigt der Weather Fit?",
    faq1A: "Der Wert vergleicht, wie gut beide Teams zur erwarteten Wettersituation passen. Berücksichtigt werden Temperatur, Luftfeuchtigkeit, Wind, Niederschlagsrisiko, Gewöhnung und wetterbezogene Toleranzprofile.",
    faq2Q: "Was bedeutet Wettervorteil?",
    faq2A: "Der Wettervorteil zeigt, welches Team besser zu den erwarteten Bedingungen passt. Kleine Unterschiede gelten als ausgeglichen. Er ist ein Kontextsignal, kein Ergebnisversprechen.",
    faq3Q: "Warum haben manche Spiele noch keinen Forecast?",
    faq3A: "Forecast-Daten liegen nur in einem begrenzten Vorhersagefenster vor. Sobald ein Spieltag nah genug ist, werden neue Open-Meteo-Daten importiert und die Match Cards aktualisiert.",
    faq4Q: "Was bedeuten die Prozentwerte?",
    faq4A: "Die Prozentwerte sind transparente MVP-Prognosen aus Teamstärke, Wetter, Zeitzone, Höhe und Standortnähe. Sie sind keine Wettquoten und keine sicheren Vorhersagen.",
    faq5Q: "Welche Daten werden beim Besuch verarbeitet?",
    faq5A: "Diese Website verwendet derzeit keine Cookies, kein Analytics und kein Werbetracking. Beim Hosting können technisch notwendige Server-Logdaten wie IP-Adresse, Zeitpunkt, aufgerufene Datei und Browserinformationen verarbeitet werden. Google Maps wird erst nach einem bewussten Klick geöffnet.",
    faq6Q: "Woher stammen Wetter-, Karten- und Turnierdaten?",
    faq6A: "Wetterdaten stammen von Open-Meteo und werden unter CC BY 4.0 genutzt. Die Kartengrundlage basiert auf Natural Earth, Public Domain. Spielplan-, Team- und Stadiondaten werden aus dokumentierten Quellen importiert und vor der Veröffentlichung plausibilisiert.",
    faq7Q: "Ist The Weather Cup ein offizielles FIFA-Angebot?",
    faq7A: "Nein. The Weather Cup ist ein unabhängiges Daten- und Analyseangebot und steht in keiner offiziellen Verbindung zur FIFA oder zu den teilnehmenden Verbänden. Namen, Logos und Marken gehören ihren jeweiligen Rechteinhabern.",
    faq8Q: "Wie verbindlich sind Wetterdaten und Prognosen?",
    faq8A: "Forecasts, Weather Fit, Wettervorteile und Siegchancen dienen ausschließlich der Information und Einordnung. Sie können sich durch neue Wetter- oder Turnierdaten ändern und sind weder Ergebnisgarantie noch Wettquote oder Handlungsempfehlung.",
    footerClaim: "Unabhängiges Wetter- und Turnierdatenangebot.",
    footerPrivacy: "Datenschutz",
    footerSources: "Datenquellen",
    footerLegal: "Rechtliche Hinweise",
    backToTop: "Nach oben",
    switchLanguage: "Switch to English",
    exportedAt: "Export",
    localExport: "Lokaler Datenexport",
    group: "Gruppe",
    allGroupMatchdays: "Alle Gruppenspieltage",
    groupMatchday: "Gruppenspieltag",
    groupStageShort: "GS",
    groupStageOpen: "GS offen",
    allGroups: "Alle Gruppen",
    tournamentDay: "Turniertag",
    tournamentDayOpen: "Turniertag offen",
    noDate: "kein Datum",
    to: "bis",
    yourTime: "Deine Zeit",
    venueTime: "Ortszeit",
    germany: "Deutschland",
    forecastPending: "Forecast offen",
    balanced: "Ausgeglichen",
    noMatches: "Keine Matches im aktuellen Filter",
    matches: "Partien",
    groups: "Gruppen",
    capacity: "Kapazität",
    stadiumType: "Stadiontyp",
    roof: "Dach",
    climateControl: "Klimatisierung",
    weatherProtection: "Wetterschutz",
    elevation: "Höhe",
    venuePanel: "Stadion & Bedingungen",
    venue: "Venue",
    googleMaps: "Google Maps",
    openVenueGoogleMaps: "Spielort in Google Maps öffnen",
    coordinate: "Koordinate",
    venueCoordinate: "Stadionkoordinate",
    approxAccuracy: "ca.",
    accuracyMeters: "m Genauigkeit",
    documentedSource: "Quelle im Datenbestand dokumentiert",
    dataFollows: "Daten folgen",
    seats: "Plätze",
    indoor: "Indoor",
    outdoor: "Outdoor",
    retractableRoof: "Schließbares Dach",
    openAir: "Offen",
    fixedRoof: "Festes Dach",
    canopy: "Tribünencanopy",
    partialCanopy: "Teilüberdacht",
    protectionHigh: "hoch",
    protectionMedium: "mittel",
    protectionPartial: "teilweise",
    protectionOpen: "offen",
    yes: "Ja",
    no: "Nein",
    humidityShort: "LF",
    kickoffTimes: "Anstoßzeiten",
    weatherLoad: "Weather Load",
    forecastOutside: "Forecast liegt noch nicht im nutzbaren Horizont.",
    socialFallback: "Social Hook folgt nach Forecast-Update.",
    weatherBalancedText: "Die Wettereignung ist ausgeglichen.",
    weatherContextSuffix: "Das ist ein Kontextindikator, kein Leistungsbeweis.",
    mapNoVenue: "Kein Spielort im aktuellen Filter",
    mapScale: "Weather Load: niedrig → hoch",
    mapForecastSummary: "Matches im aktuellen Kartenfilter mit Forecastdaten",
    mapVenueFallback: "Stadionkontext wird aus Venue-Daten berechnet.",
    openInMatchday: "Im Spieltag öffnen",
    standingsEmpty: "Noch kein Turnierstand vorhanden",
    team: "Team",
    playedShort: "Sp",
    played: "gespielt",
    status: "Status",
    weatherEdge: "Wettervorteil",
    finalScore: "Endstand",
    weatherFavouriteWon: "Wetterfavorit gewann",
    weatherBalance: "Wetterbilanz",
    weatherConfirmed: "Wettervorteil bestätigt",
    weatherNotConfirmed: "Wettervorteil nicht bestätigt",
    weatherBalancedResult: "Kein klarer Wettervorteil vor dem Spiel",
    clearWeatherEdges: "Partien mit klarem Wettervorteil",
    confirmedWeatherEdges: "Wetterfavorit gewann",
    unconfirmedWeatherEdges: "Wetterfavorit gewann nicht",
    drawnWeatherEdges: "Remis trotz Wettervorteil",
    weatherHitRate: "Trefferquote Wetterfaktor",
    weatherResultContext: "Kontexttreffer, kein Nachweis einer Ursache.",
    reportExamplesTitle: "Die Partien hinter der Quote",
    reportExamplesIntro: "Hier sieht man konkret, in welchen Spielen sich der Wettervorteil bestätigte, kippte oder in einem Remis endete.",
    reportEditionEyebrow: "Weather Cup Report 01",
    reportLeadTitle: "Die erste Bilanz nach der Gruppenphase",
    reportScope: "Scope",
    reportGoals: "Torbild",
    reportCoverage: "Event-Coverage",
    reportReadiness: "K.o.-Forecast",
    reportInsightsTitle: "Die vier wichtigsten Signale",
    reportInsightEdgeHit: "Wetterkante traf",
    reportInsightLoad: "Ø Weather Load",
    reportInsightDraws: "Remis-Anteil",
    reportInsightForecast: "K.o.-Spiele offen",
    reportFindingsTitle: "Key Findings",
    reportHistoryTitle: "Vergleich zu 2022, 2018, 2014 und 2010",
    reportHistoryIntro: "Der aktuelle Gruppenphasenstand laesst sich am saubersten als Turnier-Pace lesen: Wie torreich oder defensiv waere 2026, wenn sich dieses Niveau fortsetzt?",
    reportHistoryPaceLabel: "2026er Turnier-Pace",
    reportHistoryPaceLead: "Mehr Tore pro Spiel als in allen vier Vergleichsturnieren",
    reportHistoryPaceCaveat: "Verglichen wird der aktuelle Gruppenphasenwert 2026 mit den Gesamtturnieren 2022, 2018, 2014 und 2010.",
    reportHistoryChampion: "Sieger",
    reportHistoryTopScorer: "Top-Torschuetze",
    reportHistoryGoals: "Tore",
    reportHistoryGoalsPerMatch: "Tore/Spiel",
    reportContextTitle: "Kontext-Extremwerte",
    reportExtremeLoad: "Hoechster Load",
    reportExtremeEdge: "Schaerfste Wetterkante",
    reportExtremeTravel: "Laengste Reisekante",
    reportExtremeAltitude: "Hoechster Spielort",
    reportMethodTitle: "Methodik & Grenze",
    reportConfirmedTitle: "Wo sich der Wetterfavorit durchsetzte",
    reportMissedTitle: "Wo die Wetterkante nicht reichte",
    reportDrawTitle: "Klare Wetterkante, aber Remis",
    reportNoMatches: "Noch keine passenden Partien in dieser Kategorie.",
    reportEdgeGap: "Gap",
    reportResult: "Ergebnis",
    reportLocation: "Ort",
    reportDate: "Datum",
    reportOutcomeConfirmed: "Wettervorteil bestätigt",
    reportOutcomeMissed: "Wettervorteil nicht bestätigt",
    reportOutcomeDraw: "Wettervorteil endete im Remis",
    favoritesEyebrow: "Wettervorteil",
    favoritesTitle: "Wetterfavoriten",
    favoritesIntro: "Teams, deren Spielprofil besonders gut zu den erwarteten Bedingungen passt.",
    favoritesSelectAria: "Gruppenspieltag für Wetterfavoriten",
    favoritesEmpty: "Noch keine Wetterfavoriten mit belastbaren Forecastdaten vorhanden.",
    favoritesCount: "Favoriten",
    favoritesStrongest: "Stärkster Vorteil",
    favoritesForecastBasis: "Partien mit Wetterdaten",
    advantagePoints: "Vorteil",
    winChance: "Siegchance",
    weatherFit: "Weather Fit",
    opponent: "Gegner",
    viewMatch: "Partie ansehen",
    advantageNotice: "Die Rangliste zeigt wetterbedingte Kontextvorteile. Sie ist keine Ergebnisgarantie und kein Wettmodell.",
    advantageNoticeShort: "Wetterkontext, keine Ergebnisgarantie.",
    advantageNoticeable: "Spürbarer Wettervorteil",
    advantageStrong: "Starker Wettervorteil",
    advantageClear: "Deutlicher Wettervorteil",
    load: "Load",
    analysisFallback: "Analyse folgt, sobald Ergebnisse und Ist-Wetterdaten vorliegen.",
    noMatchAnalyses: "Noch keine Partieanalysen vorhanden",
    noAggregates: "Noch keine Aggregate vorhanden",
    noReport: "Noch keine Reportdaten vorhanden",
    matchesInDataset: "Partien im Datenstand",
    actualWeather: "mit Ist-Wetter",
    reportReady: "report-ready",
    reportCopy: "Die Turnierbilanz wird mit jeder beendeten Partie automatisch aktualisiert. Sie zeigt, wie häufig sich ein klarer Wettervorteil im Ergebnis bestätigte — als Kontextbeobachtung, nicht als Wirkungsnachweis.",
    adLabel: "Anzeige",
    adDefaultHeadline: "Partnerfläche",
    adDefaultBody: "Diese Fläche ist für einen offiziellen Dienstleister oder Medienpartner vorgesehen.",
  },
  en: {
    siteEyebrow: "World Cup 2026 Context Lab",
    heroClaim: "The daily view of the weather factor at the World Cup.",
    siteSubline: "Weather, travel, altitude and time zones for every match — data-based, bilingual, without result guarantees.",
    heroTodayCta: "View today’s matches",
    heroMapCta: "Open weather map",
    statusLoading: "Loading data status",
    navToday: "Today",
    navStats: "Stats",
    navSchedule: "Schedule",
    navMatchday: "Matchday",
    navFavorites: "Weather favourites",
    navMap: "Weather map",
    navTravel: "Travel ranking",
    navTables: "Tables",
    navFaq: "FAQ",
    todayContext: "The World Cup Day",
    todayNoMatches: "No matches today. Here are the next fixtures with the strongest context signals.",
    liveMatches: "Live matches",
    todayMatches: "Matches today",
    nextMatch: "Next match",
    highestLoad: "Highest Weather Load",
    biggestEdge: "Biggest weather advantage",
    highestTravel: "Longest travel leg",
    highestAltitude: "Highest altitude factor",
    nextUp: "Next Up",
    nextUpIntro: "The nearest fixtures and their strongest context signal.",
    topContextMatch: "Weather Match of the Day",
    upcomingMatches: "More upcoming matches",
    allUpcoming: "Open full schedule",
    realityCheck: "Reality Check",
    realityCheckIntro: "What the projection and weather advantage showed before kick-off — and how the match ended.",
    noFinishedMatches: "Results and context checks will appear here once matches finish.",
    favoritesPreview: "Weather favourites at a glance",
    travelPreview: "Travel load at a glance",
    venuePreview: "Toughest venues",
    tablePreview: "Current standings glance",
    methodologyEyebrow: "Method in brief",
    methodologyTitle: "What is a weather edge?",
    methodologyBody: "A context score comparing weather fit and match conditions. No result guarantee. Not a betting model.",
    viewAll: "View all",
    openFaq: "Open method & FAQ",
    statusLive: "Live",
    statusToday: "Today",
    statusUpcoming: "Upcoming",
    statusFinished: "Finished",
    liveContext: "View live context",
    viewGame: "View match",
    submitTip: "Make a pick",
    viewTip: "Review pick",
    topContextSignal: "Key weather factor",
    weatherShort: "Weather",
    travelShort: "Travel",
    predictionShort: "Prediction",
    distancePreviousVenue: "from previous venue",
    noPreviousTravel: "First group match",
    dataConfidence: "Data confidence",
    confidenceStable: "stable",
    confidenceMedium: "medium",
    confidenceLimited: "limited",
    matchDetails: "Match details",
    detailOverview: "Overview",
    detailWeather: "Weather",
    detailContext: "Additional conditions",
    detailVenue: "Stadium",
    detailPrediction: "Prediction & method",
    forecastWeather: "Weather forecast",
    historicalWeather: "Historical comparison",
    historicalWeatherPending: "Historical comparison values will be added once a reliable reference series is available.",
    actualWeatherPending: "Actual weather will be added automatically after the match once data becomes available.",
    actualWeatherLabel: "Actual weather",
    travelDistance: "Travel distance",
    recoveryTime: "Recovery time",
    timezoneLoad: "Time-zone factor",
    altitudeLoad: "Altitude factor",
    fanProximity: "Venue proximity",
    teamStrength: "Basic team strength",
    modelMethodNote: "All values are context indicators. They describe conditions, not outcomes, and are not a betting model.",
    forecastHelpfulEmpty: "Forecast not active yet. Historical weather, venue and travel indicators are already available.",
    weatherCoverageTitle: "Weather status",
    weatherCoverageAvailable: "Already available",
    weatherCoverageForecastSoon: "Forecast unlocks automatically closer to kickoff.",
    weatherCoverageActualSoon: "Actual weather is added after the match once observations are available.",
    weatherCoverageHistoricalSoon: "Historical comparison values are added once enough reference matches exist.",
    predictionDialogTitle: "Your pick",
    predictionQuestion: "How will the match end?",
    contextQuestion: "Will context play a visible role?",
    contextMatters: "Yes, visibly",
    contextLow: "Probably little",
    teamAWins: "Team A wins",
    drawPick: "Draw",
    teamBWins: "Team B wins",
    predictionStored: "Your pick is saved on this device.",
    predictionConfirm: "Save pick",
    predictionUpdate: "Update pick",
    predictionChooseBoth: "Please select a result and the role of context.",
    predictionSavedStrong: "Pick saved successfully",
    predictionCorrect: "Your result pick was correct.",
    predictionWrong: "Your result pick was not correct.",
    predictionPending: "Evaluation follows after full time.",
    localOnlyNote: "No login. Stored only in this browser.",
    close: "Close",
    tipScore: "Pick record",
    personalTipBalance: "Your pick record",
    noPersonalTips: "No completed picks on this device yet.",
    correctTips: "correct picks",
    forecastVsActual: "Forecast vs actual weather",
    forecastVsActualPending: "Actual weather not available yet",
    forecastVsResult: "Prediction vs result",
    predictionMatched: "Prediction matched",
    predictionMissed: "Prediction differed",
    contextNotGuarantee: "Context data shows conditions, not guarantees.",
    mapViewVenues: "Venues",
    mapViewMap: "Map",
    hardestVenues: "Toughest venues today",
    closeVenue: "Close details",
    contextOutlook: "Context outlook",
    nextGroupMatch: "Next group match",
    bestGroupFit: "Best Weather Fit",
    groupTravelLoad: "Highest travel load",
    groupWeatherLoad: "Highest Weather Load",
    faq9Q: "How does the prediction feature work?",
    faq9A: "Your picks are stored only in this browser. There is no account, no transfer of personal data and no mandatory tracking. You can remove local picks at any time through your browser data.",
    searchPlaceholder: "Team, group, city, match ID",
    modeAll: "All",
    modeEdge: "Weather advantage",
    scheduleSmart: "Relevant now",
    scheduleFull: "Full timeline",
    jumpCurrent: "Jump to current match",
    jumpLive: "Live",
    jumpToday: "Today",
    jumpNext: "Next match",
    jumpRecent: "Last finished",
    jumpStart: "Tournament start",
    jumpOpenHistory: "Show earlier matchdays",
    jumpCloseHistory: "Hide earlier matchdays",
    scheduleFocusToday: "The schedule now starts at today’s matches.",
    scheduleFocusLive: "The schedule now starts at the live matches.",
    scheduleFocusNext: "The schedule now starts at the next match.",
    scheduleFocusRecent: "The schedule now starts at the latest finished match.",
    scheduleFocusStart: "Full timeline from the opening match.",
    scheduleFocusFiltered: "Filters are active. Quick relevance jumps remain available.",
    scheduleHistoryCollapsed: "Earlier tournament days are collapsed so you reach the current context faster.",
    scheduleHistorySummary: "Earlier tournament days",
    scheduleHistoryCount: "historical matches",
    metricMatches: "Group matches",
    metricForecasts: "with forecast",
    metricEdges: "Weather advantages",
    metricTexts: "Social hooks",
    forecastBandTitle: "Forecast coverage by tournament day",
    mapEyebrow: "Weather map",
    mapTitle: "Venues & conditions",
    mapAria: "Interactive weather map",
    mapSelectAria: "Group matchday for weather map",
    mapCanvasAria: "Weather map of venues",
    mapDetailAria: "Weather map details",
    legendLow: "low",
    legendMedium: "medium",
    legendHigh: "high",
    legendPending: "Forecast pending",
    tablesEyebrow: "Tournament data",
    tablesTitle: "Standings & tables",
    standingsKnockoutTitle: "Knockout bracket",
    standingsKnockoutIntro: "The knockout stage follows the fixed FIFA match path. Open slots stay visible as winner or loser paths until the upstream match is decided.",
    standingsKnockoutMobileIntro: "On mobile, one knockout round is focused at a time. Use the buttons above to switch rounds.",
    standingsGroupsTitle: "Group standings",
    standingsGroupsIntro: "All twelve groups remain readable on their own. The knockout stage lives above them as a dedicated bracket.",
    standingsBestThirdTitle: "Best third-placed teams",
    standingsBestThirdIntro: "In 2026 the eight best third-placed teams also advance. Highlighted teams are currently on course.",
    standingsQualified: "currently through",
    standingsBubbleHint: "Jump to section",
    standingsBracketOpen: "Open in schedule",
    standingsBracketSwipe: "Swipe horizontally for the full bracket path.",
    standingsBracketPending: "Path slot open",
    standingsBracketWinnerOf: "Winner",
    standingsBracketLoserOf: "Loser",
    standingsBracketFrom: "from",
    standingsBracketThirdPlace: "Third-place match",
    standingsBracketCurrent: "Current focus",
    standingsBracketFinished: "completed",
    standingsBracketScheduled: "open",
    tabStandings: "Standings",
    tabStats: "Stats",
    tabMatches: "Matches",
    tabMatchdays: "Matchdays",
    tabPhases: "Phases",
    tabTravel: "Travel",
    tabReport: "Report",
    statsTitle: "The World Cup goal facts",
    statsIntro: "This view bundles goals, goals conceded and timing patterns from the current tournament picture. Match event coverage is shown separately so gaps stay visible.",
    statsMatchesFinished: "Finished matches",
    statsTotalGoals: "Total goals",
    statsGoalsPerMatch: "Goals per match",
    statsBtts: "Both teams scored",
    statsTopAttack: "Best attacks",
    statsTopDefense: "Most goals conceded",
    statsGoalDiff: "Best goal difference",
    statsCleanSheets: "Clean sheets",
    statsBlanked: "Failed to score",
    statsGoalsFor: "Goals",
    statsGoalsAgainst: "Conceded",
    statsGoalDifference: "Difference",
    statsCleanSheetShort: "Clean sheets",
    statsBlankShort: "No goals",
    statsPerMatch: "per match",
    statsWeatherOverlay: "Weather overlay",
    statsWeatherOverlayIntro: "Descriptive context, not proof of causation. Until actual measurements arrive, this view is limited to forecast and Weather Fit values.",
    statsLoadBuckets: "Goals by load band",
    statsLoadLow: "Low load",
    statsLoadMedium: "Medium load",
    statsLoadHigh: "High load",
    statsEdgePerformance: "Clear weather edge",
    statsEdgeWins: "Weather side won",
    statsEdgeDraws: "Weather edge ended level",
    statsEdgeLosses: "Weather side did not win",
    statsEdgeWinRate: "Weather-edge hit rate",
    statsActualWeatherPending: "There are still no robust actual-weather measurements. Any weather takeaway remains provisional.",
    statsNoSignal: "No robust stats available yet.",
    statsEventCoverageTitle: "Event coverage",
    statsEventCoverageIntro: "How many finished matches already include goal events, lineups, substitutions and hydration markers in the dataset.",
    statsEventFactsTitle: "Goal patterns from event data",
    statsEventCoverageCompact: "Coverage",
    statsEventMatchesCovered: "Matches with goal events",
    statsEventLineupsCovered: "Matches with full lineups",
    statsEventSubsCovered: "Matches with substitution events",
    statsEventHydrationCovered: "Matches with hydration markers",
    statsEventMatchesCoveredShort: "Goals",
    statsEventLineupsCoveredShort: "Lineups",
    statsEventSubsCoveredShort: "Subs",
    statsEventHydrationCoveredShort: "Hydration",
    statsEventLastUpdate: "Last event update",
    statsTopScorersTitle: "Overall scoring chart",
    statsTopScorersIntro: "The current leaders stay visible at the top; the full table continues inside the module.",
    statsTopScorersGoals: "Goals",
    statsTopScorersPrime: "Best window",
    statsTopScorersEmpty: "No reliable scoring chart is available yet.",
    statsGoalMinutePatterns: "Goal timing",
    statsGoalWindows: "Teams score most often here",
    statsConcedingWindows: "Teams concede most often here",
    statsEarlyStarters: "Fast starters",
    statsCrunchtimeScorers: "Late phase & crunchtime",
    statsFirstHalfScorers: "Most first-half goals",
    statsSecondHalfScorers: "Most second-half goals",
    statsFirstHalfConceders: "Most first-half concessions",
    statsSecondHalfConceders: "Most second-half concessions",
    statsPlayerWindows: "Players with clear timing windows",
    statsPlayerGraphicTitle: "When do the World Cup stars like to score?",
    statsPlayerGraphicIntro: "Pick a scorer and see in which windows their World Cup goals arrive.",
    statsPlayerSelectLabel: "Choose scorer",
    statsPlayerTotalGoals: "World Cup goals",
    statsPlayerPrimeWindow: "Prime window",
    statsPlayerNoGoals: "No scorers with reliable event data available yet.",
    statsDedication: "For data-crunch legend Hannes: the man who could still carve Excel spreadsheets out of wood.",
    statsHydrationWindow: "Goals after hydration breaks",
    statsCoverageOpen: "Coverage pending",
    statsNeedsEventData: "Full goal facts still require match event rows.",
    statsNoHydrationSignals: "No robust hydration signals in the dataset yet.",
    statsDataGapTitle: "Not yet possible from the current dataset",
    statsDataGapBody: "15-minute segments, fast starters, late surges, hydration-break effects, scorers, lineups, substitutions and player rankings all require match event data.",
    travelEyebrow: "Group stage · venue routing",
    travelTitle: "Team travel distances",
    travelIntro: "The comparison uses only the great-circle distance between the three consecutive match venues. Base camps, hotels and actual flight or road routes are not included.",
    travelSortAria: "Sort travel ranking",
    travelSortDistanceDesc: "Longest distance",
    travelSortDistanceAsc: "Shortest distance",
    travelSortCities: "Most different locations",
    travelSortRepeats: "Most venue repetition",
    travelSortLoad: "Highest cumulative load",
    travelLongest: "Longest route",
    travelShortest: "Shortest route",
    travelThreeCities: "Three different locations",
    travelRepeatVenue: "With a repeated venue",
    travelTeams: "Teams",
    travelDistance: "Total distance",
    travelCities: "Locations",
    travelVenues: "Venues",
    travelChanges: "Location changes",
    travelRoute: "The team's venues",
    travelSameVenue: "Matches at same venue",
    travelNoRepeat: "No venue repeated",
    travelRankNotice: "Rank for the selected sorting",
    travelMethodNote: "Calculated as stadium-to-stadium great-circle distance. Values are rounded and do not represent actual travel routes.",
    travelNoData: "No complete group-stage venue data is available.",
    faq1Q: "What does Weather Fit show?",
    faq1A: "The score compares how well both teams fit the expected weather situation. It considers temperature, humidity, wind, precipitation risk, familiarity and weather tolerance profiles.",
    faq2Q: "What does weather advantage mean?",
    faq2A: "Weather advantage shows which team is better suited to the expected conditions. Small differences are treated as balanced. It is a context signal, not a result prediction.",
    faq3Q: "Why do some matches not have a forecast yet?",
    faq3A: "Forecast data is only available inside a limited prediction window. Once a matchday is close enough, fresh Open-Meteo data is imported and the match cards update.",
    faq4Q: "What do the percentage values mean?",
    faq4A: "The percentages are transparent MVP projections based on team strength, weather, time zone, elevation and venue proximity. They are not betting odds and not guaranteed predictions.",
    faq5Q: "What data is processed when visiting the website?",
    faq5A: "This website currently uses no cookies, analytics or advertising tracking. The hosting provider may process technically necessary server logs such as IP address, timestamp, requested file and browser information. Google Maps opens only after a deliberate click.",
    faq6Q: "Where do the weather, map and tournament data come from?",
    faq6A: "Weather data is provided by Open-Meteo under CC BY 4.0. The map base uses Natural Earth public-domain data. Schedule, team and stadium data is imported from documented sources and checked for plausibility before publication.",
    faq7Q: "Is The Weather Cup an official FIFA product?",
    faq7A: "No. The Weather Cup is an independent data and analysis product and has no official affiliation with FIFA or the participating associations. Names, logos and trademarks belong to their respective owners.",
    faq8Q: "How reliable are the weather data and projections?",
    faq8A: "Forecasts, Weather Fit, weather advantages and win probabilities are provided solely for information and context. They may change as new weather or tournament data arrives and are not a result guarantee, betting odds or a recommendation to act.",
    footerClaim: "Independent weather and tournament data product.",
    footerPrivacy: "Privacy",
    footerSources: "Data sources",
    footerLegal: "Legal notice",
    backToTop: "Top",
    switchLanguage: "Zur deutschen Version wechseln",
    exportedAt: "Export",
    localExport: "Local data export",
    group: "Group",
    allGroupMatchdays: "All group matchdays",
    groupMatchday: "Group matchday",
    groupStageShort: "MD",
    groupStageOpen: "MD open",
    allGroups: "All groups",
    tournamentDay: "Tournament day",
    tournamentDayOpen: "Tournament day open",
    noDate: "no date",
    to: "to",
    yourTime: "Your time",
    venueTime: "Venue time",
    germany: "Germany",
    forecastPending: "Forecast pending",
    balanced: "Balanced",
    noMatches: "No matches in the current filter",
    matches: "matches",
    groups: "Groups",
    capacity: "Capacity",
    stadiumType: "Stadium type",
    roof: "Roof",
    climateControl: "Climate control",
    weatherProtection: "Weather protection",
    elevation: "Elevation",
    venuePanel: "Stadium & conditions",
    venue: "Venue",
    googleMaps: "Google Maps",
    openVenueGoogleMaps: "Open venue in Google Maps",
    coordinate: "Coordinate",
    venueCoordinate: "Venue coordinate",
    approxAccuracy: "approx.",
    accuracyMeters: "m accuracy",
    documentedSource: "source documented in dataset",
    dataFollows: "Data pending",
    seats: "seats",
    indoor: "Indoor",
    outdoor: "Outdoor",
    retractableRoof: "Retractable roof",
    openAir: "Open air",
    fixedRoof: "Fixed roof",
    canopy: "Stand canopy",
    partialCanopy: "Partially covered",
    protectionHigh: "high",
    protectionMedium: "medium",
    protectionPartial: "partial",
    protectionOpen: "open",
    yes: "Yes",
    no: "No",
    humidityShort: "RH",
    kickoffTimes: "Kickoff times",
    weatherLoad: "Weather Load",
    forecastOutside: "Forecast is not yet inside the usable horizon.",
    socialFallback: "Social hook follows after the forecast update.",
    weatherBalancedText: "The weather fit is balanced.",
    weatherContextSuffix: "This is a context indicator, not proof of performance.",
    mapNoVenue: "No venue in the current filter",
    mapScale: "Weather Load: low → high",
    mapForecastSummary: "Matches in the current map filter with forecast data",
    mapVenueFallback: "Venue context is calculated from venue data.",
    openInMatchday: "Open in Matchday",
    standingsEmpty: "No standings available yet",
    team: "Team",
    playedShort: "P",
    played: "played",
    status: "Status",
    weatherEdge: "Weather advantage",
    finalScore: "Full time",
    weatherFavouriteWon: "Weather favourite won",
    weatherBalance: "Weather record",
    weatherConfirmed: "Weather advantage confirmed",
    weatherNotConfirmed: "Weather advantage not confirmed",
    weatherBalancedResult: "No clear weather advantage before kick-off",
    clearWeatherEdges: "Matches with a clear weather advantage",
    confirmedWeatherEdges: "Weather favourite won",
    unconfirmedWeatherEdges: "Weather favourite did not win",
    drawnWeatherEdges: "Draws despite a weather edge",
    weatherHitRate: "Weather-factor hit rate",
    weatherResultContext: "Context hit, not evidence of causation.",
    reportExamplesTitle: "The matches behind the hit rate",
    reportExamplesIntro: "This view shows the exact matches in which the weather edge held, flipped, or ended in a draw.",
    reportEditionEyebrow: "Weather Cup Report 01",
    reportLeadTitle: "The first checkpoint after the group stage",
    reportScope: "Scope",
    reportGoals: "Goal profile",
    reportCoverage: "Event coverage",
    reportReadiness: "Knockout forecast",
    reportInsightsTitle: "The four strongest signals",
    reportInsightEdgeHit: "Weather edge held",
    reportInsightLoad: "Avg Weather Load",
    reportInsightDraws: "Draw share",
    reportInsightForecast: "Open knockout matches",
    reportFindingsTitle: "Key findings",
    reportHistoryTitle: "Benchmarks versus 2022, 2018, 2014 and 2010",
    reportHistoryIntro: "The cleanest way to read the current group-stage sample is as tournament pace: how open or high-scoring 2026 would look if this level held.",
    reportHistoryPaceLabel: "2026 tournament pace",
    reportHistoryPaceLead: "More goals per match than all four comparison tournaments",
    reportHistoryPaceCaveat: "This compares the current 2026 group-stage rate with the full tournaments in 2022, 2018, 2014 and 2010.",
    reportHistoryChampion: "Champion",
    reportHistoryTopScorer: "Top scorer",
    reportHistoryGoals: "Goals",
    reportHistoryGoalsPerMatch: "Goals/match",
    reportContextTitle: "Context extremes",
    reportExtremeLoad: "Highest load",
    reportExtremeEdge: "Sharpest edge",
    reportExtremeTravel: "Longest travel edge",
    reportExtremeAltitude: "Highest venue",
    reportMethodTitle: "Method & limit",
    reportConfirmedTitle: "Where the weather favourite delivered",
    reportMissedTitle: "Where the weather edge did not hold",
    reportDrawTitle: "Clear weather edge, but a draw",
    reportNoMatches: "No matches in this category yet.",
    reportEdgeGap: "Gap",
    reportResult: "Result",
    reportLocation: "Location",
    reportDate: "Date",
    reportOutcomeConfirmed: "Weather edge confirmed",
    reportOutcomeMissed: "Weather edge not confirmed",
    reportOutcomeDraw: "Weather edge ended in a draw",
    favoritesEyebrow: "Weather advantage",
    favoritesTitle: "Weather favourites",
    favoritesIntro: "Teams whose playing profile is especially well suited to the expected conditions.",
    favoritesSelectAria: "Group matchday for weather favourites",
    favoritesEmpty: "No weather favourites with reliable forecast data yet.",
    favoritesCount: "Favourites",
    favoritesStrongest: "Strongest advantage",
    favoritesForecastBasis: "Matches with weather data",
    advantagePoints: "Advantage",
    winChance: "Win chance",
    weatherFit: "Weather Fit",
    opponent: "Opponent",
    viewMatch: "View match",
    advantageNotice: "This ranking shows weather-related context advantages. It is not a result guarantee or betting model.",
    advantageNoticeShort: "Weather context, not a result guarantee.",
    advantageNoticeable: "Noticeable weather advantage",
    advantageStrong: "Strong weather advantage",
    advantageClear: "Clear weather advantage",
    load: "Load",
    analysisFallback: "Analysis follows once results and actual weather data are available.",
    noMatchAnalyses: "No match analyses available yet",
    noAggregates: "No aggregates available yet",
    noReport: "No report data available yet",
    matchesInDataset: "matches in dataset",
    actualWeather: "with actual weather",
    reportReady: "report-ready",
    reportCopy: "The tournament record updates automatically after every finished match. It shows how often a clear weather advantage was reflected in the result — as context, not proof of causation.",
    adLabel: "Ad",
    adDefaultHeadline: "Partner placement",
    adDefaultBody: "This placement is reserved for an official service provider, sponsor or media partner.",
  },
};

const AD_TRANSLATIONS_EN = {
  tables_top: {
    headline: "Report partner",
    body: "Placement for report sponsorship and B2B service providers.",
    call_to_action: "Request media kit",
  },
  map_sidebar: {
    headline: "Weather data partner",
    body: "Placement for providers in weather, travel, mobility or sports data.",
    call_to_action: "Get in touch",
  },
  matchday_inline: {
    headline: "Context partner",
    body: "Native ad placement between matchday overview and match list.",
    call_to_action: "Learn more",
  },
  matchday_top: {
    headline: "Matchday partner placement",
    body: "This space is reserved for an official service provider, sponsor or media partner.",
    call_to_action: "Request media kit",
  },
};

const HISTORICAL_WORLD_CUP_BASELINES = [
  {
    year: 2022,
    champion: "ARG",
    topScorer: "Kylian Mbappé",
    topScorerGoals: 8,
    matches: 64,
    goals: 172,
    goalsPerMatch: 2.69,
    note_de: "Katar 2022 endete mit 172 Toren und einem 3:3-Finale. Marokko wurde als erstes afrikanisches Team Halbfinalist.",
    note_en: "Qatar 2022 ended with 172 goals and a 3-3 final. Morocco became the first African semi-finalist.",
  },
  {
    year: 2018,
    champion: "FRA",
    topScorer: "Harry Kane",
    topScorerGoals: 6,
    matches: 64,
    goals: 169,
    goalsPerMatch: 2.64,
    note_de: "Russland 2018 brachte 169 Tore. Deutschland schied als Titelverteidiger in der Gruppenphase aus; das Turnier setzte mit 12 Eigentoren einen Rekord.",
    note_en: "Russia 2018 produced 169 goals. Germany exited in the group stage as defending champion; the tournament set a record with 12 own goals.",
  },
  {
    year: 2014,
    champion: "DEU",
    topScorer: "James Rodríguez",
    topScorerGoals: 6,
    matches: 64,
    goals: 171,
    goalsPerMatch: 2.67,
    note_de: "Brasilien 2014 blieb mit 171 Toren eines der offensivsten Turniere der Neuzeit. Die Gruppenphase brachte 136 Tore und im Halbfinale stand das 7:1 gegen Brasilien.",
    note_en: "Brazil 2014 remained one of the most attack-heavy modern tournaments with 171 goals. Its group stage produced 136 goals and the semi-final featured the 7-1 against Brazil.",
  },
  {
    year: 2010,
    champion: "ESP",
    topScorer: "Forlán / Müller / Sneijder / Villa",
    topScorerGoals: 5,
    matches: 64,
    goals: 145,
    goalsPerMatch: 2.27,
    note_de: "Suedafrika 2010 war das torarmste der vier Vergleichsturniere. Spanien gewann den Titel mit nur acht eigenen Turniertoren.",
    note_en: "South Africa 2010 was the lowest-scoring tournament of the four. Spain won the title with only eight goals of its own.",
  },
];

const MAP_BOUNDS = {
  minLon: -132,
  maxLon: -52,
  minLat: 13,
  maxLat: 62,
};

function currentReport() {
  return source.reports && source.reports.group_stage_2026 ? source.reports.group_stage_2026 : null;
}
const MAP_VIEWBOX = { width: 1000, height: 620 };
const FALLBACK_USER_TIME_ZONE = "Europe/Berlin";
const GERMAN_TEXT_FIXES = [
  [/Suedafrika/g, "Südafrika"],
  [/Suedkorea/g, "Südkorea"],
  [/Tuerkei/g, "Türkei"],
  [/Oesterreich/g, "Österreich"],
  [/Aegypten/g, "Ägypten"],
  [/Elfenbeinkueste/g, "Elfenbeinküste"],
  [/Curacao/g, "Curaçao"],
  [/fuer/g, "für"],
  [/dafuer/g, "dafür"],
  [/spaeter/g, "später"],
  [/ausgefuehrt/g, "ausgeführt"],
  [/Beruecksichtigt/g, "Berücksichtigt"],
  [/Gewoehnung/g, "Gewöhnung"],
  [/Teamstaerke/g, "Teamstärke"],
  [/Hoehen/g, "Höhen"],
  [/Hoehe/g, "Höhe"],
  [/Standortnaehe/g, "Standortnähe"],
  [/auffaellig/g, "auffällig"],
  [/groesste/g, "größte"],
  [/groesser/g, "größer"],
  [/ausserhalb/g, "außerhalb"],
  [/Anstoss/g, "Anstoß"],
  [/faellig/g, "fällig"],
];
const USER_TIME_ZONE = (() => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || FALLBACK_USER_TIME_ZONE;
  } catch {
    return FALLBACK_USER_TIME_ZONE;
  }
})();

function t(key) {
  return I18N[state.lang]?.[key] || I18N.de[key] || key;
}

function currentLocale() {
  return state.lang === "en" ? "en-GB" : "de-DE";
}

function localizedField(item, fieldBase) {
  const languageValue = item?.[`${fieldBase}_${state.lang}`];
  if (languageValue !== null && languageValue !== undefined && languageValue !== "") {
    return state.lang === "de" ? normalizeGermanText(languageValue) : languageValue;
  }
  const fallbackValue = item?.[`${fieldBase}_de`] ?? item?.[fieldBase];
  return state.lang === "de" ? normalizeGermanText(fallbackValue) : fallbackValue;
}

function valueOrDash(value, suffix = "") {
  if (value === null || value === undefined || value === "") return "–";
  return `${value}${suffix}`;
}

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "–";
  return `${Number(value).toFixed(1)}%`;
}

function score(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "–";
  return `${Math.round(Number(value))}`;
}

function zoneDisplayName(timeZone) {
  if (timeZone === "Europe/Berlin") return t("germany");
  return String(timeZone || FALLBACK_USER_TIME_ZONE).replace(/_/g, " ");
}

function normalizeGermanText(value) {
  if (value === null || value === undefined) return value;
  return GERMAN_TEXT_FIXES.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), String(value));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, "&#096;");
}

function safeHttpUrl(value) {
  if (!value) return "";
  try {
    const url = new URL(String(value), window.location.href);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "";
  } catch {
    return "";
  }
}

function zonedDateTime(match, timeZone = USER_TIME_ZONE) {
  const pendingDate = state.lang === "en" ? "Date pending" : "Termin offen";
  if (!match.date_utc) {
    return {
      key: match.local_date || "open",
      date: match.local_date || pendingDate,
      shortDate: match.local_date || pendingDate,
      time: String(match.local_time || "").slice(0, 5) || "–",
      zoneName: timeZone,
      weekday: "",
      shortLabel: `${match.local_date || pendingDate} · ${String(match.local_time || "").slice(0, 5) || "–"}`,
      detailLabel: `${match.local_date || pendingDate} · ${String(match.local_time || "").slice(0, 5) || "–"}`,
    };
  }
  const date = new Date(match.date_utc);
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat(currentLocale(), {
      timeZone,
      weekday: "short",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
      hourCycle: "h23",
    })
      .formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value])
  );
  const key = `${parts.year}-${parts.month}-${parts.day}`;
  return {
    key,
    date: `${parts.day}.${parts.month}.${parts.year}`,
    shortDate: `${parts.day}.${parts.month}.`,
    time: `${parts.hour}:${parts.minute}`,
    zoneName: parts.timeZoneName || timeZone,
    weekday: parts.weekday,
    shortLabel: `${parts.day}.${parts.month}. ${parts.hour}:${parts.minute} ${parts.timeZoneName || ""}`.trim(),
    detailLabel: `${parts.weekday}, ${parts.day}.${parts.month}.${parts.year} · ${parts.hour}:${parts.minute} ${parts.timeZoneName || ""}`.trim(),
  };
}

function viewerDateTime(match) {
  return zonedDateTime(match, USER_TIME_ZONE);
}

function hostDateTime(match) {
  return zonedDateTime(match, match.local_timezone || USER_TIME_ZONE);
}

function dateLabel(match) {
  const dateTime = viewerDateTime(match);
  return `${dateTime.shortDate} · ${dateTime.time}`;
}

function hostDateLabel(match) {
  return hostDateTime(match).detailLabel;
}

function timePair(match) {
  const viewer = viewerDateTime(match);
  const host = hostDateTime(match);
  return `<div class="time-pair">
    <div class="time-chip"><span>${t("yourTime")}</span><b>${viewer.shortLabel}</b><small>${zoneDisplayName(USER_TIME_ZONE)}</small></div>
    <div class="time-chip"><span>${t("venueTime")}</span><b>${host.shortLabel}</b><small>${match.host_city || ""}</small></div>
  </div>`;
}

function groupMatchdayLabel(value) {
  if (!value || value === "all") return t("allGroupMatchdays");
  const number = Number(value);
  if (Number.isNaN(number)) return String(value);
  return state.lang === "en" ? `${t("groupMatchday")} ${number}` : `${number}. ${t("groupMatchday")}`;
}

function compactGroupMatchdayLabel(value) {
  if (!value) return t("groupStageOpen");
  const number = Number(value);
  if (Number.isNaN(number)) return String(value);
  return state.lang === "en" ? `${t("groupStageShort")} ${number}` : `${number}. ${t("groupStageShort")}`;
}

function calendarDayLabel(match) {
  if (match.calendar_day) return `${t("tournamentDay")} ${match.calendar_day}`;
  return t("tournamentDayOpen");
}

function dateRangeLabel(matches) {
  if (!matches.length) return t("noDate");
  const dates = [...new Map(matches.map((match) => [viewerDateTime(match).key, viewerDateTime(match)])).values()];
  dates.sort((a, b) => a.key.localeCompare(b.key));
  const first = dates[0];
  const last = dates[dates.length - 1];
  return first.key === last.key ? first.date : `${first.date} ${t("to")} ${last.date}`;
}

function teamName(match, side) {
  return localizedField(match, `team_${side}_name`) || match[`team_${side}_iso3`];
}

function displayIso3(iso3) {
  return iso3 === "CHE" ? "SUI" : iso3;
}

function displayStatKey(value, label) {
  if (label === "Teams" && /^[A-Z]{3}$/.test(value || "")) {
    return displayIso3(value);
  }
  return value || "–";
}

function teamLabel(match, side) {
  return `${match[`team_${side}_flag`] || ""} ${teamName(match, side)}`;
}

function hasForecast(match) {
  return match.forecast_temp !== null && match.forecast_temp !== undefined;
}

function hasWeatherFit(match) {
  return match.team_a_weather_fit_score !== null && match.team_a_weather_fit_score !== undefined;
}

function isFinished(match) {
  return match.match_status === "finished"
    && match.result_team_a !== null
    && match.result_team_a !== undefined
    && match.result_team_b !== null
    && match.result_team_b !== undefined;
}

function resultWinnerSide(match) {
  if (!isFinished(match)) return null;
  const teamAResult = Number(match.result_team_a);
  const teamBResult = Number(match.result_team_b);
  if (teamAResult === teamBResult) return "draw";
  return teamAResult > teamBResult ? "a" : "b";
}

function weatherLeaderSide(match) {
  if (!hasWeatherFit(match)) return null;
  const teamAFit = Number(match.team_a_weather_fit_score);
  const teamBFit = Number(match.team_b_weather_fit_score);
  if (!Number.isFinite(teamAFit) || !Number.isFinite(teamBFit) || Math.abs(teamAFit - teamBFit) < 4) return null;
  return teamAFit > teamBFit ? "a" : "b";
}

function weatherFavouriteWon(match) {
  const weatherLeader = weatherLeaderSide(match);
  return Boolean(weatherLeader && resultWinnerSide(match) === weatherLeader);
}

function weatherBalanceResult(match) {
  if (!isFinished(match)) return { status: "pending", leader: null };
  const leader = weatherLeaderSide(match);
  if (!leader) return { status: "balanced", leader: null };
  return {
    status: resultWinnerSide(match) === leader ? "confirmed" : "not_confirmed",
    leader,
  };
}

function tournamentWeatherBalance() {
  const finished = source.matches.filter(isFinished);
  const comparable = finished.filter((match) => weatherLeaderSide(match));
  const confirmed = comparable.filter(weatherFavouriteWon).length;
  return {
    finished: finished.length,
    comparable: comparable.length,
    confirmed,
    notConfirmed: comparable.length - confirmed,
    hitRate: comparable.length ? Math.round((confirmed / comparable.length) * 100) : null,
  };
}

function reportMatchEntries() {
  const analysisById = new Map(((source.analysis && source.analysis.matches) || []).map((item) => [item.match_id, item]));
  const entries = source.matches
    .filter((match) => isFinished(match) && weatherLeaderSide(match))
    .map((match) => {
      const leaderSide = weatherLeaderSide(match);
      const winnerSide = resultWinnerSide(match);
      const analysis = analysisById.get(match.match_id) || {};
      const edgeTeam = match[`team_${leaderSide}_iso3`];
      return {
        match_id: match.match_id,
        label: analysis.label || `${displayIso3(match.team_a_iso3)} vs. ${displayIso3(match.team_b_iso3)}`,
        result: `${match.result_team_a}:${match.result_team_b}`,
        weather_edge: analysis.weather_edge || `${edgeTeam} Edge`,
        weather_load_score: analysis.weather_load_score ?? match.weather_load_score,
        host_city: analysis.host_city || match.host_city,
        local_date: match.local_date,
        gap: Number(match.weather_fit_edge_gap),
        category: winnerSide === "draw" ? "draw" : winnerSide === leaderSide ? "confirmed" : "missed",
      };
    })
    .sort((a, b) => (b.gap || 0) - (a.gap || 0));
  return {
    confirmed: entries.filter((item) => item.category === "confirmed"),
    missed: entries.filter((item) => item.category === "missed"),
    draw: entries.filter((item) => item.category === "draw"),
  };
}

function reportOutcomeLabel(category) {
  if (category === "confirmed") return t("reportOutcomeConfirmed");
  if (category === "draw") return t("reportOutcomeDraw");
  return t("reportOutcomeMissed");
}

function finishedDatasetMatches() {
  return source.matches.filter(isFinished);
}

function tournamentTeamStats() {
  const teams = new Map();
  const ensure = (iso3, match, side) => {
    if (!teams.has(iso3)) {
      teams.set(iso3, {
        iso3,
        flag: match[`team_${side}_flag`] || "",
        name: teamName(match, side),
        played: 0,
        wins: 0,
        draws: 0,
        losses: 0,
        goalsFor: 0,
        goalsAgainst: 0,
        cleanSheets: 0,
        failedToScore: 0,
      });
    }
    return teams.get(iso3);
  };

  finishedDatasetMatches().forEach((match) => {
    const teamA = ensure(match.team_a_iso3, match, "a");
    const teamB = ensure(match.team_b_iso3, match, "b");
    const goalsA = Number(match.result_team_a);
    const goalsB = Number(match.result_team_b);

    [
      [teamA, goalsA, goalsB],
      [teamB, goalsB, goalsA],
    ].forEach(([team, goalsFor, goalsAgainst]) => {
      team.played += 1;
      team.goalsFor += goalsFor;
      team.goalsAgainst += goalsAgainst;
      if (goalsAgainst === 0) team.cleanSheets += 1;
      if (goalsFor === 0) team.failedToScore += 1;
    });

    if (goalsA > goalsB) {
      teamA.wins += 1;
      teamB.losses += 1;
    } else if (goalsB > goalsA) {
      teamB.wins += 1;
      teamA.losses += 1;
    } else {
      teamA.draws += 1;
      teamB.draws += 1;
    }
  });

  return [...teams.values()].map((team) => ({
    ...team,
    goalDifference: team.goalsFor - team.goalsAgainst,
    goalsPerMatch: team.played ? team.goalsFor / team.played : null,
    goalsAgainstPerMatch: team.played ? team.goalsAgainst / team.played : null,
  }));
}

function tournamentStatsSummary() {
  const matches = finishedDatasetMatches();
  const totalGoals = matches.reduce((sum, match) => sum + Number(match.result_team_a) + Number(match.result_team_b), 0);
  const bothTeamsScored = matches.filter((match) => Number(match.result_team_a) > 0 && Number(match.result_team_b) > 0).length;
  return {
    finishedMatches: matches.length,
    totalGoals,
    goalsPerMatch: matches.length ? totalGoals / matches.length : null,
    bothTeamsScored,
    bothTeamsScoredShare: matches.length ? bothTeamsScored / matches.length : null,
  };
}

function weatherLoadBucketLabel(key) {
  return {
    low: t("statsLoadLow"),
    medium: t("statsLoadMedium"),
    high: t("statsLoadHigh"),
  }[key] || key;
}

function tournamentWeatherOverlay() {
  const matches = finishedDatasetMatches();
  const loadBuckets = {
    low: { matches: 0, goals: 0, avgGoals: null },
    medium: { matches: 0, goals: 0, avgGoals: null },
    high: { matches: 0, goals: 0, avgGoals: null },
  };
  const actualWeatherMatches = matches.filter((match) => match.actual_temp !== null && match.actual_temp !== undefined).length;
  const comparableEdges = matches.filter((match) => weatherLeaderSide(match));
  let edgeWins = 0;
  let edgeDraws = 0;
  let edgeLosses = 0;

  matches.forEach((match) => {
    const totalGoals = Number(match.result_team_a) + Number(match.result_team_b);
    const weatherLoad = Number(match.weather_load_score);
    if (Number.isFinite(weatherLoad)) {
      const bucket = weatherLoad >= 50 ? "high" : weatherLoad >= 25 ? "medium" : "low";
      loadBuckets[bucket].matches += 1;
      loadBuckets[bucket].goals += totalGoals;
    }

    const leader = weatherLeaderSide(match);
    const result = resultWinnerSide(match);
    if (!leader) return;
    if (result === "draw") edgeDraws += 1;
    else if (result === leader) edgeWins += 1;
    else edgeLosses += 1;
  });

  Object.values(loadBuckets).forEach((bucket) => {
    bucket.avgGoals = bucket.matches ? bucket.goals / bucket.matches : null;
  });

  return {
    actualWeatherMatches,
    loadBuckets,
    comparableEdges: comparableEdges.length,
    edgeWins,
    edgeDraws,
    edgeLosses,
    edgeWinRate: comparableEdges.length ? edgeWins / comparableEdges.length : null,
  };
}

function statLeaderboardCard(title, rows, metricLabel, valueKey, formatter = (value) => value) {
  return `<article class="analysis-card stats-card">
    <div class="analysis-card-head">
      <span>${metricLabel}</span>
      <b>${title}</b>
    </div>
    ${rows.length ? `<div class="stats-ranking">${rows.map((row, index) => `<div class="stats-ranking-row">
      <span>#${index + 1}</span>
      <b>${row.flag} ${escapeHtml(row.name)}</b>
      <small>${displayIso3(row.iso3)}</small>
      <strong>${formatter(row[valueKey], row)}</strong>
    </div>`).join("")}</div>` : `<div class="empty">${t("statsNoSignal")}</div>`}
  </article>`;
}

function weatherLoadBucketMarkup(bucketKey, bucket) {
  return `<div class="stats-load-row">
    <span>${weatherLoadBucketLabel(bucketKey)}</span>
    <b>${bucket.matches ? numberLabel(bucket.avgGoals, 2) : "–"}</b>
    <small>${bucket.matches} ${t("matches")}</small>
  </div>`;
}

function eventStatsPayload() {
  return source.event_stats && typeof source.event_stats === "object" ? source.event_stats : null;
}

function statsRatioLabel(value, total) {
  if (!Number.isFinite(Number(total)) || Number(total) <= 0) return "–";
  return `${Number(value || 0)}/${Number(total)}`;
}

function eventCoverageMetaMarkup(event) {
  const coverage = event?.coverage || {};
  const finishedMatches = Number(coverage.finished_matches || 0);
  return `<p class="stats-coverage-meta">${t("statsEventCoverageCompact")}: ${t("statsEventMatchesCoveredShort")} ${statsRatioLabel(coverage.matches_with_goal_events, finishedMatches)} · ${t("statsEventLineupsCoveredShort")} ${statsRatioLabel(coverage.matches_with_complete_lineups, finishedMatches)} · ${t("statsEventSubsCoveredShort")} ${statsRatioLabel(coverage.matches_with_substitutions, finishedMatches)} · ${t("statsEventHydrationCoveredShort")} ${statsRatioLabel(coverage.matches_with_hydration_markers, finishedMatches)}</p>`;
}

function eventBucketCardMarkup(rows) {
  return `<article class="analysis-card stats-card">
    <div class="analysis-card-head">
      <span>Timing</span>
      <b>${t("statsGoalMinutePatterns")}</b>
    </div>
    ${rows.length ? `<div class="stats-load-list">${rows.map((row) => `<div class="stats-load-row">
      <span>${escapeHtml(row.bucket)}</span>
      <small>${t("statsTotalGoals")}</small>
      <b>${row.goals}</b>
    </div>`).join("")}</div>` : `<div class="empty">${t("statsNoSignal")}</div>`}
  </article>`;
}

function eventTopListCardMarkup(label, title, rows, formatter) {
  const output = typeof formatter === "function" ? formatter : ((row) => `${row.count}`);
  return `<article class="analysis-card stats-card">
    <div class="analysis-card-head">
      <span>${label}</span>
      <b>${title}</b>
    </div>
    ${rows.length ? `<div class="stats-ranking">${rows.map((row, index) => `<div class="stats-ranking-row">
      <span>#${index + 1}</span>
      <b>${escapeHtml(displayStatKey(row.key, label))}</b>
      <small>${escapeHtml(row.bucket || "")}</small>
      <strong>${output(row)}</strong>
    </div>`).join("")}</div>` : `<div class="empty">${t("statsNoSignal")}</div>`}
  </article>`;
}

function selectedScorerProfile(event) {
  const profiles = Array.isArray(event.player_goal_timing_profiles) ? event.player_goal_timing_profiles : [];
  if (!profiles.length) return null;
  const preferred = profiles.find((row) => row.player_name === state.selectedScorer);
  if (preferred) return preferred;
  const messi = profiles.find((row) => row.player_name === "Lionel Messi");
  if (messi) {
    state.selectedScorer = messi.player_name;
    return messi;
  }
  state.selectedScorer = profiles[0].player_name;
  return profiles[0];
}

function scorerTimingGraphicMarkup(event) {
  const profiles = Array.isArray(event.player_goal_timing_profiles) ? event.player_goal_timing_profiles : [];
  const selected = selectedScorerProfile(event);
  if (!profiles.length || !selected) {
    return `<article class="analysis-card stats-card">
      <div class="analysis-card-head">
        <span>Players</span>
        <b>${t("statsPlayerGraphicTitle")}</b>
      </div>
      <p>${t("statsPlayerNoGoals")}</p>
    </article>`;
  }

  const maxGoals = Math.max(...profiles.flatMap((row) => row.buckets.map((bucket) => Number(bucket.goals || 0))), 1);
  const options = profiles.map((row) => `<option value="${escapeHtml(row.player_name)}"${row.player_name === selected.player_name ? " selected" : ""}>${escapeHtml(row.player_name)}${row.team_iso3 ? ` (${displayIso3(row.team_iso3)})` : ""}</option>`).join("");
  const bars = selected.buckets.map((bucket) => {
    const goals = Number(bucket.goals || 0);
    const width = maxGoals ? Math.max((goals / maxGoals) * 100, goals ? 10 : 0) : 0;
    return `<div class="scorer-timing-bar${goals ? " is-active" : ""}">
      <div class="scorer-timing-bar-top">
        <span>${escapeHtml(bucket.bucket)}</span>
        <b>${goals}</b>
      </div>
      <div class="scorer-timing-track" aria-hidden="true">
        <div class="scorer-timing-fill" style="width:${width}%"></div>
      </div>
    </div>`;
  }).join("");

  return `<article class="analysis-card stats-card scorer-timing-card">
    <div class="analysis-card-head">
      <span>Players</span>
      <b>${t("statsPlayerGraphicTitle")}</b>
    </div>
    <p>${t("statsPlayerGraphicIntro")}</p>
    <label class="scorer-timing-select-label" for="playerTimingSelect">${t("statsPlayerSelectLabel")}</label>
    <select id="playerTimingSelect" class="scorer-timing-select">${options}</select>
    <div class="scorer-timing-summary">
      <div><span>${escapeHtml(selected.player_name)}${selected.team_iso3 ? ` · ${displayIso3(selected.team_iso3)}` : ""}</span><b>${t("statsPlayerTotalGoals")}: ${selected.total_goals}</b></div>
      <div><span>${t("statsPlayerPrimeWindow")}</span><b>${escapeHtml(selected.top_bucket)} · ${selected.top_bucket_goals}</b></div>
    </div>
    <div class="scorer-timing-bars">${bars}</div>
  </article>`;
}

function topScorersCardMarkup(event) {
  const scorers = Array.isArray(event.top_scorers) ? event.top_scorers : [];
  if (!scorers.length) {
    return `<article class="analysis-card stats-card top-scorers-card">
      <div class="analysis-card-head">
        <span>Players</span>
        <b>${t("statsTopScorersTitle")}</b>
      </div>
      <p>${t("statsTopScorersEmpty")}</p>
    </article>`;
  }

  const leader = scorers[0];
  return `<article class="analysis-card stats-card top-scorers-card">
    <div class="analysis-card-head">
      <span>Players</span>
      <b>${t("statsTopScorersTitle")}</b>
    </div>
    <p>${t("statsTopScorersIntro")}</p>
    <div class="top-scorer-leader">
      <div>
        <span>#1</span>
        <b>${escapeHtml(leader.player_name)}</b>
        <small>${leader.team_iso3 ? displayIso3(leader.team_iso3) : "–"}</small>
      </div>
      <strong>${leader.total_goals}</strong>
    </div>
    <div class="top-scorers-scroll" role="region" aria-label="${escapeAttr(t("statsTopScorersTitle"))}">
      ${scorers.map((row, index) => `<div class="stats-ranking-row top-scorer-row">
        <span>#${index + 1}</span>
        <b>${escapeHtml(row.player_name)}</b>
        <small>${row.team_iso3 ? `${displayIso3(row.team_iso3)} · ${escapeHtml(row.top_bucket || "–")}` : escapeHtml(row.top_bucket || "")}</small>
        <strong>${row.total_goals}</strong>
      </div>`).join("")}
    </div>
  </article>`;
}

function renderEventStatsSection() {
  const event = eventStatsPayload();
  if (!event) return "";

  const goalRows = Number(event.goal_rows || 0);
  const hydrationRows = Array.isArray(event.hydration_break_post_window_goals) ? event.hydration_break_post_window_goals : [];
  const playerRows = Array.isArray(event.player_level_scoring_buckets) ? event.player_level_scoring_buckets : [];
  const coverageMeta = eventCoverageMetaMarkup(event);
  const gapNote = event?.data_gaps?.note || t("statsNeedsEventData");

  if (!goalRows) {
    return `<section class="report-section-card stats-section-card">
      <div class="report-section-head">
        <h3>${t("statsEventCoverageTitle")}</h3>
      </div>
      ${coverageMeta}
      <article class="analysis-card stats-card stats-gap-card">
        <div class="analysis-card-head">
          <span>Event Data</span>
          <b>${t("statsDataGapTitle")}</b>
        </div>
        <p>${t("statsNeedsEventData")}</p>
        <p>${escapeHtml(gapNote)}</p>
      </article>
    </section>`;
  }

  return `<section class="report-section-card stats-section-card">
    <div class="report-section-head">
      <h3>${t("statsEventFactsTitle")}</h3>
    </div>
    ${coverageMeta}
    <div class="stats-weather-grid">
      ${eventBucketCardMarkup(Array.isArray(event.goals_by_15min_bucket) ? event.goals_by_15min_bucket : [])}
      <article class="analysis-card stats-card">
        <div class="analysis-card-head">
          <span>Hydration</span>
          <b>${t("statsHydrationWindow")}</b>
        </div>
        ${hydrationRows.length ? `<div class="stats-ranking">${hydrationRows.map((row, index) => `<div class="stats-ranking-row">
          <span>#${index + 1}</span>
          <b>${escapeHtml(row.key || "–")}</b>
          <small>${t("statsTotalGoals")}</small>
          <strong>${row.count}</strong>
        </div>`).join("")}</div>` : `<p>${t("statsNoHydrationSignals")}</p>`}
      </article>
      ${topScorersCardMarkup(event)}
    </div>
    <div class="analysis-grid stats-analysis-grid">
      ${eventTopListCardMarkup("Teams", t("statsGoalWindows"), Array.isArray(event.teams_most_often_scored_in_bucket) ? event.teams_most_often_scored_in_bucket : [], (row) => `${row.count}`)}
      ${eventTopListCardMarkup("Teams", t("statsConcedingWindows"), Array.isArray(event.teams_most_often_conceded_in_bucket) ? event.teams_most_often_conceded_in_bucket : [], (row) => `${row.count}`)}
      ${eventTopListCardMarkup("Teams", t("statsEarlyStarters"), Array.isArray(event.early_starters) ? event.early_starters : [])}
      ${eventTopListCardMarkup("Teams", t("statsCrunchtimeScorers"), Array.isArray(event.crunchtime_scorers) ? event.crunchtime_scorers : [])}
      ${eventTopListCardMarkup("Teams", t("statsFirstHalfScorers"), Array.isArray(event.first_half_scoring_teams) ? event.first_half_scoring_teams : [])}
      ${eventTopListCardMarkup("Teams", t("statsSecondHalfScorers"), Array.isArray(event.second_half_scoring_teams) ? event.second_half_scoring_teams : [])}
      ${eventTopListCardMarkup("Teams", t("statsFirstHalfConceders"), Array.isArray(event.first_half_conceding_teams) ? event.first_half_conceding_teams : [])}
      ${eventTopListCardMarkup("Teams", t("statsSecondHalfConceders"), Array.isArray(event.second_half_conceding_teams) ? event.second_half_conceding_teams : [])}
      ${scorerTimingGraphicMarkup(event)}
      ${eventTopListCardMarkup("Players", t("statsPlayerWindows"), playerRows, (row) => `${row.count}`)}
    </div>
  </section>`;
}

function renderTournamentStats() {
  const summary = tournamentStatsSummary();
  const teams = tournamentTeamStats();
  if (!summary.finishedMatches || !teams.length) return `<div class="empty">${t("statsNoSignal")}</div>`;

  const topAttack = [...teams].sort((a, b) => b.goalsFor - a.goalsFor || a.goalsAgainst - b.goalsAgainst || a.name.localeCompare(b.name, currentLocale())).slice(0, 5);
  const topDefense = [...teams].sort((a, b) => b.goalsAgainst - a.goalsAgainst || b.goalsFor - a.goalsFor || a.name.localeCompare(b.name, currentLocale())).slice(0, 5);
  const topGoalDiff = [...teams].sort((a, b) => b.goalDifference - a.goalDifference || b.goalsFor - a.goalsFor || a.name.localeCompare(b.name, currentLocale())).slice(0, 5);
  const topCleanSheets = [...teams].sort((a, b) => b.cleanSheets - a.cleanSheets || a.goalsAgainst - b.goalsAgainst || a.name.localeCompare(b.name, currentLocale())).slice(0, 5);
  const topBlanked = [...teams].sort((a, b) => b.failedToScore - a.failedToScore || a.goalsFor - b.goalsFor || a.name.localeCompare(b.name, currentLocale())).slice(0, 5);
  const weather = tournamentWeatherOverlay();
  const eventSection = renderEventStatsSection();

  return `<div class="stats-summary">
    <section class="report-section-card stats-section-card">
      <div class="report-section-head">
        <h3>${t("statsTitle")}</h3>
      </div>
      <p class="copy">${t("statsIntro")}</p>
      <div class="report-kpis stats-kpis">
        <div class="metric"><span class="metric-value">${summary.finishedMatches}</span><span class="metric-label">${t("statsMatchesFinished")}</span></div>
        <div class="metric"><span class="metric-value">${summary.totalGoals}</span><span class="metric-label">${t("statsTotalGoals")}</span></div>
        <div class="metric"><span class="metric-value">${numberLabel(summary.goalsPerMatch, 2)}</span><span class="metric-label">${t("statsGoalsPerMatch")}</span></div>
        <div class="metric"><span class="metric-value">${numberLabel((summary.bothTeamsScoredShare || 0) * 100, 0)}%</span><span class="metric-label">${t("statsBtts")}</span></div>
      </div>
    </section>

    <div class="analysis-grid stats-analysis-grid">
      ${statLeaderboardCard(t("statsTopAttack"), topAttack, t("statsGoalsFor"), "goalsFor")}
      ${statLeaderboardCard(t("statsTopDefense"), topDefense, t("statsGoalsAgainst"), "goalsAgainst")}
      ${statLeaderboardCard(t("statsGoalDiff"), topGoalDiff, t("statsGoalDifference"), "goalDifference", (value) => value > 0 ? `+${value}` : String(value))}
      ${statLeaderboardCard(t("statsCleanSheets"), topCleanSheets, t("statsCleanSheetShort"), "cleanSheets")}
      ${statLeaderboardCard(t("statsBlanked"), topBlanked, t("statsBlankShort"), "failedToScore")}
    </div>

    <section class="report-section-card stats-section-card">
      <div class="report-section-head">
        <h3>${t("statsWeatherOverlay")}</h3>
      </div>
      <p class="copy">${t("statsWeatherOverlayIntro")}</p>
      <div class="stats-weather-grid">
        <article class="analysis-card stats-card">
          <div class="analysis-card-head">
            <span>${state.lang === "de" ? "Belastung" : "Load band"}</span>
            <b>${t("statsLoadBuckets")}</b>
          </div>
          <div class="stats-load-list">
            ${Object.entries(weather.loadBuckets).map(([key, bucket]) => weatherLoadBucketMarkup(key, bucket)).join("")}
          </div>
          <p>${t("statsActualWeatherPending")}</p>
        </article>
        <article class="analysis-card stats-card">
          <div class="analysis-card-head">
            <span>${state.lang === "de" ? "Wettersignal" : "Weather signal"}</span>
            <b>${t("statsEdgePerformance")}</b>
          </div>
          <div class="analysis-kpis">
            <div><span>${t("clearWeatherEdges")}</span><b>${weather.comparableEdges}</b></div>
            <div><span>${t("statsEdgeWins")}</span><b>${weather.edgeWins}</b></div>
            <div><span>${t("statsEdgeDraws")}</span><b>${weather.edgeDraws}</b></div>
            <div><span>${t("statsEdgeLosses")}</span><b>${weather.edgeLosses}</b></div>
          </div>
          <p>${t("statsEdgeWinRate")}: <b>${weather.edgeWinRate === null ? "–" : `${numberLabel(weather.edgeWinRate * 100, 0)}%`}</b> · ${state.lang === "de" ? "mit Ist-Wetter-Abgleich" : "with actual-weather verification"}: <b>${weather.actualWeatherMatches}</b>.</p>
        </article>
      </div>
    </section>
    ${eventSection}
    <p class="stats-dedication">${t("statsDedication")}</p>
  </div>`;
}

function edgeLabel(match) {
  if (!hasWeatherFit(match)) return t("forecastPending");
  const a = Number(match.team_a_weather_fit_score);
  const b = Number(match.team_b_weather_fit_score);
  if (Math.abs(a - b) < 4) return t("balanced");
  const leader = a > b ? match.team_a_iso3 : match.team_b_iso3;
  return state.lang === "en" ? `${leader} advantage` : `${leader} im Vorteil`;
}

function weatherAdvantage(match) {
  if (!hasForecast(match) || !hasWeatherFit(match)) return null;
  const a = Number(match.team_a_weather_fit_score);
  const b = Number(match.team_b_weather_fit_score);
  const gap = Math.abs(a - b);
  if (gap < 4) return null;
  const leaderSide = a > b ? "a" : "b";
  const opponentSide = leaderSide === "a" ? "b" : "a";
  return {
    match,
    gap,
    leaderSide,
    opponentSide,
    fit: Number(match[`team_${leaderSide}_weather_fit_score`]),
    probability: Number(match[`probability_team_${leaderSide}_win`]),
  };
}

function advantageTier(gap) {
  if (Number(gap) >= 20) return t("advantageClear");
  if (Number(gap) >= 10) return t("advantageStrong");
  return t("advantageNoticeable");
}

function displayText(value) {
  if (!value) return value;
  return normalizeGermanText(String(value)
    .replace(/Forecast-Edge/g, "Wettervorteil")
    .replace(/\b([A-Z]{3}) Edge\b/g, "$1 im Vorteil")
    .replace(/\bMatchday\b/g, "Spieltag")
    .replace(/Wetter, Reise, Zeitzonen und Standortfaktoren/g, "Wetter, Zeitzonen und Standortfaktoren")
    .replace(/Wetter, Reise, Zeitzonen, Hoehe und Standortnaehe/g, "Wetter, Zeitzonen, Höhe und Standortnähe")
    .replace(/None Grad/g, "noch offene Temperatur")
    .replace(/None% Luftfeuchtigkeit/g, "noch offene Luftfeuchtigkeit")
    .replace(/Reise-,\s*/g, "")
    .replace(/Reise- und Erholungswerte/g, "Kontextwerte")
    .replace(/travel_recovery_gap/g, "Kontextdaten ohne Basislager-Nachweis"));
}

function analysisAdvantageLabel(value) {
  if (!value) return "–";
  if (state.lang === "de") return displayText(value);
  return String(value).replace(/\b([A-Z]{3}) Edge\b/g, "$1 advantage").replace(/Forecast-Edge/g, "Weather advantage");
}

function googleMapsUrl(item) {
  const directUrl = safeHttpUrl(item?.maps_url);
  if (directUrl) return directUrl;
  const hasCoordinates = item?.latitude !== null && item?.longitude !== null && item?.latitude !== undefined && item?.longitude !== undefined;
  const query = hasCoordinates
    ? `${Number(item.latitude).toFixed(5)},${Number(item.longitude).toFixed(5)}`
    : `${item?.stadium_name || ""} ${item?.host_city || ""}`.trim();
  if (!query) return "";
  const url = new URL("https://www.google.com/maps/search/");
  url.searchParams.set("api", "1");
  url.searchParams.set("query", query);
  if (item?.google_place_id) {
    url.searchParams.set("query_place_id", item.google_place_id);
  }
  return url.toString();
}

function coordinateAccuracyLabel(item) {
  const precision = item?.coordinate_precision === "venue_coordinate" ? t("venueCoordinate") : t("coordinate");
  if (item?.coordinate_accuracy_m !== null && item?.coordinate_accuracy_m !== undefined && item?.coordinate_accuracy_m !== "") {
    return `${precision}, ${t("approxAccuracy")} ${Math.round(Number(item.coordinate_accuracy_m))} ${t("accuracyMeters")}`;
  }
  return `${precision}, ${t("documentedSource")}`;
}

function yesNo(value) {
  return value === true || value === "true" ? t("yes") : t("no");
}

function capacityLabel(value) {
  if (value === null || value === undefined || value === "") return t("dataFollows");
  return `${compactNumber(value)} ${t("seats")}`;
}

function stadiumTypeLabel(value) {
  const labels = {
    indoor: t("indoor"),
    outdoor: t("outdoor"),
    retractable_roof: t("retractableRoof"),
    unknown: t("dataFollows"),
  };
  return labels[value] || normalizeGermanText(value || t("dataFollows"));
}

function roofTypeLabel(value) {
  const labels = {
    open_air: t("openAir"),
    retractable_roof: t("retractableRoof"),
    fixed_translucent_canopy: t("fixedRoof"),
    canopy_over_stands: t("canopy"),
    partial_canopy: t("partialCanopy"),
    unknown: t("dataFollows"),
  };
  return labels[value] || normalizeGermanText(value || t("dataFollows"));
}

function weatherProtectionLabel(value) {
  const level = Number(value);
  if (level >= 3) return t("protectionHigh");
  if (level === 2) return t("protectionMedium");
  if (level === 1) return t("protectionPartial");
  return t("protectionOpen");
}

function venueNote(match) {
  if (state.lang === "de") return displayText(match.venue_weather_note_de);
  const type = stadiumTypeLabel(match.stadium_type_basic).toLowerCase();
  const roof = roofTypeLabel(match.roof_type).toLowerCase();
  const protection = weatherProtectionLabel(match.weather_protection_level);
  return `${match.stadium_name || t("venue")} is an ${type} venue with ${roof} roof context and ${protection} weather protection.`;
}

function venueInfoMarkup(match, compact = false) {
  if (!match) return "";
  const mapsUrl = googleMapsUrl(match);
  const contextItems = [
    [t("capacity"), capacityLabel(match.stadium_capacity)],
    [t("stadiumType"), stadiumTypeLabel(match.stadium_type_basic)],
    [t("roof"), roofTypeLabel(match.roof_type)],
    [t("climateControl"), yesNo(match.climate_control_available)],
    [t("weatherProtection"), weatherProtectionLabel(match.weather_protection_level)],
    [t("elevation"), valueOrDash(match.elevation_m, " m")],
  ];
  const cards = contextItems
    .map(([label, value]) => `<div class="venue-fact"><span>${label}</span><b>${value}</b></div>`)
    .join("");
  const noteItems = state.lang === "de"
    ? [match.venue_weather_note_de, match.climate_control_note_de, match.pitch_surface_note_de].filter(Boolean).map(displayText)
    : [venueNote(match)];
  const notes = noteItems.map((note) => `<li>${escapeHtml(note)}</li>`).join("");
  return `<section class="venue-panel${compact ? " is-compact" : ""}" aria-label="Stadioninformationen">
    <div class="venue-panel-head">
      <div>
        <p class="eyebrow">${t("venuePanel")}</p>
        <h3>${escapeHtml(match.stadium_name || t("venue"))}</h3>
        <p>${escapeHtml(match.host_city || "")}${match.host_country ? ` · ${escapeHtml(match.host_country)}` : ""}</p>
      </div>
      ${mapsUrl ? `<a class="secondary-action" href="${escapeAttr(mapsUrl)}" target="_blank" rel="noopener noreferrer">${t("googleMaps")}</a>` : ""}
    </div>
    <div class="venue-facts">${cards}</div>
    ${notes ? `<ul class="venue-notes">${notes}</ul>` : ""}
    ${match.capacity_source_note ? `<p class="venue-source">${escapeHtml(match.capacity_source_note)}</p>` : ""}
  </section>`;
}

function syncMatchControls() {
  if (els.search) els.search.value = state.query;
  if (els.matchdayFilter) els.matchdayFilter.value = state.matchday;
  if (els.groupFilter) els.groupFilter.value = state.group;
  els.modeButtons.forEach((button) => button.classList.toggle("is-active", button.dataset.mode === state.mode));
}

function scrollSelectedMatchIntoView(matchId) {
  const selectedCard = [...els.list.querySelectorAll(".quick-match-card")].find((item) => item.dataset.matchId === matchId);
  const inlineDetail = els.list.querySelector(`.inline-match-detail[data-match-id="${matchId}"]`);
  if (selectedCard) {
    selectedCard.scrollIntoView({ block: "start", behavior: "smooth" });
    if (selectedCard) selectedCard.focus({ preventScroll: true });
    return;
  }
  if (inlineDetail) {
    inlineDetail.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
}

function openMatchInMatchday(matchId) {
  const match = findMatch(matchId);
  if (!match) return;
  state.scheduleView = "smart";
  state.mode = "all";
  state.query = "";
  state.matchday = match.matchday ? String(match.matchday) : "all";
  state.group = "all";
  state.selectedId = match.match_id;
  syncMatchControls();
  renderList();
  setActiveSection("matches");
  window.requestAnimationFrame(() => scrollSelectedMatchIntoView(match.match_id));
}

function findMatch(matchId) {
  return source.matches.find((match) => match.match_id === matchId);
}

function searchable(match) {
  return [
    match.match_id,
    match.group_name,
    match.host_city,
    match.stadium_name,
    match.team_a_iso3,
    match.team_b_iso3,
    match.team_a_name_de,
    match.team_b_name_de,
    match.team_a_name_en,
    match.team_b_name_en,
    normalizeGermanText(match.team_a_name_de),
    normalizeGermanText(match.team_b_name_de),
    match.matchday_label,
    match.calendar_day_label,
  ].join(" ").toLowerCase();
}

function filteredMatches() {
  return source.matches.filter((match) => {
    if (state.mode === "edge" && (!hasWeatherFit(match) || Number(match.weather_fit_edge_gap || 0) < 4)) return false;
    if (state.matchday !== "all" && String(match.matchday) !== state.matchday) return false;
    if (state.group !== "all" && String(match.group_name) !== state.group) return false;
    if (state.query && !searchable(match).includes(state.query)) return false;
    return true;
  });
}

function isScheduleFiltered() {
  return state.mode !== "all" || state.matchday !== "all" || state.group !== "all" || Boolean(state.query);
}

function relevantScheduleMatch(kind = state.scheduleView) {
  const live = sortedByExperiencePriority(source.matches.filter((match) => matchExperienceStatus(match) === "live"));
  const today = todaysMatches();
  const upcoming = futureMatches().filter((match) => matchExperienceStatus(match) === "upcoming");
  const recent = finishedMatches();
  if (kind === "live") return live[0] || null;
  if (kind === "today") return today[0] || live[0] || null;
  if (kind === "next") return upcoming[0] || today[0] || live[0] || null;
  if (kind === "recent") return recent[0] || null;
  if (kind === "start") {
    return [...source.matches].sort((a, b) => matchTimestamp(a) - matchTimestamp(b))[0] || null;
  }
  return live[0] || today[0] || upcoming[0] || recent[0] || null;
}

function scheduleFocusStatusKey() {
  if (isScheduleFiltered()) return "scheduleFocusFiltered";
  if (state.scheduleView === "full") return "scheduleFocusStart";
  const match = relevantScheduleMatch("smart");
  if (!match) return "scheduleFocusStart";
  const status = matchExperienceStatus(match);
  if (status === "live") return "scheduleFocusLive";
  if (status === "today") return "scheduleFocusToday";
  if (status === "upcoming") return "scheduleFocusNext";
  return "scheduleFocusRecent";
}

function scheduleAnchorDateKey() {
  if (state.selectedId) {
    const selected = findMatch(state.selectedId);
    if (selected) return matchDateKey(selected);
  }
  if (state.scheduleView === "full") return null;
  const match = relevantScheduleMatch("smart");
  return match ? matchDateKey(match) : null;
}

function historicalMatchCount(groups, focusIndex) {
  if (focusIndex <= 0) return 0;
  return groups.slice(0, focusIndex).reduce((sum, group) => sum + group.matches.length, 0);
}

function renderScheduleJumpbar() {
  if (!els.scheduleJumpbar) return;
  const live = relevantScheduleMatch("live");
  const today = relevantScheduleMatch("today");
  const next = relevantScheduleMatch("next");
  const recent = relevantScheduleMatch("recent");
  const jumpButtons = [
    { key: "smart", label: t("jumpCurrent"), match: relevantScheduleMatch("smart"), view: "smart", emphasis: true },
    { key: "live", label: t("jumpLive"), match: live },
    { key: "today", label: t("jumpToday"), match: today },
    { key: "next", label: t("jumpNext"), match: next },
    { key: "recent", label: t("jumpRecent"), match: recent },
    { key: "start", label: t("jumpStart"), view: "full", match: relevantScheduleMatch("start") },
  ].filter((item, index, items) => item.match || item.view === "full" || index === 0)
    .filter((item, index, items) => items.findIndex((candidate) => candidate.key !== "smart" && candidate.match?.match_id === item.match?.match_id) === index || item.key === "smart" || item.key === "start");

  els.scheduleJumpbar.innerHTML = `<div class="schedule-view-toggle" role="group" aria-label="${t("navSchedule")}">
      <button class="schedule-view-button${state.scheduleView === "smart" ? " is-active" : ""}" type="button" data-schedule-view="smart">${t("scheduleSmart")}</button>
      <button class="schedule-view-button${state.scheduleView === "full" ? " is-active" : ""}" type="button" data-schedule-view="full">${t("scheduleFull")}</button>
    </div>
    <div class="schedule-jump-actions">
      ${jumpButtons.map((item) => {
        const meta = item.match ? `${item.match.match_id} · ${viewerDateTime(item.match).shortDate}` : "";
        return `<button class="schedule-jump-button${item.emphasis ? " is-emphasis" : ""}" type="button" data-schedule-jump="${item.key}"${item.match ? ` data-match-id="${item.match.match_id}"` : ""}${item.view ? ` data-target-view="${item.view}"` : ""}>
          <span>${item.label}</span>
          ${meta ? `<b>${meta}</b>` : ""}
        </button>`;
      }).join("")}
    </div>`;
}

function renderScheduleToolbarStatus() {
  if (!els.scheduleToolbarStatus) return;
  const note = isScheduleFiltered() ? t("scheduleFocusFiltered") : t(scheduleFocusStatusKey());
  const collapsed = !isScheduleFiltered() && state.scheduleView === "smart" ? `<span>${t("scheduleHistoryCollapsed")}</span>` : "";
  els.scheduleToolbarStatus.innerHTML = `<div class="schedule-status-note"><b>${note}</b>${collapsed}</div>`;
}

function scrollScheduleAnchorIntoView(behavior = "smooth") {
  const selectedId = state.selectedId;
  if (selectedId) {
    scrollSelectedMatchIntoView(selectedId);
    return;
  }
  const anchorKey = scheduleAnchorDateKey();
  if (!anchorKey || !els.list) return;
  const group = els.list.querySelector(`[data-date-group="${anchorKey}"]`);
  if (group) {
    group.scrollIntoView({ block: "start", behavior });
  }
}

function renderMetrics() {
  const matches = source.matches;
  const forecasts = matches.filter(hasForecast);
  const edges = matches.filter((match) => hasWeatherFit(match) && Number(match.weather_fit_edge_gap || 0) >= 4);
  const hooks = matches.filter((match) => match.preview_social_hook_de || match.weather_social_hook_de);
  els.metricMatches.textContent = matches.length;
  els.metricForecasts.textContent = forecasts.length;
  els.metricEdges.textContent = edges.length;
  els.metricTexts.textContent = hooks.length;
  els.status.textContent = source.metadata.exported_at
    ? `${t("exportedAt")} ${source.metadata.exported_at.replace("T", " ")}`
    : t("localExport");
}

function renderCoverage() {
  const grouped = new Map();
  for (const match of source.matches) {
    const key = String(match.calendar_day || match.matchday || "–");
    const item = grouped.get(key) || { total: 0, forecast: 0 };
    item.total += 1;
    if (hasForecast(match)) item.forecast += 1;
    grouped.set(key, item);
  }
  els.coverageBars.innerHTML = [...grouped.entries()]
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([key, item]) => {
      const height = item.total ? Math.max(8, Math.round((item.forecast / item.total) * 100)) : 0;
      const covered = height >= 55 ? " is-covered" : "";
      return `<div class="coverage-bar${covered}" title="${t("tournamentDay")} ${key}: ${item.forecast}/${item.total}">
        <b>${key}</b><span style="height:${height}%"></span>
      </div>`;
    })
    .join("");
}

function renderFilters() {
  const matchdays = [...new Set(source.matches.map((match) => match.matchday).filter(Boolean))].sort((a, b) => Number(a) - Number(b));
  const groups = [...new Set(source.matches.map((match) => match.group_name).filter(Boolean))].sort();
  els.matchdayFilter.innerHTML = `<option value="all">${t("allGroupMatchdays")}</option>${matchdays.map((day) => `<option value="${day}">${groupMatchdayLabel(day)}</option>`).join("")}`;
  els.groupFilter.innerHTML = `<option value="all">${t("allGroups")}</option>${groups.map((group) => `<option value="${group}">${t("group")} ${group}</option>`).join("")}`;
  if (els.mapMatchdayFilter) {
    els.mapMatchdayFilter.innerHTML = `<option value="all">${t("allGroupMatchdays")}</option>${matchdays.map((day) => `<option value="${day}">${groupMatchdayLabel(day)}</option>`).join("")}`;
  }
  if (els.favoritesMatchdayFilter) {
    els.favoritesMatchdayFilter.innerHTML = `<option value="all">${t("allGroupMatchdays")}</option>${matchdays.map((day) => `<option value="${day}">${groupMatchdayLabel(day)}</option>`).join("")}`;
  }
  syncMatchControls();
  if (els.mapMatchdayFilter) els.mapMatchdayFilter.value = state.mapMatchday;
  if (els.favoritesMatchdayFilter) els.favoritesMatchdayFilter.value = state.favoritesMatchday;
}

function teamRow(match, side) {
  const fit = match[`team_${side}_weather_fit_score`];
  const width = fit === null || fit === undefined ? 0 : Math.max(0, Math.min(100, Number(fit)));
  return `<div class="team-row">
    <div class="team-name">${teamLabel(match, side)} <small>${displayIso3(match[`team_${side}_iso3`])}</small></div>
    <div class="fit-score">${score(fit)}</div>
    <div class="fit-track"><span class="fit-fill" style="width:${width}%"></span></div>
  </div>`;
}

function finalResultMarkup(match, compact = false) {
  if (!isFinished(match)) return "";
  const weatherHit = weatherFavouriteWon(match)
    ? `<span class="weather-result-hit"><span aria-hidden="true">✓</span> ${t("weatherFavouriteWon")}</span>`
    : "";
  const context = !compact && weatherHit ? `<small>${t("weatherResultContext")}</small>` : "";
  return `<div class="final-result${compact ? " is-compact" : ""}">
    <span>${t("finalScore")}</span>
    <b>${match.result_team_a}:${match.result_team_b}</b>
    ${weatherHit}
    ${context}
  </div>`;
}

function card(match) {
  const selected = match.match_id === state.selectedId;
  const detail = selected
    ? `<section class="inline-match-detail" data-match-id="${match.match_id}" aria-label="Match Detail">${matchDetailMarkup(match)}</section>`
    : "";
  return `${quickMatchCard(match, { selected })}${detail}`;
}

function renderList() {
  const matches = filteredMatches();
  renderScheduleJumpbar();
  renderScheduleToolbarStatus();
  if (!matches.length) {
    renderMatchdaySummary(matches);
    els.list.innerHTML = `<div class="active-empty">${t("noMatches")}</div>`;
    if (els.detail) els.detail.innerHTML = "";
    return;
  }
  if (state.selectedId && !matches.some((match) => match.match_id === state.selectedId)) {
    state.selectedId = null;
  }
  renderMatchdaySummary(matches);
  els.list.innerHTML = renderMatchGroups(matches);
  renderDetail(matches.find((match) => match.match_id === state.selectedId));
}

function renderMatchdaySummary(matches) {
  if (!els.matchdaySummary) return;
  const forecastCount = matches.filter(hasForecast).length;
  const edgeCount = matches.filter((match) => hasWeatherFit(match) && Number(match.weather_fit_edge_gap || 0) >= 4).length;
  const groupCount = new Set(matches.map((match) => match.group_name).filter(Boolean)).size;
  const label = groupMatchdayLabel(state.matchday);
  els.matchdaySummary.innerHTML = `<div>
      <p class="eyebrow">${label}</p>
      <h2>${matches.length} ${t("matches")} · ${dateRangeLabel(matches)}</h2>
    </div>
    <div class="summary-kpis">
      <div><span>${t("groups")}</span><b>${groupCount || "–"}</b></div>
      <div><span>Forecast</span><b>${forecastCount}/${matches.length}</b></div>
      <div><span>${t("metricEdges")}</span><b>${edgeCount}</b></div>
    </div>`;
}

function weatherFavorites() {
  return source.matches
    .filter((match) => !isFinished(match))
    .filter((match) => state.favoritesMatchday === "all" || String(match.matchday) === state.favoritesMatchday)
    .map(weatherAdvantage)
    .filter(Boolean)
    .sort((a, b) => b.gap - a.gap || b.probability - a.probability);
}

function weatherFavoriteCard(item, index) {
  const { match, leaderSide, opponentSide, gap, fit, probability } = item;
  const viewer = viewerDateTime(match);
  return `<article class="weather-favorite-card${index < 3 ? " is-top-three" : ""}">
    <div class="favorite-card-head">
      <span class="favorite-rank">#${index + 1}</span>
      <span class="favorite-tier">${advantageTier(gap)}</span>
    </div>
    <div>
      <p class="eyebrow">${match.match_id} · ${groupMatchdayLabel(match.matchday)} · ${match.host_city}</p>
      <h3>${teamLabel(match, leaderSide)}</h3>
      <p class="favorite-opponent"><span>${t("opponent")}</span> ${teamLabel(match, opponentSide)}</p>
    </div>
    <div class="favorite-kpis">
      <div><span>${t("weatherFit")}</span><b>${score(fit)}/100</b></div>
      <div><span>${t("advantagePoints")}</span><b>+${gap.toFixed(1)}</b></div>
      <div><span>${t("winChance")}</span><b>${percent(probability)}</b></div>
    </div>
    <p class="favorite-conditions">${viewer.detailLabel} · ${valueOrDash(match.forecast_temp, "°C")} · ${valueOrDash(match.forecast_humidity, "%")} ${t("humidityShort")} · ${valueOrDash(match.forecast_wind_speed, " km/h")}</p>
    <p class="favorite-disclaimer">${t("advantageNoticeShort")}</p>
    <button class="primary-action favorite-jump" type="button" data-favorite-jump="${match.match_id}">${t("viewMatch")}</button>
  </article>`;
}

function renderWeatherFavorites() {
  if (!els.favoritesList || !els.favoritesSummary) return;
  const favorites = weatherFavorites();
  const forecastMatches = source.matches.filter((match) => {
    if (state.favoritesMatchday !== "all" && String(match.matchday) !== state.favoritesMatchday) return false;
    return hasForecast(match);
  });
  if (!favorites.length) {
    els.favoritesSummary.innerHTML = `<p>${t("advantageNotice")}</p>`;
    els.favoritesList.innerHTML = `<div class="empty">${t("favoritesEmpty")}</div>`;
    return;
  }
  const strongest = favorites[0];
  els.favoritesSummary.innerHTML = `<div>
      <p class="eyebrow">${groupMatchdayLabel(state.favoritesMatchday)}</p>
      <h3>${t("advantageNotice")}</h3>
    </div>
    <div class="favorites-summary-kpis">
      <div><span>${t("favoritesCount")}</span><b>${favorites.length}</b></div>
      <div><span>${t("favoritesStrongest")}</span><b>+${strongest.gap.toFixed(1)}</b></div>
      <div><span>${t("favoritesForecastBasis")}</span><b>${forecastMatches.length}</b></div>
    </div>`;
  els.favoritesList.innerHTML = favorites.map(weatherFavoriteCard).join("");
}

function renderMatchGroups(matches) {
  const grouped = new Map();
  for (const match of matches) {
    const dateTime = viewerDateTime(match);
    if (!grouped.has(dateTime.key)) {
      grouped.set(dateTime.key, { dateTime, matches: [] });
    }
    grouped.get(dateTime.key).matches.push(match);
  }
  const groups = [...grouped.values()].sort((a, b) => a.dateTime.key.localeCompare(b.dateTime.key));
  const anchorKey = scheduleAnchorDateKey();
  const focusIndex = anchorKey ? Math.max(0, groups.findIndex((group) => group.dateTime.key === anchorKey)) : 0;
  const focusSafeIndex = focusIndex === -1 ? 0 : focusIndex;
  const useSmartView = state.scheduleView === "smart" && !isScheduleFiltered() && groups.length > 1;
  const historyCount = useSmartView ? historicalMatchCount(groups, focusSafeIndex) : 0;

  const renderGroup = (group, options = {}) => `<section class="match-date-group${options.isFocus ? " is-focus" : ""}" data-date-group="${group.dateTime.key}">
      <div class="date-group-head">
        <span>${group.dateTime.weekday}</span>
        <b>${group.dateTime.date}</b>
        ${options.isFocus ? `<small>${statusLabel(matchExperienceStatus(group.matches[0]))}</small>` : ""}
      </div>
      <div class="date-group-list">${group.matches.map(card).join("")}</div>
    </section>`;

  if (!useSmartView || focusSafeIndex <= 0) {
    return groups.map((group, index) => renderGroup(group, { isFocus: index === focusSafeIndex && state.scheduleView === "smart" })).join("");
  }

  const history = groups.slice(0, focusSafeIndex);
  const currentAndFuture = groups.slice(focusSafeIndex);
  return `<details class="schedule-history-shell">
      <summary>
        <span>${t("scheduleHistorySummary")}</span>
        <b>${historyCount} ${t("scheduleHistoryCount")}</b>
      </summary>
      <div class="schedule-history-groups">${history.map((group) => renderGroup(group)).join("")}</div>
    </details>
    ${currentAndFuture.map((group, index) => renderGroup(group, { isFocus: index === 0 })).join("")}`;
}

function weatherNarrative(match) {
  if (state.lang === "de") {
    return displayText(match.weather_body_de) || t("forecastOutside");
  }
  if (!hasForecast(match)) return t("forecastOutside");
  if (!hasWeatherFit(match) || Math.abs(Number(match.weather_fit_edge_gap || 0)) < 4) {
    return t("weatherBalancedText");
  }
  const a = Number(match.team_a_weather_fit_score);
  const b = Number(match.team_b_weather_fit_score);
  const leaderSide = a > b ? "a" : "b";
  const trailingSide = a > b ? "b" : "a";
  const leaderScore = score(match[`team_${leaderSide}_weather_fit_score`]);
  const trailingScore = score(match[`team_${trailingSide}_weather_fit_score`]);
  return `${teamName(match, leaderSide)} appears better suited to this weather setup than ${teamName(match, trailingSide)}: Weather Fit ${leaderScore}/100 vs. ${trailingScore}/100 at ${valueOrDash(match.forecast_temp, "°C")} and ${valueOrDash(match.forecast_humidity, "%")} relative humidity. ${t("weatherContextSuffix")}`;
}

function socialNarrative(match) {
  if (state.lang === "de") {
    return displayText(match.weather_social_hook_de) || t("socialFallback");
  }
  if (!hasForecast(match)) return t("socialFallback");
  const edge = edgeLabel(match);
  return `${displayIso3(match.team_a_iso3)} vs. ${displayIso3(match.team_b_iso3)}: ${valueOrDash(match.forecast_temp, "°C")}, ${valueOrDash(match.forecast_humidity, "%")} RH, Weather Fit ${edge}. Not a betting model.`;
}

function matchDetailMarkup(match) {
  return match ? expandedMatchDetailsMarkup(match) : "";
}

function renderDetail(match) {
  if (!match || !els.detail) return;
  els.detail.innerHTML = matchDetailMarkup(match);
}

function avg(values) {
  const clean = values.filter((value) => value !== null && value !== undefined && !Number.isNaN(Number(value))).map(Number);
  if (!clean.length) return null;
  return Math.round((clean.reduce((sum, value) => sum + value, 0) / clean.length) * 10) / 10;
}

function loadClass(load) {
  if (load === null || load === undefined) return "pending";
  if (Number(load) >= 50) return "high";
  if (Number(load) >= 32) return "medium";
  return "low";
}

function mapMatches() {
  return source.matches.filter((match) => state.mapMatchday === "all" || String(match.matchday) === state.mapMatchday);
}

function venueKey(match) {
  return `${match.stadium_name}__${match.host_city}`;
}

function projectVenue(lat, lon) {
  const projected = projectGeoPoint(Number(lon), Number(lat));
  const mapX = Math.max(40, Math.min(MAP_VIEWBOX.width - 40, projected.x));
  const mapY = Math.max(34, Math.min(MAP_VIEWBOX.height - 46, projected.y));
  return {
    mapX,
    mapY,
    x: (mapX / MAP_VIEWBOX.width) * 100,
    y: (mapY / MAP_VIEWBOX.height) * 100,
  };
}

function resolveVenuePinPositions(venues) {
  const minimumDistance = isMobileViewport() ? 92 : 48;
  const diagonal = Math.round(minimumDistance * 0.72);
  const outer = Math.round(minimumDistance * 1.65);
  const offsets = [
    [0, 0],
    [0, -minimumDistance], [minimumDistance, 0], [-minimumDistance, 0], [0, minimumDistance],
    [diagonal, -diagonal], [-diagonal, -diagonal], [diagonal, diagonal], [-diagonal, diagonal],
    [0, -outer], [outer, 0], [-outer, 0], [0, outer],
    [outer, -minimumDistance], [-outer, -minimumDistance], [outer, minimumDistance], [-outer, minimumDistance],
    [minimumDistance, -outer], [-minimumDistance, -outer], [minimumDistance, outer], [-minimumDistance, outer],
  ];
  const ordered = [...venues].sort((a, b) => {
    const matchDifference = Number(b.matches.length) - Number(a.matches.length);
    return matchDifference || a.host_city.localeCompare(b.host_city, currentLocale());
  });
  const placed = [];
  const resolved = new Map();

  for (const venue of ordered) {
    let candidate = null;
    for (const [offsetX, offsetY] of offsets) {
      const mapX = Math.max(34, Math.min(MAP_VIEWBOX.width - 34, venue.position.mapX + offsetX));
      const mapY = Math.max(34, Math.min(MAP_VIEWBOX.height - 54, venue.position.mapY + offsetY));
      const hasCollision = placed.some((item) => Math.hypot(item.mapX - mapX, item.mapY - mapY) < minimumDistance);
      if (!hasCollision) {
        candidate = { mapX, mapY };
        break;
      }
    }
    const display = candidate || { mapX: venue.position.mapX, mapY: venue.position.mapY };
    placed.push(display);
    resolved.set(venue.key, {
      ...venue,
      displayPosition: {
        ...display,
        x: (display.mapX / MAP_VIEWBOX.width) * 100,
        y: (display.mapY / MAP_VIEWBOX.height) * 100,
      },
      pinShifted: Math.hypot(display.mapX - venue.position.mapX, display.mapY - venue.position.mapY) > 5,
    });
  }
  return venues.map((venue) => resolved.get(venue.key));
}

function projectGeoPoint(lon, lat) {
  return {
    x: ((lon - MAP_BOUNDS.minLon) / (MAP_BOUNDS.maxLon - MAP_BOUNDS.minLon)) * MAP_VIEWBOX.width,
    y: (1 - (lat - MAP_BOUNDS.minLat) / (MAP_BOUNDS.maxLat - MAP_BOUNDS.minLat)) * MAP_VIEWBOX.height,
  };
}

function ringPath(ring) {
  return ring
    .map(([lon, lat], index) => {
      const point = projectGeoPoint(Number(lon), Number(lat));
      return `${index === 0 ? "M" : "L"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`;
    })
    .join(" ");
}

function featurePath(feature) {
  const geometry = feature.geometry || {};
  if (geometry.type === "Polygon") {
    return geometry.coordinates.map((ring) => `${ringPath(ring)} Z`).join(" ");
  }
  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates
      .flatMap((polygon) => polygon.map((ring) => `${ringPath(ring)} Z`))
      .join(" ");
  }
  return "";
}

function renderBaseMap() {
  const paths = hostMap.features
    .map((feature) => {
      const name = feature.properties?.name_de || feature.properties?.name || "Land";
      const key = (feature.properties?.name || name).toLowerCase().replace(/[^a-z]+/g, "-");
      return `<path class="country-shape country-${key}" d="${featurePath(feature)}"><title>${name}</title></path>`;
    })
    .join("");
  const labels = [
    { label: state.lang === "en" ? "Canada" : "Kanada", lon: -104, lat: 56 },
    { label: "USA", lon: -98, lat: 38 },
    { label: state.lang === "en" ? "Mexico" : "Mexiko", lon: -102, lat: 23 },
  ]
    .map((item) => {
      const point = projectGeoPoint(item.lon, item.lat);
      return `<text class="map-country-label" x="${point.x.toFixed(1)}" y="${point.y.toFixed(1)}">${item.label}</text>`;
    })
    .join("");
  return `<svg class="map-svg" viewBox="0 0 ${MAP_VIEWBOX.width} ${MAP_VIEWBOX.height}" role="img" aria-label="${state.lang === "en" ? "Vector map of Canada, the United States and Mexico" : "Vektorkarte von Kanada, USA und Mexiko"}">
    <defs>
      <clipPath id="mapClip"><rect x="0" y="0" width="${MAP_VIEWBOX.width}" height="${MAP_VIEWBOX.height}" rx="12"></rect></clipPath>
    </defs>
    <g clip-path="url(#mapClip)">
      <rect class="map-water" width="${MAP_VIEWBOX.width}" height="${MAP_VIEWBOX.height}"></rect>
      ${paths}
      ${labels}
    </g>
  </svg>`;
}

function buildVenueWeather() {
  const venues = new Map();
  for (const match of mapMatches()) {
    if (match.latitude === null || match.longitude === null || match.latitude === undefined || match.longitude === undefined) continue;
    const key = venueKey(match);
    if (!venues.has(key)) {
      venues.set(key, {
        key,
        stadium_name: match.stadium_name,
        host_city: match.host_city,
        host_country: match.host_country,
        latitude: Number(match.latitude),
        longitude: Number(match.longitude),
        elevation_m: match.elevation_m,
        stadium_type_basic: match.stadium_type_basic,
        stadium_capacity: match.stadium_capacity,
        roof_available_boolean: match.roof_available_boolean,
        roof_type: match.roof_type,
        climate_control_available: match.climate_control_available,
        weather_protection_level: match.weather_protection_level,
        climate_control_note_de: match.climate_control_note_de,
        pitch_surface_note_de: match.pitch_surface_note_de,
        venue_weather_note_de: match.venue_weather_note_de,
        capacity_source_note: match.capacity_source_note,
        coordinate_precision: match.coordinate_precision,
        coordinate_accuracy_m: match.coordinate_accuracy_m,
        google_place_id: match.google_place_id,
        maps_url: match.maps_url,
        coordinate_verified_at: match.coordinate_verified_at,
        venue_data_quality_score: match.venue_data_quality_score,
        matches: [],
      });
    }
    venues.get(key).matches.push(match);
  }

  return [...venues.values()]
    .map((venue) => {
      const forecastMatches = venue.matches.filter(hasForecast);
      const loads = venue.matches.map((match) => match.weather_load_score);
      const temperatures = venue.matches.map((match) => match.forecast_temp);
      const humidities = venue.matches.map((match) => match.forecast_humidity);
      const winds = venue.matches.map((match) => match.forecast_wind_speed);
      const position = projectVenue(venue.latitude, venue.longitude);
      const avgLoad = avg(loads);
      return {
        ...venue,
        forecastMatches,
        position,
        avgTemp: avg(temperatures),
        avgHumidity: avg(humidities),
        avgWind: avg(winds),
        avgLoad,
        loadClass: loadClass(avgLoad),
        matchdays: [...new Set(venue.matches.map((match) => match.matchday).filter(Boolean))].sort((a, b) => Number(a) - Number(b)),
      };
    })
    .sort((a, b) => {
      const loadDiff = (b.avgLoad ?? -1) - (a.avgLoad ?? -1);
      return loadDiff || a.host_city.localeCompare(b.host_city, "de-DE");
    });
}

function pinLabel(venue) {
  if (venue.avgTemp === null) return t("protectionOpen");
  return `${Math.round(Number(venue.avgTemp))}°`;
}

function mapPin(venue) {
  const selected = venue.key === state.selectedVenueKey ? " is-selected" : "";
  const size = Math.min(36, 28 + Math.min(venue.matches.length, 4) * 2);
  const position = venue.displayPosition || venue.position;
  return `<button
    class="venue-pin ${venue.loadClass}${selected}"
    type="button"
    data-venue-key="${venue.key}"
    style="left:${position.x}%; top:${position.y}%; --pin-size:${size}px"
    title="${venue.host_city}: ${venue.forecastMatches.length}/${venue.matches.length} Forecasts">
    <span>${pinLabel(venue)}</span>
  </button>`;
}

function renderPinConnectors(venues) {
  const connectors = venues
    .filter((venue) => venue.pinShifted)
    .map((venue) => `<g>
      <line x1="${venue.position.mapX.toFixed(1)}" y1="${venue.position.mapY.toFixed(1)}" x2="${venue.displayPosition.mapX.toFixed(1)}" y2="${venue.displayPosition.mapY.toFixed(1)}"></line>
      <circle cx="${venue.position.mapX.toFixed(1)}" cy="${venue.position.mapY.toFixed(1)}" r="3"></circle>
    </g>`)
    .join("");
  if (!connectors) return "";
  return `<svg class="map-pin-connectors" viewBox="0 0 ${MAP_VIEWBOX.width} ${MAP_VIEWBOX.height}" aria-hidden="true">${connectors}</svg>`;
}

function inlineMapMatchDetail(match) {
  const mapsUrl = googleMapsUrl(match);
  return `<section class="inline-map-match-detail" data-match-id="${match.match_id}" aria-label="Partiedetail">
    <div class="detail-actions">
      <button class="primary-action" type="button" data-matchday-jump="${match.match_id}">${t("openInMatchday")}</button>
      ${mapsUrl ? `<a class="secondary-action" href="${escapeAttr(mapsUrl)}" target="_blank" rel="noopener noreferrer">${t("googleMaps")}</a>` : ""}
    </div>
    ${matchDetailMarkup(match)}
  </section>`;
}

function scrollSelectedMapMatchIntoView(matchId) {
  if (!els.mapDetail || !matchId) return;
  const game = els.mapDetail.querySelector(`.venue-game[data-match-id="${matchId}"]`);
  const detail = els.mapDetail.querySelector(`.inline-map-match-detail[data-match-id="${matchId}"]`);
  const target = game || detail;
  if (target) {
    target.scrollIntoView({ block: "start", behavior: "smooth" });
    if (game) game.focus({ preventScroll: true });
  }
}

function renderWeatherMapDetail(venue) {
  if (!els.mapDetail) return;
  if (!venue) {
    els.mapDetail.classList.remove("is-open");
    els.mapDetail.innerHTML = `<div class="empty">${t("mapNoVenue")}</div>`;
    return;
  }
  if (!state.mapSelectedMatchId || !venue.matches.some((match) => match.match_id === state.mapSelectedMatchId)) {
    state.mapSelectedMatchId = venue.matches[0]?.match_id || null;
  }
  const selectedMatch = findMatch(state.mapSelectedMatchId) || venue.matches[0];
  const mapsUrl = googleMapsUrl(selectedMatch || venue);
  const games = venue.matches
    .map((match) => {
      const selected = match.match_id === state.mapSelectedMatchId ? " is-selected" : "";
      const detail = selected ? inlineMapMatchDetail(match) : "";
      return `<li>
        <button class="venue-game${selected}" type="button" data-match-id="${match.match_id}">
          <span>${match.match_id} · ${groupMatchdayLabel(match.matchday)}</span>
          <b>${displayIso3(match.team_a_iso3)} vs. ${displayIso3(match.team_b_iso3)}</b>
          <em>${t("yourTime")} ${viewerDateTime(match).shortLabel} · ${t("venueTime")} ${hostDateTime(match).shortLabel}</em>
        </button>
        ${detail}
      </li>`;
    })
    .join("");
  const venueQuality = Number(venue.venue_data_quality_score || 0);
  const verifiedVenueFacts = venueQuality >= 70
    ? `<div><span>${t("capacity")}</span><b>${capacityLabel(venue.stadium_capacity)}</b></div>
       <div><span>${t("roof")}/${t("climateControl")}</span><b>${roofTypeLabel(venue.roof_type)} · ${yesNo(venue.climate_control_available)}</b></div>`
    : "";
  els.mapDetail.innerHTML = `<button class="map-sheet-close" type="button" data-close-map-sheet aria-label="${t("close")}">×</button>
    <div>
      <p class="eyebrow">${venue.host_country}</p>
      <h3>${venue.host_city}</h3>
      <p class="map-stadium">${venue.stadium_name}</p>
      ${mapsUrl ? `<a class="map-link" href="${escapeAttr(mapsUrl)}" target="_blank" rel="noopener noreferrer">${t("openVenueGoogleMaps")}</a>` : ""}
    </div>
    <div class="map-kpis">
      <div><span>Ø Temp</span><b>${valueOrDash(venue.avgTemp, "°C")}</b></div>
      <div><span>Ø ${t("humidityShort")}</span><b>${valueOrDash(venue.avgHumidity, "%")}</b></div>
      <div><span>Ø Wind</span><b>${valueOrDash(venue.avgWind, " km/h")}</b></div>
      <div><span>${t("weatherLoad")}</span><b>${score(venue.avgLoad)}/100</b></div>
      ${verifiedVenueFacts}
    </div>
    <p class="map-venue-note">${escapeHtml(state.lang === "de" ? displayText(venue.venue_weather_note_de) || t("mapVenueFallback") : `${venue.stadium_name} combines ${roofTypeLabel(venue.roof_type).toLowerCase()} roof context with ${weatherProtectionLabel(venue.weather_protection_level)} weather protection.`)}</p>
    <div class="map-summary">
      <b>${venue.forecastMatches.length}/${venue.matches.length}</b>
      <span>${t("mapForecastSummary")}</span>
    </div>
    <ul class="venue-games">${games}</ul>
    <div class="ad-slot ad-slot-sidebar" data-ad-slot="map_sidebar" aria-label="Anzeige Wetterkarte"></div>`;
  els.mapDetail.classList.toggle("is-open", state.mapSheetOpen);
  renderAds();
}

function renderWeatherMap() {
  if (!els.mapCanvas || !els.mapDetail) return;
  const rawVenues = buildVenueWeather();
  const venues = resolveVenuePinPositions(rawVenues);
  if (!venues.length) {
    els.mapCanvas.innerHTML = renderBaseMap();
    renderWeatherMapDetail(null);
    return;
  }
  if (!state.selectedVenueKey || !venues.some((venue) => venue.key === state.selectedVenueKey)) {
    state.selectedVenueKey = venues[0].key;
  }
  els.mapCanvas.innerHTML = `${renderBaseMap()}
    ${renderPinConnectors(venues)}
    <div class="map-scale">${t("mapScale")}</div>
    ${venues.map(mapPin).join("")}`;
  renderVenueHighlights(venues);
  renderWeatherMapDetail(venues.find((venue) => venue.key === state.selectedVenueKey));
}

function compactNumber(value) {
  if (value === null || value === undefined) return "–";
  return Number(value).toLocaleString(currentLocale());
}

function phaseLabel(value) {
  const labels = state.lang === "en"
    ? {
        group_stage: "Group stage",
        round_of_32: "Round of 32",
        round_of_16: "Round of 16",
        quarterfinals: "Quarterfinals",
        semifinals: "Semifinals",
        final: "Final",
      }
    : {
        group_stage: "Gruppenphase",
        round_of_32: "Sechzehntelfinale",
        round_of_16: "Achtelfinale",
        quarterfinals: "Viertelfinale",
        semifinals: "Halbfinale",
        final: "Finale",
      };
  return labels[value] || value || "–";
}

function renderStandings() {
  const standings = source.standings || {};
  return renderEnhancedStandings(standings);
}

function groupStageMatches() {
  return source.matches.filter((match) => String(match.tournament_stage || "").toLowerCase().includes("group"));
}

function venueDistanceKm(from, to) {
  const rawCoordinates = [from.latitude, from.longitude, to.latitude, to.longitude];
  if (rawCoordinates.some((value) => value === null || value === undefined || value === "")) return null;
  const latitudeA = Number(from.latitude);
  const longitudeA = Number(from.longitude);
  const latitudeB = Number(to.latitude);
  const longitudeB = Number(to.longitude);
  if ([latitudeA, longitudeA, latitudeB, longitudeB].some(Number.isNaN)) return null;
  const radians = (value) => value * Math.PI / 180;
  const latitudeDelta = radians(latitudeB - latitudeA);
  const longitudeDelta = radians(longitudeB - longitudeA);
  const calculation = Math.sin(latitudeDelta / 2) ** 2
    + Math.cos(radians(latitudeA)) * Math.cos(radians(latitudeB)) * Math.sin(longitudeDelta / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(calculation));
}

function teamTravelRanking() {
  const teams = new Map();
  groupStageMatches().forEach((match) => {
    ["a", "b"].forEach((side) => {
      const iso3 = match[`team_${side}_iso3`];
      if (!iso3) return;
      if (!teams.has(iso3)) {
        teams.set(iso3, {
          iso3,
          flag: match[`team_${side}_flag`] || "",
          name_de: match[`team_${side}_name_de`] || iso3,
          name_en: match[`team_${side}_name_en`] || match[`team_${side}_name_de`] || iso3,
          group: match.group_name || "–",
          matches: [],
        });
      }
      teams.get(iso3).matches.push(match);
    });
  });

  return [...teams.values()].map((team) => {
    const matches = team.matches.sort((a, b) => String(a.date_utc || "").localeCompare(String(b.date_utc || "")));
    const legs = [];
    let totalDistanceKm = 0;
    for (let index = 1; index < matches.length; index += 1) {
      const distanceKm = venueDistanceKm(matches[index - 1], matches[index]);
      if (distanceKm === null) continue;
      totalDistanceKm += distanceKm;
      legs.push(distanceKm);
    }
    const cityCounts = new Map();
    const venueCounts = new Map();
    matches.forEach((match) => {
      cityCounts.set(match.host_city, (cityCounts.get(match.host_city) || 0) + 1);
      venueCounts.set(match.stadium_name, (venueCounts.get(match.stadium_name) || 0) + 1);
    });
    const repeatVenue = [...venueCounts.entries()].sort((a, b) => b[1] - a[1])[0] || ["", 0];
    const cityChanges = matches.slice(1).filter((match, index) => match.host_city !== matches[index].host_city).length;
    const venueChanges = matches.slice(1).filter((match, index) => match.stadium_name !== matches[index].stadium_name).length;
    const latestMatch = matches[matches.length - 1];
    const latestSide = latestMatch?.team_a_iso3 === team.iso3 ? "a" : "b";
    const cumulativeRecoveryLoad = Number(latestMatch?.[`team_${latestSide}_cumulative_recovery_load`]);
    return {
      ...team,
      matches,
      legs,
      totalDistanceKm,
      uniqueCities: cityCounts.size,
      uniqueVenues: venueCounts.size,
      cityChanges,
      venueChanges,
      repeatVenueName: repeatVenue[0],
      maxMatchesAtVenue: repeatVenue[1],
      repeatedVenueGames: matches.length - venueCounts.size,
      cumulativeRecoveryLoad: Number.isFinite(cumulativeRecoveryLoad) ? cumulativeRecoveryLoad : null,
      complete: matches.length === 3 && legs.length === 2,
    };
  }).filter((team) => team.complete);
}

function travelTeamName(team) {
  return state.lang === "en" ? team.name_en : normalizeGermanText(team.name_de);
}

function travelDistanceLabel(value) {
  return `${new Intl.NumberFormat(currentLocale(), { maximumFractionDigits: 0 }).format(Math.round(value))} km`;
}

function sortedTravelRanking(rows) {
  const comparison = {
    distance_desc: (a, b) => b.totalDistanceKm - a.totalDistanceKm,
    distance_asc: (a, b) => a.totalDistanceKm - b.totalDistanceKm,
    cities_desc: (a, b) => b.uniqueCities - a.uniqueCities || b.uniqueVenues - a.uniqueVenues || b.venueChanges - a.venueChanges || b.totalDistanceKm - a.totalDistanceKm,
    repeats_desc: (a, b) => b.maxMatchesAtVenue - a.maxMatchesAtVenue || b.repeatedVenueGames - a.repeatedVenueGames || a.totalDistanceKm - b.totalDistanceKm,
    load_desc: (a, b) => Number(b.cumulativeRecoveryLoad || -1) - Number(a.cumulativeRecoveryLoad || -1) || b.totalDistanceKm - a.totalDistanceKm,
  }[state.travelSort] || ((a, b) => b.totalDistanceKm - a.totalDistanceKm);
  return [...rows].sort((a, b) => comparison(a, b) || travelTeamName(a).localeCompare(travelTeamName(b), currentLocale()));
}

function travelRouteMarkup(team) {
  return team.matches.map((match, index) => `<span class="travel-stop">
      <b>${escapeHtml(match.host_city)}</b>
      <small>${escapeHtml(match.stadium_name)}</small>
      ${index < team.matches.length - 1 ? `<i aria-hidden="true">→</i>` : ""}
    </span>`).join("");
}

function travelRankingRow(team, index) {
  const repeatText = team.maxMatchesAtVenue > 1
    ? `${team.maxMatchesAtVenue} × ${escapeHtml(team.repeatVenueName)}`
    : t("travelNoRepeat");
  return `<article class="travel-ranking-row">
    <header class="travel-ranking-head">
      <span class="travel-rank">#${index + 1}</span>
      <div class="travel-team">
        <b>${team.flag} ${escapeHtml(travelTeamName(team))}</b>
        <small>${displayIso3(team.iso3)} · ${t("group")} ${escapeHtml(team.group)}</small>
      </div>
      <div class="travel-total"><span>${t("travelDistance")}</span><b>${travelDistanceLabel(team.totalDistanceKm)}</b></div>
    </header>
    <div class="travel-kpis">
      <div><span>${t("travelCities")}</span><b>${team.uniqueCities}</b></div>
      <div><span>${t("travelVenues")}</span><b>${team.uniqueVenues}</b></div>
      <div><span>${t("travelChanges")}</span><b>${team.cityChanges}</b></div>
      <div><span>${t("travelSameVenue")}</span><b>${repeatText}</b></div>
    </div>
    <details class="travel-details">
      <summary>${t("travelRoute")}</summary>
      <div class="travel-route-block"><div class="travel-route">${travelRouteMarkup(team)}</div></div>
    </details>
  </article>`;
}

function renderTravelRanking() {
  const rows = teamTravelRanking();
  if (!rows.length) return `<div class="empty">${t("travelNoData")}</div>`;
  const distanceSorted = [...rows].sort((a, b) => b.totalDistanceKm - a.totalDistanceKm);
  const longest = distanceSorted[0];
  const shortest = distanceSorted[distanceSorted.length - 1];
  const maxCities = Math.max(...rows.map((team) => team.uniqueCities));
  const maxCityTeams = rows.filter((team) => team.uniqueCities === maxCities).length;
  const repeatTeams = rows.filter((team) => team.maxMatchesAtVenue > 1).length;
  const sortedRows = sortedTravelRanking(rows);
  return `<section class="travel-ranking">
    <div class="travel-ranking-intro">
      <div>
        <p class="eyebrow">${t("travelEyebrow")}</p>
        <h2>${t("travelTitle")}</h2>
        <p>${t("travelIntro")}</p>
      </div>
      <select id="travelSort" aria-label="${t("travelSortAria")}">
        <option value="distance_desc"${state.travelSort === "distance_desc" ? " selected" : ""}>${t("travelSortDistanceDesc")}</option>
        <option value="distance_asc"${state.travelSort === "distance_asc" ? " selected" : ""}>${t("travelSortDistanceAsc")}</option>
        <option value="cities_desc"${state.travelSort === "cities_desc" ? " selected" : ""}>${t("travelSortCities")}</option>
        <option value="repeats_desc"${state.travelSort === "repeats_desc" ? " selected" : ""}>${t("travelSortRepeats")}</option>
      </select>
    </div>
    <div class="travel-summary">
      <div><span>${t("travelLongest")}</span><b>${longest.flag} ${escapeHtml(travelTeamName(longest))}</b><small>${travelDistanceLabel(longest.totalDistanceKm)}</small></div>
      <div><span>${t("travelShortest")}</span><b>${shortest.flag} ${escapeHtml(travelTeamName(shortest))}</b><small>${travelDistanceLabel(shortest.totalDistanceKm)}</small></div>
      <div><span>${t("travelThreeCities")}</span><b>${maxCityTeams} ${t("travelTeams")}</b><small>${maxCities} ${t("travelCities")}</small></div>
      <div><span>${t("travelRepeatVenue")}</span><b>${repeatTeams} ${t("travelTeams")}</b><small>${t("travelSameVenue")}</small></div>
    </div>
    <div class="travel-ranking-label">${t("travelRankNotice")}</div>
    <div class="travel-ranking-list">${sortedRows.map(travelRankingRow).join("")}</div>
    <p class="travel-method-note">${t("travelMethodNote")}</p>
  </section>`;
}

function analysisCard(item) {
  return `<article class="analysis-card">
    <div class="analysis-card-head">
      <span>${item.match_id || item.label || item.scope || "–"}</span>
      <b>${item.label || item.title || ""}</b>
    </div>
    <div class="analysis-kpis">
      <div><span>${t("status")}</span><b>${item.status || "scheduled"}</b></div>
      <div><span>${t("weatherEdge")}</span><b>${analysisAdvantageLabel(item.weather_edge)}</b></div>
      <div><span>${t("load")}</span><b>${score(item.weather_load_score)}/100</b></div>
    </div>
    <p>${state.lang === "de" ? displayText(item.note_de) || t("analysisFallback") : item.note_en || t("analysisFallback")}</p>
  </article>`;
}

function aggregateCard(label, metrics) {
  return `<article class="analysis-card">
    <div class="analysis-card-head">
      <span>${label}</span>
      <b>${metrics.finished}/${metrics.matches} ${t("played")}</b>
    </div>
    <div class="analysis-kpis">
      <div><span>Forecast</span><b>${metrics.forecast_matches}</b></div>
      <div><span>${t("metricEdges")}</span><b>${metrics.weather_fit_edges}</b></div>
      <div><span>${t("reportReady")}</span><b>${metrics.report_ready_matches}</b></div>
    </div>
    <p>Ø Weather Load: ${valueOrDash(metrics.avg_weather_load_score, "/100")}. ${state.lang === "de" ? "Actual-Wetter vorhanden" : "Actual weather available"}: ${metrics.actual_weather_matches} ${t("matches")}.</p>
  </article>`;
}

function reportMatchCard(item) {
  return `<article class="analysis-card report-match-card">
    <div class="analysis-card-head">
      <span>${item.match_id}</span>
      <b>${item.label}</b>
    </div>
    <div class="analysis-kpis">
      <div><span>${t("reportResult")}</span><b>${item.result}</b></div>
      <div><span>${t("weatherEdge")}</span><b>${analysisAdvantageLabel(item.weather_edge)}</b></div>
      <div><span>${t("reportEdgeGap")}</span><b>${score(item.gap)}/100</b></div>
      <div><span>${t("load")}</span><b>${score(item.weather_load_score)}/100</b></div>
    </div>
    <p class="report-match-meta">${reportOutcomeLabel(item.category)} · ${t("reportDate")}: ${item.local_date || "–"} · ${t("reportLocation")}: ${item.host_city || "–"}</p>
  </article>`;
}

function reportFindingRows(report) {
  if (!report) return [];
  return state.lang === "de" ? (report.key_findings_de || []) : (report.key_findings_en || []);
}

function reportMethodNote(report) {
  if (!report) return "";
  return state.lang === "de" ? (report.method_note_de || "") : (report.method_note_en || "");
}

function reportHeadline(report) {
  if (!report) return "";
  return state.lang === "de" ? (report.headline_de || "") : (report.headline_en || "");
}

function reportSummaryLine(report) {
  if (!report) return "";
  return state.lang === "de" ? (report.summary_de || "") : (report.summary_en || "");
}

function reportInsightCard(label, value, detail) {
  return `<article class="report-insight-card">
    <span>${label}</span>
    <b>${value}</b>
    <small>${detail}</small>
  </article>`;
}

function renderReportLead(report) {
  if (!report) return "";
  const readiness = report.knockout_readiness || {};
  const forecastShare = Number.isFinite(Number(readiness.forecast_share)) ? `${numberLabel(Number(readiness.forecast_share) * 100, 0)}%` : "–";
  return `<section class="report-hero-card">
    <div class="report-hero-copy">
      <p class="eyebrow">${t("reportEditionEyebrow")}</p>
      <h3>${t("reportLeadTitle")}</h3>
      <p class="copy">${reportHeadline(report)}</p>
      <p class="copy">${reportSummaryLine(report)}</p>
    </div>
    <div class="report-hero-meta">
      <div><span>${t("reportScope")}</span><b>${state.lang === "de" ? report.scope_label_de : report.scope_label_en}</b></div>
      <div><span>${t("reportGoals")}</span><b>${report.total_goals} · ${numberLabel(report.goals_per_match, 2)} ${t("statsPerMatch")}</b></div>
      <div><span>${t("reportCoverage")}</span><b>${report.event_coverage.goal_event_matches}/${report.event_coverage.finished_matches}</b></div>
      <div><span>${t("reportReadiness")}</span><b>${readiness.forecast_matches}/${readiness.upcoming_matches || 0} · ${forecastShare}</b></div>
    </div>
  </section>`;
}

function renderReportInsights(report) {
  if (!report) return "";
  return `<section class="report-section-card">
    <div class="report-section-head">
      <h3>${t("reportInsightsTitle")}</h3>
    </div>
    <div class="report-insight-grid">
      ${reportInsightCard(t("reportInsightEdgeHit"), report.weather_edge_hit_rate === null ? "–" : `${report.weather_edge_hit_rate}%`, `${report.weather_edge_confirmed}/${report.comparable_matches} ${t("confirmedWeatherEdges")}`)}
      ${reportInsightCard(t("reportInsightLoad"), report.avg_weather_load_score === null ? "–" : `${numberLabel(report.avg_weather_load_score, 1)}/100`, state.lang === "de" ? `${report.high_load_matches} Partien mit mindestens mittlerer Last` : `${report.high_load_matches} matches in at least the medium-load band`)}
      ${reportInsightCard(t("reportInsightDraws"), report.draw_share === null ? "–" : `${numberLabel(report.draw_share * 100, 0)}%`, `${report.draws} ${t("matches")} ${state.lang === "de" ? "endeten remis" : "ended level"}`)}
      ${reportInsightCard(t("reportInsightForecast"), report.knockout_readiness.upcoming_matches || 0, `${report.knockout_readiness.forecast_matches}/${report.knockout_readiness.upcoming_matches || 0} ${state.lang === "de" ? "mit Forecast" : "with forecast"}`)}
    </div>
  </section>`;
}

function renderReportFindingList(report) {
  const items = reportFindingRows(report);
  if (!report || !items.length) return "";
  return `<section class="report-section-card">
    <div class="report-section-head">
      <h3>${t("reportFindingsTitle")}</h3>
    </div>
    <ul class="report-finding-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
  </section>`;
}

function historicalComparisonSummary(report) {
  if (!report) return null;
  const currentRate = Number(report.goals_per_match || 0);
  const baselines = HISTORICAL_WORLD_CUP_BASELINES.map((item) => ({
    ...item,
    delta: Number((currentRate - Number(item.goalsPerMatch || 0)).toFixed(2)),
  }));
  const bestHistorical = baselines.reduce((best, item) => (item.goalsPerMatch > best.goalsPerMatch ? item : best), baselines[0]);
  return {
    currentRate,
    bestHistorical,
    baselines,
  };
}

function historicalBaselineCard(item, currentRate) {
  const delta = Number((currentRate - Number(item.goalsPerMatch || 0)).toFixed(2));
  const deltaLabel = delta >= 0
    ? `${state.lang === "de" ? "+" : "+"}${numberLabel(delta, 2)}`
    : numberLabel(delta, 2);
  const note = state.lang === "de" ? item.note_de : item.note_en;
  return `<article class="historical-card">
    <div class="historical-card-top">
      <span>${item.year}</span>
      <b>${item.goals} ${t("reportHistoryGoals")}</b>
    </div>
    <div class="historical-card-metric">
      <strong>${numberLabel(item.goalsPerMatch, 2)}</strong>
      <small>${t("reportHistoryGoalsPerMatch")}</small>
    </div>
    <div class="historical-card-meta">
      <div><span>${t("reportHistoryChampion")}</span><b>${displayIso3(item.champion)}</b></div>
      <div><span>${t("reportHistoryTopScorer")}</span><b>${escapeHtml(item.topScorer)} · ${item.topScorerGoals}</b></div>
      <div><span>${state.lang === "de" ? "Delta zu 2026" : "Delta vs 2026"}</span><b>${deltaLabel}</b></div>
    </div>
    <p>${escapeHtml(note)}</p>
  </article>`;
}

function renderHistoricalComparison(report) {
  const summary = historicalComparisonSummary(report);
  if (!summary) return "";
  return `<section class="report-section-card historical-section-card">
    <div class="report-section-head">
      <h3>${t("reportHistoryTitle")}</h3>
    </div>
    <p class="copy">${t("reportHistoryIntro")}</p>
    <div class="historical-pace-callout">
      <span>${t("reportHistoryPaceLabel")}</span>
      <b>${numberLabel(summary.currentRate, 2)} ${t("reportHistoryGoalsPerMatch")}</b>
      <small>${t("reportHistoryPaceLead")}</small>
      <p>${t("reportHistoryPaceCaveat")}</p>
    </div>
    <div class="historical-scroll-rail">
      ${summary.baselines.map((item) => historicalBaselineCard(item, summary.currentRate)).join("")}
    </div>
  </section>`;
}

function reportExtremeCard(title, item) {
  if (!item) return "";
  return `<article class="analysis-card report-match-card">
    <div class="analysis-card-head">
      <span>${escapeHtml(item.match_id || "–")}</span>
      <b>${escapeHtml(item.label || "–")}</b>
    </div>
    <div class="analysis-kpis">
      <div><span>${t("reportResult")}</span><b>${escapeHtml(item.result || "–")}</b></div>
      <div><span>${t("reportEdgeGap")}</span><b>${score(item.gap)}/100</b></div>
      <div><span>${t("load")}</span><b>${score(item.weather_load_score)}/100</b></div>
    </div>
    <p class="report-match-meta">${escapeHtml(title)} · ${t("reportLocation")}: ${escapeHtml(item.host_city || "–")} · ${t("reportDate")}: ${escapeHtml(item.local_date || "–")}</p>
  </article>`;
}

function renderReportExtremes(report) {
  if (!report || !report.context_extremes) return "";
  return `<section class="report-section-card">
    <div class="report-section-head">
      <h3>${t("reportContextTitle")}</h3>
    </div>
    <div class="analysis-grid report-analysis-grid">
      ${reportExtremeCard(t("reportExtremeLoad"), report.context_extremes.highest_load)}
      ${reportExtremeCard(t("reportExtremeEdge"), report.context_extremes.sharpest_edge)}
      ${reportExtremeCard(t("reportExtremeTravel"), report.context_extremes.longest_travel)}
      ${reportExtremeCard(t("reportExtremeAltitude"), report.context_extremes.highest_altitude)}
    </div>
  </section>`;
}

function renderReportBucket(title, items) {
  return `<section class="report-section-card">
    <div class="report-section-head">
      <h3>${title}</h3>
      <span>${items.length}</span>
    </div>
    ${items.length ? `<div class="analysis-grid report-analysis-grid">${items.map(reportMatchCard).join("")}</div>` : `<div class="empty">${t("reportNoMatches")}</div>`}
  </section>`;
}

function renderMatchAnalyses() {
  const matches = (source.analysis && source.analysis.matches) || [];
  if (!matches.length) return `<div class="empty">${t("noMatchAnalyses")}</div>`;
  return `<div class="analysis-grid">${matches.map(analysisCard).join("")}</div>`;
}

function renderAggregateGroup(grouped, labelMapper = (value) => value) {
  const entries = Object.entries(grouped || {}).sort(([a], [b]) => {
    const numberA = Number(a);
    const numberB = Number(b);
    if (!Number.isNaN(numberA) && !Number.isNaN(numberB)) return numberA - numberB;
    return String(a).localeCompare(String(b), "de-DE");
  });
  if (!entries.length) return `<div class="empty">${t("noAggregates")}</div>`;
  return `<div class="analysis-grid">${entries.map(([label, metrics]) => aggregateCard(labelMapper(label), metrics)).join("")}</div>`;
}

function renderReportSummary() {
  const tournament = source.analysis && source.analysis.tournament;
  if (!tournament) return `<div class="empty">${t("noReport")}</div>`;
  const report = currentReport();
  const liveBalance = tournamentWeatherBalance();
  const balance = report ? {
    finished: report.finished_matches,
    comparable: report.comparable_matches,
    confirmed: report.weather_edge_confirmed,
    hitRate: report.weather_edge_hit_rate,
  } : liveBalance;
  const tips = predictionScoreSummary();
  const buckets = report && report.featured_matches ? report.featured_matches : reportMatchEntries();
  return `<div class="report-summary">
    ${renderReportLead(report)}
    ${renderReportInsights(report)}
    <div class="report-kpis">
      <div class="metric"><span class="metric-value">${balance.finished}</span><span class="metric-label">${t("played")}</span></div>
      <div class="metric"><span class="metric-value">${balance.comparable}</span><span class="metric-label">${t("clearWeatherEdges")}</span></div>
      <div class="metric"><span class="metric-value">${balance.confirmed}</span><span class="metric-label">${t("confirmedWeatherEdges")}</span></div>
      <div class="metric"><span class="metric-value">${balance.hitRate === null ? "–" : `${balance.hitRate}%`}</span><span class="metric-label">${t("weatherHitRate")}</span></div>
    </div>
    <div class="report-balance-grid">
      <section class="report-balance-card">
        <p class="eyebrow">${t("weatherBalance")}</p>
        <div><span>${t("confirmedWeatherEdges")}</span><b>${balance.confirmed}</b></div>
        <div><span>${t("unconfirmedWeatherEdges")}</span><b>${buckets.missed.length}</b></div>
        <div><span>${t("drawnWeatherEdges")}</span><b>${buckets.draw.length}</b></div>
      </section>
      <section class="report-balance-card">
        <p class="eyebrow">${t("personalTipBalance")}</p>
        ${tips.total ? `<div><span>${t("correctTips")}</span><b>${tips.correct}/${tips.total}</b></div>` : `<div class="active-empty">${t("noPersonalTips")}</div>`}
      </section>
    </div>
    <section class="report-section-card">
      <div class="report-section-head">
        <h3>${t("reportExamplesTitle")}</h3>
      </div>
      <p class="copy">${t("reportExamplesIntro")}</p>
    </section>
    ${renderReportFindingList(report)}
    ${renderHistoricalComparison(report)}
    ${renderReportExtremes(report)}
    ${renderReportBucket(t("reportConfirmedTitle"), buckets.confirmed)}
    ${renderReportBucket(t("reportMissedTitle"), buckets.missed)}
    ${renderReportBucket(t("reportDrawTitle"), buckets.draw)}
    ${report ? `<section class="report-section-card"><div class="report-section-head"><h3>${t("reportMethodTitle")}</h3></div><p class="copy">${escapeHtml(reportMethodNote(report))}</p></section>` : ""}
    <p class="copy">${t("reportCopy")}</p>
  </div>`;
}

function isMobileViewport() {
  return window.matchMedia("(max-width: 640px)").matches;
}

function adMatchesDevice(ad) {
  const targeting = String(ad.device_targeting || "all");
  if (targeting === "all") return true;
  return targeting === (isMobileViewport() ? "mobile" : "desktop");
}

function pickAd(slotKey) {
  const candidates = ads
    .filter((ad) => ad.slot_key === slotKey && adMatchesDevice(ad))
    .sort((a, b) => Number(b.priority || 0) - Number(a.priority || 0) || Number(b.weight || 0) - Number(a.weight || 0));
  return candidates[0];
}

function renderAdCreative(ad) {
  const clickUrl = safeHttpUrl(ad.click_url);
  const imageUrl = safeHttpUrl(ad.image_url);
  const pixelUrl = safeHttpUrl(ad.tracking_pixel_url);
  const translatedAd = state.lang === "en" ? AD_TRANSLATIONS_EN[ad.slot_key] || {} : {};
  const adLabel = translatedAd.label || ad[`label_${state.lang}`] || ad.label || t("adLabel");
  const adHeadline = translatedAd.headline || ad[`headline_${state.lang}`] || ad.headline || ad.creative_name || t("adDefaultHeadline");
  const adBody = translatedAd.body || ad[`body_${state.lang}`] || ad.body || t("adDefaultBody");
  const adCta = translatedAd.call_to_action || ad[`call_to_action_${state.lang}`] || ad.call_to_action;
  const style = [
    ad.background_color ? `--ad-bg:${escapeAttr(ad.background_color)}` : "",
    ad.text_color ? `--ad-ink:${escapeAttr(ad.text_color)}` : "",
    ad.max_width ? `--ad-max:${Number(ad.max_width)}px` : "",
    ad.min_height ? `--ad-min:${Number(ad.min_height)}px` : "",
  ]
    .filter(Boolean)
    .join(";");
  const media = imageUrl
    ? `<img class="ad-image" src="${escapeAttr(imageUrl)}" alt="${escapeAttr(ad.alt_text || adHeadline || t("adLabel"))}" loading="lazy">`
    : "";
  const cta = clickUrl && adCta
    ? `<a class="ad-cta" href="${escapeAttr(clickUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(state.lang === "de" ? normalizeGermanText(adCta) : adCta)}</a>`
    : "";
  const pixel = pixelUrl ? `<img class="ad-pixel" src="${escapeAttr(pixelUrl)}" alt="" aria-hidden="true">` : "";
  return `<aside class="ad-card" style="${style}">
    <div class="ad-content">
      <span class="ad-label">${escapeHtml(state.lang === "de" ? normalizeGermanText(adLabel) : adLabel)}</span>
      ${media}
      <div class="ad-copy">
        <b>${escapeHtml(state.lang === "de" ? displayText(adHeadline) : adHeadline)}</b>
        <p>${escapeHtml(state.lang === "de" ? displayText(adBody) : adBody)}</p>
      </div>
      ${cta}
    </div>
    ${pixel}
  </aside>`;
}

function renderAds() {
  els.adSlots = [...document.querySelectorAll("[data-ad-slot]")];
  document.documentElement.classList.toggle("ads-enabled", ADS_ENABLED);
  if (!ADS_ENABLED) {
    els.adSlots.forEach((slot) => {
      slot.hidden = true;
      slot.innerHTML = "";
    });
    return;
  }
  els.adSlots.forEach((slot) => {
    const ad = pickAd(slot.dataset.adSlot);
    if (!ad) {
      slot.hidden = true;
      slot.innerHTML = "";
      return;
    }
    slot.hidden = false;
    slot.innerHTML = renderAdCreative(ad);
  });
}

function renderStaticUi() {
  document.documentElement.lang = state.lang;
  document.title = "The Weather Cup 2026";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  });
  if (els.languageToggle) {
    els.languageToggle.textContent = state.lang === "de" ? "EN" : "DE";
    els.languageToggle.setAttribute("aria-label", t("switchLanguage"));
  }
  if (els.mapMatchdayFilter) els.mapMatchdayFilter.setAttribute("aria-label", t("mapSelectAria"));
  if (els.favoritesMatchdayFilter) els.favoritesMatchdayFilter.setAttribute("aria-label", t("favoritesSelectAria"));
  if (els.mapCanvas) els.mapCanvas.setAttribute("aria-label", t("mapCanvasAria"));
  if (els.mapDetail) els.mapDetail.setAttribute("aria-label", t("mapDetailAria"));
  syncAnalysisChrome();
}

function refreshLanguageSensitiveUi() {
  renderStaticUi();
  renderMetrics();
  renderCoverage();
  renderFilters();
  renderWeatherMap();
  renderWeatherFavorites();
  renderList();
  renderTravelSection();
  renderAnalysis();
  renderAds();
  renderExperience();
}

function updateBackToTopVisibility() {
  if (!els.backToTop) return;
  els.backToTop.hidden = window.scrollY < 520;
}

function renderAnalysis() {
  if (!els.analysisContent) return;
  if (state.analysisMode === "stats") {
    els.analysisContent.innerHTML = renderTournamentStats();
  } else if (state.analysisMode === "matches") {
    els.analysisContent.innerHTML = renderMatchAnalyses();
  } else if (state.analysisMode === "matchdays") {
    els.analysisContent.innerHTML = renderAggregateGroup((source.analysis || {}).matchdays, groupMatchdayLabel);
  } else if (state.analysisMode === "phases") {
    els.analysisContent.innerHTML = renderAggregateGroup((source.analysis || {}).phases, phaseLabel);
  } else if (state.analysisMode === "report") {
    els.analysisContent.innerHTML = renderReportSummary();
  } else {
    els.analysisContent.innerHTML = renderStandings();
  }
  renderAds();
}

function renderTravelSection() {
  if (!els.travelContent) return;
  els.travelContent.innerHTML = renderTravelRanking();
}

function syncAnalysisChrome() {
  if (els.analysisEyebrow) {
    els.analysisEyebrow.textContent = t("tablesEyebrow");
  }
  if (els.analysisTitle) {
    els.analysisTitle.textContent = state.analysisMode === "stats" ? t("statsTitle") : t("tablesTitle");
  }
  if (els.analysisTabs) {
    els.analysisTabs.hidden = state.analysisMode === "stats";
  }
  els.analysisButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.analysisMode === state.analysisMode);
  });
}

function setActiveSection(sectionName) {
  state.activeSection = sectionName;
  let activeButton = null;
  els.navButtons.forEach((button) => {
    let isActive = button.dataset.sectionTarget === sectionName;
    if (sectionName === "analysis" && button.dataset.sectionTarget === "analysis") {
      if (button.dataset.analysisModeTarget === "stats") {
        isActive = state.analysisMode === "stats";
      } else {
        isActive = state.analysisMode !== "stats";
      }
    }
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-current", isActive ? "page" : "false");
    if (isActive) activeButton = button;
  });
  els.sections.forEach((section) => {
    section.classList.toggle("is-active", section.dataset.section === sectionName);
  });
  const nav = activeButton?.parentElement;
  if (nav && nav.scrollWidth > nav.clientWidth) {
    window.requestAnimationFrame(() => activeButton.scrollIntoView({ block: "nearest", inline: "center" }));
  }
  const activeSection = els.sections.find((section) => section.dataset.section === sectionName);
  if (activeSection && sectionName !== "home") {
    window.requestAnimationFrame(() => activeSection.scrollIntoView({ block: "start", behavior: "smooth" }));
  }
  if (sectionName === "matches") {
    window.requestAnimationFrame(() => scrollScheduleAnchorIntoView("smooth"));
  }
}

function bindEvents() {
  if (els.languageToggle) {
    els.languageToggle.addEventListener("click", () => {
      state.lang = state.lang === "de" ? "en" : "de";
      refreshLanguageSensitiveUi();
      trackEvent("language_switch", { language: state.lang });
    });
  }
  if (els.backToTop) {
    els.backToTop.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    window.addEventListener("scroll", updateBackToTopVisibility, { passive: true });
  }
  els.legalLinks.forEach((button) => {
    button.addEventListener("click", () => {
      const target = document.querySelector(`#${button.dataset.legalTarget}`);
      if (!target) return;
      setActiveSection("faq");
      target.open = true;
      window.requestAnimationFrame(() => target.scrollIntoView({ block: "center", behavior: "smooth" }));
    });
  });
  els.navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.sectionTarget === "analysis") {
        state.analysisMode = button.dataset.analysisModeTarget || "standings";
        syncAnalysisChrome();
        renderAnalysis();
      }
      setActiveSection(button.dataset.sectionTarget);
      trackEvent("tab_change", { section: button.dataset.sectionTarget, mode: button.dataset.analysisModeTarget || null });
    });
  });
  if (els.scheduleJumpbar) {
    els.scheduleJumpbar.addEventListener("click", (event) => {
      const viewToggle = event.target.closest("[data-schedule-view]");
      if (viewToggle) {
        state.scheduleView = viewToggle.dataset.scheduleView;
        renderList();
        trackEvent("schedule_view_change", { view: state.scheduleView });
        window.requestAnimationFrame(() => scrollScheduleAnchorIntoView("smooth"));
        return;
      }
      const jump = event.target.closest("[data-schedule-jump]");
      if (!jump) return;
      const targetView = jump.dataset.targetView;
      if (targetView) state.scheduleView = targetView;
      const matchId = jump.dataset.matchId;
      if (jump.dataset.scheduleJump === "start") {
        state.selectedId = null;
        renderList();
        window.requestAnimationFrame(() => {
          const firstGroup = els.list.querySelector(".match-date-group");
          if (firstGroup) firstGroup.scrollIntoView({ block: "start", behavior: "smooth" });
        });
      } else if (matchId) {
        state.selectedId = matchId;
        renderList();
        window.requestAnimationFrame(() => scrollSelectedMatchIntoView(matchId));
      }
      trackEvent("schedule_jump", { target: jump.dataset.scheduleJump, match_id: matchId || null, view: state.scheduleView });
    });
  }
  els.search.addEventListener("input", (event) => {
    state.query = event.target.value.trim().toLowerCase();
    renderList();
  });
  els.modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.mode = button.dataset.mode;
      els.modeButtons.forEach((item) => item.classList.toggle("is-active", item === button));
      renderList();
    });
  });
  els.matchdayFilter.addEventListener("change", (event) => {
    state.matchday = event.target.value;
    renderList();
  });
  els.groupFilter.addEventListener("change", (event) => {
    state.group = event.target.value;
    renderList();
  });
  if (els.mapMatchdayFilter) {
    els.mapMatchdayFilter.addEventListener("change", (event) => {
      state.mapMatchday = event.target.value;
      state.selectedVenueKey = null;
      state.mapSelectedMatchId = null;
      state.mapSheetOpen = false;
      renderWeatherMap();
      trackEvent("map_filter_change", { matchday: state.mapMatchday });
    });
  }
  if (els.favoritesMatchdayFilter) {
    els.favoritesMatchdayFilter.addEventListener("change", (event) => {
      state.favoritesMatchday = event.target.value;
      renderWeatherFavorites();
      trackEvent("ranking_filter_change", { ranking: "weather_favorites", matchday: state.favoritesMatchday });
    });
  }
  if (els.mapCanvas) {
    els.mapCanvas.addEventListener("click", (event) => {
      const pin = event.target.closest(".venue-pin");
      if (!pin) return;
      state.selectedVenueKey = pin.dataset.venueKey;
      state.mapSelectedMatchId = null;
      state.mapSheetOpen = true;
      renderWeatherMap();
      trackEvent("map_venue_select", { venue: state.selectedVenueKey });
    });
  }
  els.mapViewButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.mapView = button.dataset.mapView;
      renderWeatherMap();
      trackEvent("map_view_change", { view: state.mapView });
    });
  });
  if (els.venueHighlights) {
    els.venueHighlights.addEventListener("click", (event) => {
      const target = event.target.closest("[data-venue-highlight]");
      if (!target) return;
      state.selectedVenueKey = target.dataset.venueHighlight;
      state.mapSelectedMatchId = null;
      state.mapSheetOpen = true;
      state.mapView = "map";
      renderWeatherMap();
      trackEvent("venue_highlight_click", { venue: state.selectedVenueKey });
    });
  }
  if (els.mapDetail) {
    els.mapDetail.addEventListener("click", (event) => {
      if (event.target.closest("[data-close-map-sheet]")) {
        state.mapSheetOpen = false;
        els.mapDetail.classList.remove("is-open");
        return;
      }
      const jump = event.target.closest("[data-matchday-jump]");
      if (jump) {
        openMatchInMatchday(jump.dataset.matchdayJump);
        return;
      }
      const game = event.target.closest(".venue-game");
      if (!game) return;
      state.mapSelectedMatchId = game.dataset.matchId;
      state.selectedId = game.dataset.matchId;
      state.mapSheetOpen = true;
      renderWeatherMap();
      window.requestAnimationFrame(() => scrollSelectedMapMatchIntoView(state.mapSelectedMatchId));
    });
  }
  if (els.favoritesList) {
    els.favoritesList.addEventListener("click", (event) => {
      const jump = event.target.closest("[data-favorite-jump]");
      if (!jump) return;
      openMatchInMatchday(jump.dataset.favoriteJump);
    });
  }
  els.list.addEventListener("click", (event) => {
    const prediction = event.target.closest("[data-predict-match]");
    if (prediction) {
      openPredictionDialog(prediction.dataset.predictMatch);
      return;
    }
    const cardEl = event.target.closest(".quick-match-card");
    if (!cardEl) return;
    state.selectedId = cardEl.dataset.matchId;
    renderList();
    trackEvent("match_card_expand", { match_id: state.selectedId, source: "schedule" });
    window.requestAnimationFrame(() => scrollSelectedMatchIntoView(state.selectedId));
  });
  els.list.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const cardEl = event.target.closest(".quick-match-card");
    if (!cardEl) return;
    event.preventDefault();
    state.selectedId = cardEl.dataset.matchId;
    renderList();
    window.requestAnimationFrame(() => scrollSelectedMatchIntoView(state.selectedId));
  });
  els.analysisButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.analysisMode = button.dataset.analysisMode;
      syncAnalysisChrome();
      renderAnalysis();
      setActiveSection("analysis");
      trackEvent("table_subtab_change", { mode: state.analysisMode });
    });
  });
  if (els.travelContent) {
    els.travelContent.addEventListener("change", (event) => {
      if (event.target.id !== "travelSort") return;
      state.travelSort = event.target.value;
      renderTravelSection();
      trackEvent("ranking_filter_change", { ranking: "travel", sort: state.travelSort });
    });
  }
  if (els.analysisContent) {
    els.analysisContent.addEventListener("click", (event) => {
      const openMatchButton = event.target.closest("[data-open-match]");
      if (openMatchButton?.dataset.openMatch) {
        openMatchInMatchday(openMatchButton.dataset.openMatch);
        return;
      }
      const stageJumpButton = event.target.closest("[data-bracket-stage-target]");
      if (stageJumpButton?.dataset.bracketStageTarget) {
        state.knockoutStage = stageJumpButton.dataset.bracketStageTarget;
        renderAnalysis();
        const target = els.analysisContent.querySelector(`[data-bracket-stage="${stageJumpButton.dataset.bracketStageTarget}"]`);
        target?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "start" });
      }
    });
    els.analysisContent.addEventListener("change", (event) => {
      if (event.target.id !== "playerTimingSelect") return;
      state.selectedScorer = event.target.value;
      renderAnalysis();
    });
  }
}

function init() {
  renderStaticUi();
  renderMetrics();
  renderCoverage();
  renderFilters();
  bindEvents();
  setActiveSection(state.activeSection);
  renderWeatherMap();
  renderWeatherFavorites();
  renderList();
  renderTravelSection();
  renderAnalysis();
  renderAds();
  initExperience();
  updateBackToTopVisibility();
}

init();
