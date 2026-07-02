# Review Candidate Thumbnails Design

## Purpose

The public review cockpit is now artifact-backed, but the frame preview was still an abstract CSS scene. This slice adds public-safe PNG thumbnails so the cockpit feels like a real human-review surface while keeping all operational and location claims bounded.

## Scope

- Generate deterministic PNG thumbnails under `site/assets/review-candidates/`.
- Add each thumbnail path to `site/assets/review_queue.json` under `frame_preview.image`.
- Update the cockpit to render the thumbnail as an image layer behind the bbox and motion trail overlays.
- Keep embedded fallback candidates usable if the JSON asset fails to load.
- Add tests that every thumbnail path is public-safe, exists, and has a PNG signature.

## Safety Boundary

The thumbnails are synthetic public-demo images. They are not mission footage, not evidence of a real person, and do not contain original location context. The overlays remain review-candidate overlays, not operational truth.

## Validation

Tests verify generator freshness, image path safety, PNG signatures, and site rendering hooks. Browser verification should confirm that `assets/review_queue.json` loads, candidate images render in the cockpit frame, and review actions still update the decision log.