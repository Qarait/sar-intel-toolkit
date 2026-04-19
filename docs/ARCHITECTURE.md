# Architecture

```text
Search Area
   ↓
Grid Planner
   ↓
Waypoints

Video Frames ──→ Person Detector ──→ Frame-level Detections
                                      ↓
Telemetry Simulator / Replay ──→ Geotag Fusion
                                      ↓
alerts.json
                                      ↓
Tracker + Kalman Prediction
                                      ↓
Track Scoring
                                      ↓
tracks.json
                                      ↓
GeoJSON Export
                                      ↓
tracks.geojson
```

## Modules

### planner.py

Generates lawnmower-style waypoint grids from a bounded search area. This exists so the project can simulate mission planning inputs without requiring an external flight-planning system.

### detector.py

Runs person detection on video frames and emits frame-level bounding boxes with confidence scores. This exists to turn raw imagery into candidate human detections for downstream fusion and tracking.

### telemetry.py

Provides either simulated waypoint-following telemetry or replayed telemetry from CSV with interpolation over time. This exists so the rest of the pipeline can work against a consistent drone-state interface in both synthetic and replay workflows.

### fusion.py

Projects frame detections into approximate geographic positions using altitude, field of view, and optional heading-aware nadir rotation. This exists to convert image-space detections into map-relevant alert coordinates.

### tracker.py

Associates detections across frames using IoU, proximity, and optional Kalman-based bbox prediction, then summarizes confirmed tracks and scoring metadata. This exists to reduce repeated frame-level detections into higher-level detection sequences that are easier to review.

### geojson_export.py

Transforms confirmed tracks into GeoJSON features and writes map-ready output. This exists to support GIS tools and simple operational visualization without changing the track summary schema.

### main.py

Orchestrates the end-to-end pipeline from config loading through planning, detection, fusion, tracking, and output writing. This exists to provide a single reproducible entry point for offline demos, replay runs, and regression checks.

## Why the pipeline is split this way

- Planning is separate from telemetry so synthetic mission paths and replayed flight logs can share the same downstream processing.
- Detection is separated from geotag fusion so image inference and geographic projection can evolve independently.
- Tracking sits after alert generation because the project preserves frame-level outputs while also producing deduplicated track summaries.
- GeoJSON export is a final translation step so map-specific formatting does not leak into the tracker or alert schemas.