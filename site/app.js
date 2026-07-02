const baseMetrics = [
  {
    label: "Frame-level signals",
    value: "2502",
    detail: "Possible-person alerts from the representative static demo run.",
  },
  {
    label: "Detection tracks",
    value: "23",
    detail: "Repeated detections grouped into reviewable detection-track objects.",
  },
  {
    label: "Map features",
    value: "pending",
    detail: "Loaded directly from the sanitized public GeoJSON asset.",
  },
  {
    label: "Telemetry",
    value: "simulated",
    detail: "Static demo uses repeatable simulated telemetry inputs.",
  },
  {
    label: "Geotagging",
    value: "pose aware",
    detail: "Flat-ground pose-aware projection for approximate demo coordinates.",
  },
  {
    label: "Tracking",
    value: "kalman",
    detail: "Kalman-assisted continuity across short missed detections.",
  },
];

const TRACK_CARD_LIMIT = 5;
const FILTER_OPTIONS = [
  { value: "all", label: "All tracks" },
  { value: "high_confidence_person", label: "High confidence" },
  { value: "possible_person", label: "Possible person" },
  { value: "marginal_person", label: "Marginal" },
];

let allFeatures = [];
let visibleFeatures = [];
let currentFilter = "all";
let showingAllCards = false;
let demoGeoJson = null;
let mapInstance = null;
let mapLayer = null;

function formatCoordinate(value) {
  if (typeof value !== "number") {
    return "n/a";
  }

  return value.toFixed(6);
}

function displayValue(value, fallback = "n/a") {
  return value ?? fallback;
}

function appendTextElement(parent, tagName, text, className) {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  element.textContent = String(text);
  parent.appendChild(element);
  return element;
}

function appendDefinition(parent, term, value) {
  const row = document.createElement("div");
  appendTextElement(row, "dt", term);
  appendTextElement(row, "dd", displayValue(value));
  parent.appendChild(row);
}

function appendPopupLine(parent, label, value) {
  parent.appendChild(document.createElement("br"));
  parent.appendChild(document.createTextNode(`${label}: ${displayValue(value)}`));
}

function setMapMessage(message, hideMap = true) {
  const fallback = document.getElementById("map-fallback");
  const mapTarget = document.getElementById("map");

  if (fallback) {
    fallback.hidden = false;
    fallback.textContent = message;
  }

  if (mapTarget) {
    if (hideMap) {
      mapTarget.setAttribute("hidden", "hidden");
    } else {
      mapTarget.removeAttribute("hidden");
    }
  }
}

function hideMapMessage() {
  const fallback = document.getElementById("map-fallback");
  if (fallback) {
    fallback.hidden = true;
  }
}

function setLoadingState() {
  renderMetrics(null);
  renderTrackCards([], { loading: true, totalCount: 0 });
  renderFeatureSnippet(null, { loading: true });
  renderFilterControls();
  setMapMessage("Map loading. Loading sanitized GeoJSON...", true);
}

function fetchDemoGeoJson() {
  return fetch("assets/demo_tracks.geojson").then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  });
}

function renderMetrics(features) {
  const container = document.getElementById("metrics-grid");
  const summary = document.getElementById("metrics-summary");
  if (!container) {
    return;
  }

  container.innerHTML = "";

  const isLoading = features === null;
  const featureCount = Array.isArray(features) ? features.length : 0;
  const totalCount = allFeatures.length;

  const metrics = baseMetrics.map((metric) => {
    if (metric.label !== "Map features") {
      return metric;
    }

    return {
      ...metric,
      value: isLoading ? "pending" : String(featureCount),
      detail: isLoading
        ? "Metrics pending while the sanitized demo asset loads."
        : `Visible sanitized features: ${featureCount} of ${totalCount}.`,
    };
  });

  if (summary) {
    if (isLoading) {
      summary.innerHTML = 'Metrics pending. <strong>Loading sanitized GeoJSON...</strong>';
    } else if (currentFilter === "all") {
      summary.innerHTML = `Loaded <strong>${featureCount}</strong> sanitized GeoJSON features from <code>assets/demo_tracks.geojson</code>.`;
    } else {
      summary.innerHTML = `Showing <strong>${featureCount}</strong> of <strong>${totalCount}</strong> sanitized GeoJSON features for <code>${currentFilter}</code>.`;
    }
  }

  for (const metric of metrics) {
    const card = document.createElement("article");
    card.className = "metric-card";
    card.innerHTML = `
      <span>${metric.label}</span>
      <strong>${metric.value}</strong>
      <p>${metric.detail}</p>
    `;
    container.appendChild(card);
  }
}

