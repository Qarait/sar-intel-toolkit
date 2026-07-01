# Roadmap

SAR-INTEL is evolving from a detection-and-map prototype into a search-confidence toolkit:

> What was searched, what was found, what may have been missed, and where should a human review next?

This roadmap is bold about direction and conservative about claims. Every new intelligence feature needs a validation method before it is treated as trustworthy.

## Completed foundations

- Output schema validation
- Run manifest and provenance reporting
- Telemetry replay
- Track deduplication and scoring
- GeoJSON export
- Pose-aware flat-ground geotagging
- Public VisDrone DET validation harness
- Landing page with GeoJSON demo
- SHA256-pinned VisDrone validation manifests
- Fixed-threshold AP / PR-curve reporting for detector comparisons

## Near-term

- Add a detector comparison gate that refuses apples-to-oranges fine-tune claims.
- Prototype coverage-confidence grid logic with synthetic planted-target mechanics/ranking validation; defer calibrated probability claims until fine-tuned recall inputs and held-out validation exist.
- Add motion-first candidate tracklets from frame differencing or optical flow.
- Add a review queue that ranks track-level candidates by uncertainty, motion, and detector evidence.
- Keep SAR priors minimal at first: last known position, elapsed time, simple movement radius, and optional search-area polygon.

## Longer-term

- Failure injector for GPS jitter, telemetry dropout, altitude drift, missing frames, corrupted frames, and timestamp gaps
- Camera calibration workflow
- Geotag uncertainty ellipses instead of point-only map markers
- Terrain-aware geotagging experiments
- Real drone telemetry adapters
- Video-level tracking validation on public drone datasets
- Advanced SAR priors only after the core coverage/motion/review loop is tested

The purpose of this roadmap is to show direction and prioritization, not to commit to delivery dates or operational readiness.
