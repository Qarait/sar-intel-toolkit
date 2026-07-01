# Motion-First Tracklets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small, tested motion-first candidate layer that converts synthetic video frames into persistent motion tracklets.

**Architecture:** Create a pure `motion_tracklets.py` module with dataclasses and deterministic functions. Tests create tiny NumPy frames with known motion and assert candidate extraction, persistence filtering, and scoring behavior. No detector fusion, map UI, or video file IO belongs in this slice.

**Tech Stack:** Python 3.12, NumPy, OpenCV connected components, pytest.

---

## Files

- Create `motion_tracklets.py`: frame differencing, candidate extraction, tracklet linking, persistence scoring.
- Create `tests/test_motion_tracklets.py`: synthetic-frame tests for motion mechanics.
- Modify `docs/ROADMAP.md`: mark motion-first tracklets as started/first slice.

---

### Task 1: Motion Candidate And Tracklet Core

- [ ] **Step 1: Write failing tests**

Create `tests/test_motion_tracklets.py` with tests for no motion, persistent moving square, flicker rejection, and stable scoring.

- [ ] **Step 2: Verify red**

Run: `python -m pytest tests/test_motion_tracklets.py -q`

Expected: fails because `motion_tracklets.py` does not exist.

- [ ] **Step 3: Implement minimal module**

Create `motion_tracklets.py` with `MotionCandidate`, `MotionTracklet`, `detect_motion_candidates`, and `build_motion_tracklets`.

- [ ] **Step 4: Verify green**

Run: `python -m pytest tests/test_motion_tracklets.py -q`

Expected: all motion tests pass.

- [ ] **Step 5: Full verification and commit**

Run: `python -m pytest`

Expected: all tests pass.

Commit: `git commit -m "Add motion-first tracklet prototype"`