function renderTrackCards(features, options = {}) {
  const container = document.getElementById("track-card-grid");
  const summary = document.getElementById("track-card-summary");
  const toggle = document.getElementById("toggle-track-cards");
  if (!container) {
    return;
  }

  container.innerHTML = "";

  const isLoading = Boolean(options.loading);
  const isError = Boolean(options.error);
  const totalCount = options.totalCount ?? features.length;

  if (summary) {
    if (isLoading) {
      summary.textContent = "Loading sanitized GeoJSON...";
    } else if (isError) {
      summary.textContent = "Track cards unavailable because the sanitized GeoJSON could not be loaded.";
    } else if (totalCount === 0) {
      summary.textContent = "No tracks match the current filter.";
    } else {
      const visibleCount = showingAllCards ? features.length : Math.min(TRACK_CARD_LIMIT, features.length);
      summary.textContent = `Showing ${visibleCount} of ${totalCount} tracks. Use filters or show all to inspect the full sanitized demo set.`;
    }
  }

  if (toggle) {
    const shouldShowToggle = !isLoading && !isError && totalCount > TRACK_CARD_LIMIT;
    toggle.hidden = !shouldShowToggle;
    toggle.textContent = showingAllCards ? "Show fewer" : "Show all tracks";
  }

  if (isLoading || isError || features.length === 0) {
    const message = document.createElement("p");
    message.className = "track-empty-state";
    message.textContent = isLoading
      ? "Loading sanitized GeoJSON..."
      : isError
        ? "Track cards are unavailable because the demo GeoJSON could not be loaded."
        : "No tracks match the current filter.";
    container.appendChild(message);
    return;
  }

  const displayFeatures = showingAllCards ? features : features.slice(0, TRACK_CARD_LIMIT);

  for (const feature of displayFeatures) {
    const properties = feature.properties || {};
    const coordinates = feature.geometry?.coordinates || [null, null];
    const card = document.createElement("article");
    card.className = "track-card";

    const head = document.createElement("div");
    head.className = "track-card-head";
    appendTextElement(head, "h3", `Track ${displayValue(properties.track_id, "?")}`);
    appendTextElement(head, "span", displayValue(properties.track_class, "unknown"), "track-pill");
    card.appendChild(head);

    const details = document.createElement("dl");
    appendDefinition(details, "Score", properties.track_score);
    appendDefinition(details, "Hits", properties.hits);
    appendDefinition(details, "Mean confidence", properties.mean_confidence);
    appendDefinition(details, "Duration (s)", properties.duration_seconds);
    appendDefinition(details, "Coordinates", `[${formatCoordinate(coordinates[0])}, ${formatCoordinate(coordinates[1])}]`);
    card.appendChild(details);

    container.appendChild(card);
  }
}

function colorForTrackClass(trackClass) {
  if (trackClass === "high_confidence_person") {
    return "#214c77";
  }
  if (trackClass === "possible_person") {
    return "#3b6c7f";
  }
  return "#8ca1b3";
}

function renderFeatureSnippet(features, options = {}) {
  const snippetTarget = document.getElementById("snippet");
  if (!snippetTarget) {
    return;
  }

  if (options.loading) {
    snippetTarget.textContent = "Loading sanitized GeoJSON...";
    return;
  }

  if (options.error) {
    snippetTarget.textContent = `Failed to load demo GeoJSON: ${options.error}`;
    return;
  }

  if (!Array.isArray(features) || features.length === 0) {
    snippetTarget.textContent = "No sanitized features match the current filter.";
    return;
  }

  snippetTarget.textContent = JSON.stringify(features[0], null, 2);
}

function renderFilterControls() {
  const container = document.getElementById("filter-controls");
  if (!container) {
    return;
  }

  container.innerHTML = "";

  for (const option of FILTER_OPTIONS) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = option.value === currentFilter ? "filter-button is-active" : "filter-button";
    button.textContent = option.label;
    button.disabled = allFeatures.length === 0;
    button.addEventListener("click", () => {
      currentFilter = option.value;
      showingAllCards = false;
      applyFilter();
    });
    container.appendChild(button);
  }
}

