# SAR-INTEL TOOLKIT

This version runs person detection on video frames, fuses detections with simulated drone telemetry, and deduplicates repeated detections into confirmed tracks across frames.

## Architecture

```
Video → Frame Extraction → Person Detection (YOLO) → Geotag Fusion → Alert Output
                                                ↓
                                           Tracker (IoU + GPS) → Track Deduplication → Track Output
```

The pipeline processes each video frame independently, detects people, fuses detections with simulated drone GPS, and optionally associates detections across frames into higher-level tracks.

## New in v0.2

- **Track Association:** Links frame-level detections across time using bounding-box IoU, approximate GPS proximity, frame-gap limits, and minimum-hit thresholds.
- **Dual Output:** Preserves `alerts.json` (one detection per frame, backward-compatible) and adds `tracks.json` (confirmed detection sequences).
- **Validation:** Real street footage (3840×2160, 25fps, ~14 sec) produced **1699 frame-level alerts deduplicated into 29 confirmed tracks** — a ~58.6× reduction.

## New in v0.3.0

- **Telemetry Replay Mode:** Load timestamped drone telemetry from CSV files instead of simulating GPS motion.
- **Dynamic Altitude:** Altitude is now sourced from telemetry state rather than fixed config, enabling realistic geotagging with altitude variation.
- **Time Interpolation:** Telemetry states (lat/lon/altitude/yaw/pitch/roll) are linearly interpolated by video/event time, enabling smooth position estimation between logged waypoints.
- **Orientation Fields:** Yaw, pitch, and roll are parsed from telemetry for future pose-aware geotagging (currently parsed, not yet used in geolocation).
- **Validation:** Both simulated and replay modes pass regression tests; output schemas unchanged.

## New in v0.4.0

- **Confidence-Weighted Track Scoring:** Each confirmed track now receives a `track_score` derived from mean confidence, peak confidence, and detection density across the track's lifetime.
- **Track Classification:** Tracks are classified into `high_confidence_person`, `possible_person`, or `marginal_person` based on configurable score thresholds.
- **New `tracks.json` Fields:** `duration_seconds`, `detection_density`, `track_score`, and `track_class` are added to every confirmed track. All existing fields are preserved for backward compatibility.
- **Configurable Scoring:** The `track_scoring` section in `config.yaml` controls scoring weights and thresholds. Set `enabled: false` to omit scoring fields.
- **No behavioral changes:** Detector, telemetry, geotagging, and alert schemas are unchanged. Track association logic is unchanged.

## New in v0.5.0

- **GeoJSON Track Export:** Confirmed tracks can now be exported as a GeoJSON `FeatureCollection` for direct use in GIS and web-map tools.
- **Map-Ready Geometry:** Each confirmed track becomes a GeoJSON `Point` feature using `[longitude, latitude]` coordinate order.
- **Visualization Weighting:** Each feature includes `heatmap_weight`, which prefers `track_score` and falls back to confidence fields when scoring is unavailable.
- **Configurable Filtering:** The `geojson` config block can drop low-score tracks or exclude `marginal_person` tracks from the export without changing `tracks.json`.
- **No behavioral changes:** Detector behavior, tracker association, telemetry replay, geotagging, and `alerts.json` remain unchanged.

## New in v0.6.0

- **Kalman/SORT-style Prediction:** Tracks can now use a lightweight constant-velocity Kalman motion model to predict the next bounding box during brief missed detections.
- **Improved Continuity:** Predicted bounding boxes help maintain a single track across short detector dropouts or unstable frame-to-frame localization.
- **Same Association Signals:** IoU and GPS proximity are still used for matching; the Kalman layer only improves the bbox target used by IoU.
- **Optional Metadata:** When Kalman tracking is enabled, confirmed tracks also include `motion_model`, `missed_frames`, and `max_consecutive_misses`.
- **No identity claims:** This is not full re-identification and does not guarantee unique real-world people.

## Run

Ultralytics-first config:

```bash
pip install -r requirements.txt
python main.py --config config.yaml
```

Offline-safe config:

```bash
pip install -r requirements.txt
python main.py --config config.offline.yaml
```

## Inputs

- `config.yaml` or `config.offline.yaml`
- `sample_data/video.mp4`

## Outputs

- `sample_data/path.json` — search grid waypoints
- `output/alerts.json` — frame-level detections (one per person per frame)
- `output/tracks.json` — deduplicated confirmed person tracks
- `output/tracks.geojson` — optional GeoJSON FeatureCollection of confirmed tracks for mapping tools

## Sample Output

### `output/alerts.json`

One entry per detected person per frame. Below is a real run on daylight street footage (3840×2160, 25fps, ~14 seconds):

```json
[
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489098, "lon": -79.3807224, "confidence": 0.9394, "type": "possible_person"},
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489074, "lon": -79.3805245, "confidence": 0.899, "type": "possible_person"},
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489804, "lon": -79.3807982, "confidence": 0.684, "type": "possible_person"},
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489707, "lon": -79.3809351, "confidence": 0.5061, "type": "possible_person"},
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489103, "lon": -79.3807232, "confidence": 0.9351, "type": "possible_person"}
]
```

