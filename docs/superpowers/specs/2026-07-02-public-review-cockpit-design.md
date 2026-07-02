# Public Review Cockpit Design

## Purpose

The project now has motion candidates, uncertainty-ranked review queues, and persisted reviewer decisions. The public site needs to show that product direction visually: not just a map of detections, but a human review cockpit where candidates, uncertainty, and decisions are visible together.

This slice makes the audience understand the future product: SAR-INTEL is becoming a search-confidence and review workflow, not a magic detector.

## Scope

- Add a public-site review cockpit section.
- Show a visual frame preview with a candidate box and motion trail.
- Show an uncertainty-ranked candidate queue.
- Show candidate details: motion score, coverage miss probability, review priority, location hint, and why the candidate was surfaced.
- Add demo review actions: confirm candidate, mark uncertain, reject candidate.
- Render an in-page decision log using the same vocabulary as the persisted review-decision module.

## Boundaries

- Browser decisions are demo state only.
- This does not persist decisions to disk or GitHub Pages storage.
- A confirmed candidate means reviewed in the demo workflow, not operational ground truth.
- This is not field SAR software.

## Interaction Model

The user selects a candidate from the queue. The cockpit updates the frame preview, metadata, and action buttons. When the user records a decision, the candidate status changes and a decision-log event is added at the top of the log.

The queue stays deliberately small in this slice so the interaction is legible and testable. Later slices can connect it to generated review queue JSON and real frame crops.

## Validation

The public-site hardening test checks that the cockpit exists, exposes candidate-review actions, and avoids operational overclaim language such as `victim found`.

Manual browser verification should confirm that the cockpit renders on desktop and mobile, the buttons update status, and text does not overlap.