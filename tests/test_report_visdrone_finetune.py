import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "report_visdrone_finetune.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("report_visdrone_finetune", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _run(threshold_rows, checksum="fixed-manifest", ap=0.20):
    return {
        "mode": "sweep",
        "average_precision": ap,
        "validation_manifest": {"checksum": checksum},
        "results": threshold_rows,
    }


def _row(threshold, precision, recall):
    return {
        "confidence_threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": 0.1,
        "true_positives": 10,
        "false_positives": 2,
        "false_negatives": 90,
    }


def test_report_allows_improvement_claim_only_when_gate_passes():
    module = _load_module()
    baseline = _run([
        _row(0.10, precision=0.60, recall=0.10),
        _row(0.25, precision=0.80, recall=0.057),
    ], ap=0.20)
    candidate = _run([
        _row(0.10, precision=0.58, recall=0.22),
        _row(0.25, precision=0.76, recall=0.16),
    ], ap=0.28)

    report = module.build_finetune_report(
        baseline,
        candidate,
        training_metadata={"model": "runs/visdrone_person/yolo26n/weights/best.pt", "dataset": "visdrone_person"},
        recall_delta=0.05,
        min_precision_ratio=0.90,
        ap_delta=0.03,
    )

    assert report["type"] == "sar-intel-visdrone-finetune-report"
    assert report["verdict"] == "candidate_improved"
    assert report["claim"]["allowed"] is True
    assert "same pinned validation manifest" in report["claim"]["language"]
    assert report["validation"]["manifest_checksum"] == "fixed-manifest"
    assert report["validation"]["thresholds_compared"] == ["0.10", "0.25"]
    assert report["training"]["dataset"] == "visdrone_person"


def test_report_blocks_improvement_claim_when_recall_or_precision_gate_fails():
    module = _load_module()
    baseline = _run([_row(0.25, precision=0.80, recall=0.057)], ap=0.20)
    candidate = _run([_row(0.25, precision=0.30, recall=0.18)], ap=0.30)

    report = module.build_finetune_report(
        baseline,
        candidate,
        recall_delta=0.05,
        min_precision_ratio=0.90,
        ap_delta=0.03,
    )

    assert report["verdict"] == "candidate_not_proven"
    assert report["claim"]["allowed"] is False
    assert "precision collapsed at threshold 0.25" in report["comparison"]["reasons"]
    assert "Do not describe this detector as improved" in report["claim"]["language"]


def test_report_marks_shared_manifest_checksum_none_when_manifests_differ():
    module = _load_module()
    baseline = _run([_row(0.25, precision=0.80, recall=0.10)], checksum="baseline", ap=0.30)
    candidate = _run([_row(0.25, precision=0.80, recall=0.20)], checksum="candidate", ap=0.40)

    report = module.build_finetune_report(baseline, candidate)

    assert report["claim"]["allowed"] is False
    assert report["validation"]["manifest_checksum"] is None
    assert report["validation"]["baseline_manifest_checksum"] == "baseline"
    assert report["validation"]["candidate_manifest_checksum"] == "candidate"
    assert "validation manifest checksum mismatch" in report["comparison"]["reasons"]

def test_cli_writes_report_and_returns_nonzero_for_failed_gate(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    output_path = tmp_path / "report.json"
    baseline_path.write_text(json.dumps(_run([_row(0.25, precision=0.80, recall=0.10)], ap=0.30)), encoding="utf-8")
    candidate_path.write_text(json.dumps(_run([_row(0.25, precision=0.20, recall=0.30)], ap=0.40)), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/report_visdrone_finetune.py",
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(candidate_path),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert output_path.exists()
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["claim"]["allowed"] is False
    assert "Fine-tune report: FAIL" in result.stdout