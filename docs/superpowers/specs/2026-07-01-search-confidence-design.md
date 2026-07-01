# Search Confidence Design

## Purpose

SAR-INTEL should move beyond "here are detections" and become a search-confidence system:

> What was searched, what was found, what may have been missed, and where should a human review next?

This direction is bold because it treats the current detector weakness as product truth instead of hiding it. A low-recall aerial detector cannot honestly promise complete person finding. It can help measure search coverage, surface uncertain regions, and prioritize human review.

## Product Identity

Primary identity:

> SAR-INTEL turns drone footage into search confidence.

Supporting identity:

> An open, simulation-first SAR triage toolkit that estimates what the drone saw, what it may have missed, and where reviewers should look next.

The project should not compete as the largest aerial detector. It should compete as the most transparent, reviewable, SAR-aware open toolkit for post-flight drone search analysis.

## Build Order

The next phase should be sequenced in this order:

1. Detector calibration and comparison gates.
2. Coverage-confidence prototype with validation tests.
3. Motion-first tracklet candidates.
4. Human review queue ranked by uncertainty, motion, and detector score.
5. Minimal SAR prior.
6. Failure injector.
7. Advanced priors and geotag uncertainty ellipses.

This order keeps the project bold without building a plausible-looking but unvalidated heatmap.

## Module 1: Detector Calibration Gate

Coverage confidence depends on calibrated detector behavior. Before using recall in coverage math, the project needs a repeatable baseline and a fine-tuned comparison path.

Inputs:

- Pinned validation manifest with image/annotation SHA256 hashes.
- Fixed confidence thresholds, initially `0.10`, `0.25`, and `0.50`.
- IoU threshold, initially `0.5`.
- Baseline model output and candidate fine-tuned model output.

Outputs:

- Precision, recall, F1, AP, and PR-curve points.
- Same-manifest comparison result.
- Explicit pass/fail gate for whether a model counts as improved.

Improvement should require recall improvement at fixed thresholds without unacceptable precision collapse, plus AP/PR-curve improvement on the same pinned validation manifest. Coverage-confidence code must treat recall as an input that can be recalibrated after fine-tuning; it must not bake the current baseline recall into the model as a final truth.

## Module 2: Coverage Confidence

Coverage confidence is the flagship idea. The output should not be only detected tracks; it should estimate where the search process remains weak.

For each search grid cell, compute:

- Pass count.
- Approximate camera footprint coverage.
- Altitude range.
- Track/detection evidence.
- Calibrated detector recall estimate for comparable conditions.
- Miss probability estimate.
- Confidence class for review and reporting.

Initial version can use simple flat-grid math and coarse altitude bands. It should not require terrain-aware photogrammetry.

Validation must ship with the prototype:

- Synthetic grid with planted targets.
- Simulated missed detections.
- Multiple pass-count and altitude scenarios.
- Assertions that low-coverage and planted-miss cells are classified as uncertain.

The first prototype validates mechanics and ranking behavior on synthetic inputs: weaker coverage produces higher miss probability, planted targets without detections remain uncertain, and uncertain cells can be prioritized for review. It does not yet prove calibrated real-world probabilities. A cell with `0.70` miss probability should not be described as a real-world 70% miss rate until the detector has been calibrated against appropriate aerial/SAR data and the coverage model has been validated against held-out planted-target or field-like footage.

The map is not trustworthy merely because it looks good; it is trustworthy only if its uncertainty behavior is tested and its recall inputs are recalibrated when better detector metrics become available.

## Module 3: Motion-First Tracklets

Real SAR footage is video, not isolated images. Motion should become a first-class candidate signal.

Pipeline:

```text
video frames
  -> frame differencing / optical flow
  -> small moving candidate blobs
  -> temporal tracklets
  -> detector confirmation when available
  -> reviewer queue
```

The first version should favor simple, inspectable methods over complex deep models:

- Background differencing between nearby frames.
- Morphological cleanup.
- Size and persistence filters.
- Tracklet scoring by duration, speed stability, and motion contrast.

Motion tracklets should be allowed to surface candidates even when the appearance detector is weak.

## Module 4: Review Queue

The project metric should become:

> true candidates found per reviewer minute

The review queue should rank candidates by:

- Coverage uncertainty.
- Motion persistence.
- Detector confidence.
- Track score.
- Pass count and altitude.

A reviewer should work at track-level, not frame-level, with fast decisions:

- Confirm.
- Reject.
- Uncertain.

The first version can be static or file-based. It does not need accounts, live collaboration, or operational dispatch features.

## Module 5: Minimal SAR Prior

The SAR prior should start deliberately small.

Initial inputs:

- Last known position.
- Elapsed time.
- Simple movement radius.
- Optional search-area polygon.

Deferred inputs:

- Terrain class.
- Road/trail/water proximity.
- Lost-person behavior profiles.
- Formal domain-specific SAR behavior models.

This avoids scope creep while still giving the system a transparent prior that can later fuse with coverage and candidate ranking.

## Module 6: Failure Injector

Because the project is simulation-first, it should deliberately stress itself before anyone trusts it.

Initial perturbations:

- GPS jitter.
- Telemetry dropout.
- Altitude drift.
- Heading drift.
- Missing frames.
- Corrupted frames.
- Timestamp gaps.

Outputs:

- Perturbed mission artifacts.
- Degradation report.
- Pass/fail assertions for graceful failure.

This makes operational-envelope honesty visible in the repo, not just written in limitations docs.

## Data Flow

The eventual system is a feedback loop, not a strict waterfall:

```text
video + telemetry + optional search prior
  -> detector + motion candidates
  -> tracklets + map evidence
  -> coverage confidence
  -> ranked human review queue
  -> updated confidence and mission brief
```

Low-coverage cells can lower the threshold for review candidates. Confirmed or rejected candidates can update later confidence reporting.

## Technical Boundaries

Keep the first implementation small:

- No live drone integration.
- No operational dispatch workflow.
- No terrain-aware geotagging requirement.
- No hidden model claims.
- No unvalidated confidence maps.

Each intelligence feature needs a matching validation method.

## Testing And Validation

Required validation by module:

- Detector: pinned manifest, fixed thresholds, AP/PR curve.
- Coverage: planted-target and synthetic-miss mechanics/ranking tests first; calibrated probability tests only after calibrated detector recall inputs exist.
- Motion: persistence, false-positive, and missed-frame tests.
- Review queue: deterministic ranking tests and reviewer-workload metrics.
- Failure injector: perturbation tests and graceful-degradation assertions.

## Success Criteria

This phase succeeds when SAR-INTEL can credibly answer:

- Where did the drone search?
- How well was each area searched?
- What did the system find?
- What might it have missed?
- What should a human review next?
- What failed under stress?

The project should feel less like a model demo and more like an honest rescue-intelligence instrument.
