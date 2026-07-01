# Search Confidence First Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first executable slice of the SAR-INTEL search-confidence direction: a detector comparison gate and a tested coverage-confidence prototype.

**Architecture:** Keep the detector comparison gate separate from coverage logic. The comparison script validates apples-to-apples VisDrone run outputs; the coverage module consumes already-calibrated recall assumptions and mission-like pass data to produce uncertainty cells. Both pieces are file-based, deterministic, and testable without live drone integration.

**Tech Stack:** Python 3.12, standard library JSON/dataclasses/pathlib/math, pytest, existing VisDrone evaluator JSON outputs.

---

## File Structure

- Create `scripts/compare_visdrone_runs.py`: CLI and pure functions for comparing a baseline evaluator JSON to a candidate evaluator JSON.
- Create `tests/test_compare_visdrone_runs.py`: TDD coverage for manifest mismatch, fixed-threshold recall improvement, precision-collapse rejection, and AP regression rejection.
- Create `coverage_confidence.py`: small pure-Python module for search-grid cells, pass evidence, and miss-probability estimates.
- Create `tests/test_coverage_confidence.py`: synthetic planted-target/coverage behavior tests.
- Modify `docs/VISDRONE_VALIDATION.md`: document how to run and interpret the comparison gate.
- Modify `docs/ROADMAP.md`: update after the first slice lands if implementation changes the roadmap wording.

---

### Task 1: Detector Comparison Gate

**Files:**
- Create: `scripts/compare_visdrone_runs.py`
- Create: `tests/test_compare_visdrone_runs.py`
- Modify: `docs/VISDRONE_VALIDATION.md`

- [ ] **Step 1: Write failing tests for comparison behavior**

Create `tests/test_compare_visdrone_runs.py` with:

```python
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "compare_visdrone_runs.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("compare_visdrone_runs", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _run(threshold_rows, checksum="abc123", ap=0.20):
    return {
        "mode": "sweep",
        "average_precision": ap,
        "validation_manifest": {"checksum": checksum},
        "results": threshold_rows,
    }


def _row(threshold, precision, recall, f1=0.1):
    return {
        "confidence_threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": 1,
        "false_positives": 1,
        "false_negatives": 1,
    }


def test_rejects_manifest_mismatch():
    module = _load_module()
    baseline = _run([_row(0.25, precision=0.8, recall=0.10)], checksum="base")
    candidate = _run([_row(0.25, precision=0.8, recall=0.20)], checksum="candidate")

    result = module.compare_runs(baseline, candidate)

    assert result["passed"] is False
    assert result["reasons"] == ["validation manifest checksum mismatch"]


def test_passes_when_recall_and_ap_improve_without_precision_collapse():
    module = _load_module()
    baseline = _run([
        _row(0.10, precision=0.60, recall=0.20),
        _row(0.25, precision=0.80, recall=0.10),
    ], ap=0.30)
    candidate = _run([
        _row(0.10, precision=0.58, recall=0.32),
        _row(0.25, precision=0.78, recall=0.18),
    ], ap=0.42)

    result = module.compare_runs(
        baseline,
        candidate,
        recall_delta=0.05,
        min_precision_ratio=0.90,
        ap_delta=0.03,
    )

    assert result["passed"] is True
    assert result["thresholds"]["0.10"]["recall_delta"] == 0.12
    assert result["thresholds"]["0.25"]["recall_delta"] == 0.08


def test_rejects_threshold_shopping_precision_collapse():
    module = _load_module()
    baseline = _run([_row(0.25, precision=0.80, recall=0.10)], ap=0.30)
    candidate = _run([_row(0.25, precision=0.30, recall=0.40)], ap=0.45)

    result = module.compare_runs(
        baseline,
        candidate,
        recall_delta=0.05,
        min_precision_ratio=0.90,
        ap_delta=0.03,
    )

    assert result["passed"] is False
    assert "precision collapsed at threshold 0.25" in result["reasons"]


def test_rejects_average_precision_regression():
    module = _load_module()
    baseline = _run([_row(0.25, precision=0.80, recall=0.10)], ap=0.30)
    candidate = _run([_row(0.25, precision=0.80, recall=0.20)], ap=0.31)

    result = module.compare_runs(
        baseline,
        candidate,
        recall_delta=0.05,
        min_precision_ratio=0.90,
        ap_delta=0.03,
    )

    assert result["passed"] is False
    assert "average precision did not improve enough" in result["reasons"]
```

- [ ] **Step 2: Run tests to verify red**

Run:

```bash
python -m pytest tests/test_compare_visdrone_runs.py -q
```

Expected: fail because `scripts/compare_visdrone_runs.py` does not exist.

- [ ] **Step 3: Implement comparison script**

Create `scripts/compare_visdrone_runs.py` with pure functions:

```python
import argparse
import json
from pathlib import Path
from typing import Any, Sequence


def _threshold_key(value: float) -> str:
    return f"{float(value):.2f}"


def _rows_by_threshold(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {_threshold_key(row["confidence_threshold"]): row for row in run.get("results", [])}


def _manifest_checksum(run: dict[str, Any]) -> str | None:
    manifest = run.get("validation_manifest") or {}
    return manifest.get("checksum")


def compare_runs(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    recall_delta: float = 0.05,
    min_precision_ratio: float = 0.90,
    ap_delta: float = 0.03,
) -> dict[str, Any]:
    reasons: list[str] = []
    threshold_results: dict[str, dict[str, float]] = {}

    if _manifest_checksum(baseline) != _manifest_checksum(candidate):
        return {
            "passed": False,
            "reasons": ["validation manifest checksum mismatch"],
            "thresholds": {},
        }

    baseline_rows = _rows_by_threshold(baseline)
    candidate_rows = _rows_by_threshold(candidate)
    common_thresholds = sorted(set(baseline_rows) & set(candidate_rows))
    if not common_thresholds:
        reasons.append("no matching fixed thresholds")

    for threshold in common_thresholds:
        base = baseline_rows[threshold]
        cand = candidate_rows[threshold]
        base_precision = float(base["precision"])
        cand_precision = float(cand["precision"])
        base_recall = float(base["recall"])
        cand_recall = float(cand["recall"])
        precision_ratio = cand_precision / base_precision if base_precision else 0.0
        current_recall_delta = cand_recall - base_recall
        threshold_results[threshold] = {
            "baseline_precision": base_precision,
            "candidate_precision": cand_precision,
            "precision_ratio": precision_ratio,
            "baseline_recall": base_recall,
            "candidate_recall": cand_recall,
            "recall_delta": round(current_recall_delta, 12),
        }
        if current_recall_delta < recall_delta:
            reasons.append(f"recall did not improve enough at threshold {threshold}")
        if precision_ratio < min_precision_ratio:
            reasons.append(f"precision collapsed at threshold {threshold}")

    baseline_ap = float(baseline.get("average_precision", 0.0))
    candidate_ap = float(candidate.get("average_precision", 0.0))
    if candidate_ap - baseline_ap < ap_delta:
        reasons.append("average precision did not improve enough")

    return {
        "passed": not reasons,
        "reasons": reasons,
        "average_precision": {
            "baseline": baseline_ap,
            "candidate": candidate_ap,
            "delta": round(candidate_ap - baseline_ap, 12),
        },
        "thresholds": threshold_results,
    }


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(data: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two VisDrone evaluator sweep outputs.")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", default="output/visdrone_det_comparison.json")
    parser.add_argument("--recall-delta", type=float, default=0.05)
    parser.add_argument("--min-precision-ratio", type=float, default=0.90)
    parser.add_argument("--ap-delta", type=float, default=0.03)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = compare_runs(
        load_json(args.baseline),
        load_json(args.candidate),
        recall_delta=args.recall_delta,
        min_precision_ratio=args.min_precision_ratio,
        ap_delta=args.ap_delta,
    )
    output_path = write_json(result, args.output)
    print(f"Saved VisDrone comparison to {output_path}")
    if result["passed"]:
        print("Comparison gate: PASS")
        return 0
    print("Comparison gate: FAIL")
    for reason in result["reasons"]:
        print(f"- {reason}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused tests to green**

Run:

```bash
python -m pytest tests/test_compare_visdrone_runs.py -q
```

Expected: `4 passed`.

- [ ] **Step 5: Update validation docs**

Add a section to `docs/VISDRONE_VALIDATION.md` named `## Fine-tune comparison gate` with this command:

```bash
python scripts/compare_visdrone_runs.py \
  --baseline output/visdrone_det_sweep.json \
  --candidate output/visdrone_det_finetuned_sweep.json \
  --recall-delta 0.05 \
  --min-precision-ratio 0.90 \
  --ap-delta 0.03 \
  --output output/visdrone_det_comparison.json
```

Explain that a candidate model should not be described as improved unless this gate passes on the same validation manifest.

- [ ] **Step 6: Run full tests and commit**

Run:

```bash
python -m pytest
```

Expected: all tests pass.

Commit:

```bash
git add scripts/compare_visdrone_runs.py tests/test_compare_visdrone_runs.py docs/VISDRONE_VALIDATION.md
git commit -m "Add VisDrone comparison gate"
```

---

### Task 2: Coverage Confidence Prototype

**Files:**
- Create: `coverage_confidence.py`
- Create: `tests/test_coverage_confidence.py`
- Modify: `docs/ROADMAP.md` only if the implementation changes terminology.

- [ ] **Step 1: Write failing coverage tests**

Create `tests/test_coverage_confidence.py` with:

