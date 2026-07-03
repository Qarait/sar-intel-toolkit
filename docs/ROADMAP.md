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
- Fine-tune report gate for publish/no-publish aerial recall claims
- Aerial dataset intake audit for HERIDAL, SeaDronesSee, VisDrone-person, Okutama-Action, and AU-AIR
- HERIDAL-style person-only YOLO conversion for the first external SAR-relevant training source
- Combined person-YOLO dataset builder with source-prefixed files and provenance manifest
- Recall experiment runner that links dataset provenance, candidate sweep, and fine-tune claim gate

## Near-term

- Add a detector comparison gate that refuses apples-to-oranges fine-tune claims.
- Prototype coverage-confidence grid logic with synthetic planted-target mechanics/ranking validation; defer calibrated probability claims until fine-tuned recall inputs and held-out validation exist.
- Add motion-first candidate tracklets from frame differencing or optical flow. First slice: synthetic-frame motion candidates and persistence-scored tracklets.
- Add a review queue that ranks track-level candidates by uncertainty, motion, and detector evidence. First slices: JSON-ready motion records, uncertainty-weighted review ranking, persisted reviewer decisions, a public review cockpit preview, a public-safe review queue asset, and synthetic candidate thumbnails.
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
