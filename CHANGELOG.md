# Changelog

## v0.11.4 — Landing page UX polish

Added:
- Demo loading state for metrics, map area, track cards, and feature snippet
- Track filters for `all`, `high_confidence_person`, `possible_person`, and `marginal_person`
- Track-card expand/collapse controls with a default 5-card preview
- SVG favicon for the static landing page

Fixed:
- Decoupled GeoJSON loading from Leaflet map rendering so non-map UI still renders if Leaflet is unavailable
- Improved map fallback behavior while keeping metrics, cards, and snippet visible

Unchanged:
- Python pipeline behavior
- Configs
- Schemas
- Validation docs

## v0.10.0 — VisDrone aerial validation harness

Added:
- VisDrone DET validation script
- Person-category evaluation for `pedestrian` and `people`
- Precision/recall/F1 summary output
- Unit tests for annotation parsing, IoU, matching, and metrics
- VisDrone validation documentation

Unchanged:
- Main pipeline behavior
- Detector behavior
- Tracker behavior
- Geotagging behavior
- Output schemas

## v0.9.1 — Configuration documentation alignment

Fixed:
- Updated `docs/CONFIGURATION.md` to document `pose_aware_flat_ground`
- Documented `pose_fallback_mode`
- Updated README current-capability wording after v0.9.0
- Removed stale wording that implied pose-aware geotagging was still only future work

Unchanged:
- Runtime behavior
- Output schemas
- Detector/tracker/telemetry behavior

## v0.9.0 — Pose-aware flat-ground geotagging

Added:
- Optional `pose_aware_flat_ground` geotagging mode
- Geotagging model design documentation
- Pose-aware geotagging tests covering yaw, pitch, roll, invalid geometry, and failure paths

Fixed:
- Explicitly handled invalid pose-aware ground intersections
- Added optional pose-aware fallback configuration to `heading_aware_nadir` or `nadir`

Unchanged:
- Detector behavior
- Tracker behavior
- Telemetry replay behavior
- `alerts.json` schema
- `tracks.json` schema
- `tracks.geojson` schema

## v0.8.3 — Tracker validation and claims-matrix fix

Added:
- Dedicated Kalman missed-frame continuity test
- Defensive tracker input validation tests

Fixed:
- Corrected claims matrix test references
- Ignored malformed tracker detections with invalid bounding boxes or non-finite values
- Clamped confidence values to [0, 1]
- Guarded Kalman prediction against invalid dt values

Unchanged:
- Detector behavior
- Telemetry replay behavior
- Geotagging behavior
- Output schemas

## v0.8.0 — Mission profile presets

Added:
- `mission_profile` config support
- Built-in `sar_daylight` profile
- Built-in `sar_low_visibility` profile
- Mission profile resolver with deep-merge config overrides
- Mission profile documentation

Unchanged:
- Detector behavior
- Telemetry replay behavior
- Geotagging behavior
- Tracker association behavior
- Output schemas

Notes:
- Wildfire and thermal/night profiles are documented as future/custom profiles requiring validated models.
- Mission profiles are tuning presets, not operational flight guidance.

## v0.7.2 — Release verification and claims matrix

Added:
- Synthetic acceptance pipeline test
- Release verification script
- Claims matrix mapping README claims to tests/docs
- Acceptance fixtures for telemetry and detections

Fixed:
- Planner floating-point terminal waypoint duplication bug

Validation:
- compileall passes
- pytest passes
- offline config passes
- replay config passes

## v0.7 — heading-aware geotagging

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

## v0.6 — Kalman/SORT-style prediction

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

## v0.5 — GeoJSON export

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

## v0.4 — confidence-weighted track scoring

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

## v0.3 — telemetry log replay

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

## v0.2 — tracking and deduplication

Added:
- Track association across frames using bounding-box IoU, approximate GPS proximity, frame-gap limits, and minimum-hit thresholds
- Dual-output flow preserving `alerts.json` while adding confirmed `tracks.json`
- Validation on real street footage showing 1699 frame-level alerts deduplicated into 29 confirmed tracks

Unchanged:
- Frame-level alerts remain backward-compatible

Limitations:
- Tracks represent confirmed detection sequences, not guaranteed unique people
- One person can fragment into multiple tracks in difficult scenes

## v0.1 — frame-level SAR alert pipeline

Added:
- Search-area configuration and lawnmower grid planning
- Frame-by-frame person detection over video input
- Approximate geotag fusion from drone position, altitude, and camera field of view
- Frame-level `alerts.json` output for possible-person detections

Unchanged:
- No multi-frame deduplication yet
- No telemetry replay yet
- No track scoring or GeoJSON export yet

Limitations:
- Alerts are raw frame-level detections, so the same person can appear many times
- Geotagging is approximate and assumes a nadir-style flat-ground projection