```python
from coverage_confidence import CoveragePass, SearchCell, estimate_cell_confidence, rank_uncertain_cells


def test_more_passes_reduce_miss_probability():
    cell = SearchCell(cell_id="A1", center_lat=43.0, center_lon=-79.0)
    one_pass = [CoveragePass(cell_id="A1", altitude_m=60.0, recall_estimate=0.30)]
    three_passes = one_pass * 3

    one = estimate_cell_confidence(cell, one_pass)
    three = estimate_cell_confidence(cell, three_passes)

    assert one["miss_probability"] == 0.70
    assert round(three["miss_probability"], 3) == 0.343
    assert three["confidence"] > one["confidence"]


def test_planted_miss_keeps_cell_uncertain():
    cell = SearchCell(cell_id="B2", center_lat=43.0, center_lon=-79.0, planted_target=True)
    passes = [CoveragePass(cell_id="B2", altitude_m=80.0, recall_estimate=0.20, detected=False)]

    result = estimate_cell_confidence(cell, passes)

    assert result["class"] == "uncertain"
    assert result["planted_miss"] is True


def test_rank_uncertain_cells_prioritizes_high_miss_probability():
    cells = [
        SearchCell(cell_id="A", center_lat=0.0, center_lon=0.0),
        SearchCell(cell_id="B", center_lat=0.0, center_lon=1.0),
    ]
    passes = [
        CoveragePass(cell_id="A", altitude_m=50.0, recall_estimate=0.80),
        CoveragePass(cell_id="B", altitude_m=100.0, recall_estimate=0.20),
    ]

    ranked = rank_uncertain_cells(cells, passes)

    assert [item["cell_id"] for item in ranked] == ["B", "A"]
```

- [ ] **Step 2: Run tests to verify red**

Run:

```bash
python -m pytest tests/test_coverage_confidence.py -q
```

Expected: fail because `coverage_confidence.py` does not exist.

- [ ] **Step 3: Implement minimal coverage module**

Create `coverage_confidence.py` with:

```python
from dataclasses import dataclass
from math import prod
from typing import Iterable


@dataclass(frozen=True)
class SearchCell:
    cell_id: str
    center_lat: float
    center_lon: float
    planted_target: bool = False


@dataclass(frozen=True)
class CoveragePass:
    cell_id: str
    altitude_m: float
    recall_estimate: float
    detected: bool = False


def _clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def estimate_cell_confidence(cell: SearchCell, passes: Iterable[CoveragePass]) -> dict[str, object]:
    matching_passes = [item for item in passes if item.cell_id == cell.cell_id]
    miss_probability = prod(
        1.0 - _clamp_probability(item.recall_estimate) for item in matching_passes
    ) if matching_passes else 1.0
    confidence = 1.0 - miss_probability
    planted_miss = cell.planted_target and not any(item.detected for item in matching_passes)
    confidence_class = "uncertain" if miss_probability >= 0.50 or planted_miss else "covered"
    return {
        "cell_id": cell.cell_id,
        "center_lat": cell.center_lat,
        "center_lon": cell.center_lon,
        "pass_count": len(matching_passes),
        "miss_probability": round(miss_probability, 12),
        "confidence": round(confidence, 12),
        "class": confidence_class,
        "planted_miss": planted_miss,
    }


def rank_uncertain_cells(cells: Iterable[SearchCell], passes: Iterable[CoveragePass]) -> list[dict[str, object]]:
    pass_list = list(passes)
    estimates = [estimate_cell_confidence(cell, pass_list) for cell in cells]
    return sorted(estimates, key=lambda item: float(item["miss_probability"]), reverse=True)
```

- [ ] **Step 4: Run focused tests to green**

Run:

```bash
python -m pytest tests/test_coverage_confidence.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Run full tests and commit**

Run:

```bash
python -m pytest
```

Expected: all tests pass.

Commit:

```bash
git add coverage_confidence.py tests/test_coverage_confidence.py docs/ROADMAP.md
git commit -m "Add coverage confidence prototype"
```

---

### Task 3: Verification And PR

**Files:**
- Modify: no source files unless verification reveals a real bug.

- [ ] **Step 1: Run release verification**

Run:

```bash
python scripts/verify_release.py
```

Expected: release verification passes. If `sample_data/path.json` is rewritten, restore it with:

```bash
git restore --source=HEAD -- sample_data/path.json
```

- [ ] **Step 2: Check final status**

Run:

```bash
git status -sb
```

Expected: clean working tree after all commits.

- [ ] **Step 3: Push branch**

Run:

```bash
git push -u origin codex/search-confidence-roadmap
```

Expected: branch pushed to GitHub.

- [ ] **Step 4: Open draft PR**

Run:

```bash
gh pr create --repo Qarait/sar-intel-toolkit --draft --base main --head codex/search-confidence-roadmap --title "Add search-confidence first slice" --body "## Summary
- Adds a detector comparison gate for same-manifest VisDrone fine-tune claims.
- Adds the first tested coverage-confidence prototype for miss-probability ranking.
- Documents the SAR-INTEL search-confidence roadmap and design.

## Validation
- python -m pytest
- python scripts\\verify_release.py"
```

Expected: draft PR URL returned.