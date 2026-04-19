# Changelog

## v0.7.0 — Heading-aware geotagging

Added:
- `geotagging.mode: nadir | heading_aware_nadir`
- Yaw-aware rotation of image-space offsets into world-space east/north offsets
- `geotagging.target_point: bbox_center | bbox_bottom_center`
- Optional non-breaking geotagging metadata on enriched detections before tracking

Unchanged:
- `alerts.json` schema
- `tracks.json` schema
- GeoJSON schema
- Detector, tracker, and telemetry replay behavior

Limitations:
- Still assumes flat ground
- Does not yet perform full pitch/roll/camera-pose photogrammetry

## v0.6.0 — Kalman/SORT-style track prediction

Added:
- Lightweight constant-velocity Kalman motion model for next-bbox prediction during brief missed detections
- Improved continuity across short detector dropouts and unstable frame-to-frame localization
- Optional track metadata: `motion_model`, `missed_frames`, and `max_consecutive_misses`

Unchanged:
- IoU and GPS proximity remain the association signals
- `alerts.json` schema
- Existing track fields remain backward-compatible

Limitations:
- Not full re-identification
- Does not guarantee unique real-world people

## v0.5.0 — GeoJSON track export

Added:
- GeoJSON `FeatureCollection` export for confirmed tracks
- Map-ready `Point` features using `[longitude, latitude]`
- `heatmap_weight` for map visualization weighting
- Configurable GeoJSON filtering via `geojson.enabled`, `geojson.min_track_score`, and `geojson.include_marginal_tracks`

Unchanged:
- Detector behavior
- Tracker association behavior
- Telemetry replay behavior
- `alerts.json` schema

Limitations:
- GeoJSON export is driven from confirmed tracks only
- Alerts are not exported as GeoJSON

## v0.4.0 — Confidence-weighted track scoring

Added:
- `track_score` derived from mean confidence, peak confidence, and detection density
- `track_class`: `high_confidence_person`, `possible_person`, or `marginal_person`
- `duration_seconds` and `detection_density` fields on confirmed tracks
- Configurable scoring weights and thresholds in `track_scoring`

Unchanged:
- Detector behavior
- Telemetry behavior
- Geotagging behavior
- Track association logic
- `alerts.json` schema

Limitations:
- Confidence classes are not identity claims
- Scoring can be disabled to omit added metadata

## v0.3.0 — Telemetry replay

Added:
- `telemetry.mode: replay` for timestamped CSV telemetry playback
- Dynamic altitude from telemetry state instead of fixed config altitude
- Linear interpolation of `lat`, `lon`, `altitude_m`, `yaw_deg`, `pitch_deg`, and `roll_deg`
- Parsed orientation fields for future pose-aware geotagging

Unchanged:
- Output schemas
- Simulated telemetry mode remains available

Limitations:
- Pose fields are parsed but not yet used for full pose-aware geolocation
- Geotagging remains approximate and flat-ground

## v0.2.0 — Track association and deduplicated outputs

Added:
- Track association across frames using bounding-box IoU, approximate GPS proximity, frame-gap limits, and minimum-hit thresholds
- Dual-output flow preserving `alerts.json` while adding confirmed `tracks.json`
- Validation on real street footage showing 1699 frame-level alerts deduplicated into 29 confirmed tracks

Unchanged:
- Frame-level alerts remain backward-compatible

Limitations:
- Tracks represent confirmed detection sequences, not guaranteed unique people
- One person can fragment into multiple tracks in difficult scenes