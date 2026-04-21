import argparse
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
    parser.add_argument("--model", default="yolo26n.pt", help="Model path or identifier passed to PersonDetector.")
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.25,
        help="Minimum detector confidence to keep a detection.",
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
) -> tuple[ImageEvaluation, list[dict[str, float | list[float]]]]:
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
    return summary, detections


def evaluate_dataset(
    dataset_root: str | Path,
    split: str,
    max_images: int | None,
    model: str,
    confidence_threshold: float,
    iou_threshold: float,
) -> dict[str, Any]:
    split_root = resolve_split_root(dataset_root, split)
    images_dir = split_root / "images"
    annotations_dir = split_root / "annotations"

    image_paths = sorted(images_dir.glob("*.jpg"))
    if max_images is not None:
        image_paths = image_paths[:max_images]

    detector = PersonDetector(model_path=model, confidence_threshold=confidence_threshold)

    per_image: list[dict[str, Any]] = []
    gt_person_count = 0
    detection_count = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    confidence_total = 0.0

    for image_path in image_paths:
        annotation_path = annotations_dir / f"{image_path.stem}.txt"
        if not annotation_path.exists():
            raise FileNotFoundError(f"Missing annotation file for {image_path.name}: {annotation_path}")

        summary, detections = evaluate_image(image_path, annotation_path, detector, iou_threshold)
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

        gt_person_count += summary.gt_count
        detection_count += summary.detections
        true_positives += summary.tp
        false_positives += summary.fp
        false_negatives += summary.fn
        confidence_total += sum(float(detection["confidence"]) for detection in detections)

    metrics = compute_metrics(true_positives, false_positives, false_negatives)
    mean_confidence = safe_ratio(confidence_total, detection_count)

    return {
        "images_evaluated": len(image_paths),
        "gt_person_count": gt_person_count,
        "detection_count": detection_count,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
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


def write_output(result: dict[str, Any], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = evaluate_dataset(
        dataset_root=args.dataset_root,
        split=args.split,
        max_images=args.max_images,
        model=args.model,
        confidence_threshold=args.confidence_threshold,
        iou_threshold=args.iou_threshold,
    )
    output_path = write_output(result, args.output)
    print(f"Saved VisDrone DET validation summary to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())