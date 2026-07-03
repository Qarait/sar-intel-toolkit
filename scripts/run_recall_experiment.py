from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_visdrone_finetune import build_finetune_report  # noqa: E402


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(data: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output


def require_file(path: str | Path, label: str) -> Path:
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Missing {label}: {resolved}")
    return resolved


def build_training_metadata(
    *,
    dataset_yaml: Path,
    dataset_manifest: Path,
    experiment_name: str,
    mode: str,
) -> dict[str, Any]:
    return {
        "type": "sar-intel-recall-training-metadata",
        "version": 1,
        "experiment_name": experiment_name,
        "mode": mode,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "yaml": str(dataset_yaml),
            "yaml_sha256": sha256_file(dataset_yaml),
            "manifest": str(dataset_manifest),
            "manifest_sha256": sha256_file(dataset_manifest),
            "manifest_payload": load_json(dataset_manifest),
        },
        "note": "Precomputed mode records provenance and gates an existing candidate sweep; it does not train a model.",
    }


def run_precomputed_experiment(
    *,
    dataset_yaml: str | Path,
    dataset_manifest: str | Path,
    baseline_sweep: str | Path,
    candidate_sweep: str | Path,
    output_dir: str | Path,
    experiment_name: str = "recall-experiment",
    recall_delta: float = 0.05,
    min_precision_ratio: float = 0.90,
    ap_delta: float = 0.03,
) -> dict[str, Any]:
    dataset_yaml_path = require_file(dataset_yaml, "dataset yaml")
    dataset_manifest_path = require_file(dataset_manifest, "dataset manifest")
    baseline_path = require_file(baseline_sweep, "baseline sweep")
    candidate_path = require_file(candidate_sweep, "candidate sweep")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    training_metadata = build_training_metadata(
        dataset_yaml=dataset_yaml_path,
        dataset_manifest=dataset_manifest_path,
        experiment_name=experiment_name,
        mode="precomputed-candidate",
    )
    write_json(training_metadata, output / "training_metadata.json")
    shutil.copy2(candidate_path, output / "candidate_sweep.json")

    report = build_finetune_report(
        load_json(baseline_path),
        load_json(candidate_path),
        training_metadata=training_metadata,
        recall_delta=recall_delta,
        min_precision_ratio=min_precision_ratio,
        ap_delta=ap_delta,
    )
    write_json(report, output / "finetune_report.json")

    summary = {
        "type": "sar-intel-recall-experiment-summary",
        "version": 1,
        "experiment_name": experiment_name,
        "mode": "precomputed-candidate",
        "claim_allowed": bool(report["claim"]["allowed"]),
        "verdict": report["verdict"],
        "dataset": training_metadata["dataset"],
        "outputs": {
            "training_metadata": str(output / "training_metadata.json"),
            "candidate_sweep": str(output / "candidate_sweep.json"),
            "finetune_report": str(output / "finetune_report.json"),
        },
        "comparison_reasons": report["comparison"].get("reasons", []),
    }
    write_json(summary, output / "recall_experiment_summary.json")
    return summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or assemble a SAR-INTEL aerial recall experiment report.")
    parser.add_argument("--dataset-yaml", required=True)
    parser.add_argument("--dataset-manifest", required=True)
    parser.add_argument("--baseline-sweep", required=True)
    parser.add_argument("--candidate-sweep", required=True, help="Precomputed candidate sweep JSON to gate.")
    parser.add_argument("--output-dir", default="output/recall_experiment")
    parser.add_argument("--experiment-name", default="recall-experiment")
    parser.add_argument("--recall-delta", type=float, default=0.05)
    parser.add_argument("--min-precision-ratio", type=float, default=0.90)
    parser.add_argument("--ap-delta", type=float, default=0.03)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_precomputed_experiment(
            dataset_yaml=args.dataset_yaml,
            dataset_manifest=args.dataset_manifest,
            baseline_sweep=args.baseline_sweep,
            candidate_sweep=args.candidate_sweep,
            output_dir=args.output_dir,
            experiment_name=args.experiment_name,
            recall_delta=args.recall_delta,
            min_precision_ratio=args.min_precision_ratio,
            ap_delta=args.ap_delta,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    status = "PASS" if summary["claim_allowed"] else "FAIL"
    print(f"Recall experiment: {status}")
    print(f"Summary: {Path(args.output_dir) / 'recall_experiment_summary.json'}")
    return 0 if summary["claim_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())