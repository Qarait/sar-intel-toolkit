const baseMetrics = [
  {
    label: "Frame-level alerts",
    value: "2502",
    detail: "Representative count from the local static demo run.",
  },
  {
    label: "Confirmed tracks",
    value: "23",
    detail: "Deduplicated tracks after scoring and tracking.",
  },
  {
    label: "GeoJSON features",
    value: "pending",
    detail: "Count loaded directly from the sanitized demo asset.",
  },
  {
    label: "Telemetry mode",
    value: "simulated",
    detail: "Static demo uses simulated telemetry inputs.",
  },
  {
    label: "Geotagging mode",
    value: "pose_aware_flat_ground",
    detail: "Flat-ground pose-aware projection for approximate coordinates.",
  },
  {
    label: "Tracking model",
    value: "kalman",
    detail: "Kalman-assisted multi-frame track continuity.",
  },
];

const TRACK_CARD_LIMIT = 5;
const FILTER_OPTIONS = [
  { value: "all", label: "All" },
  { value: "high_confidence_person", label: "high_confidence_person" },
  { value: "possible_person", label: "possible_person" },
  { value: "marginal_person", label: "marginal_person" },
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
    if (metric.label !== "GeoJSON features") {
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
    card.innerHTML = `
      <div class="track-card-head">
        <h3>Track ${properties.track_id ?? "?"}</h3>
        <span class="track-pill">${properties.track_class ?? "unknown"}</span>
      </div>
      <dl>
        <div><dt>Score</dt><dd>${properties.track_score ?? "n/a"}</dd></div>
        <div><dt>Hits</dt><dd>${properties.hits ?? "n/a"}</dd></div>
        <div><dt>Mean confidence</dt><dd>${properties.mean_confidence ?? "n/a"}</dd></div>
        <div><dt>Duration (s)</dt><dd>${properties.duration_seconds ?? "n/a"}</dd></div>
        <div><dt>Coordinates</dt><dd>[${formatCoordinate(coordinates[0])}, ${formatCoordinate(coordinates[1])}]</dd></div>
      </dl>
    `;
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
      marker.bindPopup(
        `Track ${properties.track_id}<br>` +
        `Class: ${properties.track_class}<br>` +
        `Score: ${properties.track_score}<br>` +
        `Hits: ${properties.hits}`
      );
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