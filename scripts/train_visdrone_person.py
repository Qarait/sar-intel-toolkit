import argparse
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a person-only YOLO model on a prepared VisDrone dataset.")
    parser.add_argument(
        "--data",
        required=True,
        help="Path to visdrone_person.yaml for the prepared YOLO dataset.",
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
) -> dict[str, Any]:
    dataset_yaml = Path(data)
    if not dataset_yaml.exists():
        raise FileNotFoundError(f"Missing training data file: {dataset_yaml}")
    expected_best_path = Path(project) / name / "weights" / "best.pt"

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
    return {
        "dataset_yaml": str(dataset_yaml),
        "save_dir": str(save_dir) if save_dir is not None else None,
        "best_path": str(expected_best_path),
        "model": model,
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
    )
    print(f"likely_best_pt: {result['best_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())