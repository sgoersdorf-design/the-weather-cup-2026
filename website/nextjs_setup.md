# Next.js Setup

## Empfohlene Struktur

```text
app/
  [locale]/
    page.tsx
    matches/page.tsx
    matches/[matchId]/page.tsx
    venues/page.tsx
    teams/page.tsx
    rankings/page.tsx
    methodik/page.tsx
components/
  TeamBadge.tsx
  MatchCard.tsx
  WeatherPanel.tsx
  TravelPanel.tsx
  TimezonePanel.tsx
  AltitudePanel.tsx
  FanProximityPanel.tsx
  PredictionPanel.tsx
  VenueMap.tsx
  RankingTable.tsx
  LanguageSwitcher.tsx
  DisclaimerBox.tsx
lib/
  supabase.ts
  i18n.ts
  formatters.ts
  data-contract.ts
```

## Routen

- `/de`
- `/en`
- `/de/matches`
- `/en/matches`
- `/de/matches/[matchId]`
- `/en/matches/[matchId]`
- `/de/venues`
- `/en/venues`
- `/de/teams`
- `/en/teams`
- `/de/rankings`
- `/en/rankings`
- `/de/methodik`
- `/en/methodology`

## Environment

```bash
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
```

Keine Secret-Keys oder Service-Role-Keys im Frontend verwenden. Der Publishable Key ist fuer Browser-Apps gedacht; echte Datenrechte werden trotzdem ueber Row Level Security und Policies in Supabase abgesichert.