**Fields:**
- `timestamp`: UTC time of the alert (from video start_time_utc + frame_idx / fps)
- `lat`, `lon`: estimated person location (nadir-camera projection from bbox and camera FOV)
- `confidence`: YOLO detector confidence (0–1)
- `type`: alert class ("possible_person" for this version)

### `output/tracks.json`

Confirmed detection sequences deduplicated across frames. Each track summarizes a series of linked frame-level detections:

```json
[
  {
    "track_id": 1,
    "type": "possible_person_track",
    "first_seen": "2026-04-18T15:00:00Z",
    "last_seen": "2026-04-18T15:00:03Z",
    "first_frame": 0,
    "last_frame": 80,
    "hits": 78,
    "lat": 43.6489106,
    "lon": -79.380667,
    "max_confidence": 0.956,
    "mean_confidence": 0.8951,
    "representative_bbox": [2669.81, 627.01, 3839.31, 2144.29],
    "duration_seconds": 3.2,
    "detection_density": 0.9625,
    "track_score": 0.9235,
    "track_class": "high_confidence_person"
  },
  {
    "track_id": 2,
    "type": "possible_person_track",
    "first_seen": "2026-04-18T15:00:00Z",
    "last_seen": "2026-04-18T15:00:08Z",
    "first_frame": 5,
    "last_frame": 198,
    "hits": 156,
    "lat": 43.6489373,
    "lon": -79.3798213,
    "max_confidence": 0.9265,
    "mean_confidence": 0.8842,
    "representative_bbox": [1400.22, 530.14, 1648.61, 1180.75]
  }
]
```

**Track Fields:**
- `track_id`: Unique identifier within the run
- `type`: "possible_person_track" (preserved for backward compatibility)
- `first_seen`, `last_seen`: UTC timestamps of first and last frame
- `first_frame`, `last_frame`: Frame indices
- `hits`: Number of frames in which this track was detected
- `lat`, `lon`: Confidence-weighted mean position across all frames
- `max_confidence`: Peak detector confidence in the track
- `mean_confidence`: Average detector confidence across all detections
- `representative_bbox`: Bounding box with highest confidence
- `duration_seconds`: Track lifespan in seconds (`(last_frame - first_frame) / fps`)
- `detection_density`: Fraction of processed frames in which the track was detected (0–1)
- `track_score`: Weighted score combining mean confidence, peak confidence, and detection density (0–1)
- `track_class`: Confidence classification — `high_confidence_person` (≥0.80), `possible_person` (≥0.55), or `marginal_person` (<0.55)
- `motion_model`: Optional tracking motion model used for the track (`"kalman"` when enabled)
- `missed_frames`: Current count of consecutive processed frames missed at export time when Kalman prediction is enabled
- `max_consecutive_misses`: Largest consecutive miss streak bridged by prediction during the track lifetime

> **Note:** `track_class` is a confidence classification of the detection sequence, not a verified identity or guaranteed unique human. A single person can appear as multiple tracks due to occlusion or out-of-frame motion. A single track may represent more than one person in dense scenes.

### `output/tracks.geojson`

GeoJSON export writes one feature per confirmed track. Geometry always uses `[longitude, latitude]`, never `[latitude, longitude]`.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-79.380667, 43.6489106]
      },
      "properties": {
        "track_id": 1,
        "type": "possible_person_track",
        "track_class": "high_confidence_person",
        "track_score": 0.9235,
        "heatmap_weight": 0.9235,
        "duration_seconds": 3.2,
        "detection_density": 0.9625,
        "hits": 78,
        "mean_confidence": 0.8951,
        "max_confidence": 0.956,
        "first_seen": "2026-04-18T15:00:00Z",
        "last_seen": "2026-04-18T15:00:03Z",
        "first_frame": 0,
        "last_frame": 80,
        "representative_bbox": [2669.81, 627.01, 3839.31, 2144.29]
      }
    }
  ]
}
```

`heatmap_weight` can be used directly by map tools for heatmap layers, graduated symbols, or label filtering.

### Geotagging Limitations

The geotagging step is intentionally approximate and suitable for simulation-first workflows:
- Assumes a nadir-looking (downward-facing) camera
- Assumes flat ground with no terrain model
- No lens distortion correction
- Suitable for SAR planning and area deconfliction, not for precise strike coordinates

For operational systems, geotagging should be replaced with proper camera calibration, ground-truth terrain data, and multi-sensor fusion.

**Real Test Results:**
- Clip: 3840×2160 street footage, 25 fps, ~14 sec
- Frame-level detections: 1699 alerts in `alerts.json`
- Confirmed tracks: 29 tracks in `tracks.json`
- Reduction: ~58.6× fewer unique tracks than frame-level detections
- Confidence range: 0.50–0.95 (realistic spread)
- Coordinates: Clustered by track, drifting smoothly with simulated drone path

## Configuration

### Telemetry Modes

The toolkit supports two telemetry modes: **simulated** (default) and **replay**.

#### Simulated Mode (Default)

Simulates GPS motion along a pre-planned grid at constant speed:

```yaml
telemetry:
  mode: simulated
  replay_path: sample_data/telemetry.csv
