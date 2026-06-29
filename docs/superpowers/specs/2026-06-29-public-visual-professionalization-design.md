# Public Visual Professionalization Design

## Purpose

Make SAR-INTEL TOOLKIT publicly compelling for a broad audience while preserving technical credibility. The presentation should feel humanitarian and futuristic: a hopeful rescue-intelligence project that people can understand, share, star, and ask about within seconds.

The project should not present itself as a full drone operations platform or an operational SAR replacement. It should present itself boldly as an open-source rescue-intelligence layer that transforms drone-style video, telemetry, detections, tracking, scoring, and GeoJSON into reviewable mission outputs.

## Public Positioning

Primary message:

> Drone footage into rescue intelligence.

Supporting message:

> SAR-INTEL TOOLKIT transforms drone video and telemetry into detected persons, confirmed tracks, confidence scores, and map-ready outputs for humanitarian search-and-rescue research.

Safety line:

> Designed for research, simulation, and human-reviewed SAR workflows. Not a replacement for trained responders or operational command decisions.

This safety line belongs in visible supporting sections, footer copy, docs, and report outputs. The first screen should lead with value and purpose, not disclaimers.

## Audience

The public-facing experience should speak to:

- GitHub visitors deciding whether to star, fork, or contribute.
- Humanitarian technology communities.
- Open-source geospatial and mapping communities.
- Drone, computer-vision, and emergency-management technologists.
- Nontechnical viewers who need to understand the project through visuals.

## Visual Direction

Use bold humanitarian futurism:

- Aerial search imagery or generated rescue-drone visuals.
- High-contrast map panels with confident track points and confidence classes.
- Annotated detection frames showing boxes and scores.
- A clear pipeline animation or visual sequence.
- Validation metrics presented as evidence, not dense academic text.
- A mission report preview that makes outputs tangible.

Avoid military, surveillance, or weaponized aesthetics. The tone should be rescue, coordination, and open-source public benefit.

## Scope

Build a visual proof pack with four user-visible surfaces:

1. Public landing page upgrade in `site/`.
2. README upgrade with screenshots, demo GIF/image references, and a clearer public story.
3. Generated or static demo assets in `site/assets/` and/or `docs/assets/`.
4. A lightweight mission report preview that demonstrates how outputs become a human-readable rescue intelligence summary.

## Landing Page Design

The first viewport should make the project understandable in ten seconds:

- Full-width cinematic hero.
- Headline: "Drone footage into rescue intelligence."
- Subheadline explaining detection, tracking, geotagging, confidence, and map outputs.
- Primary actions: "View Demo", "See GitHub", "Explore Validation".
- A visible hint of the next section on desktop and mobile.

Below the hero:

- A "How it works" section with four visual steps: capture, detect, track, map.
- A live-feeling map demo powered by the existing sanitized GeoJSON.
- A visual validation section with precision, recall, F1, TP, FP, and FN.
- A mission report preview with summary metrics, track table, and map snapshot styling.
- A "Built for human review" section with the safety line.

## README Design

The README should become a strong public entry point:

- Lead with the bold positioning.
- Include a visual demo section near the top.
- Show the pipeline as a compact diagram or screenshot.
- Link to landing page, validation, safety, architecture, configuration, and roadmap.
- Keep the VisDrone recall result visible but frame it as baseline evidence and improvement target.
- Add a "Why this matters" section focused on reducing review burden and turning repeated detections into map-ready intelligence.

## Demo Assets

Use project-native visuals wherever possible:

- Sanitized GeoJSON map screenshot.
- Annotated detection frame mock or generated example.
- Mission report preview screenshot.
- Social preview card.
- Optional short GIF showing the pipeline sequence.

If generated imagery is used, it must be clearly illustrative and not claimed as real incident footage. Real project outputs should be prioritized for credibility.

## Mission Report Preview

Add a public-facing report preview that demonstrates what a run produces:

- Mission summary metrics.
- Track classes and confidence scores.
- Map-ready coordinates shown as approximate demo output.
- A compact limitations/safety note.
- Links back to schemas and validation.

This can initially be a static HTML section on the landing page. A generated report CLI can be a later implementation phase.

## Technical Boundaries

Keep the first implementation lightweight:

- No backend service.
- No account system.
- No live drone integration.
- No operational claims.
- No new model training requirement for the public visual pass.

Prefer static assets and existing outputs so GitHub Pages remains simple and reliable.

## Testing And Verification

Verify:

- Landing page renders on desktop and mobile.
- Map demo still loads `site/assets/demo_tracks.geojson`.
- Text does not overlap at common viewport sizes.
- README links resolve.
- No public copy overclaims operational readiness.
- Existing Python tests still pass if code changes are made outside `site/` and docs.

For frontend checks, use a local static server and browser screenshot review.

## Success Criteria

The project feels professional when viewed cold from GitHub or the landing page:

- A nontechnical viewer understands the mission in ten seconds.
- A technical viewer sees evidence, validation, outputs, and limitations.
- The homepage has a bold visual identity rather than a documentation-only feel.
- The README is shareable and visually anchored.
- The project is positioned as open-source humanitarian SAR intelligence, not a generic drone platform.

