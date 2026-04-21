# SAR-INTEL TOOLKIT

[![CI](https://github.com/Qarait/sar-intel-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Qarait/sar-intel-toolkit/actions/workflows/ci.yml)

Simulation-first mission intelligence toolkit for search-and-rescue drone workflows.

It generates search grids, processes video detections, fuses detections with drone telemetry, tracks possible people across frames, and exports structured alerts, tracks, and map-ready GeoJSON.

See CHANGELOG.md for version history and capability progression.

Project constraints and non-goals are documented in docs/LIMITATIONS.md.

Safety and intended-use guidance are documented in docs/SAFETY.md.

Detailed system flow and module responsibilities are documented in docs/ARCHITECTURE.md.

Configuration options and section-by-section YAML reference are documented in docs/CONFIGURATION.md.

Mission profile presets and their scope are documented in docs/MISSION_PROFILES.md.

Near-term and longer-term project priorities are documented in docs/ROADMAP.md.

## New in v0.10.1

The toolkit now includes a documented VisDrone DET validation run for public aerial-drone imagery.

The validation harness evaluates the existing person detector against VisDrone `pedestrian` and `people` annotations and reports precision, recall, F1, TP, FP, FN, and per-image summaries.

Initial full validation split result:

- Images evaluated: 548
- GT person boxes: 13,969
- Detections: 975
- TP: 802
- FP: 173
- FN: 13,167
- Precision: 0.8226
- Recall: 0.0574
- F1: 0.1073

This is an aerial-person detection sanity check, not an operational SAR benchmark. The baseline model was not trained specifically on VisDrone aerial-person imagery, so low recall is expected.

## Proof stack

- Automated tests live in `tests/`.
- Output contracts live in `schemas/` and are validated in test coverage.
- Real validation notes live in `docs/VALIDATION.md`.
- Public aerial-drone validation results: `docs/VISDRONE_VALIDATION.md`.
- Each run writes `output/run_manifest.json` to record provenance.
- CI runs compile checks, pytest, and offline/replay smoke tests.

## Current capabilities

- Search grid generation
- Video person detection
- Simulated or replayed drone telemetry
- Approximate geotag fusion
- Heading-aware nadir projection
- Pose-aware flat-ground geotagging using yaw/pitch/roll
- Multi-frame tracking with optional Kalman prediction
- Confidence-weighted track scoring
- GeoJSON export
- Mission profiles

See CHANGELOG.md for release history.

## Mission profiles

The toolkit supports config-driven mission profiles.

Built-in verified profiles:
- sar_daylight
- sar_low_visibility

Future/custom profiles can tune detector thresholds, tracking parameters, and scoring weights, but profiles do not replace model validation or operational authorization.

See docs/MISSION_PROFILES.md.

## Design decisions

- `alerts.json` remains frame-level for backward compatibility.
- `tracks.json` is the deduplicated analytical output.
- GeoJSON is generated from tracks, not raw alerts, to avoid map clutter.
- Telemetry replay was added before live drone integration to keep testing reproducible.
- Pose-aware flat-ground geotagging was added before terrain-aware photogrammetry to improve realism while keeping the math inspectable and bounded.

### Pose-aware flat-ground geotagging

`pose_aware_flat_ground` uses telemetry `yaw_deg`, `pitch_deg`, and `roll_deg` to rotate an image ray onto a flat ground plane.

It is more realistic than heading-only projection when aircraft attitude is available, but it is still not terrain-aware photogrammetry and does not replace camera calibration or field validation.

## Suggested review path

1. Read `config.replay.yaml`
2. Run `python main.py --config config.replay.yaml`
3. Inspect `output/alerts.json`
4. Inspect `output/tracks.json`
5. Inspect `output/run_manifest.json`
6. Load `output/tracks.geojson` into a map viewer
7. Read `docs/LIMITATIONS.md`

## Run

Ultralytics-first config:

```bash
pip install -r requirements.txt
python main.py --config config.yaml
```

Model weights are not required for offline mode. Online YOLO mode may download weights on first use.

This repository does not commit model weight binaries. If you want to use a custom YOLO checkpoint, place it locally and point `detector.model` at that path; otherwise use the default online download behavior or the offline-safe HOG configuration.

Offline-safe config:

```bash
pip install -r requirements.txt
python main.py --config config.offline.yaml
```

## Validation

```bash
python -m pytest
python main.py --config config.offline.yaml
python main.py --config config.replay.yaml
```

Detailed validation notes and real-footage results are in docs/VALIDATION.md.

## Release verification

Run:

```bash
python scripts/verify_release.py
```

This verifies the core advertised pipeline without requiring online model downloads.

See [docs/CLAIMS_MATRIX.md](docs/CLAIMS_MATRIX.md) for the public claim-to-test mapping.

## Inputs

- `config.yaml` or `config.offline.yaml`
- `sample_data/video.mp4`

## Outputs

- `sample_data/path.json` — search grid waypoints
- `output/alerts.json` — frame-level detections (one per person per frame)
- `output/tracks.json` — deduplicated confirmed person tracks
- `output/tracks.geojson` — optional GeoJSON FeatureCollection of confirmed tracks for mapping tools
- `output/run_manifest.json` — provenance summary describing what produced the run outputs

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
- `lat`, `lon`: estimated target location from the configured geotagging mode, camera FOV, telemetry, and selected bounding-box point
- `confidence`: YOLO detector confidence (0–1)
- `type`: alert class (currently `possible_person`)

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
- Suitable for SAR planning and area deconfliction, not for ground-truth localization or operational decision-making without human review

For operational systems, geotagging should be replaced with proper camera calibration, ground-truth terrain data, and multi-sensor fusion.

### Heading-aware Geotagging

`heading_aware_nadir` uses telemetry `yaw_deg` to rotate image-space offsets into world-space east/north offsets before applying them to the drone position.

`pose_aware_flat_ground` is also available as an optional mode. It uses telemetry `yaw_deg`, `pitch_deg`, and `roll_deg` to rotate an image ray onto a flat ground plane. This is still approximate, assumes flat ground and a simplified downward-facing camera model, and is not terrain-aware photogrammetry.

```yaml
geotagging:
  mode: pose_aware_flat_ground   # nadir | heading_aware_nadir | pose_aware_flat_ground
  target_point: bbox_bottom_center   # bbox_center | bbox_bottom_center
  include_geotag_metadata: false
  pose_fallback_mode: heading_aware_nadir
```

- `mode: nadir`: Preserves the original behavior where image right maps directly to east and image up maps directly to north.
- `mode: heading_aware_nadir`: Rotates image-space offsets by telemetry `yaw_deg`, so the projected target moves with aircraft heading.
- `mode: pose_aware_flat_ground`: Rotates a camera ray using telemetry yaw, pitch, and roll and intersects it with a flat ground plane. It is more realistic than nadir-only offset rotation but still depends on flat-ground and camera-model assumptions.
- `target_point: bbox_center`: Uses the center of the detection box.
- `target_point: bbox_bottom_center`: Uses the bottom-center of the detection box.
- `include_geotag_metadata`: Adds `geotag_mode`, `geotag_yaw_deg`, and `geotag_target_point` to enriched detections before tracking when enabled.
- `pose_fallback_mode`: Optional fallback for `pose_aware_flat_ground` when the projected ray does not hit the flat ground plane in a valid way. Supported values are `nadir` and `heading_aware_nadir`.

See `docs/GEOTAGGING_MODEL.md` for the coordinate-frame and angle-convention assumptions behind the geotagging modes.

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
- `yaw_deg`, `pitch_deg`, `roll_deg`: Drone orientation in degrees (required; used by `pose_aware_flat_ground` and still subject to the documented flat-ground assumptions)

**Interpolation Behavior:**
- Telemetry is linearly interpolated between logged rows based on video/event time
- Times before the first row use the first row's state
- Times after the last row use the last row's state (safe for short logs with longer videos)
- All six fields (lat, lon, altitude, yaw, pitch, roll) are interpolated

**Geotagging with Replay:**

When using replay mode:
- **Altitude** from the CSV is used for nadir-camera geolocation, enabling realistic vertical accuracy variation
- **lat/lon** are interpolated to smooth position between logged waypoints
- **yaw/pitch/roll** are available for `pose_aware_flat_ground` when a flat-ground pose-aware projection is desired
- Current geotagging remains approximate and assumes flat ground and nadir camera
- In `heading_aware_nadir` mode, `yaw_deg` is used to rotate image offsets into world-space east/north directions

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

- `motion_model`: Set to `none` for baseline greedy tracking or `kalman` to enable constant-velocity bbox prediction
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
- `heading_aware_nadir` uses yaw only. `pose_aware_flat_ground` additionally uses yaw, pitch, and roll, but still assumes flat ground and is not terrain-aware calibrated photogrammetry.
- GeoJSON geometry uses `[longitude, latitude]` order to match the GeoJSON specification.
- GeoJSON export is driven from confirmed tracks only. Alerts are not exported as GeoJSON.
- `config.yaml` uses a pretrained Ultralytics detector and may download weights on first online use. `config.offline.yaml` forces OpenCV HOG detection for offline operation and does not require model weights.
- SimpleTracker remains lightweight: greedy IoU + proximity matching with an optional NumPy Kalman prediction layer.
