# Configuration Reference

This document describes the YAML configuration surface used by the toolkit. Example configurations live in `config.yaml`, `config.offline.yaml`, `config.replay.yaml`, and `config.real.yaml`.

The pipeline currently reads these top-level sections:

- `mission_profile`
- `mission_profiles`
- `search_area`
- `mission`
- `video`
- `detector`
- `camera`
- `telemetry`
- `tracking`
- `track_scoring`
- `geotagging`
- `geojson`
- `output`

Mission profile behavior and built-in presets are documented in `docs/MISSION_PROFILES.md`.

## mission_profile

Selects a named preset to deep-merge into the loaded config before the run starts.

Fields:
- scalar string such as `sar_daylight` or `sar_low_visibility`

Behavior:
- If omitted, the config is used as written.
- If present, the selected profile is applied before detector, tracking, telemetry, and output components are created.
- The resolved preset name is exposed internally as `resolved_mission_profile` and printed once at runtime.

Notes:
- Mission profiles tune existing config values; they do not change core pipeline behavior.
- Unsupported names raise a startup error listing available built-in and custom profiles.

## mission_profiles

Optional mapping of custom named presets defined inside a config file.

Behavior:
- Custom entries are checked before built-in presets with the same name.
- Each profile is deep-merged into the base config, so nested sections such as `tracking.kalman` and `track_scoring.weights` can override only the keys they need.

Notes:
- This mechanism is intended for validated mission-specific tuning, not automatic detector switching or schema changes.

## search_area

Defines the bounding box used by the grid planner.

Fields:
- `min_lat`: minimum latitude of the search area
- `min_lon`: minimum longitude of the search area
- `max_lat`: maximum latitude of the search area
- `max_lon`: maximum longitude of the search area

Notes:
- `min_lat < max_lat` and `min_lon < max_lon` are required.
- These values are consumed by `planner.py` when generating the waypoint grid.

## mission

Defines grid-planning and simulated-flight parameters.

Fields:
- `altitude_m`: planned flight altitude in meters
- `lane_spacing_m`: row spacing for the lawnmower grid in meters
- `forward_step_m`: spacing between waypoints along each row in meters
- `drone_speed_mps`: simulated drone speed in meters per second

Notes:
- All values must be greater than zero.
- `drone_speed_mps` is used only when `telemetry.mode` is `simulated`.

## video

Controls the video input and timestamping behavior.

Fields:
- `path`: input video path passed to OpenCV
- `frame_stride`: process every `N`th frame; `1` means process every frame
- `start_time_utc`: UTC timestamp assigned to frame `0`

Defaults and behavior:
- `frame_stride` defaults to `1` if omitted.
- `start_time_utc` must be an ISO 8601 UTC-style timestamp such as `2026-04-17T19:30:00Z`.
- If FPS metadata cannot be read from the video file, the runtime falls back to `30.0` FPS and logs a warning.

## detector

Controls the person detector backend and confidence filtering.

Fields:
- `model`: detector backend or model path
- `confidence_threshold`: minimum confidence required to keep a detection

Supported values:
- `model: hog` forces the OpenCV HOG people detector
- `model: yolov8n.pt` or another Ultralytics-compatible model path uses YOLO when available

Notes:
- If Ultralytics is unavailable or model initialization fails, the code falls back to HOG.
- `confidence_threshold` is applied by both HOG and YOLO paths.

## camera

Defines the camera field-of-view values used for approximate geotagging.

Fields:
- `horizontal_fov_deg`: horizontal field of view in degrees
- `vertical_fov_deg`: vertical field of view in degrees

Notes:
- These values affect image-space to ground-offset projection in `fusion.py`.
- They matter even in replay mode because geotagging still uses the current video frame geometry.

## telemetry

Controls whether drone state comes from simulation or replay.

Fields:
- `mode`: telemetry source mode
- `replay_path`: CSV telemetry log path used in replay mode

Supported values:
- `mode: simulated`
- `mode: replay`

Behavior:
- In `simulated` mode, the toolkit derives drone position from the generated waypoint path and `mission.drone_speed_mps`.
- In `replay` mode, `telemetry.replay_path` is required and must point to a CSV file with the expected telemetry columns.

Replay CSV requirements:
- `timestamp`
- `lat`
- `lon`
- `altitude_m`
- `yaw_deg`
- `pitch_deg`
- `roll_deg`

Notes:
- Replay timestamps are interpolated over time.
- Out-of-range replay requests are clamped to the first or last telemetry row.

## tracking

Controls multi-frame track association and optional Kalman prediction.

Fields:
- `enabled`: enable or disable track association entirely
- `include_track_id_in_alerts`: when true, include `track_id` in frame-level alerts
- `iou_threshold`: minimum bounding-box IoU for association
- `max_frame_gap`: maximum processed-frame gap allowed for linking detections
- `max_position_distance_m`: maximum geographic distance in meters for association
- `min_hits`: minimum number of matched detections required before a track is exported
- `motion_model`: tracking motion model
- `kalman`: nested Kalman filter settings

