from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

DATASET_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "heridal",
        "name": "HERIDAL",
        "task": "aerial-person-detection",
        "sar_relevance": "mountain/wilderness SAR imagery",
        "required_paths": ["images", "annotations"],
        "claim_status": "candidate-training-source",
        "notes": "Use only after local license/access review; not committed to this repo.",
    },
    {
        "id": "seadronessee",
        "name": "SeaDronesSee",
        "task": "aerial-person-detection",
        "sar_relevance": "maritime drone SAR imagery",
        "required_paths": ["images", "annotations"],
        "claim_status": "candidate-training-source",
        "notes": "Dataset layouts vary by release; audit before writing a converter.",
    },
    {
        "id": "visdrone-person",
        "name": "VisDrone person-only",
        "task": "aerial-person-detection",
        "sar_relevance": "general aerial pedestrian/people detection baseline",
        "required_paths": ["images/train", "images/val", "labels/train", "labels/val", "visdrone_person.yaml"],
        "claim_status": "candidate-training-source",
        "notes": "Prepared by scripts/prepare_visdrone_person_yolo.py.",
    },
    {
        "id": "okutama-action",
        "name": "Okutama-Action",
        "task": "aerial-person-detection",
        "sar_relevance": "aerial human imagery with action-oriented scenes",
        "required_paths": ["images", "annotations"],
        "claim_status": "candidate-training-source",
        "notes": "Treat as supplementary domain-transfer data, not a SAR benchmark.",
    },
    {
        "id": "au-air",
        "name": "AU-AIR",
        "task": "aerial-person-detection",
        "sar_relevance": "low-altitude UAV traffic/person imagery",
        "required_paths": ["images", "annotations"],
        "claim_status": "candidate-training-source",
        "notes": "Useful for domain diversity; not SAR-specific.",
    },
]


def _registry_by_id() -> dict[str, dict[str, Any]]:
    return {dataset["id"]: dataset for dataset in DATASET_REGISTRY}


def parse_dataset_root(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("dataset roots must use id=path format")
    dataset_id, path = value.split("=", 1)
    dataset_id = dataset_id.strip()
    if dataset_id not in _registry_by_id():
        raise argparse.ArgumentTypeError(f"unknown dataset id: {dataset_id}")
    return dataset_id, Path(path)


def audit_dataset(dataset: dict[str, Any], root: Path | None) -> dict[str, Any]:
    result = {
        "id": dataset["id"],
        "name": dataset["name"],
        "task": dataset["task"],
        "claim_status": dataset["claim_status"],
        "root": str(root) if root is not None else None,
        "required_paths": dataset["required_paths"],
        "missing_paths": [],
        "status": "not_configured",
        "notes": dataset["notes"],
    }
    if root is None:
        return result
    if not root.exists():
        result["status"] = "missing_root"
        return result
    missing = [relative for relative in dataset["required_paths"] if not (root / relative).exists()]
    result["missing_paths"] = missing
    result["status"] = "ready_for_converter" if not missing else "missing_required_paths"
    return result


def build_dataset_audit(dataset_roots: Mapping[str, str | Path]) -> dict[str, Any]:
    normalized_roots = {dataset_id: Path(root) for dataset_id, root in dataset_roots.items()}
    datasets = [audit_dataset(dataset, normalized_roots.get(dataset["id"])) for dataset in DATASET_REGISTRY]
    summary: dict[str, int] = {}
    for item in datasets:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    return {
        "type": "sar-intel-aerial-dataset-audit",
        "version": 1,
        "purpose": "Track external aerial-person datasets needed to move beyond the pre-fine-tune baseline.",
        "summary": summary,
        "datasets": datasets,
    }


def write_json(data: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit external aerial-person datasets for SAR-INTEL fine-tuning readiness.")
    parser.add_argument("--dataset-root", action="append", default=[], type=parse_dataset_root, help="Dataset root in id=path form.")
    parser.add_argument("--output", default="output/aerial_dataset_audit.json")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_dataset_audit(dict(args.dataset_root))
    output = write_json(report, args.output)
    print(f"Aerial dataset audit written to {output}")
    print(f"Ready for converter: {report['summary'].get('ready_for_converter', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())