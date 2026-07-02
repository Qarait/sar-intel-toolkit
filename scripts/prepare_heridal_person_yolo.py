from __future__ import annotations

import argparse
import csv
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from PIL import Image

PERSON_LABELS = {"person", "human", "pedestrian", "people"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def yolo_line(xmin: float, ymin: float, xmax: float, ymax: float, image_width: int, image_height: int) -> str:
    xmin = max(0.0, min(float(image_width), xmin))
    xmax = max(0.0, min(float(image_width), xmax))
    ymin = max(0.0, min(float(image_height), ymin))
    ymax = max(0.0, min(float(image_height), ymax))
    if xmax <= xmin or ymax <= ymin:
        raise ValueError("invalid bounding box with non-positive area")
    cx = ((xmin + xmax) / 2.0) / image_width
    cy = ((ymin + ymax) / 2.0) / image_height
    width = (xmax - xmin) / image_width
    height = (ymax - ymin) / image_height
    return f"0 {cx:.6f} {cy:.6f} {width:.6f} {height:.6f}"


def image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as frame:
        return frame.size


def image_paths(images_dir: Path) -> list[Path]:
    return sorted(path for path in images_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)


def parse_xml_annotations(annotation_path: Path) -> list[tuple[float, float, float, float]]:
    root = ET.parse(annotation_path).getroot()
    boxes = []
    for obj in root.findall(".//object"):
        name = (obj.findtext("name") or "person").strip().lower()
        if name and name not in PERSON_LABELS:
            continue
        box = obj.find("bndbox")
        if box is None:
            continue
        boxes.append((
            float(box.findtext("xmin", "0")),
            float(box.findtext("ymin", "0")),
            float(box.findtext("xmax", "0")),
            float(box.findtext("ymax", "0")),
        ))
    return boxes


def parse_csv_annotations(csv_path: Path) -> dict[str, list[tuple[float, float, float, float]]]:
    grouped: dict[str, list[tuple[float, float, float, float]]] = defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            label = (row.get("class") or row.get("label") or "person").strip().lower()
            if label not in PERSON_LABELS:
                continue
            filename = row.get("filename") or row.get("image") or row.get("file")
            if not filename:
                raise ValueError("CSV annotation row is missing filename/image/file")
            grouped[Path(filename).name].append((
                float(row["xmin"]),
                float(row["ymin"]),
                float(row["xmax"]),
                float(row["ymax"]),
            ))
    return dict(grouped)


def materialize_image(source: Path, destination: Path, copy_mode: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if copy_mode == "copy":
        shutil.copy2(source, destination)
    elif copy_mode == "symlink":
        if destination.exists():
            destination.unlink()
        destination.symlink_to(source.resolve())
    else:
        raise ValueError("copy_mode must be copy or symlink")


def write_dataset_yaml(output_root: Path) -> None:
    (output_root / "heridal_person.yaml").write_text(
        "train: images/train\nval: images/train\nnc: 1\nnames: ['person']\n",
        encoding="utf-8",
    )


def load_annotation_map(annotations_dir: Path) -> tuple[str, dict[str, list[tuple[float, float, float, float]]]]:
    csv_path = annotations_dir / "annotations.csv"
    if csv_path.exists():
        return "csv", parse_csv_annotations(csv_path)
    xml_files = sorted(annotations_dir.glob("*.xml"))
    if xml_files:
        return "voc_xml", {path.with_suffix(".jpg").name: parse_xml_annotations(path) for path in xml_files}
    raise FileNotFoundError("Expected annotations as annotations/*.xml or annotations/annotations.csv")


def convert_dataset(heridal_root: str | Path, output_root: str | Path, *, copy_mode: str = "copy") -> dict[str, int | str]:
    root = Path(heridal_root)
    output = Path(output_root)
    images_dir = root / "images"
    annotations_dir = root / "annotations"
    if not images_dir.is_dir():
        raise FileNotFoundError(f"Missing images directory: {images_dir}")
    if not annotations_dir.is_dir():
        raise FileNotFoundError(f"Expected annotations directory: {annotations_dir}")

    annotation_format, annotations = load_annotation_map(annotations_dir)
    output_images = output / "images" / "train"
    output_labels = output / "labels" / "train"
    output_labels.mkdir(parents=True, exist_ok=True)

    image_count = 0
    box_count = 0
    for image_path in image_paths(images_dir):
        width, height = image_size(image_path)
        boxes = annotations.get(image_path.name) or annotations.get(image_path.with_suffix(".jpg").name) or []
        lines = [yolo_line(*box, image_width=width, image_height=height) for box in boxes]
        materialize_image(image_path, output_images / image_path.name, copy_mode)
        (output_labels / f"{image_path.stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        image_count += 1
        box_count += len(lines)

    write_dataset_yaml(output)
    return {"images": image_count, "boxes": box_count, "annotation_format": annotation_format}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a local HERIDAL-style aerial-person dataset to person-only YOLO format.")
    parser.add_argument("--heridal-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--copy-mode", choices=("copy", "symlink"), default="copy")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = convert_dataset(args.heridal_root, args.output_root, copy_mode=args.copy_mode)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"HERIDAL conversion complete: {result['images']} images, {result['boxes']} boxes, format={result['annotation_format']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())