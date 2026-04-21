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

function renderMetrics(featureCount) {
  const container = document.getElementById("metrics-grid");
  const summary = document.getElementById("metrics-summary");
  if (!container) {
    return;
  }

  container.innerHTML = "";

  const metrics = baseMetrics.map((metric) => {
    if (metric.label !== "GeoJSON features") {
      return metric;
    }

    return {
      ...metric,
      value: String(featureCount),
      detail: featureCount === 23
        ? "Count loaded from the sanitized demo asset: 23 features."
        : `Count loaded from the sanitized demo asset: ${featureCount} features.`,
    };
  });

  if (summary) {
    summary.innerHTML = `Loaded <strong>${featureCount}</strong> sanitized GeoJSON features from <code>assets/demo_tracks.geojson</code>.`;
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

function renderTrackCards(features) {
  const container = document.getElementById("track-card-grid");
  if (!container) {
    return;
  }

  container.innerHTML = "";

  for (const feature of features.slice(0, TRACK_CARD_LIMIT)) {
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
        <div><dt>Coordinates</dt><dd>[${coordinates[0]}, ${coordinates[1]}]</dd></div>
      </dl>
    `;
    container.appendChild(card);
  }
}

function showMapFallback(message) {
  const fallback = document.getElementById("map-fallback");
  const mapTarget = document.getElementById("map");
  if (fallback) {
    fallback.hidden = false;
    fallback.textContent = message;
  }
  if (mapTarget) {
    mapTarget.setAttribute("hidden", "hidden");
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

async function renderMap() {
  if (typeof L === "undefined") {
    showMapFallback(
      "Map preview unavailable because the Leaflet map library did not load. The sanitized dataset is still available at assets/demo_tracks.geojson and uses [longitude, latitude] coordinate order."
    );
    return;
  }

  const response = await fetch("assets/demo_tracks.geojson");
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  const geojson = await response.json();
  const features = Array.isArray(geojson.features) ? geojson.features : [];

  renderMetrics(features.length);
  renderTrackCards(features);

  const snippetTarget = document.getElementById("snippet");
  if (snippetTarget && features.length > 0) {
    snippetTarget.textContent = JSON.stringify(features[0], null, 2);
  }

  const mapTarget = document.getElementById("map");
  if (!mapTarget) {
    return;
  }

  const map = L.map(mapTarget, {
    zoomControl: false,
    scrollWheelZoom: false,
  });

  L.control.zoom({ position: "bottomright" }).addTo(map);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  const layer = L.geoJSON(geojson, {
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
  }).addTo(map);

  map.fitBounds(layer.getBounds(), { padding: [32, 32] });
}

renderMap().catch((error) => {
  renderMetrics(0);
  const snippetTarget = document.getElementById("snippet");
  if (snippetTarget) {
    snippetTarget.textContent = `Failed to load demo GeoJSON: ${error}`;
  }
  showMapFallback(
    `Map preview unavailable because the demo GeoJSON could not be rendered: ${error}. The sanitized dataset is still available at assets/demo_tracks.geojson and uses [longitude, latitude] coordinate order.`
  );
});