Supported values:
- `motion_model: none`
- `motion_model: kalman`

`tracking.kalman` fields:
- `process_noise`: process noise applied during prediction
- `measurement_noise`: measurement noise applied during update
- `initial_uncertainty`: starting covariance scale for new tracks

Defaults used by the code when keys are omitted:
- `enabled: false`
- `include_track_id_in_alerts: false`
- `iou_threshold: 0.25`
- `max_frame_gap: 10`
- `max_position_distance_m: 12.0`
- `min_hits: 3`
- `motion_model: none`
- `process_noise: 1.0`
- `measurement_noise: 10.0`
- `initial_uncertainty: 100.0`

## track_scoring

Controls confidence-weighted scoring on confirmed tracks.

Fields:
- `enabled`: enable or disable scoring metadata
- `high_confidence_threshold`: threshold for `high_confidence_person`
- `possible_confidence_threshold`: threshold for `possible_person`
- `weights`: nested scoring weights

`track_scoring.weights` fields:
- `mean_confidence`: weight for average detection confidence
- `max_confidence`: weight for peak detection confidence
- `detection_density`: weight for how consistently the track appears over time

Defaults used by the code when keys are omitted:
- `enabled: true`
- `high_confidence_threshold: 0.80`
- `possible_confidence_threshold: 0.55`
- `mean_confidence: 0.55`
- `max_confidence: 0.25`
- `detection_density: 0.20`

Notes:
- If scoring is disabled, the tracker still exports confirmed tracks, but scoring-related fields are omitted.

## geotagging

Controls how image detections are projected into approximate geographic coordinates.

Fields:
- `mode`: geotagging mode
- `target_point`: image point selected from the bounding box
- `include_geotag_metadata`: include extra geotag fields on enriched detections before tracking
- `pose_fallback_mode`: optional fallback mode used only when `pose_aware_flat_ground` cannot intersect the flat ground plane

Supported `mode` values:
- `nadir`
- `heading_aware_nadir`
- `pose_aware_flat_ground`

Supported `target_point` values:
- `bbox_center`
- `bbox_bottom_center`

Supported `pose_fallback_mode` values:
- omitted / null
- `nadir`
- `heading_aware_nadir`

Behavior:
- `nadir` uses camera-relative offsets directly.
- `heading_aware_nadir` rotates camera/image offsets by telemetry `yaw_deg`.
- `pose_aware_flat_ground` builds a camera ray from the selected image point, rotates it using telemetry `yaw_deg`, `pitch_deg`, and `roll_deg`, and intersects it with a flat ground plane.
- If `pose_aware_flat_ground` cannot intersect the ground plane and `pose_fallback_mode` is set, the pipeline falls back to that configured mode.
- If no fallback is configured, the run raises a clear error.

Notes:
- `pose_aware_flat_ground` is still approximate.
- It assumes flat ground.
- It assumes the telemetry yaw/pitch/roll sign conventions match `docs/GEOTAGGING_MODEL.md`.
- It does not use terrain data.
- It does not perform full calibrated photogrammetry.
- `include_geotag_metadata` defaults to `false`.

## geojson

Controls optional GeoJSON export for confirmed tracks.

Fields:
- `enabled`: enable or disable GeoJSON export
- `tracks_path`: output path for the GeoJSON file
- `min_track_score`: minimum score required for a track to appear in GeoJSON
- `include_marginal_tracks`: include or exclude tracks classified as `marginal_person`

Defaults used by the code when keys are omitted:
- `enabled: false`
- `tracks_path: output/tracks.geojson`
- `min_track_score: 0.0`
- `include_marginal_tracks: true`

Notes:
- GeoJSON export operates on confirmed tracks, not raw alerts.
- Geometry uses `[longitude, latitude]` order.

## output

Controls where generated artifacts are written.

Fields:
- `alerts_path`: frame-level alert output path
- `tracks_path`: confirmed-track JSON output path
- `waypoints_path`: waypoint-grid output path

Behavior:
- `alerts_path` is required because it also determines where `run_manifest.json` is written.
- `tracks_path` is used only when tracking is enabled.
- Parent directories are created automatically when needed.

Related generated artifact:
- `run_manifest.json` is written next to `alerts_path`, not configured separately.

## Example

```yaml
video:
  path: sample_data/video.mp4
  frame_stride: 2
  start_time_utc: "2026-04-17T19:30:00Z"

detector:
  model: hog
  confidence_threshold: 0.5

telemetry:
  mode: replay
  replay_path: sample_data/telemetry.csv

tracking:
  enabled: true
  motion_model: kalman

track_scoring:
  enabled: true

geotagging:
  mode: pose_aware_flat_ground
  target_point: bbox_bottom_center
  include_geotag_metadata: false
  pose_fallback_mode: heading_aware_nadir

geojson:
  enabled: true
  tracks_path: output/tracks.geojson

output:
  alerts_path: output/alerts.json
  tracks_path: output/tracks.json
  waypoints_path: sample_data/path.json
```