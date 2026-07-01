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