# Public Visual Professionalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bold humanitarian-futuristic public presentation for SAR-INTEL TOOLKIT using a static GitHub Pages site, shareable visual assets, and a stronger README.

**Architecture:** Keep the public experience static and repo-native. `site/index.html` owns the content structure, `site/styles.css` owns the visual system and responsive layout, `site/app.js` continues to power the GeoJSON map/cards, and generated/static assets live under `site/assets/` and `docs/assets/`.

**Tech Stack:** HTML, CSS, vanilla JavaScript, Leaflet, static GeoJSON, GitHub Pages, Markdown.

---

### Task 1: Create Public Visual Assets

**Files:**
- Create: `site/assets/hero-rescue-intelligence.png`
- Create: `site/assets/social-preview.png`
- Create: `docs/assets/public-demo-preview.png`

- [ ] **Step 1: Generate the hero image**

Use the image generation tool with this prompt:

```text
Create a cinematic but credible humanitarian search-and-rescue drone technology hero image. A rescue drone surveys a mountainous or forest-edge landscape at dawn, with subtle futuristic map overlays, glowing search grid lines, and small non-military interface markers. The mood is hopeful, clean, open-source humanitarian technology. No weapons, no police/military insignia, no disaster gore, no text in the image. Wide 16:9 composition with space for headline text on the left.
```

Expected: `site/assets/hero-rescue-intelligence.png` exists and is suitable as a first-viewport website hero.

- [ ] **Step 2: Generate the social preview image**

Use the image generation tool with this prompt:

```text
Create a public social preview image for an open-source humanitarian drone search-and-rescue intelligence toolkit. Show a clean futuristic map interface with drone path lines, highlighted detection points, confidence rings, and a hopeful rescue-technology atmosphere. No readable text, no logos, no weapons, no military look. Landscape 1200x630 style composition.
```

Expected: `site/assets/social-preview.png` exists and works for GitHub/social preview usage.

- [ ] **Step 3: Capture or create the public demo preview**

After the landing page is implemented, capture a desktop screenshot of the hero plus map/report area and save it as `docs/assets/public-demo-preview.png`.

Run:

```powershell
python -m http.server 8000 --directory site
```

Expected: Local server starts and the page is reachable at `http://localhost:8000`.

- [ ] **Step 4: Commit visual assets**

```bash
git add site/assets/hero-rescue-intelligence.png site/assets/social-preview.png docs/assets/public-demo-preview.png
git commit -m "Add public visual demo assets"
```

Expected: Commit succeeds with only asset files staged.

---

### Task 2: Rebuild Landing Page Structure

**Files:**
- Modify: `site/index.html`

- [ ] **Step 1: Replace the document metadata**

In `site/index.html`, update the `<title>` and description to:

```html
<title>SAR-INTEL TOOLKIT | Drone footage into rescue intelligence</title>
<meta
  name="description"
  content="Open-source humanitarian SAR intelligence toolkit that turns drone video and telemetry into detections, tracks, confidence scores, and map-ready GeoJSON."
>
<meta property="og:title" content="SAR-INTEL TOOLKIT">
<meta property="og:description" content="Drone footage into rescue intelligence.">
<meta property="og:image" content="assets/social-preview.png">
```

Expected: Browser tab and social metadata use the bold public positioning.

- [ ] **Step 2: Replace the hero header**

Replace the current `<header class="hero" id="top">...</header>` with:

```html
<header class="hero" id="top">
  <div class="hero-media" aria-hidden="true"></div>
  <div class="hero-inner">
    <p class="eyebrow">Open-source humanitarian SAR intelligence</p>
    <h1>Drone footage into rescue intelligence.</h1>
    <p class="subtitle">
      SAR-INTEL TOOLKIT transforms drone-style video and telemetry into detected persons, confirmed tracks, confidence scores, and map-ready GeoJSON.
    </p>
    <div class="hero-actions">
      <a class="button button-primary" href="#demo">View Demo</a>
      <a class="button button-secondary" href="https://github.com/Qarait/sar-intel-toolkit" target="_blank" rel="noreferrer">See GitHub</a>
      <a class="button button-tertiary" href="#validation">Explore Validation</a>
    </div>
    <div class="hero-proof" aria-label="Project proof points">
      <article><strong>23</strong><span>confirmed demo tracks</span></article>
      <article><strong>GeoJSON</strong><span>map-ready outputs</span></article>
      <article><strong>Open</strong><span>MIT licensed toolkit</span></article>
    </div>
  </div>
</header>
```

