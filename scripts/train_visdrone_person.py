import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


def parse_batch(value: str) -> int | float:
    normalized = value.strip().lower()
    if normalized == "auto":
        return -1

    try:
        return int(normalized)
    except ValueError:
        try:
            return float(normalized)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("batch must be an integer, float, or 'auto'.") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_training_metadata(
    *,
    dataset_yaml: str | Path,
    dataset_manifest: str | Path | None,
    model: str,
    epochs: int,
    imgsz: int,
    batch: int | float,
    project: str,
    name: str,
    best_path: str | Path,
    save_dir: str | Path | None,
    status: str,
) -> dict[str, Any]:
    dataset_yaml_path = Path(dataset_yaml)
    dataset: dict[str, Any] = {
        "yaml": str(dataset_yaml_path),
        "yaml_sha256": sha256_file(dataset_yaml_path),
    }
    if dataset_manifest is not None:
        manifest_path = Path(dataset_manifest)
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing dataset manifest: {manifest_path}")
        dataset.update(
            {
                "manifest": str(manifest_path),
                "manifest_sha256": sha256_file(manifest_path),
                "manifest_payload": load_json(manifest_path),
            }
        )

    return {
        "type": "sar-intel-training-metadata",
        "version": 1,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset,
        "training": {
            "model": model,
            "epochs": epochs,
            "imgsz": imgsz,
            "batch": batch,
            "project": project,
            "name": name,
        },
        "outputs": {
            "save_dir": str(save_dir) if save_dir is not None else None,
            "best_path": str(best_path),
        },
    }


def write_training_metadata(metadata: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return output


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a person-only YOLO model on a prepared aerial-person dataset.")
    parser.add_argument(
        "--data",
        required=True,
        help="Path to a prepared person-only YOLO dataset YAML.",
    )
    parser.add_argument(
        "--model",
        default="yolo26n.pt",
        help="Initial YOLO checkpoint to fine-tune.",
    )
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs.")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size.")
    parser.add_argument("--batch", type=parse_batch, default=-1, help="Training batch size, memory fraction, or 'auto'.")
    parser.add_argument("--project", default="runs/visdrone_person", help="Training project directory.")
    parser.add_argument("--name", default="yolo26n_visdrone_person", help="Training run name.")
    parser.add_argument("--dataset-manifest", help="Optional combined dataset manifest JSON for provenance.")
    parser.add_argument("--metadata-output", help="Where to write training metadata JSON.")
    parser.add_argument("--metadata-only", action="store_true", help="Write metadata without importing Ultralytics or training.")
    return parser.parse_args(argv)


def run_training(
    *,
    data: str | Path,
    model: str,
    epochs: int,
    imgsz: int,
    batch: int | float,
    project: str,
    name: str,
    dataset_manifest: str | Path | None = None,
    metadata_output: str | Path | None = None,
    metadata_only: bool = False,
) -> dict[str, Any]:
    dataset_yaml = Path(data)
    if not dataset_yaml.exists():
        raise FileNotFoundError(f"Missing training data file: {dataset_yaml}")
    expected_best_path = Path(project) / name / "weights" / "best.pt"

    if metadata_only:
        metadata = build_training_metadata(
            dataset_yaml=dataset_yaml,
            dataset_manifest=dataset_manifest,
            model=model,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            project=project,
            name=name,
            best_path=expected_best_path,
            save_dir=Path(project) / name,
            status="metadata_only",
        )
        if metadata_output:
            write_training_metadata(metadata, metadata_output)
        return {
            "dataset_yaml": str(dataset_yaml),
            "save_dir": str(Path(project) / name),
            "best_path": str(expected_best_path),
            "model": model,
            "metadata": metadata,
            "metadata_output": str(metadata_output) if metadata_output else None,
        }

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Ultralytics is required for training. Install project dependencies before running this script."
        ) from exc

    trainer = YOLO(model)
    kwargs: dict[str, Any] = {
        "data": str(dataset_yaml),
        "epochs": epochs,
        "imgsz": imgsz,
        "batch": batch,
        "project": project,
        "name": name,
    }

    results = trainer.train(**kwargs)
    save_dir = getattr(results, "save_dir", None)
    metadata = build_training_metadata(
        dataset_yaml=dataset_yaml,
        dataset_manifest=dataset_manifest,
        model=model,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=project,
        name=name,
        best_path=expected_best_path,
        save_dir=save_dir,
        status="trained",
    )
    if metadata_output:
        write_training_metadata(metadata, metadata_output)
    return {
        "dataset_yaml": str(dataset_yaml),
        "save_dir": str(save_dir) if save_dir is not None else None,
        "best_path": str(expected_best_path),
        "model": model,
        "metadata": metadata,
        "metadata_output": str(metadata_output) if metadata_output else None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_training(
        data=args.data,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
        dataset_manifest=args.dataset_manifest,
        metadata_output=args.metadata_output,
        metadata_only=args.metadata_only,
    )
    print(f"likely_best_pt: {result['best_path']}")
    if result.get("metadata_output"):
        print(f"training_metadata: {result['metadata_output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())