function filteredGeoJson(features) {
  return {
    ...(demoGeoJson || { type: "FeatureCollection" }),
    features,
  };
}

function renderMapIfAvailable(features, geojson) {
  demoGeoJson = geojson;

  if (typeof L === "undefined") {
    setMapMessage(
      "Map preview unavailable because the Leaflet map library did not load. Metrics, track cards, and the demo feature snippet are still available below.",
      true
    );
    return;
  }

  const mapTarget = document.getElementById("map");
  if (!mapTarget) {
    return;
  }

  mapTarget.removeAttribute("hidden");

  if (!mapInstance) {
    mapInstance = L.map(mapTarget, {
      zoomControl: false,
      scrollWheelZoom: false,
    });

    L.control.zoom({ position: "bottomright" }).addTo(mapInstance);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(mapInstance);
  }

  if (mapLayer) {
    mapInstance.removeLayer(mapLayer);
    mapLayer = null;
  }

  if (features.length === 0) {
    setMapMessage("No tracks match the current filter. Change the filter to restore the map layer.", false);
    return;
  }

  hideMapMessage();

  mapLayer = L.geoJSON(filteredGeoJson(features), {
    pointToLayer(feature, latlng) {
      const score = Number(feature.properties.track_score || 0);
      return L.circleMarker(latlng, {
        radius: 6 + Math.round(score * 9),
        color: "#f7fbff",
        weight: 2,
        fillColor: colorForTrackClass(feature.properties.track_class),
        fillOpacity: 0.9,
      });
    },
    onEachFeature(feature, marker) {
      const properties = feature.properties || {};
      const popup = document.createElement("div");
      appendTextElement(popup, "strong", `Track ${displayValue(properties.track_id, "?")}`);
      appendPopupLine(popup, "Review class", properties.track_class);
      appendPopupLine(popup, "Confidence score", properties.track_score);
      appendPopupLine(popup, "Frame hits", properties.hits);
      marker.bindPopup(popup);
    },
  }).addTo(mapInstance);

  const bounds = mapLayer.getBounds();
  if (bounds.isValid()) {
    mapInstance.fitBounds(bounds, { padding: [32, 32] });
  }
}

function applyFilter() {
  visibleFeatures = currentFilter === "all"
    ? [...allFeatures]
    : allFeatures.filter((feature) => feature.properties?.track_class === currentFilter);

  renderFilterControls();
  renderMetrics(visibleFeatures);
  renderTrackCards(visibleFeatures, { totalCount: visibleFeatures.length });
  renderFeatureSnippet(visibleFeatures);

  if (demoGeoJson) {
    renderMapIfAvailable(visibleFeatures, demoGeoJson);
  }
}

function renderErrorState(error) {
  allFeatures = [];
  visibleFeatures = [];
  renderFilterControls();
  renderMetrics([]);
  renderTrackCards([], { error: true, totalCount: 0 });
  renderFeatureSnippet([], { error });
  setMapMessage(
    `Map preview unavailable because the demo GeoJSON could not be loaded: ${error}. Metrics, track cards, and the feature snippet reflect the load failure.`,
    true
  );

  const summary = document.getElementById("metrics-summary");
  if (summary) {
    summary.innerHTML = `Failed to load <code>assets/demo_tracks.geojson</code>: <strong>${error}</strong>.`;
  }
}

const toggleTrackCardsButton = document.getElementById("toggle-track-cards");
if (toggleTrackCardsButton) {
  toggleTrackCardsButton.addEventListener("click", () => {
    showingAllCards = !showingAllCards;
    renderTrackCards(visibleFeatures, { totalCount: visibleFeatures.length });
  });
}

setLoadingState();

fetchDemoGeoJson()
  .then((geojson) => {
    const features = Array.isArray(geojson.features) ? geojson.features : [];
    demoGeoJson = geojson;
    allFeatures = features;
    currentFilter = "all";
    showingAllCards = false;
    applyFilter();
  })
  .catch((error) => {
    renderErrorState(String(error));
  });