Expected: First viewport leads with the public message, visual proof points, and action links.

- [ ] **Step 3: Add a four-step story section**

Insert this section immediately after `<main class="page">`:

```html
<section class="story-strip" aria-label="How SAR-INTEL TOOLKIT works">
  <article>
    <span>01</span>
    <h2>Scan</h2>
    <p>Drone-style footage and mission telemetry become structured review inputs.</p>
  </article>
  <article>
    <span>02</span>
    <h2>Detect</h2>
    <p>Person detections are converted into geotagged possible-person alerts.</p>
  </article>
  <article>
    <span>03</span>
    <h2>Track</h2>
    <p>Repeated detections are linked into confidence-scored tracks.</p>
  </article>
  <article>
    <span>04</span>
    <h2>Map</h2>
    <p>Confirmed tracks export as GeoJSON for maps, dashboards, and review.</p>
  </article>
</section>
```

Expected: Nontechnical visitors understand the pipeline before reaching dense details.

- [ ] **Step 4: Add a visual proof section**

Insert this section before the map section:

```html
<section class="panel visual-proof-panel">
  <div>
    <p class="section-tag">Visual proof</p>
    <h2>From noisy footage to reviewable rescue signals.</h2>
    <p>
      The public demo presents the toolkit as a rescue-intelligence layer: detections become scored tracks, tracks become map features, and every output stays available for human review.
    </p>
  </div>
  <div class="proof-stage" aria-label="Detection and map preview">
    <div class="frame-preview">
      <span class="scan-line"></span>
      <div class="bbox bbox-primary"><strong>possible_person</strong><small>0.91</small></div>
      <div class="bbox bbox-secondary"><strong>possible_person</strong><small>0.74</small></div>
    </div>
    <div class="mission-card">
      <span>Mission intelligence preview</span>
      <strong>23 confirmed tracks</strong>
      <p>Confidence-scored outputs ready for map review and downstream tools.</p>
    </div>
  </div>
</section>
```

Expected: Landing page gains a strong visual asset even before visitors interact with the map.

- [ ] **Step 5: Retitle existing sections**

Update existing section headings:

```html
<p class="section-tag">Mission noise</p>
<h2>Search footage becomes usable intelligence when repeated detections are connected.</h2>
```

```html
<p class="section-tag">Pipeline</p>
<h2>Plan, detect, geotag, track, score, export.</h2>
```

```html
<p class="section-tag">Demo intelligence</p>
<h2>Live metrics from the sanitized public demo.</h2>
```

Expected: Copy becomes more direct and public-facing.

- [ ] **Step 6: Add a mission report preview**

Insert this section after the map panel:

```html
<section class="panel report-panel">
  <div>
    <p class="section-tag">Mission report</p>
    <h2>A run becomes a human-readable rescue intelligence brief.</h2>
    <p>
      The toolkit already exports machine-readable files. The public presentation shows how those artifacts become a concise report for review, triage, and communication.
    </p>
  </div>
  <div class="report-preview">
    <div class="report-header">
      <span>SAR-INTEL brief</span>
      <strong>Sanitized demo run</strong>
    </div>
    <dl>
      <div><dt>Alerts</dt><dd>2,502</dd></div>
      <div><dt>Confirmed tracks</dt><dd>23</dd></div>
      <div><dt>Geotag mode</dt><dd>pose_aware_flat_ground</dd></div>
      <div><dt>Output</dt><dd>tracks.geojson</dd></div>
    </dl>
    <p>
      Designed for research, simulation, and human-reviewed SAR workflows. Not a replacement for trained responders or operational command decisions.
    </p>
  </div>
</section>
```

