const PREDICTION_STORAGE_KEY = "weatherCupPredictions";
const predictionDrafts = {};

function trackEvent(name, detail = {}) {
  const event = {
    name,
    detail,
    timestamp: new Date().toISOString(),
  };
  window.WM_ANALYTICS_EVENTS = window.WM_ANALYTICS_EVENTS || [];
  window.WM_ANALYTICS_EVENTS.push(event);
  window.dispatchEvent(new CustomEvent("weathercup:analytics", { detail: event }));
}

function localDateKey(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: USER_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const values = Object.fromEntries(parts.filter((part) => part.type !== "literal").map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function matchDateKey(match) {
  return viewerDateTime(match).key;
}

function matchTimestamp(match) {
  const value = Date.parse(match.date_utc || "");
  return Number.isNaN(value) ? Number.MAX_SAFE_INTEGER : value;
}

function matchExperienceStatus(match) {
  const rawStatus = String(match.match_status || "scheduled").toLowerCase();
  if (["live", "in_progress"].includes(rawStatus)) return "live";
  if (isFinished(match)) return "finished";
  if (matchDateKey(match) === localDateKey()) return "today";
  return "upcoming";
}

function statusLabel(status) {
  const labels = {
    live: t("statusLive"),
    today: t("statusToday"),
    upcoming: t("statusUpcoming"),
    finished: t("statusFinished"),
  };
  return labels[status] || labels.upcoming;
}

function statusBadgeMarkup(match) {
  const status = matchExperienceStatus(match);
  return `<span class="match-status status-${status}">${status === "live" ? `<i aria-hidden="true"></i>` : ""}${statusLabel(status)}</span>`;
}

function sortedByExperiencePriority(matches) {
  const priority = { live: 0, today: 1, upcoming: 2, finished: 3 };
  return [...matches].sort((a, b) => {
    const statusDifference = priority[matchExperienceStatus(a)] - priority[matchExperienceStatus(b)];
    if (statusDifference) return statusDifference;
    if (isFinished(a) && isFinished(b)) return matchTimestamp(b) - matchTimestamp(a);
    return matchTimestamp(a) - matchTimestamp(b);
  });
}

function futureMatches() {
  return sortedByExperiencePriority(source.matches.filter((match) => !isFinished(match)));
}

function todaysMatches() {
  return sortedByExperiencePriority(
    source.matches.filter((match) => matchDateKey(match) === localDateKey() && !isFinished(match))
  );
}

function finishedMatches() {
  return source.matches.filter(isFinished).sort((a, b) => matchTimestamp(b) - matchTimestamp(a));
}

function numberLabel(value, maximumFractionDigits = 0) {
  if (value === null || value === undefined || value === "" || Number.isNaN(Number(value))) return "–";
  return new Intl.NumberFormat(currentLocale(), { maximumFractionDigits }).format(Number(value));
}

function matchTravelDistance(match) {
  const values = [match.team_a_travel_distance_km, match.team_b_travel_distance_km]
    .filter((value) => value !== null && value !== undefined && !Number.isNaN(Number(value)))
    .map(Number);
  return values.length ? Math.max(...values) : null;
}

function matchAltitudeLoad(match) {
  const values = [match.team_a_altitude_load_score, match.team_b_altitude_load_score]
    .filter((value) => value !== null && value !== undefined && !Number.isNaN(Number(value)))
    .map(Number);
  return values.length ? Math.max(...values) : Number(match.elevation_m || 0) / 30;
}

function predictionLeader(match) {
  const probabilities = [
    { side: "a", value: Number(match.probability_team_a_win) },
    { side: "draw", value: Number(match.probability_draw) },
    { side: "b", value: Number(match.probability_team_b_win) },
  ].filter((item) => Number.isFinite(item.value));
  return probabilities.sort((a, b) => b.value - a.value)[0] || null;
}

function factorLabel(value) {
  const labels = state.lang === "en"
    ? {
        weather_load: "Weather Load",
        weather_load_gap: "Weather Load",
        weather_fit_gap: "Weather Fit",
        altitude_load: "Altitude",
        altitude_load_gap: "Altitude",
        circadian_load_gap: "Time zone",
        fan_proximity_gap: "Venue proximity",
        travel_recovery_gap: "Travel & recovery",
        team_strength_gap: "Basic team strength",
      }
    : {
        weather_load: "Weather Load",
        weather_load_gap: "Weather Load",
        weather_fit_gap: "Weather Fit",
        altitude_load: "Höhenlage",
        altitude_load_gap: "Höhenlage",
        circadian_load_gap: "Zeitzone",
        fan_proximity_gap: "Standortnähe",
        travel_recovery_gap: "Reise & Erholung",
        team_strength_gap: "Basis-Teamstärke",
      };
  return labels[value] || (state.lang === "en" ? "Match context" : "Spielkontext");
}

function topContextSignal(match) {
  const factor = factorLabel(match.biggest_load_factor);
  const leader = weatherLeaderSide(match);
  const weatherGap = Number(match.weather_fit_edge_gap || 0);
  if (leader && weatherGap >= 4) {
    return `${t("weatherEdge")}: ${teamLabel(match, leader)} +${numberLabel(weatherGap, 1)}`;
  }
  if (factor.includes("Höhe") || factor.includes("Altitude")) {
    return `${factor}: ${numberLabel(match.elevation_m)} m`;
  }
  return `${factor}: ${score(match.weather_load_score)}/100`;
}

function predictionMetricLabel(match) {
  const leader = predictionLeader(match);
  if (!leader) return "–";
  if (leader.side === "draw") return `${state.lang === "en" ? "Draw" : "Remis"} ${percent(leader.value)}`;
  return `${match[`team_${leader.side}_iso3`]} ${percent(leader.value)}`;
}

function quickMatchCard(match, options = {}) {
  const status = matchExperienceStatus(match);
  const selected = options.selected ? " is-selected" : "";
  const emphasis = options.emphasis ? " is-emphasis" : "";
  const compact = options.compact ? " is-compact" : "";
  const viewer = viewerDateTime(match);
  const host = hostDateTime(match);
  const travel = matchTravelDistance(match);
  const actionLabel = status === "live" ? t("liveContext") : t("viewGame");
  const scoreA = isFinished(match) ? `<b class="quick-score">${match.result_team_a}</b>` : "";
  const scoreB = isFinished(match) ? `<b class="quick-score">${match.result_team_b}</b>` : "";
  return `<article class="quick-match-card status-${status}${selected}${emphasis}${compact}" data-match-id="${match.match_id}" tabindex="0">
    <header class="quick-card-head">
      <div>${statusBadgeMarkup(match)}<span class="quick-match-id">${match.match_id}</span></div>
      <div class="quick-kickoff"><b>${viewer.time}</b><span>${viewer.shortDate} · ${t("yourTime")}</span></div>
    </header>
    <div class="quick-teams">
      <div><span class="quick-flag">${match.team_a_flag || ""}</span><b>${escapeHtml(teamName(match, "a"))}</b><small>${match.team_a_iso3}</small>${scoreA}</div>
      <div><span class="quick-flag">${match.team_b_flag || ""}</span><b>${escapeHtml(teamName(match, "b"))}</b><small>${match.team_b_iso3}</small>${scoreB}</div>
    </div>
    <div class="quick-venue"><b>${escapeHtml(match.host_city || "")}</b><span>${escapeHtml(match.stadium_name || "")} · ${t("venueTime")} ${host.time}</span></div>
    <div class="context-signal"><span>${t("topContextSignal")}</span><b>${topContextSignal(match)}</b></div>
    <div class="quick-metrics">
      <div><span>${t("weatherShort")}</span><b>${score(match.weather_load_score)}/100</b></div>
      <div><span>${t("travelShort")}</span><b>${travel === null ? t("noPreviousTravel") : `${numberLabel(travel)} km`}</b></div>
      <div><span>${t("predictionShort")}</span><b>${predictionMetricLabel(match)}</b></div>
    </div>
    <div class="quick-card-meta"><span>${groupMatchdayLabel(match.matchday)} · ${t("group")} ${match.group_name || "–"}</span><span>${edgeLabel(match)}</span></div>
    <footer class="quick-card-actions">
      <button class="primary-action" type="button" data-open-match="${match.match_id}">${actionLabel}</button>
      ${!isFinished(match) ? `<button class="secondary-action" type="button" data-predict-match="${match.match_id}">${t("submitTip")}</button>` : ""}
    </footer>
  </article>`;
}

function teamContextFacts(match, side) {
  const travel = match[`team_${side}_travel_distance_km`];
  const recoveryHours = match[`team_${side}_recovery_hours`];
  const timezone = match[`team_${side}_circadian_load_score`];
  const altitude = match[`team_${side}_altitude_load_score`];
  const fan = match[`team_${side}_fan_proximity_score`];
  const strength = match[`team_${side}_strength_score`];
  return `<article class="team-context-card">
    <h4>${teamLabel(match, side)} <small>${match[`team_${side}_iso3`]}</small></h4>
    <dl>
      <div><dt>${t("travelDistance")}</dt><dd>${travel === null || travel === undefined ? t("noPreviousTravel") : `${numberLabel(travel)} km`}</dd></div>
      <div><dt>${t("recoveryTime")}</dt><dd>${recoveryHours === null || recoveryHours === undefined ? t("dataFollows") : `${numberLabel(recoveryHours, 1)} h`}</dd></div>
      <div><dt>${t("timezoneLoad")}</dt><dd>${score(timezone)}/100</dd></div>
      <div><dt>${t("altitudeLoad")}</dt><dd>${score(altitude)}/100</dd></div>
      <div><dt>${t("fanProximity")}</dt><dd>${score(fan)}/100</dd></div>
      <div><dt>${t("teamStrength")}</dt><dd>${strength === null || strength === undefined ? t("dataFollows") : `${score(strength)}/100`}</dd></div>
    </dl>
  </article>`;
}

function forecastFactsMarkup(match, actual = false) {
  const prefix = actual ? "actual" : "forecast";
  const temperature = match[`${prefix}_temp`];
  if (temperature === null || temperature === undefined) {
    return `<div class="active-empty">${actual ? t("actualWeatherPending") : t("forecastHelpfulEmpty")}</div>`;
  }
  return `<div class="weather-fact-row">
    <div><span>Temp</span><b>${valueOrDash(temperature, "°C")}</b></div>
    <div><span>${t("humidityShort")}</span><b>${valueOrDash(match[`${prefix}_humidity`], "%")}</b></div>
    <div><span>Wind</span><b>${valueOrDash(match[`${prefix}_wind_speed`], " km/h")}</b></div>
    <div><span>${actual ? t("actualWeatherLabel") : t("weatherLoad")}</span><b>${actual ? valueOrDash(match.actual_precipitation, " mm") : `${score(match.weather_load_score)}/100`}</b></div>
  </div>`;
}

function weatherCoverageItems(match) {
  const items = [];
  if (match.host_city) items.push(match.host_city);
  if (match.stadium_name) items.push(match.stadium_name);
  if (match.elevation_m !== null && match.elevation_m !== undefined) items.push(`${numberLabel(match.elevation_m)} m`);
  const travel = matchTravelDistance(match);
  if (travel !== null && travel !== undefined) items.push(`${numberLabel(travel)} km ${t("travelShort")}`);
  return items;
}

function weatherStatusCard(title, copy, tone = "pending") {
  return `<article class="weather-status-card is-${tone}">
    <span>${escapeHtml(title)}</span>
    <p>${escapeHtml(copy)}</p>
  </article>`;
}

function weatherCoverageMarkup(match) {
  const available = weatherCoverageItems(match);
  const forecastReady = hasForecast(match);
  const actualReady = match.actual_temp !== null && match.actual_temp !== undefined;
  const forecastBlock = forecastReady
    ? `<section class="weather-status-section">
        <h3>${t("forecastWeather")}</h3>
        ${forecastFactsMarkup(match)}
      </section>`
    : "";
  const actualBlock = actualReady
    ? `<section class="weather-status-section">
        <h3>${t("actualWeatherLabel")}</h3>
        ${forecastFactsMarkup(match, true)}
      </section>`
    : "";

  return `<div class="weather-coverage-panel">
    <div class="weather-coverage-head">
      <div>
        <span>${t("weatherCoverageTitle")}</span>
        <b>${forecastReady ? t("forecastWeather") : t("forecastHelpfulEmpty")}</b>
      </div>
      ${available.length ? `<div class="weather-coverage-tags">${available.map((item) => `<i>${escapeHtml(item)}</i>`).join("")}</div>` : ""}
    </div>
    ${forecastBlock}
    ${actualBlock}
    ${!forecastReady || !actualReady ? `<div class="weather-status-grid">
      ${!forecastReady ? weatherStatusCard(t("forecastWeather"), t("weatherCoverageForecastSoon"), "soon") : ""}
      ${!actualReady ? weatherStatusCard(t("actualWeatherLabel"), t("weatherCoverageActualSoon"), "pending") : ""}
      ${weatherStatusCard(t("historicalWeather"), t("weatherCoverageHistoricalSoon"), "muted")}
    </div>` : ""}
    ${available.length ? `<div class="weather-coverage-available">
      <span>${t("weatherCoverageAvailable")}</span>
      <div>${available.map((item) => `<b>${escapeHtml(item)}</b>`).join("")}</div>
    </div>` : ""}
  </div>`;
}

function probabilityBarsMarkup(match) {
  const items = [
    [match.team_a_iso3, match.probability_team_a_win],
    ["X", match.probability_draw],
    [match.team_b_iso3, match.probability_team_b_win],
  ];
  return `<div class="probability-bars">${items.map(([label, value]) => `<div><span>${label}</span><i><b style="width:${Math.max(0, Math.min(100, Number(value || 0)))}%"></b></i><strong>${percent(value)}</strong></div>`).join("")}</div>`;
}

function weatherBalanceMarkup(match) {
  if (!isFinished(match)) return "";
  const balance = weatherBalanceResult(match);
  const labels = {
    confirmed: t("weatherConfirmed"),
    not_confirmed: t("weatherNotConfirmed"),
    balanced: t("weatherBalancedResult"),
  };
  return `<div class="weather-balance-verdict is-${balance.status}">
    <span>${t("weatherBalance")}</span>
    <b>${labels[balance.status] || t("weatherBalancedResult")}</b>
    ${balance.leader ? `<small>${teamLabel(match, balance.leader)} · ${edgeLabel(match)}</small>` : ""}
  </div>`;
}

function expandedMatchDetailsMarkup(match) {
  const viewer = viewerDateTime(match);
  const host = hostDateTime(match);
  const storedPrediction = loadPredictions()[match.match_id];
  return `<div class="expanded-match-head">
      <div>
        <p class="eyebrow">${match.match_id} · ${groupMatchdayLabel(match.matchday)} · ${t("group")} ${match.group_name || "–"}</p>
        <h2>${teamLabel(match, "a")} vs. ${teamLabel(match, "b")}</h2>
      </div>
      ${statusBadgeMarkup(match)}
    </div>
    ${finalResultMarkup(match)}
    ${weatherBalanceMarkup(match)}
    <details class="detail-accordion" open>
      <summary>${t("detailOverview")}</summary>
      <div class="accordion-content">
        <div class="kickoff-panel" aria-label="${t("kickoffTimes")}">
          <div class="kickoff-item is-primary"><span>${t("yourTime")}</span><b>${viewer.detailLabel}</b></div>
          <div class="kickoff-item"><span>${t("venueTime")} · ${escapeHtml(match.host_city || "")}</span><b>${host.detailLabel}</b></div>
        </div>
        <div class="detail-grid">
          <div class="fact"><span>${t("weatherFit")}</span><b>${edgeLabel(match)}</b></div>
          <div class="fact"><span>${t("weatherLoad")}</span><b>${score(match.weather_load_score)}/100</b></div>
          <div class="fact"><span>${t("elevation")}</span><b>${valueOrDash(match.elevation_m, " m")}</b></div>
          <div class="fact"><span>${t("venue")}</span><b>${escapeHtml(match.stadium_name || "–")}</b></div>
        </div>
        <p class="copy">${weatherNarrative(match)}</p>
      </div>
    </details>
    <details class="detail-accordion">
      <summary>${t("detailWeather")}</summary>
      <div class="accordion-content">
        ${weatherCoverageMarkup(match)}
      </div>
    </details>
    <details class="detail-accordion">
      <summary>${t("detailVenue")}</summary>
      <div class="accordion-content">${venueInfoMarkup(match)}</div>
    </details>
    <details class="detail-accordion">
      <summary>${t("detailPrediction")}</summary>
      <div class="accordion-content">
        ${probabilityBarsMarkup(match)}
        <div class="prediction-method-note"><b>${factorLabel(match.biggest_load_factor)}</b><span>${t("modelMethodNote")}</span></div>
        ${!isFinished(match) || storedPrediction?.result_pick ? `<button class="secondary-action" type="button" data-predict-match="${match.match_id}">${isFinished(match) ? t("viewTip") : t("submitTip")}</button>` : ""}
      </div>
    </details>`;
}

function loadPredictions() {
  try {
    const stored = JSON.parse(localStorage.getItem(PREDICTION_STORAGE_KEY) || "{}");
    return stored && typeof stored === "object" ? stored : {};
  } catch {
    return {};
  }
}

function savePrediction(matchId, prediction) {
  const predictions = loadPredictions();
  predictions[matchId] = {
    ...(predictions[matchId] || {}),
    result_pick: prediction.result_pick,
    context_pick: prediction.context_pick,
    created_at: predictions[matchId]?.created_at || new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  localStorage.setItem(PREDICTION_STORAGE_KEY, JSON.stringify(predictions));
  trackEvent("prediction_submit", { match_id: matchId });
}

function resultCategory(match) {
  const winner = resultWinnerSide(match);
  if (winner === "a") return "team_a_win";
  if (winner === "b") return "team_b_win";
  if (winner === "draw") return "draw";
  return null;
}

function predictionOutcome(match, prediction) {
  if (!prediction?.result_pick) return "";
  if (!isFinished(match)) return t("predictionPending");
  return prediction.result_pick === resultCategory(match) ? t("predictionCorrect") : t("predictionWrong");
}

function predictionDialogMarkup(match, options = {}) {
  const storedPrediction = loadPredictions()[match.match_id] || {};
  const prediction = predictionDrafts[match.match_id] || storedPrediction;
  const outcome = predictionOutcome(match, storedPrediction);
  const complete = Boolean(prediction.result_pick && prediction.context_pick);
  const hasStoredPrediction = Boolean(storedPrediction.result_pick && storedPrediction.context_pick);
  return `<div class="prediction-dialog-head">
      <div><p class="eyebrow">${match.match_id}</p><h2 id="predictionDialogTitle">${t("predictionDialogTitle")}</h2></div>
      <button class="dialog-close" type="button" data-close-prediction aria-label="${t("close")}">×</button>
    </div>
    <div class="prediction-match-label">${teamLabel(match, "a")} <span>vs.</span> ${teamLabel(match, "b")}</div>
    <fieldset>
      <legend>${t("predictionQuestion")}</legend>
      <div class="prediction-options three">
        <button class="${prediction.result_pick === "team_a_win" ? "is-selected" : ""}" type="button" data-prediction-field="result_pick" data-prediction-value="team_a_win"${isFinished(match) ? " disabled" : ""}>${match.team_a_iso3}</button>
        <button class="${prediction.result_pick === "draw" ? "is-selected" : ""}" type="button" data-prediction-field="result_pick" data-prediction-value="draw"${isFinished(match) ? " disabled" : ""}>X</button>
        <button class="${prediction.result_pick === "team_b_win" ? "is-selected" : ""}" type="button" data-prediction-field="result_pick" data-prediction-value="team_b_win"${isFinished(match) ? " disabled" : ""}>${match.team_b_iso3}</button>
      </div>
    </fieldset>
    <fieldset>
      <legend>${t("contextQuestion")}</legend>
      <div class="prediction-options two">
        <button class="${prediction.context_pick === "context_matters" ? "is-selected" : ""}" type="button" data-prediction-field="context_pick" data-prediction-value="context_matters"${isFinished(match) ? " disabled" : ""}>${t("contextMatters")}</button>
        <button class="${prediction.context_pick === "context_low" ? "is-selected" : ""}" type="button" data-prediction-field="context_pick" data-prediction-value="context_low"${isFinished(match) ? " disabled" : ""}>${t("contextLow")}</button>
      </div>
    </fieldset>
    ${!isFinished(match) ? `<button class="primary-action prediction-confirm" type="button" data-confirm-prediction${complete ? "" : " disabled"}>${hasStoredPrediction ? t("predictionUpdate") : t("predictionConfirm")}</button>` : ""}
    ${!complete && !isFinished(match) ? `<p class="prediction-helper">${t("predictionChooseBoth")}</p>` : ""}
    ${options.confirmed ? `<p class="prediction-feedback is-confirmed">✓ ${t("predictionSavedStrong")}</p>` : ""}
    ${isFinished(match) && storedPrediction.result_pick ? `<p class="prediction-feedback">${outcome}</p>` : ""}
    <p class="prediction-privacy">${t("localOnlyNote")}</p>`;
}

function openPredictionDialog(matchId) {
  const match = findMatch(matchId);
  if (!match || !els.predictionDialog || !els.predictionDialogContent) return;
  els.predictionDialog.dataset.matchId = matchId;
  predictionDrafts[matchId] = { ...(loadPredictions()[matchId] || {}) };
  els.predictionDialogContent.innerHTML = predictionDialogMarkup(match);
  if (!els.predictionDialog.open) els.predictionDialog.showModal();
  if (isFinished(match) && loadPredictions()[matchId]?.result_pick) {
    trackEvent("prediction_result_view", { match_id: matchId });
  }
}

function predictionScoreSummary() {
  const predictions = loadPredictions();
  const evaluated = source.matches.filter((match) => isFinished(match) && predictions[match.match_id]?.result_pick);
  const correct = evaluated.filter((match) => predictions[match.match_id].result_pick === resultCategory(match)).length;
  return { total: evaluated.length, correct };
}

function todayContextItems() {
  const today = todaysMatches();
  const basis = today.length ? today : futureMatches().slice(0, 6);
  const next = futureMatches()[0];
  const highestLoad = [...basis].sort((a, b) => Number(b.weather_load_score || -1) - Number(a.weather_load_score || -1))[0];
  const biggestEdge = [...basis].sort((a, b) => Number(b.weather_fit_edge_gap || -1) - Number(a.weather_fit_edge_gap || -1))[0];
  const highestTravel = [...basis].sort((a, b) => Number(matchTravelDistance(b) || -1) - Number(matchTravelDistance(a) || -1))[0];
  const highestAltitude = [...basis].sort((a, b) => matchAltitudeLoad(b) - matchAltitudeLoad(a))[0];
  const liveCount = today.filter((match) => matchExperienceStatus(match) === "live").length;
  const items = [
    { label: t("todayMatches"), value: String(today.length || basis.length), match: today[0] || next },
  ];
  if (liveCount) items.push({ label: t("liveMatches"), value: String(liveCount), match: today.find((match) => matchExperienceStatus(match) === "live") });
  if (next) items.push({ label: t("nextMatch"), value: `${next.team_a_iso3} vs. ${next.team_b_iso3} · ${viewerDateTime(next).time}`, match: next });
  if (highestLoad) items.push({ label: t("highestLoad"), value: `${highestLoad.host_city} · ${score(highestLoad.weather_load_score)}/100`, match: highestLoad });
  if (biggestEdge && Number(biggestEdge.weather_fit_edge_gap || 0) >= 4) items.push({ label: t("biggestEdge"), value: edgeLabel(biggestEdge), match: biggestEdge });
  if (highestTravel && Number(matchTravelDistance(highestTravel)) > 0) items.push({ label: t("highestTravel"), value: `${numberLabel(matchTravelDistance(highestTravel))} km`, match: highestTravel });
  if (highestAltitude) items.push({ label: t("highestAltitude"), value: `${highestAltitude.host_city} · ${numberLabel(highestAltitude.elevation_m)} m`, match: highestAltitude });
  return { today, basis, items };
}

function sectionHeading(title, copy = "", action = "") {
  return `<div class="home-section-head"><div><h2>${title}</h2>${copy ? `<p>${copy}</p>` : ""}</div>${action}</div>`;
}

function realityCheckCard(match) {
  const weatherLeader = weatherLeaderSide(match);
  const resultWinner = resultWinnerSide(match);
  const weatherText = weatherLeader
    ? `${state.lang === "en" ? "Weather fit favoured" : "Der Wetterfit lag bei"} ${teamLabel(match, weatherLeader)}.`
    : `${state.lang === "en" ? "Weather fit was balanced." : "Der Wetterfit war ausgeglichen."}`;
  const resultText = resultWinner === "draw"
    ? (state.lang === "en" ? "The match ended level." : "Die Partie endete remis.")
    : `${state.lang === "en" ? "The result went to" : "Das Ergebnis ging an"} ${teamLabel(match, resultWinner)}.`;
  return `<article class="reality-card">
    <header><span>${t("realityCheck")}</span><b>${match.match_id}</b></header>
    <h3>${teamName(match, "a")} <strong>${match.result_team_a}:${match.result_team_b}</strong> ${teamName(match, "b")}</h3>
    <p>${weatherText} ${resultText} ${t("contextNotGuarantee")}</p>
    ${weatherBalanceMarkup(match)}
    ${match.actual_temp === null || match.actual_temp === undefined ? "" : `<div class="reality-signals"><div><span>${t("forecastVsActual")}</span><b>${match.forecast_temp}° → ${match.actual_temp}°</b></div></div>`}
    <button class="secondary-action" type="button" data-open-match="${match.match_id}">${t("viewGame")}</button>
  </article>`;
}

function homeFavoritesPreview() {
  const rows = futureMatches().map(weatherAdvantage).filter(Boolean).sort((a, b) => b.gap - a.gap).slice(0, 3);
  if (!rows.length) return `<div class="active-empty">${t("favoritesEmpty")}</div>`;
  return `<div class="compact-ranking">${rows.map((item, index) => `<button type="button" data-open-match="${item.match.match_id}"><span>#${index + 1}</span><b>${teamLabel(item.match, item.leaderSide)}</b><small>+${numberLabel(item.gap, 1)} · ${item.match.team_a_iso3} vs. ${item.match.team_b_iso3}</small></button>`).join("")}</div>`;
}

function homeTravelPreview() {
  const rows = teamTravelRanking().sort((a, b) => b.totalDistanceKm - a.totalDistanceKm).slice(0, 3);
  if (!rows.length) return `<div class="active-empty">${t("travelNoData")}</div>`;
  return `<div class="compact-ranking">${rows.map((team, index) => `<button type="button" data-section-jump="travel"><span>#${index + 1}</span><b>${team.flag} ${escapeHtml(travelTeamName(team))}</b><small>${travelDistanceLabel(team.totalDistanceKm)} · ${team.uniqueCities} ${t("travelCities")}</small></button>`).join("")}</div>`;
}

function homeVenuePreview() {
  const venues = buildVenueWeather().slice(0, 3);
  if (!venues.length) return `<div class="active-empty">${t("mapNoVenue")}</div>`;
  return `<div class="venue-preview-grid">${venues.map((venue) => `<button type="button" data-home-venue="${escapeAttr(venue.key)}"><span class="load-dot ${venue.loadClass}"></span><b>${escapeHtml(venue.host_city)}</b><small>${score(venue.avgLoad)}/100 · ${valueOrDash(venue.avgTemp, "°C")}</small></button>`).join("")}</div>`;
}

function teamDisplayNameByIso(iso3) {
  const match = source.matches.find((item) => item.team_a_iso3 === iso3 || item.team_b_iso3 === iso3);
  if (!match) return iso3;
  const side = match.team_a_iso3 === iso3 ? "a" : "b";
  return teamName(match, side);
}

function homeTablePreview() {
  const todayGroups = [...new Set(todaysMatches().map((match) => match.group_name).filter(Boolean))];
  const group = todayGroups[0] || futureMatches()[0]?.group_name || Object.keys(source.standings || {})[0];
  const table = source.standings?.[group] || [];
  if (!table.length) return `<div class="active-empty">${t("standingsEmpty")}</div>`;
  return `<div class="mini-standing"><h3>${t("group")} ${group}</h3>${table.map((team, index) => `<div><span>${index + 1}</span><b>${team.flag || ""} ${escapeHtml(teamDisplayNameByIso(team.iso3))}</b><small>${team.played} ${t("playedShort")} · ${team.points} Pts</small></div>`).join("")}</div>`;
}

function renderHeroSignal() {
  if (!els.heroSignal) return;
  const context = todayContextItems();
  const next = futureMatches()[0];
  const tips = predictionScoreSummary();
  const parts = [];
  if (context.today.length) parts.push(`<span><b>${context.today.length}</b> ${t("todayMatches")}</span>`);
  else if (next) parts.push(`<span>${t("nextMatch")}: <b>${next.team_a_iso3} vs. ${next.team_b_iso3}</b> · ${viewerDateTime(next).shortLabel}</span>`);
  const topLoad = context.basis.sort((a, b) => Number(b.weather_load_score || 0) - Number(a.weather_load_score || 0))[0];
  if (topLoad) parts.push(`<span>${t("highestLoad")}: <b>${topLoad.host_city} ${score(topLoad.weather_load_score)}/100</b></span>`);
  if (tips.total) parts.push(`<span>${t("tipScore")}: <b>${tips.correct}/${tips.total}</b></span>`);
  els.heroSignal.innerHTML = parts.join("");
}

function renderHomeDashboard() {
  if (!els.homeDashboard) return;
  const context = todayContextItems();
  const next = futureMatches();
  const nextUp = next.slice(0, 4);
  const upcoming = next.slice(4, 10);
  const topContext = [...next.slice(0, 14)].sort((a, b) => {
    const scoreA = Number(a.weather_load_score || 0) + Number(a.weather_fit_edge_gap || 0) * 1.8 + matchAltitudeLoad(a) * 0.25;
    const scoreB = Number(b.weather_load_score || 0) + Number(b.weather_fit_edge_gap || 0) * 1.8 + matchAltitudeLoad(b) * 0.25;
    return scoreB - scoreA;
  })[0];
  const finished = finishedMatches().slice(0, 3);
  els.homeDashboard.innerHTML = `
    <section class="today-context-section" id="todayContext">
      ${sectionHeading(t("todayContext"))}
      ${!context.today.length ? `<div class="today-fallback">${t("todayNoMatches")}</div>` : ""}
      <div class="today-context-strip">${context.items.map((item) => `<button type="button" data-context-match="${item.match?.match_id || ""}"><span>${item.label}</span><b>${item.value}</b></button>`).join("")}</div>
    </section>
    <section class="home-module next-up-module" id="nextUp">
      ${sectionHeading(t("nextUp"), t("nextUpIntro"), `<button class="text-action" type="button" data-section-jump="matches">${t("allUpcoming")}</button>`)}
      <div class="next-up-carousel">${nextUp.map((match, index) => quickMatchCard(match, { compact: true, emphasis: index === 0 })).join("")}</div>
    </section>
    ${topContext ? `<section class="home-module top-context-module">${sectionHeading(t("topContextMatch"))}<div class="top-context-layout">${quickMatchCard(topContext, { emphasis: true })}<div class="top-context-explainer"><span>${t("topContextSignal")}</span><b>${topContextSignal(topContext)}</b><p>${t("methodologyBody")}</p></div></div></section>` : ""}
    ${upcoming.length ? `<section class="home-module">${sectionHeading(t("upcomingMatches"))}<div class="upcoming-grid">${upcoming.map((match) => quickMatchCard(match, { compact: true })).join("")}</div></section>` : ""}
    <section class="home-module reality-module">
      ${sectionHeading(t("realityCheck"), t("realityCheckIntro"))}
      ${finished.length ? `<div class="reality-grid">${finished.map(realityCheckCard).join("")}</div>` : `<div class="active-empty">${t("noFinishedMatches")}</div>`}
    </section>
    <section class="home-preview-grid">
      <article class="home-preview-panel">${sectionHeading(t("favoritesPreview"), "", `<button class="text-action" type="button" data-section-jump="favorites">${t("viewAll")}</button>`)}${homeFavoritesPreview()}</article>
      <article class="home-preview-panel">${sectionHeading(t("travelPreview"), "", `<button class="text-action" type="button" data-section-jump="travel">${t("viewAll")}</button>`)}${homeTravelPreview()}</article>
    </section>
    <section class="home-preview-grid">
      <article class="home-preview-panel">${sectionHeading(t("venuePreview"), "", `<button class="text-action" type="button" data-section-jump="map">${t("viewAll")}</button>`)}${homeVenuePreview()}</article>
      <article class="home-preview-panel">${sectionHeading(t("tablePreview"), "", `<button class="text-action" type="button" data-section-jump="analysis">${t("viewAll")}</button>`)}${homeTablePreview()}</article>
    </section>
    <section class="methodology-box">
      <div><p class="eyebrow">${t("methodologyEyebrow")}</p><h2>${t("methodologyTitle")}</h2><p>${t("methodologyBody")}</p></div>
      <button class="secondary-action" type="button" data-section-jump="faq">${t("openFaq")}</button>
    </section>`;
}

function renderVenueHighlights(venues) {
  if (!els.venueHighlights) return;
  const todayVenueKeys = new Set(todaysMatches().map(venueKey));
  const highlighted = [...venues]
    .sort((a, b) => Number(todayVenueKeys.has(b.key)) - Number(todayVenueKeys.has(a.key)) || Number(b.avgLoad || 0) - Number(a.avgLoad || 0))
    .slice(0, 5);
  els.venueHighlights.innerHTML = highlighted.map((venue) => `<button type="button" data-venue-highlight="${escapeAttr(venue.key)}" class="${venue.key === state.selectedVenueKey ? "is-selected" : ""}"><span class="load-dot ${venue.loadClass}"></span><b>${escapeHtml(venue.host_city)}</b><small>${score(venue.avgLoad)}/100 · ${valueOrDash(venue.avgTemp, "°C")}</small></button>`).join("");
  els.mapViewButtons.forEach((button) => button.classList.toggle("is-active", button.dataset.mapView === state.mapView));
  document.querySelector(".weather-map-layout")?.classList.toggle("show-map", state.mapView === "map");
}

function groupContextOutlook(group) {
  const matches = source.matches.filter((match) => match.group_name === group);
  const next = sortedByExperiencePriority(matches.filter((match) => !isFinished(match)))[0];
  const highestLoad = [...matches].sort((a, b) => Number(b.weather_load_score || -1) - Number(a.weather_load_score || -1))[0];
  const highestTravel = [...matches].sort((a, b) => Number(matchTravelDistance(b) || -1) - Number(matchTravelDistance(a) || -1))[0];
  const fits = [];
  matches.forEach((match) => ["a", "b"].forEach((side) => {
    const fit = Number(match[`team_${side}_weather_fit_score`]);
    if (Number.isFinite(fit)) fits.push({ match, side, fit });
  }));
  const bestFit = fits.sort((a, b) => b.fit - a.fit)[0];
  return `<div class="group-outlook"><span>${t("contextOutlook")}</span><div>
    <p><small>${t("nextGroupMatch")}</small><b>${next ? `${next.team_a_iso3} vs. ${next.team_b_iso3} · ${viewerDateTime(next).shortLabel}` : t("dataFollows")}</b></p>
    <p><small>${t("groupWeatherLoad")}</small><b>${highestLoad ? `${highestLoad.host_city} · ${score(highestLoad.weather_load_score)}/100` : t("dataFollows")}</b></p>
    <p><small>${t("groupTravelLoad")}</small><b>${highestTravel && matchTravelDistance(highestTravel) !== null ? `${numberLabel(matchTravelDistance(highestTravel))} km` : t("noPreviousTravel")}</b></p>
    <p><small>${t("bestGroupFit")}</small><b>${bestFit ? `${teamLabel(bestFit.match, bestFit.side)} · ${score(bestFit.fit)}/100` : t("dataFollows")}</b></p>
  </div></div>`;
}

const KNOCKOUT_STAGE_ORDER = ["round_of_32", "round_of_16", "quarterfinals", "semifinals", "final"];
const KNOCKOUT_PARENT_MATCHES = {
  89: [73, 75],
  90: [74, 77],
  91: [76, 78],
  92: [79, 80],
  93: [83, 84],
  94: [81, 82],
  95: [86, 88],
  96: [85, 87],
  97: [89, 90],
  98: [91, 92],
  99: [93, 94],
  100: [95, 96],
  101: [97, 98],
  102: [99, 100],
  103: [101, 102],
  104: [101, 102],
};

function groupStandingKeys(standings) {
  return Object.keys(standings)
    .filter((group) => /^[A-L]$/.test(String(group)))
    .sort((a, b) => a.localeCompare(b, "en"));
}

function knockoutMatches() {
  return source.matches.filter((match) => String(match.tournament_stage || "").toLowerCase() !== "group_stage");
}

function knockoutStageMatches(stage) {
  return knockoutMatches()
    .filter((match) => match.tournament_stage === stage)
    .sort((a, b) => matchTimestamp(a) - matchTimestamp(b) || String(a.match_id).localeCompare(String(b.match_id), "en"));
}

function knockoutStageSummary(stage) {
  const matches = knockoutStageMatches(stage);
  const completed = matches.filter(isFinished).length;
  return { stage, matches, completed, remaining: matches.length - completed };
}

function knockoutFocusStage() {
  const summaries = KNOCKOUT_STAGE_ORDER.map(knockoutStageSummary).filter((summary) => summary.matches.length);
  return summaries.find((summary) => summary.remaining > 0)?.stage || summaries[summaries.length - 1]?.stage || null;
}

function knockoutReferenceInfo(code) {
  const value = String(code || "");
  const matchNumber = value.match(/^([WL])(\d{2,3})$/);
  if (!matchNumber) return null;
  const [, resultKey, rawId] = matchNumber;
  return {
    code: value,
    matchId: `M${rawId}`,
    kind: resultKey === "W" ? "winner" : "loser",
    label: resultKey === "W" ? t("standingsBracketWinnerOf") : t("standingsBracketLoserOf"),
  };
}

function knockoutSlotInfo(match, side) {
  const code = String(match[`team_${side}_iso3`] || "");
  const reference = knockoutReferenceInfo(code);
  if (reference) {
    return {
      flag: "",
      name: `${reference.label} ${reference.matchId}`,
      meta: `${t("standingsBracketFrom")} ${reference.matchId}`,
      placeholder: true,
      iso3: "",
    };
  }
  return {
    flag: match[`team_${side}_flag`] || "",
    name: teamName(match, side),
    meta: displayIso3(match[`team_${side}_iso3`]),
    placeholder: false,
    iso3: String(match[`team_${side}_iso3`] || ""),
  };
}

function inferredResolvedSide(match) {
  if (!isFinished(match)) return null;
  const scoreA = Number(match.result_team_a);
  const scoreB = Number(match.result_team_b);
  if (Number.isFinite(scoreA) && Number.isFinite(scoreB) && scoreA !== scoreB) {
    return scoreA > scoreB ? "a" : "b";
  }
  const currentMatchNumber = Number(String(match.match_id || "").replace(/\D/g, ""));
  if (!Number.isFinite(currentMatchNumber)) return null;
  const downstream = knockoutMatches().find((candidate) => candidate.tournament_stage !== "third_place" && (() => {
    const parentIds = KNOCKOUT_PARENT_MATCHES[Number(String(candidate.match_id || "").replace(/\D/g, ""))] || [];
    return parentIds.includes(currentMatchNumber);
  })());
  if (!downstream) return null;
  const parentIds = KNOCKOUT_PARENT_MATCHES[Number(String(downstream.match_id || "").replace(/\D/g, ""))] || [];
  const slotIndex = parentIds.indexOf(currentMatchNumber);
  if (slotIndex === -1) return null;
  const downstreamSide = slotIndex === 0 ? "a" : "b";
  const resolvedIso = String(downstream[`team_${downstreamSide}_iso3`] || "");
  if (!resolvedIso || knockoutReferenceInfo(resolvedIso)) return null;
  if (resolvedIso === String(match.team_a_iso3 || "")) return "a";
  if (resolvedIso === String(match.team_b_iso3 || "")) return "b";
  return null;
}

function knockoutStageButton(summary, activeStage) {
  const active = summary.stage === activeStage ? " is-active" : "";
  return `<button class="knockout-stage-button${active}" type="button" data-bracket-stage-target="${summary.stage}" aria-label="${t("standingsBubbleHint")}">
    <span>${phaseLabel(summary.stage)}</span>
    <b>${summary.completed}/${summary.matches.length}</b>
  </button>`;
}

function renderBestThirdRace(standings) {
  const rows = groupStandingKeys(standings)
    .map((group) => ({ ...standings[group][2], group }))
    .filter((row) => row && row.iso3)
    .sort((a, b) => (
      Number(b.points || 0) - Number(a.points || 0)
      || Number(b.goal_difference || 0) - Number(a.goal_difference || 0)
      || Number(b.goals_for || 0) - Number(a.goals_for || 0)
      || teamDisplayNameByIso(a.iso3).localeCompare(teamDisplayNameByIso(b.iso3), currentLocale())
    ));
  if (!rows.length) return "";
  return `<section class="standings-panel standings-best-third">
    <div class="standings-panel-head">
      <div>
        <p class="eyebrow">${t("standingsBestThirdTitle")}</p>
        <h3>${t("standingsBestThirdTitle")}</h3>
      </div>
      <p>${t("standingsBestThirdIntro")}</p>
    </div>
    <div class="best-third-grid">
      ${rows.map((team, index) => `<article class="best-third-card${index < 8 ? " is-qualified" : ""}">
        <div class="best-third-rank">#${index + 1}</div>
        <div class="best-third-team">
          <b>${team.flag || ""} ${escapeHtml(teamDisplayNameByIso(team.iso3))}</b>
          <small>${t("group")} ${escapeHtml(team.group)} · ${displayIso3(team.iso3)}</small>
        </div>
        <div class="best-third-summary">
          <b>${numberLabel(team.points)}</b>
          <span>Pts</span>
        </div>
        <div class="best-third-kpis">
          <span>${team.played} ${t("playedShort")}</span>
          <span>GD ${numberLabel(team.goal_difference)}</span>
        </div>
        ${index < 8 ? `<em>${t("standingsQualified")}</em>` : ""}
      </article>`).join("")}
    </div>
  </section>`;
}

function knockoutTeamRow(match, side) {
  const info = knockoutSlotInfo(match, side);
  const resolvedSide = inferredResolvedSide(match);
  const winnerClass = resolvedSide === side ? " is-advanced" : "";
  const placeholderClass = info.placeholder ? " is-placeholder" : "";
  const scoreLabel = isFinished(match) ? `<strong>${valueOrDash(match[`result_team_${side}`])}</strong>` : "";
  const flag = info.flag ? `<span class="knockout-flag">${info.flag}</span>` : `<span class="knockout-path-marker">${info.placeholder ? "→" : "•"}</span>`;
  return `<div class="knockout-team-row${winnerClass}${placeholderClass}">
    <div class="knockout-team-main">
      ${flag}
      <div>
        <b>${escapeHtml(info.name)}</b>
        <small>${escapeHtml(info.meta || t("standingsBracketPending"))}</small>
      </div>
    </div>
    ${scoreLabel}
  </div>`;
}

function knockoutCard(match) {
  const status = matchExperienceStatus(match);
  const stageLabel = match.tournament_stage === "third_place" ? t("standingsBracketThirdPlace") : phaseLabel(match.tournament_stage);
  const viewer = viewerDateTime(match);
  const metaBits = [viewer.shortLabel, match.host_city].filter(Boolean).join(" · ");
  return `<article class="knockout-card status-${status}">
    <div class="knockout-card-head">
      <div>
        <span>${match.match_id}</span>
        <b>${stageLabel}</b>
      </div>
      <i>${statusLabel(status)}</i>
    </div>
    <div class="knockout-card-meta">${escapeHtml(metaBits)}</div>
    <div class="knockout-team-list">
      ${knockoutTeamRow(match, "a")}
      ${knockoutTeamRow(match, "b")}
    </div>
    <button class="knockout-open" type="button" data-open-match="${match.match_id}">${t("standingsBracketOpen")}</button>
  </article>`;
}

function renderKnockoutBracket() {
  const focusStage = knockoutFocusStage();
  const stageSummaries = KNOCKOUT_STAGE_ORDER.map(knockoutStageSummary).filter((summary) => summary.matches.length);
  if (!stageSummaries.length) return "";
  const activeStage = stageSummaries.some((summary) => summary.stage === state.knockoutStage)
    ? state.knockoutStage
    : focusStage;
  const thirdPlaceMatches = knockoutStageMatches("third_place");
  return `<section class="standings-panel knockout-panel">
    <div class="standings-panel-head">
      <div>
        <p class="eyebrow">${t("standingsKnockoutTitle")}</p>
        <h3>${t("standingsKnockoutTitle")}</h3>
      </div>
      <p>${t("standingsKnockoutIntro")}</p>
    </div>
    <div class="knockout-stage-nav">
      ${stageSummaries.map((summary) => knockoutStageButton(summary, activeStage)).join("")}
    </div>
    <p class="knockout-scroll-hint">${t("standingsKnockoutMobileIntro")}</p>
    <div class="knockout-board" data-active-stage="${activeStage || ""}">
      ${stageSummaries.map((summary) => `<section class="knockout-column${summary.stage === activeStage ? " is-active" : ""}" data-bracket-stage="${summary.stage}">
        <div class="knockout-column-head${summary.stage === focusStage ? " is-current" : ""}${summary.stage === activeStage ? " is-active" : ""}">
          <span>${phaseLabel(summary.stage)}</span>
          <b>${summary.completed}/${summary.matches.length} ${summary.remaining ? t("standingsBracketScheduled") : t("standingsBracketFinished")}</b>
        </div>
        <div class="knockout-column-list">
          ${summary.matches.map(knockoutCard).join("")}
        </div>
      </section>`).join("")}
    </div>
    ${thirdPlaceMatches.length ? `<div class="knockout-third-place">
      <div class="knockout-column-head">
        <span>${t("standingsBracketThirdPlace")}</span>
        <b>${thirdPlaceMatches.filter(isFinished).length}/${thirdPlaceMatches.length} ${thirdPlaceMatches.some((match) => !isFinished(match)) ? t("standingsBracketScheduled") : t("standingsBracketFinished")}</b>
      </div>
      <div class="knockout-third-place-list">${thirdPlaceMatches.map(knockoutCard).join("")}</div>
    </div>` : ""}
  </section>`;
}

function renderGroupStandings(standings) {
  const groups = groupStandingKeys(standings);
  if (!groups.length) return `<div class="active-empty">${t("standingsEmpty")}</div>`;
  const relevant = new Set(todaysMatches().map((match) => match.group_name).filter(Boolean));
  if (!relevant.size) relevant.add(futureMatches()[0]?.group_name || groups[0]);
  return `<section class="standings-panel group-standings-panel">
    <div class="standings-panel-head">
      <div>
        <p class="eyebrow">${t("standingsGroupsTitle")}</p>
        <h3>${t("standingsGroupsTitle")}</h3>
      </div>
      <p>${t("standingsGroupsIntro")}</p>
    </div>
    <div class="standings-grid enhanced">${groups.map((group) => `<details class="standing-group"${relevant.has(group) ? " open" : ""}>
      <summary><span>${t("group")} ${group}</span><b>${standings[group][0]?.flag || ""} ${standings[group][0]?.iso3 || ""} · ${standings[group][0]?.points || 0} Pts</b></summary>
      <div class="standing-group-content">
        <div class="standing-table"><table><thead><tr><th>${t("team")}</th><th>${t("playedShort")}</th><th>GD</th><th>Pts</th></tr></thead><tbody>${standings[group].map((team) => `<tr><td>${team.flag || ""} ${escapeHtml(teamDisplayNameByIso(team.iso3))} <small>${team.iso3}</small></td><td>${team.played}</td><td>${team.goal_difference}</td><td><b>${team.points}</b></td></tr>`).join("")}</tbody></table></div>
        ${groupContextOutlook(group)}
      </div>
    </details>`).join("")}</div>
  </section>`;
}

function renderEnhancedStandings(standings) {
  const groups = groupStandingKeys(standings);
  if (!groups.length) return `<div class="active-empty">${t("standingsEmpty")}</div>`;
  return `<div class="standings-layout">
    ${renderBestThirdRace(standings)}
    ${renderKnockoutBracket()}
    ${renderGroupStandings(standings)}
  </div>`;
}

function renderExperience() {
  renderHeroSignal();
  renderHomeDashboard();
}

function initExperience() {
  if (window.__weatherCupExperienceBound) {
    renderExperience();
    return;
  }
  window.__weatherCupExperienceBound = true;
  els.heroTodayCta?.addEventListener("click", () => {
    setActiveSection("home");
    document.querySelector("#nextUp")?.scrollIntoView({ behavior: "smooth", block: "start" });
    trackEvent("hero_cta_click", { target: "today" });
  });
  els.heroMapCta?.addEventListener("click", () => {
    setActiveSection("map");
    trackEvent("hero_cta_click", { target: "map" });
  });
  els.homeDashboard?.addEventListener("click", (event) => {
    const prediction = event.target.closest("[data-predict-match]");
    if (prediction) {
      openPredictionDialog(prediction.dataset.predictMatch);
      return;
    }
    const matchTarget = event.target.closest("[data-open-match], [data-context-match]");
    if (matchTarget) {
      const matchId = matchTarget.dataset.openMatch || matchTarget.dataset.contextMatch;
      if (matchId) {
        trackEvent(matchTarget.dataset.contextMatch ? "today_strip_click" : "next_up_card_click", { match_id: matchId });
        openMatchInMatchday(matchId);
      }
      return;
    }
    const venueTarget = event.target.closest("[data-home-venue]");
    if (venueTarget) {
      state.selectedVenueKey = venueTarget.dataset.homeVenue;
      state.mapSheetOpen = true;
      setActiveSection("map");
      renderWeatherMap();
      return;
    }
    const sectionTarget = event.target.closest("[data-section-jump]");
    if (sectionTarget) setActiveSection(sectionTarget.dataset.sectionJump);
  });
  els.predictionDialogContent?.addEventListener("click", (event) => {
    if (event.target.closest("[data-close-prediction]")) {
      els.predictionDialog.close();
      return;
    }
    const confirmation = event.target.closest("[data-confirm-prediction]");
    if (confirmation) {
      const matchId = els.predictionDialog.dataset.matchId;
      const draft = predictionDrafts[matchId] || {};
      if (!draft.result_pick || !draft.context_pick) return;
      savePrediction(matchId, draft);
      els.predictionDialogContent.innerHTML = predictionDialogMarkup(findMatch(matchId), { confirmed: true });
      renderHeroSignal();
      renderAnalysis();
      return;
    }
    const option = event.target.closest("[data-prediction-field]");
    if (!option) return;
    const matchId = els.predictionDialog.dataset.matchId;
    predictionDrafts[matchId] = {
      ...(predictionDrafts[matchId] || {}),
      [option.dataset.predictionField]: option.dataset.predictionValue,
    };
    els.predictionDialogContent.innerHTML = predictionDialogMarkup(findMatch(matchId));
  });
  els.predictionDialog?.addEventListener("click", (event) => {
    if (event.target === els.predictionDialog) els.predictionDialog.close();
  });
  document.querySelectorAll(".faq details").forEach((item) => item.addEventListener("toggle", () => {
    if (item.open) trackEvent("faq_open", { id: item.id || item.querySelector("summary")?.textContent });
  }));
  renderExperience();
}
