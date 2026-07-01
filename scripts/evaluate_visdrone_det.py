import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import cv2


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from detector import PersonDetector


PERSON_CATEGORY_IDS = {1, 2}


@dataclass(frozen=True)
class ImageEvaluation:
    image: str
    gt_count: int
    detections: int
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate person detection on VisDrone DET validation images.")
    parser.add_argument("--dataset-root", required=True, help="Path to VisDrone2019-DET-val or its parent directory.")
    parser.add_argument("--split", default="val", choices=["val"], help="VisDrone DET split to evaluate.")
    parser.add_argument("--max-images", type=int, default=None, help="Optional cap on images evaluated.")
    parser.add_argument(
        "--model",
        default="yolo26n.pt",
        help=(
            "Model path or identifier passed to PersonDetector. "
            "The published VisDrone baseline uses yolo26n.pt."
        ),
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.25,
        help="Minimum detector confidence to keep a detection.",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Evaluate multiple confidence thresholds using one detector pass at the lowest threshold.",
    )
    parser.add_argument(
        "--sweep-thresholds",
        default="0.10,0.25,0.50",
        help="Comma-separated confidence thresholds to evaluate when --sweep is enabled.",
    )
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=0.5,
        help="IoU threshold used for greedy TP/FP matching.",
    )
    parser.add_argument(
        "--output",
        default="output/visdrone_det_validation.json",
        help="Path to the JSON summary to write.",
    )
    parser.add_argument(
        "--validation-manifest",
        default=None,
        help=(
            "Optional pinned validation manifest JSON. When provided, the evaluator "
            "verifies the exact image/annotation file list, sizes, and SHA256 hashes."
        ),
    )
    parser.add_argument(
        "--write-validation-manifest",
        default=None,
        help="Optional path to write the validation manifest used for this run.",
    )
    return parser.parse_args(argv)


def resolve_split_root(dataset_root: str | Path, split: str) -> Path:
    root = Path(dataset_root)
    candidates = [root, root / f"VisDrone2019-DET-{split}"]

    for candidate in candidates:
        if (candidate / "images").is_dir() and (candidate / "annotations").is_dir():
            return candidate

    raise FileNotFoundError(
        f"Could not find a VisDrone DET {split} split under {root}. Expected images/ and annotations/ directories."
    )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_checksum_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "split": manifest["split"],
        "max_images": manifest.get("max_images"),
        "record_count": manifest["record_count"],
        "records": manifest["records"],
    }


