# Claims Matrix

| Public claim | Verified by |
|---|---|
| Generates search grids | `tests/test_planner.py` |
| Supports telemetry replay | `tests/test_telemetry_replay.py` |
| Supports heading-aware geotagging | `tests/test_fusion_heading.py` |
| Tracks detections across frames | `tests/test_tracker_scoring.py` |
| Supports Kalman missed-frame continuity | `tests/test_tracker_kalman.py` |
| Scores confirmed tracks | `tests/test_tracker_scoring.py` |
| Exports GeoJSON with [lon, lat] | `tests/test_geojson_export.py` |
| Core advertised pipeline works without YOLO or a large video | `tests/test_acceptance_pipeline.py` |
| Full pipeline works without online model download | `scripts/verify_release.py` |
| Real-footage validation: 1699 → 29 | `docs/VALIDATION.md` |