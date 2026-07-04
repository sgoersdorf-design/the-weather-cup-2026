# Repository-Pfad-Regel

## Kanonischer Pfad

Für dieses Projekt ist der verbindliche lokale Hauptpfad:

```text
/Users/steffengorsdorf/Projects/wm-projekt
```

## Was das praktisch bedeutet

- Alle Codeänderungen müssen in diesem Repo erfolgen.
- Alle lokalen Builds, Refresh-Läufe und Exporte müssen von diesem Repo ausgehen.
- GitHub-Pushes und Netlify-Deploys dürfen nur aus diesem Repo ausgelöst werden.
- Launchd-/Automationsdateien müssen auf dieses Repo zeigen.
- Alte oder leere Arbeitskopien unter `Documents/...` gelten nicht mehr als Quelle der Wahrheit.

## Technische Vorkehrungen im Projekt

- `scripts/refresh_mvp.command` priorisiert automatisch den kanonischen Repo-Pfad.
- `scripts/publish_repo_update.command` priorisiert automatisch den kanonischen Repo-Pfad.
- `python.pipelines.generate_launchd_refresh_schedule` erzeugt Launchd-Konfigurationen standardmäßig für den kanonischen Repo-Pfad.

## Regel für künftige Entwicklung

Wenn ein neuer Guide, ein Skript, eine Automation, ein Build-Hinweis oder ein externer Integrationsschritt einen absoluten Projektpfad braucht, muss dort dieser Pfad verwendet werden:

```text
/Users/steffengorsdorf/Projects/wm-projekt
```

Wenn ein Schritt ohne absoluten Pfad auskommt, soll der Repo-Root relativ aus der Skriptposition oder aus Git ermittelt werden.
