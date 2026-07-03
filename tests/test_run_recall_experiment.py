import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_recall_experiment.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_recall_experiment", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sweep(recall, precision=0.80, checksum="manifest", ap=0.30):
    return {
        "mode": "sweep",
        "average_precision": ap,
        "validation_manifest": {"checksum": checksum},
        "results": [
            {
                "confidence_threshold": 0.25,
                "precision": precision,
                "recall": recall,
                "f1": 0.1,
                "true_positives": 1,
                "false_positives": 1,
                "false_negatives": 1,
            }
        ],
    }


def test_precomputed_candidate_builds_experiment_outputs(tmp_path):
    module = _load_module()
    dataset_yaml = tmp_path / "combined_person.yaml"
    dataset_yaml.write_text("train: images/train\nval: images/val\nnc: 1\nnames: ['person']\n", encoding="utf-8")
    dataset_manifest = tmp_path / "combined_manifest.json"
    dataset_manifest.write_text(json.dumps({"type": "sar-intel-combined-person-yolo-dataset", "summary": {"images": 2}}), encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline.write_text(json.dumps(_sweep(0.10, ap=0.20)), encoding="utf-8")
    candidate.write_text(json.dumps(_sweep(0.20, precision=0.78, ap=0.28)), encoding="utf-8")

    summary = module.run_precomputed_experiment(
        dataset_yaml=dataset_yaml,
        dataset_manifest=dataset_manifest,
        baseline_sweep=baseline,
        candidate_sweep=candidate,
        output_dir=tmp_path / "experiment",
        experiment_name="smoke",
    )

    out = tmp_path / "experiment"
    assert (out / "training_metadata.json").exists()
    assert (out / "candidate_sweep.json").exists()
    assert (out / "finetune_report.json").exists()
    assert (out / "recall_experiment_summary.json").exists()
    assert summary["experiment_name"] == "smoke"
    assert summary["claim_allowed"] is True
    assert summary["dataset"]["manifest_sha256"]


def test_precomputed_experiment_fails_for_missing_dataset_manifest(tmp_path):
    module = _load_module()
    dataset_yaml = tmp_path / "combined_person.yaml"
    dataset_yaml.write_text("train: images/train\n", encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline.write_text(json.dumps(_sweep(0.10)), encoding="utf-8")
    candidate.write_text(json.dumps(_sweep(0.20)), encoding="utf-8")

    try:
        module.run_precomputed_experiment(
            dataset_yaml=dataset_yaml,
            dataset_manifest=tmp_path / "missing.json",
            baseline_sweep=baseline,
            candidate_sweep=candidate,
            output_dir=tmp_path / "experiment",
        )
    except FileNotFoundError as exc:
        assert "dataset manifest" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_cli_precomputed_mode_writes_summary(tmp_path):
    dataset_yaml = tmp_path / "combined_person.yaml"
    dataset_yaml.write_text("train: images/train\n", encoding="utf-8")
    dataset_manifest = tmp_path / "combined_manifest.json"
    dataset_manifest.write_text(json.dumps({"summary": {"images": 2}}), encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline.write_text(json.dumps(_sweep(0.10, ap=0.20)), encoding="utf-8")
    candidate.write_text(json.dumps(_sweep(0.20, precision=0.78, ap=0.28)), encoding="utf-8")
    output_dir = tmp_path / "experiment"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_recall_experiment.py",
            "--dataset-yaml",
            str(dataset_yaml),
            "--dataset-manifest",
            str(dataset_manifest),
            "--baseline-sweep",
            str(baseline),
            "--candidate-sweep",
            str(candidate),
            "--output-dir",
            str(output_dir),
            "--experiment-name",
            "cli-smoke",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Recall experiment: PASS" in result.stdout
    assert json.loads((output_dir / "recall_experiment_summary.json").read_text(encoding="utf-8"))["experiment_name"] == "cli-smoke"