const fallbackReviewCandidates = [
  {
    id: "motion-0007",
    title: "Tree-line motion candidate",
    frameRange: "frames 184-193",
    status: "unreviewed",
    priority: 14.6,
    motionScore: 8.1,
    missProbability: 0.65,
    evidence: "Persistent small motion against a mostly static background.",
    locationHint: "northwest grid cell",
    bbox: { left: 28, top: 36, width: 22, height: 30 },
    trail: [
      { left: 30, top: 62 },
      { left: 36, top: 58 },
      { left: 43, top: 54 },
    ],
  },
  {
    id: "motion-0012",
    title: "Ridge-path uncertainty candidate",
    frameRange: "frames 241-249",
    status: "unreviewed",
    priority: 12.2,
    motionScore: 6.7,
    missProbability: 0.55,
    evidence: "Lower motion score, but coverage confidence says this cell deserves another human look.",
    locationHint: "ridge path edge",
    bbox: { left: 56, top: 24, width: 18, height: 24 },
    trail: [
      { left: 58, top: 46 },
      { left: 61, top: 43 },
      { left: 65, top: 41 },
    ],
  },
  {
    id: "motion-0019",
    title: "Open-field flicker candidate",
    frameRange: "frames 318-322",
    status: "unreviewed",
    priority: 8.4,
    motionScore: 5.9,
    missProbability: 0.25,
    evidence: "Short-lived motion that remains below confirmation threshold until reviewed.",
    locationHint: "open field pass",
    bbox: { left: 41, top: 52, width: 16, height: 20 },
    trail: [
      { left: 43, top: 70 },
      { left: 47, top: 68 },
      { left: 50, top: 66 },
    ],
  },
];

const reviewDecisionActions = [
  { status: "confirmed", label: "Confirm candidate" },
  { status: "uncertain", label: "Mark uncertain" },
  { status: "rejected", label: "Reject candidate" },
];

let reviewCandidates = [...fallbackReviewCandidates];
let selectedReviewCandidateId = reviewCandidates[0]?.id || null;
let reviewDecisionLog = [];

function fetchPublicReviewQueue() {
  return fetch("assets/review_queue.json").then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  });
}

function normalizeReviewQueueCandidate(candidate) {
  const preview = candidate.frame_preview || {};
  return {
    id: candidate.tracklet_id,
    title: candidate.title,
    frameRange: candidate.frame_range,
    status: candidate.status || "unreviewed",
    priority: Number(candidate.review_priority || 0),
    motionScore: Number(candidate.motion_score || 0),
    missProbability: Number(candidate.coverage_miss_probability || 0),
    evidence: candidate.evidence,
    locationHint: candidate.location_hint,
    bbox: preview.bbox_percent || { left: 40, top: 40, width: 18, height: 24 },
    trail: Array.isArray(preview.motion_trail_percent) ? preview.motion_trail_percent : [],
  };
}

function applyReviewQueuePayload(payload) {
  const candidates = Array.isArray(payload?.candidates)
    ? payload.candidates.map(normalizeReviewQueueCandidate).filter((candidate) => candidate.id)
    : [];

  if (candidates.length === 0) {
    return false;
  }

  reviewCandidates = candidates;
  selectedReviewCandidateId = reviewCandidates[0].id;
  reviewDecisionLog = [];
  renderReviewCockpit();
  return true;
}

function loadPublicReviewQueue() {
  fetchPublicReviewQueue()
    .then((payload) => {
      if (!applyReviewQueuePayload(payload)) {
        renderReviewCockpit();
      }
    })
    .catch(() => {
      renderReviewCockpit();
    });
}
function reviewStatusLabel(status) {
  if (status === "confirmed") {
    return "confirmed by reviewer";
  }
  if (status === "rejected") {
    return "rejected by reviewer";
  }
  if (status === "uncertain") {
    return "uncertain after review";
  }
  return "unreviewed";
}

function selectedReviewCandidate() {
  return reviewCandidates.find((candidate) => candidate.id === selectedReviewCandidateId) || reviewCandidates[0];
}

function renderReviewStats() {
  const container = document.getElementById("review-stat-grid");
  if (!container) {
    return;
  }

  container.innerHTML = "";
  const counts = {
    candidates: reviewCandidates.length,
    unresolved: reviewCandidates.filter((candidate) => candidate.status === "unreviewed").length,
    decisions: reviewDecisionLog.length,
  };

  for (const item of [
    { label: "Candidates", value: counts.candidates },
    { label: "Unresolved", value: counts.unresolved },
    { label: "Decisions", value: counts.decisions },
  ]) {
    const card = document.createElement("article");
    appendTextElement(card, "span", item.label);
    appendTextElement(card, "strong", item.value);
    container.appendChild(card);
  }
}

