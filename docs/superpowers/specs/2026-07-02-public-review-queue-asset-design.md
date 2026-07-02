# Public Review Queue Asset Design

## Purpose

The public review cockpit should demonstrate the project architecture, not only a hand-coded interface. This slice moves the cockpit candidate queue into a public-safe JSON asset that can be regenerated and checked by tests.

The goal is to make the public demo feel like a real artifact pipeline: generated review candidates feed the cockpit, reviewer actions remain browser-demo state, and the safety boundary stays explicit.

## Scope

- Add `site/assets/review_queue.json` as a sanitized public demo asset.
- Add `scripts/build_public_review_queue.py` to generate and check that asset deterministically.
- Update `site/app.js` to fetch `assets/review_queue.json`, normalize its snake_case records into the cockpit view model, and fall back to embedded demo candidates if loading fails.
- Add tests that verify the asset is current, public-safe, review-ready, and referenced by the site.

## Public Safety Boundary

The asset contains no original mission coordinates, GPS fields, latitude/longitude fields, or operational incident context. It uses review-candidate identifiers, frame ranges, normalized frame-preview percentages, motion score, coverage miss probability, and review priority.

A candidate is still a candidate. The public cockpit does not claim that any record is a person or a field-ready SAR finding.

## Validation

The test suite checks that `scripts/build_public_review_queue.py --check` matches the committed asset, that candidates are sorted by review priority, that frame-preview geometry is bounded to percentages, and that the public site loads the asset before fallback state.