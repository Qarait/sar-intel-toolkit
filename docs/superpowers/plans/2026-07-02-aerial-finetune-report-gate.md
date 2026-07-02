# Aerial Fine-Tune Report Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible report gate that decides whether a fine-tuned aerial-person detector can honestly be described as improved.

**Architecture:** Keep `compare_visdrone_runs.py` as the metric authority and add `scripts/report_visdrone_finetune.py` as an orchestration/reporting layer. The report layer wraps comparison results with claim language, validation provenance, gate settings, and optional training metadata.

**Tech Stack:** Python stdlib, existing JSON sweep outputs, pytest, existing VisDrone evaluator/comparison scripts.

---

### Task 1: Report Gate Tests

**Files:**
- Create: `tests/test_report_visdrone_finetune.py`

- [x] **Step 1: Write failing tests**

Add tests for a passing candidate, a failed precision gate, and CLI non-zero behavior when the gate fails.

- [x] **Step 2: Verify red**

Run: `python -m pytest tests\test_report_visdrone_finetune.py -q`

Expected: FAIL because `scripts/report_visdrone_finetune.py` does not exist.

### Task 2: Report Gate Implementation

**Files:**
- Create: `scripts/report_visdrone_finetune.py`
- Modify: `docs/TRAINING_VISDRONE.md`
- Modify: `docs/VISDRONE_VALIDATION.md`
- Modify: `docs/ROADMAP.md`

- [x] **Step 1: Implement report builder**

Create `build_finetune_report()` that calls `compare_runs()` and emits `type`, `version`, `verdict`, `claim`, `gates`, `validation`, `training`, and `comparison` fields.

- [x] **Step 2: Implement CLI**

Add `--baseline`, `--candidate`, `--training-metadata`, `--output`, `--recall-delta`, `--min-precision-ratio`, `--ap-delta`, and `--always-zero`.

- [x] **Step 3: Verify green**

Run: `python -m pytest tests\test_report_visdrone_finetune.py -q`

Expected: PASS.

### Task 3: Full Verification And Merge

**Files:**
- All modified files

- [ ] **Step 1: Run focused checks**

Run: `python -m pytest tests\test_report_visdrone_finetune.py tests\test_compare_visdrone_runs.py -q`

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest`

- [ ] **Step 3: Run release verification**

Run: `python scripts\verify_release.py`

- [ ] **Step 4: Commit, push, PR, and merge after CI**

Commit the feature branch, push it, create a PR, wait for GitHub Actions, and merge only after checks pass.