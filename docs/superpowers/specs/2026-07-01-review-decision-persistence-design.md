# Review Decision Persistence Design

## Purpose

The review queue can now produce candidate records, but a human-in-the-loop workflow needs an audit trail of what reviewers did with those candidates. This slice adds a minimal persistence layer for review decisions so candidate review can survive process boundaries and later feed UI, metrics, and reviewer-reliability work.

This is not a claim that a candidate is a person. A `confirmed` decision means a reviewer confirmed the candidate in the review workflow, not that SAR-INTEL produced ground truth.

## Scope

- Represent review decisions for motion/review candidates keyed by `tracklet_id`.
- Support the statuses `confirmed`, `rejected`, and `uncertain`.
- Store reviewer id, UTC decision timestamp, optional note, and optional confidence.
- Serialize decisions to JSON-ready records.
- Append decisions to a JSONL audit log and load them back.
- Merge the latest decision for each tracklet into existing review queue records.

## Out of Scope

- User authentication or identity management.
- Concurrent edit conflict resolution beyond append-log ordering by timestamp.
- UI controls for confirm/reject/uncertain.
- Treating reviewer decisions as operational truth.
- Reviewer fatigue scoring, which should build on these persisted events later.

## Data Model

A review decision record has this shape:

```json
{
  "tracklet_id": "motion-0001",
  "status": "confirmed",
  "reviewer": "operator-a",
  "decided_at": "2026-07-01T18:30:00Z",
  "note": "Visible moving person near tree line.",
  "confidence": 0.82
}
```

`note` and `confidence` are optional. Confidence is constrained to the `[0.0, 1.0]` interval.

## Behavior

`ReviewDecision` validates required fields and supported statuses when created. Serialization emits stable JSON-ready dictionaries with UTC timestamps ending in `Z`.

`append_review_decision_jsonl` writes one decision per line, preserving an append-friendly audit trail. `load_review_decisions_jsonl` reads those records back into typed decisions.

`apply_review_decisions` does not mutate the original queue. It copies queue records and overlays the latest decision by `tracklet_id`, setting the candidate status and embedding the review record under `review`.

## Validation

The test suite covers:

- JSON-ready serialization.
- unsupported status rejection.
- confidence range validation.
- latest-decision merge behavior.
- append/load JSONL round-trip.
- chronological serialization of a decision list.

This validates the persistence mechanics. It does not validate reviewer correctness, review UX quality, or field reliability.