```

- `mode`: Set to `"simulated"` to interpolate drone position along waypoints at constant speed
- `replay_path`: Ignored in simulated mode; included for config portability

#### Replay Mode

Loads timestamped telemetry from a CSV file and interpolates states by video/event time:

```yaml
telemetry:
  mode: replay
  replay_path: sample_data/telemetry.csv
```

- `mode`: Set to `"replay"` to load and interpolate real or logged drone telemetry
- `replay_path`: Path to CSV file with timestamped telemetry (required)

**CSV Format:**

```
timestamp,lat,lon,altitude_m,yaw_deg,pitch_deg,roll_deg
2026-04-17T19:30:00.000Z,43.649000,-79.381000,60.0,90.0,0.0,0.0
2026-04-17T19:30:02.000Z,43.649000,-79.380800,60.0,90.0,0.0,0.0
2026-04-17T19:30:04.000Z,43.649000,-79.380600,60.0,90.0,0.0,0.0
```

**CSV Fields:**
- `timestamp`: ISO 8601 timestamp (UTC, required)
- `lat`, `lon`: Latitude and longitude (decimal degrees, required)
- `altitude_m`: Altitude in meters (required; used for nadir geolocation)
- `yaw_deg`, `pitch_deg`, `roll_deg`: Drone orientation in degrees (required; parsed for future pose-aware geotagging)

**Interpolation Behavior:**
- Telemetry is linearly interpolated between logged rows based on video/event time
- Times before the first row use the first row's state
- Times after the last row use the last row's state (safe for short logs with longer videos)
- All six fields (lat, lon, altitude, yaw, pitch, roll) are interpolated

**Geotagging with Replay:**

When using replay mode:
- **Altitude** from the CSV is used for nadir-camera geolocation, enabling realistic vertical accuracy variation
- **lat/lon** are interpolated to smooth position between logged waypoints
- **yaw/pitch/roll** are parsed and available for future pose-aware transformations (not yet used)
- Current geotagging remains approximate and assumes flat ground and nadir camera

**Example:** Use `config.replay.yaml` with `sample_data/telemetry.csv` to test replay mode:

```bash
python main.py --config config.replay.yaml
```

### Tracking Parameters

Edit the `tracking:` section in `config.yaml` to tune track association:

```yaml
tracking:
  enabled: true
  include_track_id_in_alerts: false
  iou_threshold: 0.25                  # Bounding-box IoU minimum for match
  max_frame_gap: 10                    # Max frames allowed between detections in one track
  max_position_distance_m: 12.0        # Max GPS distance for same-track match
  min_hits: 3                          # Minimum detections before track is confirmed
  motion_model: kalman                 # none | kalman
  kalman:
    process_noise: 1.0
    measurement_noise: 10.0
    initial_uncertainty: 100.0
```

- `motion_model`: Set to `none` for the v0.5-style tracker or `kalman` to enable constant-velocity bbox prediction
- `kalman.process_noise`: How quickly the predicted state is allowed to drift
- `kalman.measurement_noise`: How strongly detections pull the predicted state back toward the observed bbox
- `kalman.initial_uncertainty`: Starting covariance for new tracks

### GeoJSON Export

Use the `geojson:` section to control optional GeoJSON output:

```yaml
geojson:
  enabled: true
  tracks_path: output/tracks.geojson
  min_track_score: 0.0
  include_marginal_tracks: true
```

- `enabled`: Writes GeoJSON output from confirmed tracks only
- `tracks_path`: Destination for the GeoJSON FeatureCollection
- `min_track_score`: Skips tracks below this score threshold when `track_score` is present
- `include_marginal_tracks`: Excludes `marginal_person` tracks when set to `false`

## Notes

- Tracks are **confirmed detection sequences**, not guaranteed unique real-world people. Occlusion, out-of-frame motion, or detector instability can fragment one person into multiple tracks.
- `track_class` is a confidence classification of the detection sequence — not a verified identity or guaranteed unique human.
- Kalman/SORT-style prediction improves continuity across short missed detections, but it is not a full SORT implementation and does not use Hungarian assignment.
- GeoJSON geometry uses `[longitude, latitude]` order to match the GeoJSON specification.
- GeoJSON export is driven from confirmed tracks only. Alerts are not exported as GeoJSON.
- `config.yaml` uses a pretrained Ultralytics detector. `config.offline.yaml` forces OpenCV HOG detection for offline operation.
- SimpleTracker remains lightweight: greedy IoU + proximity matching with an optional NumPy Kalman prediction layer.
- **v0.6 Validation:** Both `config.offline.yaml` (simulated) and `config.replay.yaml` (replay) pass end-to-end tests. Alert schema, detector behavior, telemetry replay behavior, and geotagging remain unchanged.
