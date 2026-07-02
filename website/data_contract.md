# Frontend Data Contract

## MatchCard

```ts
type MatchCardDTO = {
  matchId: string
  tournamentStage: string
  groupName?: string
  matchday?: number
  matchdayLabel?: string
  calendarDay?: number
  calendarDayLabel?: string
  localDate: string
  localTime: string
  localTimezone: string
  hostCity: string
  stadiumName: string
  stadiumCapacity?: number
  stadiumTypeBasic?: 'indoor' | 'outdoor' | 'retractable_roof' | 'unknown'
  roofAvailableBoolean?: boolean
  roofType?: string
  climateControlAvailable?: boolean
  weatherProtectionLevel?: number
  climateControlNoteDe?: string
  pitchSurfaceNoteDe?: string
  venueWeatherNoteDe?: string
  capacitySourceNote?: string
  latitude?: number
  longitude?: number
  coordinatePrecision?: string
  coordinateAccuracyM?: number
  googlePlaceId?: string
  mapsUrl?: string
  teamA: TeamBadgeDTO
  teamB: TeamBadgeDTO
  weather?: WeatherDTO
  weatherFit?: WeatherFitDTO
  timezone?: TeamComparisonDTO
  altitude?: TeamComparisonDTO
  fanProximity?: TeamComparisonDTO
  prediction?: PredictionDTO
  generatedText?: GeneratedTextDTO
  postMatchEvents?: PostMatchEventBundleDTO
  dataQualityScore: number
}
```

`matchday` ist der sportliche Gruppenspieltag (`1. Gruppenspieltag` bis `3. Gruppenspieltag`). `calendarDay` ist der operative Turniertag für Forecast-Abdeckung und tägliche Datenaktualisierung.

Reisekontext wird im Website-Datenvertrag aktuell nicht ausgespielt, solange keine bestätigten Team-Basislager und daraus ableitbaren Anreiserouten vorliegen.

Venue-Koordinaten steuern die Wetterkarte. `mapsUrl` ist der bevorzugte externe Absprung für eine präzise Google-Maps-Ansicht. `googlePlaceId` bleibt optional und sollte erst nach sauberem Venue-Audit ergänzt werden.

## TeamBadge

```ts
type TeamBadgeDTO = {
  iso2: string
  iso3: string
  name: string
  flagEmoji?: string
}
```

## Ad Placement

```ts
type AdPlacementDTO = {
  slotKey: 'matchday_top' | 'matchday_inline' | 'map_sidebar' | 'tables_top' | string
  sectionKey: string
  placementKey: string
  displayName: string
  allowedSizes?: string
  maxWidth?: number
  minHeight?: number
  deviceTargeting: 'all' | 'mobile' | 'desktop'
  priority: number
  weight: number
  creativeKey: string
  creativeType: 'native' | 'image' | 'html' | 'network_tag'
  label: string
  headline?: string
  body?: string
  callToAction?: string
  imageUrl?: string
  clickUrl?: string
  trackingPixelUrl?: string
  backgroundColor?: string
  textColor?: string
  campaignKey: string
  partnerKey?: string
}
```

Der MVP rendert bevorzugt `native`-Creatives. Drittanbieter-Scripte oder Netzwerk-Tags sollten erst nach Consent-, Datenschutz- und Performance-Prüfung aktiviert werden.

## Weather

```ts
type WeatherDTO = {
  forecastTemp?: number
  forecastHumidity?: number
  forecastWindSpeed?: number
  forecastPrecipitationProbability?: number
  forecastHeatIndex?: number
  weatherLoadScore?: number
  dataQualityScore: number
}
```

## Weather Fit

```ts
type WeatherFitDTO = {
  sourceWeatherType: 'forecast' | 'actual' | 'historical'
  weatherTempC?: number
  weatherHumidity?: number
  weatherWindSpeed?: number
  precipitationProbability?: number
  weatherLoadScore?: number
  teamA: TeamWeatherFitDTO
  teamB: TeamWeatherFitDTO
  edge: 'team_a' | 'team_b' | 'balanced' | 'unknown'
  edgeTeamIso3?: string
  edgeGap?: number
  uncertaintyLevel: 'low' | 'medium' | 'high' | 'unknown'
  explanation?: string
}

type TeamWeatherFitDTO = {
  iso3: string
  weatherFitScore?: number
  weatherFamiliarityScore?: number
  weatherToleranceScore?: number
  effectiveWeatherLoadScore?: number
  weatherFitLabel?: 'strong_fit' | 'moderate_fit' | 'neutral_fit' | 'low_fit'
}
```

## Team Comparison

```ts
type TeamComparisonDTO = {
  teamAValue?: number | string
  teamBValue?: number | string
  edge?: 'team_a' | 'team_b' | 'balanced' | 'unknown'
  dataQualityScore: number
}
```

## Prediction

```ts
type PredictionDTO = {
  predictedResultCategory: 'team_a_win' | 'draw' | 'team_b_win' | 'unknown'
  probabilityTeamAWin?: number
  probabilityDraw?: number
  probabilityTeamBWin?: number
  mainContextAdvantage?: 'team_a' | 'team_b' | 'balanced' | 'unknown'
  biggestLoadFactor?: string
  uncertaintyLevel: 'low' | 'medium' | 'high' | 'unknown'
}
```

## Generated Text

```ts
type GeneratedTextDTO = {
  language: 'de' | 'en'
  contentType: 'match_preview' | 'post_match_update'
  headline?: string
  subheadline?: string
  teaser?: string
  body?: string
  socialHook?: string
}
```

## Post-Match Events

```ts
type PostMatchEventBundleDTO = {
  teamSheets?: TeamSheetDTO[]
  appearances?: PlayerAppearanceDTO[]
  events?: MatchEventDTO[]
}

type TeamSheetDTO = {
  teamIso3: string
  formation?: string
  coachName?: string
  captainPlayerName?: string
  hydrationBreakPlanned?: boolean
}

type PlayerAppearanceDTO = {
  teamIso3: string
  playerName: string
  appearanceRole: 'starter' | 'bench' | 'unused'
  shirtNumber?: number
  positionLabel?: string
  minuteIn?: number
  minuteOut?: number
  minutesPlayed?: number
  isCaptain?: boolean
  isGoalkeeper?: boolean
}

type MatchEventDTO = {
  matchId: string
  teamIso3?: string
  beneficiaryTeamIso3?: string
  playerName?: string
  relatedPlayerName?: string
  eventType:
    | 'goal'
    | 'own_goal'
    | 'penalty_goal'
    | 'missed_penalty'
    | 'yellow_card'
    | 'red_card'
    | 'sub_in'
    | 'sub_out'
    | 'hydration_break_start'
    | 'hydration_break_end'
    | 'var_overturn'
    | 'other'
  minute: number
  stoppageMinute?: number
  period?: '1H' | '2H' | 'ET1' | 'ET2' | 'PEN' | 'unknown'
  scoreboardTeamA?: number
  scoreboardTeamB?: number
  notes?: string
}
```

## Analysis Report

```ts
type AnalysisReportDTO = {
  scopeType: 'match' | 'matchday' | 'phase' | 'tournament'
  scopeKey: string
  language: 'de' | 'en'
  title?: string
  summary?: string
  body?: string
  metrics: {
    matches: number
    avgForecastWeatherLoadScore?: number
    avgActualWeatherLoadScore?: number
    avgForecastWeatherEdgeGap?: number
    highActualWeatherLoadMatches?: number
    alignmentCounts?: Record<string, number>
  }
}
```