Expected: Public visitors can see the end-user value of the artifacts.

- [ ] **Step 7: Commit landing page HTML**

```bash
git add site/index.html
git commit -m "Refresh public landing page story"
```

Expected: Commit includes only `site/index.html`.

---

### Task 3: Rebuild Visual Styling

**Files:**
- Modify: `site/styles.css`

- [ ] **Step 1: Replace the root theme**

Replace the current `:root` block with:

```css
:root {
  --night: #08111f;
  --night-soft: #102033;
  --paper: #f4f8fb;
  --paper-strong: #ffffff;
  --ink: #eaf3ff;
  --ink-dark: #102033;
  --muted: #9fb2c8;
  --muted-dark: #52657c;
  --line: rgba(234, 243, 255, 0.16);
  --line-dark: rgba(16, 32, 51, 0.12);
  --cyan: #5ee3ff;
  --signal: #b8f36b;
  --coral: #ff8f70;
  --blue: #2c76ff;
  --shadow: 0 26px 80px rgba(3, 9, 18, 0.28);
}
```

Expected: Palette shifts from quiet documentation page to humanitarian-futuristic presentation.

- [ ] **Step 2: Update body and hero styles**

Add or replace these blocks:

```css
body {
  margin: 0;
  font-family: "Space Grotesk", sans-serif;
  color: var(--ink);
  background: var(--night);
}

.hero {
  position: relative;
  min-height: 92vh;
  display: grid;
  align-items: end;
  overflow: hidden;
  padding: 48px 0 56px;
}

.hero-media {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(8, 17, 31, 0.96) 0%, rgba(8, 17, 31, 0.76) 45%, rgba(8, 17, 31, 0.34) 100%),
    url("assets/hero-rescue-intelligence.png") center/cover;
}

.hero-inner {
  position: relative;
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

h1 {
  max-width: 820px;
  margin-bottom: 18px;
  font-size: clamp(3rem, 8vw, 7.4rem);
  line-height: 0.92;
  letter-spacing: 0;
}

.subtitle {
  max-width: 760px;
  color: #d6e6f8;
  font-size: clamp(1.1rem, 2vw, 1.45rem);
  line-height: 1.45;
  font-weight: 600;
}
```

Expected: Hero becomes cinematic and readable, with no negative letter spacing.

- [ ] **Step 3: Add story and proof styles**

Add these blocks:

```css
.story-strip {
  width: min(1180px, calc(100% - 32px));
  margin: -34px auto 28px;
  position: relative;
  z-index: 3;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  border: 1px solid var(--line);
  background: rgba(234, 243, 255, 0.14);
}

.story-strip article {
  min-height: 190px;
  padding: 24px;
  background: rgba(12, 28, 50, 0.94);
}

.story-strip span,
.section-tag {
  color: var(--signal);
}

.story-strip h2 {
  margin: 18px 0 10px;
  color: var(--ink);
  font-size: 1.55rem;
}

.story-strip p {
  color: var(--muted);
  margin: 0;
}

.visual-proof-panel,
.report-panel {
  display: grid;
  grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.15fr);
  gap: 28px;
  align-items: center;
}

.proof-stage {
  position: relative;
  min-height: 380px;
  border: 1px solid var(--line);
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(94, 227, 255, 0.16), transparent 38%),
    linear-gradient(180deg, #122641, #07111f);
}

.frame-preview {
  position: absolute;
  inset: 26px;
  border: 1px solid rgba(94, 227, 255, 0.28);
  background:
    linear-gradient(rgba(94, 227, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(94, 227, 255, 0.08) 1px, transparent 1px);
  background-size: 34px 34px;
}

.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  top: 42%;
  height: 2px;
  background: var(--signal);
  box-shadow: 0 0 24px rgba(184, 243, 107, 0.86);
}

.bbox {
  position: absolute;
  display: grid;
  gap: 4px;
  padding: 8px;
  border: 2px solid var(--signal);
  color: var(--ink);
  background: rgba(8, 17, 31, 0.64);
}

.bbox-primary {
  width: 160px;
  height: 112px;
  left: 18%;
  top: 34%;
}

.bbox-secondary {
  width: 126px;
  height: 92px;
  right: 17%;
  top: 22%;
  border-color: var(--cyan);
}

.mission-card,
.report-preview {
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: var(--shadow);
}
```