def compute_manifest_checksum(manifest: dict[str, Any]) -> str:
    payload = json.dumps(
        _manifest_checksum_payload(manifest),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_validation_manifest(
    dataset_root: str | Path,
    split: str,
    max_images: int | None,
) -> dict[str, Any]:
    split_root = resolve_split_root(dataset_root, split)
    images_dir = split_root / "images"
    annotations_dir = split_root / "annotations"

    image_paths = sorted(images_dir.glob("*.jpg"))
    if max_images is not None:
        image_paths = image_paths[:max_images]

    records: list[dict[str, Any]] = []
    for image_path in image_paths:
        annotation_path = annotations_dir / f"{image_path.stem}.txt"
        if not annotation_path.exists():
            raise FileNotFoundError(
                f"Missing annotation file for {image_path.name}: {annotation_path}"
            )

        records.append(
            {
                "image": image_path.name,
                "annotation": annotation_path.name,
                "image_size_bytes": image_path.stat().st_size,
                "annotation_size_bytes": annotation_path.stat().st_size,
                "image_sha256": sha256_file(image_path),
                "annotation_sha256": sha256_file(annotation_path),
            }
        )

    manifest: dict[str, Any] = {
        "version": 1,
        "split": split,
        "max_images": max_images,
        "record_count": len(records),
        "records": records,
    }
    manifest["checksum"] = compute_manifest_checksum(manifest)
    return manifest


def load_validation_manifest(path: str | Path) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    expected_checksum = manifest.get("checksum")
    actual_checksum = compute_manifest_checksum(manifest)
    if expected_checksum != actual_checksum:
        raise ValueError(
            f"Manifest checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
        )
    return manifest


def validate_manifest_files(
    manifest: dict[str, Any],
    dataset_root: str | Path,
    split: str,
) -> list[tuple[Path, Path]]:
    if manifest.get("split") != split:
        raise ValueError(
            f"Manifest split mismatch: expected {split!r}, got {manifest.get('split')!r}"
        )

    expected_manifest_checksum = manifest.get("checksum")
    actual_manifest_checksum = compute_manifest_checksum(manifest)
    if expected_manifest_checksum != actual_manifest_checksum:
        raise ValueError(
            "Manifest checksum mismatch: "
            f"expected {expected_manifest_checksum}, got {actual_manifest_checksum}"
        )

    split_root = resolve_split_root(dataset_root, split)
    pairs: list[tuple[Path, Path]] = []

    for record in manifest["records"]:
        image_path = split_root / "images" / record["image"]
        annotation_path = split_root / "annotations" / record["annotation"]

        checks = [
            ("image", image_path, record["image_size_bytes"], record["image_sha256"]),
            (
                "annotation",
                annotation_path,
                record["annotation_size_bytes"],
                record["annotation_sha256"],
            ),
        ]
        for label, path, expected_size, expected_hash in checks:
            if not path.exists():
                raise FileNotFoundError(f"Manifest {label} file is missing: {path}")
            if path.stat().st_size != expected_size:
                raise ValueError(f"{label} size mismatch for {path.name}")
            actual_hash = sha256_file(path)
            if actual_hash != expected_hash:
                raise ValueError(f"{label} SHA256 mismatch for {path.name}")

        pairs.append((image_path, annotation_path))

    return pairs


def get_validation_file_pairs(
    dataset_root: str | Path,
    split: str,
    max_images: int | None,
    validation_manifest: str | Path | None,
) -> tuple[list[tuple[Path, Path]], dict[str, Any]]:
    if validation_manifest is not None:
        manifest = load_validation_manifest(validation_manifest)
        if manifest.get("max_images") != max_images:
            raise ValueError(
                "Manifest max_images mismatch: "
                f"expected {max_images!r}, got {manifest.get('max_images')!r}"
            )
        return validate_manifest_files(manifest, dataset_root, split), manifest

    manifest = build_validation_manifest(dataset_root, split, max_images)
    return validate_manifest_files(manifest, dataset_root, split), manifest

def load_image(image_path: Path) -> Any:
    frame = cv2.imread(str(image_path))
    if frame is None:
        raise ValueError(f"Unable to read image: {image_path}")
    return frame


def xywh_to_xyxy(box: Sequence[float]) -> list[float]:
    if len(box) != 4:
        raise ValueError(f"Expected a 4-value box, got {box!r}")

    x, y, width, height = box
    return [float(x), float(y), float(x + width), float(y + height)]


def parse_annotation_line(line: str) -> list[float] | None:
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 6:
        raise ValueError(f"Malformed annotation line: {line!r}")

    bbox_left = float(parts[0])
    bbox_top = float(parts[1])
    bbox_width = float(parts[2])
    bbox_height = float(parts[3])
    score = int(float(parts[4]))
    object_category = int(float(parts[5]))

    if score != 1 or object_category not in PERSON_CATEGORY_IDS:
        return None
    if bbox_width <= 0 or bbox_height <= 0:
        return None

    return xywh_to_xyxy([bbox_left, bbox_top, bbox_width, bbox_height])


def parse_visdrone_annotation_file(path: str | Path) -> list[list[float]]:
    boxes: list[list[float]] = []
    annotation_path = Path(path)
    for line in annotation_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parsed = parse_annotation_line(line)
        if parsed is not None:
            boxes.append(parsed)
    return boxes


def bbox_iou(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_width = max(0.0, inter_x2 - inter_x1)
    inter_height = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_width * inter_height
    if inter_area <= 0.0:
        return 0.0

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union_area = area_a + area_b - inter_area
    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


def safe_ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def parse_sweep_thresholds(value: str) -> list[float]:
    thresholds: list[float] = []

    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue

        try:
            threshold = float(part)
        except ValueError as exc:
            raise ValueError(f"Invalid sweep threshold {part!r}") from exc

        if threshold < 0.0 or threshold > 1.0:
            raise ValueError(
                f"Invalid sweep threshold {threshold!r}; expected value in [0.0, 1.0]."
            )

        thresholds.append(threshold)

    if not thresholds:
        raise ValueError("At least one sweep threshold is required.")

    return sorted(set(thresholds))


def filter_detections_by_threshold(
    detections: Iterable[dict[str, Any]],
    confidence_threshold: float,
) -> list[dict[str, Any]]:
    return [detection for detection in detections if float(detection["confidence"]) >= confidence_threshold]


def match_detections_to_ground_truth(
    detections: Iterable[dict[str, Any]],
    gt_boxes: Sequence[Sequence[float]],
    iou_threshold: float,
) -> tuple[int, int, int]:
    unmatched_gt = set(range(len(gt_boxes)))
    true_positives = 0
    false_positives = 0

    sorted_detections = sorted(detections, key=lambda item: float(item["confidence"]), reverse=True)

    for detection in sorted_detections:
        best_gt_index = None
        best_iou = -1.0

        for gt_index in unmatched_gt:
            iou = bbox_iou(detection["bbox"], gt_boxes[gt_index])
            if iou > best_iou:
                best_iou = iou
                best_gt_index = gt_index

        if best_gt_index is not None and best_iou >= iou_threshold:
            unmatched_gt.remove(best_gt_index)
            true_positives += 1
        else:
            false_positives += 1

    false_negatives = len(unmatched_gt)
    return true_positives, false_positives, false_negatives


def compute_precision_recall_curve(
    image_records: Sequence[dict[str, Any]],
    iou_threshold: float,
) -> dict[str, Any]:
    total_gt = sum(len(record["gt_boxes"]) for record in image_records)
    unmatched_by_image = {
        record["image"]: set(range(len(record["gt_boxes"]))) for record in image_records
    }
    gt_by_image = {record["image"]: record["gt_boxes"] for record in image_records}

    ranked_detections: list[dict[str, Any]] = []
    for record in image_records:
        for detection in record["detections"]:
            ranked_detections.append(
                {
                    "image": record["image"],
                    "confidence": float(detection["confidence"]),
                    "bbox": detection["bbox"],
                }
            )

    ranked_detections.sort(key=lambda item: item["confidence"], reverse=True)

    points: list[dict[str, float | int]] = []
    true_positives = 0
    false_positives = 0
    precision_at_true_positives: list[float] = []

    for detection in ranked_detections:
        image_name = detection["image"]
        unmatched_gt = unmatched_by_image[image_name]
        gt_boxes = gt_by_image[image_name]
        best_gt_index = None
        best_iou = -1.0

        for gt_index in unmatched_gt:
            iou = bbox_iou(detection["bbox"], gt_boxes[gt_index])
            if iou > best_iou:
                best_iou = iou
                best_gt_index = gt_index

        if best_gt_index is not None and best_iou >= iou_threshold:
            unmatched_gt.remove(best_gt_index)
            true_positives += 1
            precision_at_true_positives.append(
                safe_ratio(true_positives, true_positives + false_positives)
            )
        else:
            false_positives += 1

        points.append(
            {
                "confidence": detection["confidence"],
                "precision": safe_ratio(true_positives, true_positives + false_positives),
                "recall": safe_ratio(true_positives, total_gt),
                "tp": true_positives,
                "fp": false_positives,
            }
        )

    average_precision = safe_ratio(sum(precision_at_true_positives), total_gt)
    return {
        "average_precision": average_precision,
        "points": points,
    }

def compute_metrics(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    f1 = safe_ratio(2 * precision * recall, precision + recall)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def load_ground_truth(annotation_path: Path) -> list[list[float]]:
    return parse_visdrone_annotation_file(annotation_path)


def compute_iou(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    return bbox_iou(box_a, box_b)


def greedy_match(
    detections: Iterable[dict[str, Any]],
    gt_boxes: Sequence[Sequence[float]],
    iou_threshold: float,
) -> tuple[int, int, int]:
    return match_detections_to_ground_truth(detections, gt_boxes, iou_threshold)


def evaluate_image(
    image_path: Path,
    annotation_path: Path,
    detector: PersonDetector,
    iou_threshold: float,
) -> tuple[ImageEvaluation, list[dict[str, float | list[float]]], list[list[float]]]:
    gt_boxes = load_ground_truth(annotation_path)
    frame = load_image(image_path)
    raw_detections = detector.detect(frame)
    detections = [
        {"confidence": float(detection.confidence), "bbox": [float(value) for value in detection.bbox]}
        for detection in raw_detections
    ]

    true_positives, false_positives, false_negatives = match_detections_to_ground_truth(
        detections,
        gt_boxes,
        iou_threshold,
    )
    metrics = compute_metrics(true_positives, false_positives, false_negatives)

    summary = ImageEvaluation(
        image=image_path.name,
        gt_count=len(gt_boxes),
        detections=len(detections),
        tp=true_positives,
        fp=false_positives,
        fn=false_negatives,
        precision=metrics["precision"],
        recall=metrics["recall"],
    )
    return summary, detections, gt_boxes


def evaluate_dataset(
    dataset_root: str | Path,
    split: str,
    max_images: int | None,
    model: str,
    confidence_threshold: float,
    iou_threshold: float,
    validation_manifest: str | Path | None = None,
) -> dict[str, Any]:
    file_pairs, manifest = get_validation_file_pairs(
        dataset_root,
        split,
        max_images,
        validation_manifest,
    )

    detector = PersonDetector(model_path=model, confidence_threshold=confidence_threshold)

    per_image: list[dict[str, Any]] = []
    image_records: list[dict[str, Any]] = []
    gt_person_count = 0
    detection_count = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    confidence_total = 0.0

    for image_path, annotation_path in file_pairs:
        summary, detections, gt_boxes = evaluate_image(
            image_path,
            annotation_path,
            detector,
            iou_threshold,
        )
        per_image.append(
            {
                "image": summary.image,
                "gt_count": summary.gt_count,
                "detections": summary.detections,
                "tp": summary.tp,
                "fp": summary.fp,
                "fn": summary.fn,
                "precision": summary.precision,
                "recall": summary.recall,
            }
        )
        image_records.append(
            {
                "image": summary.image,
                "gt_boxes": gt_boxes,
                "detections": detections,
            }
        )

        gt_person_count += summary.gt_count
        detection_count += summary.detections
        true_positives += summary.tp
        false_positives += summary.fp
        false_negatives += summary.fn
        confidence_total += sum(float(detection["confidence"]) for detection in detections)

    metrics = compute_metrics(true_positives, false_positives, false_negatives)
    mean_confidence = safe_ratio(confidence_total, detection_count)
    pr_curve = compute_precision_recall_curve(image_records, iou_threshold)

    return {
        "images_evaluated": len(file_pairs),
        "gt_person_count": gt_person_count,
        "detection_count": detection_count,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "average_precision": pr_curve["average_precision"],
        "precision_recall_curve": pr_curve["points"],
        "mean_confidence": mean_confidence,
        "confidence_threshold": confidence_threshold,
        "iou_threshold": iou_threshold,
        "model": model,
        "dataset_root": str(Path(dataset_root).resolve()),
        "split": split,
        "max_images": max_images,
        "validation_manifest": manifest,
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "per_image": per_image,
    }


def summarize_cached_evaluation(
    image_records: Sequence[dict[str, Any]],
    confidence_threshold: float,
    iou_threshold: float,
    *,
    dataset_root: str | Path,
    split: str,
    max_images: int | None,
    model: str,
) -> dict[str, Any]:
    per_image: list[dict[str, Any]] = []
    gt_person_count = 0
    detection_count = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    confidence_total = 0.0

    for record in image_records:
        image_name = record["image"]
        gt_boxes = record["gt_boxes"]
        all_detections = record["detections"]
        detections = filter_detections_by_threshold(
            all_detections,
            confidence_threshold,
        )

        tp, fp, fn = match_detections_to_ground_truth(
            detections,
            gt_boxes,
            iou_threshold,
        )
        metrics = compute_metrics(tp, fp, fn)

        per_image.append(
            {
                "image": image_name,
                "gt_count": len(gt_boxes),
                "detections": len(detections),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": metrics["precision"],
                "recall": metrics["recall"],
            }
        )

        gt_person_count += len(gt_boxes)
        detection_count += len(detections)
        true_positives += tp
        false_positives += fp
        false_negatives += fn
        confidence_total += sum(float(detection["confidence"]) for detection in detections)

    metrics = compute_metrics(true_positives, false_positives, false_negatives)
    mean_confidence = safe_ratio(confidence_total, detection_count)
    pr_curve = compute_precision_recall_curve(image_records, iou_threshold)

    return {
        "images_evaluated": len(image_records),
        "gt_person_count": gt_person_count,
        "detection_count": detection_count,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "average_precision": pr_curve["average_precision"],
        "precision_recall_curve": pr_curve["points"],
        "mean_confidence": mean_confidence,
        "confidence_threshold": confidence_threshold,
        "iou_threshold": iou_threshold,
        "model": model,
        "dataset_root": str(Path(dataset_root).resolve()),
        "split": split,
        "max_images": max_images,
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "per_image": per_image,
    }


def evaluate_dataset_sweep(
    dataset_root: str | Path,
    split: str,
    max_images: int | None,
    model: str,
    sweep_thresholds: Sequence[float],
    iou_threshold: float,
    validation_manifest: str | Path | None = None,
) -> dict[str, Any]:
    thresholds = sorted(set(float(value) for value in sweep_thresholds))
    if not thresholds:
        raise ValueError("At least one sweep threshold is required.")

    base_threshold = min(thresholds)
    file_pairs, manifest = get_validation_file_pairs(
        dataset_root,
        split,
        max_images,
        validation_manifest,
    )

    detector = PersonDetector(model_path=model, confidence_threshold=base_threshold)

    image_records: list[dict[str, Any]] = []

    for image_path, annotation_path in file_pairs:
        gt_boxes = load_ground_truth(annotation_path)
        frame = load_image(image_path)
        raw_detections = detector.detect(frame)

        detections = [
            {
                "confidence": float(detection.confidence),
                "bbox": [float(value) for value in detection.bbox],
            }
            for detection in raw_detections
        ]

        image_records.append(
            {
                "image": image_path.name,
                "gt_boxes": gt_boxes,
                "detections": detections,
            }
        )

    pr_curve = compute_precision_recall_curve(image_records, iou_threshold)
    results = [
        summarize_cached_evaluation(
            image_records,
            confidence_threshold=threshold,
            iou_threshold=iou_threshold,
            dataset_root=dataset_root,
            split=split,
            max_images=max_images,
            model=model,
        )
        for threshold in thresholds
    ]

    return {
        "mode": "sweep",
        "dataset_root": str(Path(dataset_root).resolve()),
        "split": split,
        "model": model,
        "iou_threshold": iou_threshold,
        "sweep_thresholds": thresholds,
        "base_detector_threshold": base_threshold,
        "max_images": max_images,
        "average_precision": pr_curve["average_precision"],
        "precision_recall_curve": pr_curve["points"],
        "validation_manifest": manifest,
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "results": results,
    }


def write_output(result: dict[str, Any], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.sweep:
        thresholds = parse_sweep_thresholds(args.sweep_thresholds)
        result = evaluate_dataset_sweep(
            dataset_root=args.dataset_root,
            split=args.split,
            max_images=args.max_images,
            model=args.model,
            sweep_thresholds=thresholds,
            iou_threshold=args.iou_threshold,
            validation_manifest=args.validation_manifest,
        )
    else:
        result = evaluate_dataset(
            dataset_root=args.dataset_root,
            split=args.split,
            max_images=args.max_images,
            model=args.model,
            confidence_threshold=args.confidence_threshold,
            iou_threshold=args.iou_threshold,
            validation_manifest=args.validation_manifest,
        )
    output_path = write_output(result, args.output)
    print(f"Saved VisDrone DET validation summary to {output_path}")
    print(f"Validation manifest checksum: {result['validation_manifest']['checksum']}")
    print(f"Average precision: {result['average_precision']:.4f}")

    if args.write_validation_manifest:
        manifest_path = write_output(result["validation_manifest"], args.write_validation_manifest)
        print(f"Saved validation manifest to {manifest_path}")

    if args.sweep:
        print("\nConfidence threshold sweep:")
        print("threshold,detections,tp,fp,fn,precision,recall,f1")
        for row in result["results"]:
            print(
                f'{row["confidence_threshold"]:.2f},'
                f'{row["detection_count"]},'
                f'{row["true_positives"]},'
                f'{row["false_positives"]},'
                f'{row["false_negatives"]},'
                f'{row["precision"]:.4f},'
                f'{row["recall"]:.4f},'
                f'{row["f1"]:.4f}'
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())