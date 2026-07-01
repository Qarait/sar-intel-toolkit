import importlib.util
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