Expected: Page gains a bold proof visualization without depending on fragile external footage.

- [ ] **Step 4: Convert panels to dark presentation surfaces**

Update `.panel`, `.metric-card`, `.track-card`, `.outputs-grid article`, `.links-grid a`, `.validation-stats article`, and `.snippet-card` so their backgrounds use dark translucent surfaces:

```css
.panel {
  margin-top: 28px;
  padding: 30px;
  border: 1px solid var(--line);
  background: rgba(14, 30, 52, 0.9);
  box-shadow: var(--shadow);
}

.metric-card,
.validation-stats article,
.track-card,
.outputs-grid article,
.links-grid a {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--line);
  color: var(--ink);
}
```

Expected: Existing dynamic content remains readable inside the new identity.

- [ ] **Step 5: Add responsive rules**

Add these rules at the end:

```css
@media (max-width: 960px) {
  .story-strip,
  .visual-proof-panel,
  .report-panel {
    grid-template-columns: 1fr 1fr;
  }

  .hero {
    min-height: 86vh;
  }
}

@media (max-width: 680px) {
  .story-strip,
  .visual-proof-panel,
  .report-panel {
    grid-template-columns: 1fr;
  }

  .hero {
    min-height: 92vh;
    padding-top: 36px;
  }

  .hero-proof {
    grid-template-columns: 1fr;
  }
}
```

Expected: No text overlap on mobile and hero still shows the first section hint.

- [ ] **Step 6: Commit styling**

```bash
git add site/styles.css
git commit -m "Restyle public site with bold rescue identity"
```

Expected: Commit includes only `site/styles.css`.

---

### Task 4: Improve Dynamic Demo Copy

**Files:**
- Modify: `site/app.js`

- [ ] **Step 1: Update metric labels**

Replace `baseMetrics` with:

```javascript
const baseMetrics = [
  {
    label: "Frame-level signals",
    value: "2502",
    detail: "Possible-person alerts from the representative static demo run.",
  },
  {
    label: "Confirmed tracks",
    value: "23",
    detail: "Repeated detections grouped into reviewable track objects.",
  },
  {
    label: "Map features",
    value: "pending",
    detail: "Loaded directly from the sanitized public GeoJSON asset.",
  },
  {
    label: "Telemetry",
    value: "simulated",
    detail: "Static demo uses repeatable simulated telemetry inputs.",
  },
  {
    label: "Geotagging",
    value: "pose aware",
    detail: "Flat-ground pose-aware projection for approximate demo coordinates.",
  },
  {
    label: "Tracking",
    value: "kalman",
    detail: "Kalman-assisted continuity across short missed detections.",
  },
];
```

Expected: Metrics read as public-facing intelligence signals instead of raw implementation labels.

- [ ] **Step 2: Update track filter labels**

Replace `FILTER_OPTIONS` with:

```javascript
const FILTER_OPTIONS = [
  { value: "all", label: "All tracks" },
  { value: "high_confidence_person", label: "High confidence" },
  { value: "possible_person", label: "Possible person" },
  { value: "marginal_person", label: "Marginal" },
];
```

Expected: Filter controls are easier for public visitors to understand.

- [ ] **Step 3: Improve popup copy**

Replace the `marker.bindPopup(...)` call with:

```javascript
marker.bindPopup(
  `<strong>Track ${properties.track_id}</strong><br>` +
  `Review class: ${properties.track_class}<br>` +
  `Confidence score: ${properties.track_score}<br>` +
  `Frame hits: ${properties.hits}`
);
```

Expected: Map popups sound like review intelligence rather than debug output.

- [ ] **Step 4: Commit JavaScript copy update**