function renderReviewCandidateList() {
  const container = document.getElementById("review-candidate-list");
  if (!container) {
    return;
  }

  container.innerHTML = "";
  for (const candidate of reviewCandidates) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = candidate.id === selectedReviewCandidateId ? "review-candidate is-active" : "review-candidate";
    button.addEventListener("click", () => {
      selectedReviewCandidateId = candidate.id;
      renderReviewCockpit();
    });

    const heading = document.createElement("span");
    heading.className = "review-candidate-title";
    heading.textContent = candidate.title;
    button.appendChild(heading);

    const meta = document.createElement("span");
    meta.className = "review-candidate-meta";
    meta.textContent = `${candidate.id} · priority ${candidate.priority.toFixed(1)} · ${reviewStatusLabel(candidate.status)}`;
    button.appendChild(meta);

    container.appendChild(button);
  }
}

function renderReviewFrame(candidate) {
  const title = document.getElementById("review-frame-title");
  const status = document.getElementById("review-frame-status");
  const box = document.getElementById("review-candidate-box");
  const trail = document.getElementById("review-motion-trail");
  const details = document.getElementById("review-details");

  if (title) {
    title.textContent = `${candidate.title} · ${candidate.frameRange}`;
  }
  if (status) {
    status.textContent = reviewStatusLabel(candidate.status);
    status.dataset.status = candidate.status;
  }
  if (box) {
    box.style.left = `${candidate.bbox.left}%`;
    box.style.top = `${candidate.bbox.top}%`;
    box.style.width = `${candidate.bbox.width}%`;
    box.style.height = `${candidate.bbox.height}%`;
    box.textContent = candidate.id;
  }
  if (trail) {
    trail.innerHTML = "";
    for (const point of candidate.trail) {
      const dot = document.createElement("span");
      dot.style.left = `${point.left}%`;
      dot.style.top = `${point.top}%`;
      trail.appendChild(dot);
    }
  }
  if (details) {
    details.innerHTML = "";
    appendDefinition(details, "Motion score", candidate.motionScore.toFixed(1));
    appendDefinition(details, "Coverage miss probability", candidate.missProbability.toFixed(2));
    appendDefinition(details, "Review priority", candidate.priority.toFixed(1));
    appendDefinition(details, "Location hint", candidate.locationHint);
    appendDefinition(details, "Why surfaced", candidate.evidence);
  }
}

function renderReviewActions(candidate) {
  const container = document.getElementById("review-actions");
  if (!container) {
    return;
  }

  container.innerHTML = "";
  for (const action of reviewDecisionActions) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `review-action review-action-${action.status}`;
    button.textContent = action.label;
    button.addEventListener("click", () => {
      candidate.status = action.status;
      reviewDecisionLog.unshift({
        trackletId: candidate.id,
        status: action.status,
        reviewer: "public-demo-reviewer",
        decidedAt: new Date().toISOString(),
      });
      renderReviewCockpit();
    });
    container.appendChild(button);
  }
}

function renderReviewLog() {
  const container = document.getElementById("review-log");
  if (!container) {
    return;
  }

  container.innerHTML = "";
  if (reviewDecisionLog.length === 0) {
    appendTextElement(container, "p", "No demo decisions yet. Select a candidate and record a review action.");
    return;
  }

  for (const decision of reviewDecisionLog.slice(0, 5)) {
    const item = document.createElement("article");
    appendTextElement(item, "strong", `${decision.trackletId}: ${reviewStatusLabel(decision.status)}`);
    appendTextElement(item, "span", `${decision.reviewer} · ${decision.decidedAt}`);
    container.appendChild(item);
  }
}

function renderReviewCockpit() {
  const candidate = selectedReviewCandidate();
  if (!candidate) {
    return;
  }

  renderReviewStats();
  renderReviewCandidateList();
  renderReviewFrame(candidate);
  renderReviewActions(candidate);
  renderReviewLog();
}

loadPublicReviewQueue();