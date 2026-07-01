# Motion-First Tracklets Design

## Purpose

SAR-INTEL should treat drone footage as video evidence, not a pile of still images. At altitude, a person can be weak or invisible to an appearance detector in any single frame, while still producing a persistent motion signal across time. This slice adds the first inspectable motion-first candidate layer.

## Product Role

Motion-first tracklets are not verified person detections. They are review candidates that can raise recall by surfacing persistent small motion even when the appearance detector is uncertain or silent.

The feature supports the search-confidence direction:

- low-confidence coverage cells can later lower review thresholds for motion candidates;
- persistent motion can push a cell or tracklet higher in the review queue;
- rejected motion candidates can help tune false-positive filters.

## First Slice

The first implementation uses simple, deterministic computer vision:

1. Convert adjacent frames to grayscale.
2. Compute absolute frame difference.
3. Threshold changed pixels.
4. Use connected components to create motion candidates.
5. Link candidates across time by nearest centroid.
6. Keep only tracklets that persist for enough frames.
7. Score tracklets by persistence and motion stability.

This is deliberately not optical flow yet. Frame differencing is cheap, testable, and enough to prove the interface.

## Boundaries

- No detector fusion in this slice.
- No map/review UI wiring in this slice.
- No claim that motion candidates are people.
- No real-video benchmark claim yet.
- No dependency beyond existing `numpy` and `opencv-python`.

## Validation

The first tests use synthetic frames because they provide known motion truth:

- a moving square produces a tracklet;
- identical frames produce no candidates;
- a one-frame flicker is rejected by persistence filtering;
- persistent movement receives a higher score than unstable movement.

These tests validate mechanics and ranking behavior. They do not prove real-world SAR recall improvement; that requires later tests on field-like footage.

## Data Structures

`MotionCandidate` records frame index, bounding box, centroid, area, and mean frame-difference intensity.

`MotionTracklet` records linked candidates, duration, displacement, and score.

The module should remain pure and file-free so later pipeline code can feed it frames from video readers, tests, or synthetic generators.