```bash
git add site/app.js
git commit -m "Polish public demo copy"
```

Expected: Commit includes only `site/app.js`.

---

### Task 5: Upgrade README Opening

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the opening section**

Replace the paragraph from the title through the current documentation links with:

```markdown
# SAR-INTEL TOOLKIT

[![CI](https://github.com/Qarait/sar-intel-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Qarait/sar-intel-toolkit/actions/workflows/ci.yml)

**Drone footage into rescue intelligence.**

SAR-INTEL TOOLKIT is an open-source humanitarian search-and-rescue intelligence pipeline. It turns drone-style video and telemetry into possible-person detections, confirmed tracks, confidence scores, run provenance, and map-ready GeoJSON.

![SAR-INTEL TOOLKIT public demo](docs/assets/public-demo-preview.png)

Project landing page: https://qarait.github.io/sar-intel-toolkit/

## Why this matters

Drone search footage can become noisy fast: repeated detections, uncertain positions, and too many frames for a human reviewer to scan manually. This toolkit turns that stream into structured outputs that can be inspected, scored, mapped, and improved.

## Public proof

- Automated tests live in `tests/`.
- Output contracts live in `schemas/` and are validated in test coverage.
- Public aerial-drone validation results live in `docs/VISDRONE_VALIDATION.md`.
- Project constraints and non-goals live in `docs/LIMITATIONS.md`.
- Safety and intended-use guidance live in `docs/SAFETY.md`.
- System flow and module responsibilities live in `docs/ARCHITECTURE.md`.
- Configuration options live in `docs/CONFIGURATION.md`.
- Mission profile presets live in `docs/MISSION_PROFILES.md`.
- Near-term priorities live in `docs/ROADMAP.md`.
```

Expected: README opens with public positioning, visual preview, and proof links.

- [ ] **Step 2: Add a visual demo section**

Insert after "Public proof":

```markdown
## Visual demo

The public site presents a sanitized demo run with:

- mission-style summary metrics
- confidence-scored track cards
- interactive GeoJSON map features
- a representative mission report preview
- validation and safety context

The demo is static and public-safe. It is intended to communicate the workflow, not to represent a real incident location.
```

Expected: README tells visitors what they can see before asking them to run code.

- [ ] **Step 3: Commit README update**

```bash
git add README.md
git commit -m "Strengthen public README presentation"
```

Expected: Commit includes only `README.md`.

---

### Task 6: Browser Verification

**Files:**
- Inspect: `site/index.html`
- Inspect: `site/styles.css`
- Inspect: `site/app.js`
- Inspect: `README.md`

- [ ] **Step 1: Start static server**

Run:

```powershell
python -m http.server 8000 --directory site
```

Expected: Server reports it is serving HTTP on port 8000.

- [ ] **Step 2: Verify desktop layout**

Open `http://localhost:8000` in a real browser at `1440x1000`.

Expected:
- Hero image renders.
- Headline is readable.
- Story strip is visible below the hero.
- Map loads and displays track markers.
- Mission report preview is visible.
- No major text overlap.

- [ ] **Step 3: Verify mobile layout**

Resize browser to `390x844`.

Expected:
- Hero text remains inside viewport.
- Buttons wrap cleanly.
- Story cards stack or form a readable two-column layout.
- Map, track cards, and report preview do not overlap.

- [ ] **Step 4: Verify link and asset references**

Run:

```powershell
Test-Path site\assets\hero-rescue-intelligence.png
Test-Path site\assets\social-preview.png
Test-Path docs\assets\public-demo-preview.png
```

Expected: Each command prints `True`.

- [ ] **Step 5: Run smoke tests**

Run:

```powershell
python scripts\verify_release.py
```

Expected: Release verification exits successfully.

- [ ] **Step 6: Final commit if verification fixes were needed**

If verification required layout or copy fixes, stage only those changed files:

```bash
git add site/index.html site/styles.css site/app.js README.md docs/assets/public-demo-preview.png
git commit -m "Verify public visual presentation"
```

Expected: Commit includes only verification fixes and generated preview updates.

