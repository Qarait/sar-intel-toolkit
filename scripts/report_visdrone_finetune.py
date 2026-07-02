from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compare_visdrone_runs import compare_runs, load_json, write_json  # noqa: E402

REPORT_TYPE = "sar-intel-visdrone-finetune-report"
REPORT_VERSION = 1


def _thresholds_compared(comparison: dict[str, Any]) -> list[str]:
    return sorted(comparison.get("thresholds", {}).keys())


def _manifest_checksum(run: dict[str, Any]) -> str | None:
    manifest = run.get("validation_manifest") or {}
    checksum = manifest.get("checksum")
    return str(checksum) if checksum else None


def _shared_manifest_checksum(baseline: dict[str, Any], candidate: dict[str, Any]) -> str | None:
    baseline_checksum = _manifest_checksum(baseline)
    candidate_checksum = _manifest_checksum(candidate)
    if baseline_checksum and baseline_checksum == candidate_checksum:
        return baseline_checksum
    return None


def _normalize_training_metadata(training_metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not training_metadata:
        return {
            "provided": False,
            "note": "No training metadata supplied. Attach model, dataset, and run metadata before publishing fine-tuned metrics.",
        }
    normalized = {str(key): value for key, value in training_metadata.items()}
    normalized["provided"] = True
    return normalized


def _claim_language(passed: bool) -> str:
    if passed:
        return (
            "Candidate detector is eligible to be described as improved on this VisDrone aerial-person gate: "
            "it was compared on the same pinned validation manifest, at matching fixed confidence thresholds, "
            "without an unacceptable precision collapse, and with improved average precision."
        )
    return (
        "Do not describe this detector as improved. The candidate has not passed the same-manifest, "
        "fixed-threshold recall, precision-ratio, and average-precision gates required for an aerial-person recall claim."
    )


def build_finetune_report(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    training_metadata: dict[str, Any] | None = None,
    recall_delta: float = 0.05,
    min_precision_ratio: float = 0.90,
    ap_delta: float = 0.03,
) -> dict[str, Any]:
    comparison = compare_runs(
        baseline,
        candidate,
        recall_delta=recall_delta,
        min_precision_ratio=min_precision_ratio,
        ap_delta=ap_delta,
    )
    passed = bool(comparison["passed"])
    thresholds = _thresholds_compared(comparison)
    return {
        "type": REPORT_TYPE,
        "version": REPORT_VERSION,
        "verdict": "candidate_improved" if passed else "candidate_not_proven",
        "claim": {
            "allowed": passed,
            "language": _claim_language(passed),
        },
        "gates": {
            "recall_delta": recall_delta,
            "min_precision_ratio": min_precision_ratio,
            "ap_delta": ap_delta,
        },
        "validation": {
            "manifest_checksum": _shared_manifest_checksum(baseline, candidate),
            "baseline_manifest_checksum": _manifest_checksum(baseline),
            "candidate_manifest_checksum": _manifest_checksum(candidate),
            "thresholds_compared": thresholds,
        },
        "training": _normalize_training_metadata(training_metadata),
        "comparison": comparison,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a publishable VisDrone fine-tune report from baseline and candidate sweep outputs."
    )
    parser.add_argument("--baseline", required=True, help="Baseline VisDrone sweep JSON.")
    parser.add_argument("--candidate", required=True, help="Candidate/fine-tuned VisDrone sweep JSON.")
    parser.add_argument("--training-metadata", help="Optional JSON file describing the training run.")
    parser.add_argument("--output", default="output/visdrone_finetune_report.json")
    parser.add_argument("--recall-delta", type=float, default=0.05)
    parser.add_argument("--min-precision-ratio", type=float, default=0.90)
    parser.add_argument("--ap-delta", type=float, default=0.03)
    parser.add_argument(
        "--always-zero",
        action="store_true",
        help="Write the report but exit 0 even when the gate fails. Useful for exploratory local runs.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    training_metadata = load_json(args.training_metadata) if args.training_metadata else None
    report = build_finetune_report(
        load_json(args.baseline),
        load_json(args.candidate),
        training_metadata=training_metadata,
        recall_delta=args.recall_delta,
        min_precision_ratio=args.min_precision_ratio,
        ap_delta=args.ap_delta,
    )
    output_path = write_json(report, args.output)
    print(f"Saved VisDrone fine-tune report to {output_path}")
    if report["claim"]["allowed"]:
        print("Fine-tune report: PASS")
        return 0
    print("Fine-tune report: FAIL")
    for reason in report["comparison"].get("reasons", []):
        print(f"- {reason}")
    return 0 if args.always_zero else 1


if __name__ == "__main__":
    raise SystemExit(main())