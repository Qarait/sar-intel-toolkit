# Tracklet Review Export Design

## Purpose

Motion tracklets need to leave the algorithm layer as reviewable artifacts. This slice creates a small JSON-ready representation and a deterministic review queue so later UI and coverage-map work can consume motion candidates without re-running video analysis.

## Scope

The slice exports motion tracklets with frame range, duration, score, displacement, and per-frame candidate geometry. It also ranks review items by motion score plus coverage miss probability.

## Boundaries

- Tracklet records are review candidates, not confirmed people.
- Queue status starts as `unreviewed`; confirm/reject/uncertain persistence is a later slice.
- Coverage uncertainty is consumed as an input keyed by tracklet ID; this slice does not compute map cells.

## Validation

Synthetic tests assert JSON-ready serialization, uncertainty-first ranking, and safe defaults when coverage evidence is missing.