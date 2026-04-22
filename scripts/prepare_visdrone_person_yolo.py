import argparse
import shutil
from pathlib import Path
from typing import Sequence

import cv2


PERSON_CATEGORY_IDS = {1, 2}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a person-only YOLO dataset from VisDrone DET splits.")
    parser.add_argument(
        "--visdrone-root",
        required=True,
        help="Path to the extracted VisDrone root containing VisDrone2019-DET-train and VisDrone2019-DET-val.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Output directory for the generated YOLO dataset layout.",
    )
    parser.add_argument(
        "--copy-mode",
        choices=["copy", "symlink"],
        default="copy",
        help="How to place images into the YOLO dataset layout. Default: copy.",
    )
    return parser.parse_args(argv)


def xywh_to_yolo(
    x: float,
    y: float,
    width: float,
    height: float,
    image_width: int,
    image_height: int,
) -> list[float]:
    if image_width <= 0 or image_height <= 0:
        raise ValueError("Image dimensions must be positive.")
    if width <= 0 or height <= 0:
        raise ValueError("Bounding box dimensions must be positive.")

    center_x = (x + (width / 2.0)) / float(image_width)
    center_y = (y + (height / 2.0)) / float(image_height)
    norm_width = width / float(image_width)
    norm_height = height / float(image_height)
    return [center_x, center_y, norm_width, norm_height]


def convert_annotation_line_to_yolo(
    line: str,
    *,
    image_width: int,
    image_height: int,
) -> str | None:
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 6:
        raise ValueError(f"Malformed annotation line: {line!r}")

    x = float(parts[0])
    y = float(parts[1])
    width = float(parts[2])
    height = float(parts[3])
    score = int(float(parts[4]))
    category = int(float(parts[5]))

    if score != 1 or category not in PERSON_CATEGORY_IDS:
        return None
    if width <= 0 or height <= 0:
        return None

    yolo_box = xywh_to_yolo(
        x=x,
        y=y,
        width=width,
        height=height,
        image_width=image_width,
        image_height=image_height,
    )
    return "0 " + " ".join(f"{value:.6f}" for value in yolo_box)


def resolve_split_root(visdrone_root: str | Path, split: str) -> Path:
    root = Path(visdrone_root)
    candidates = [root / f"VisDrone2019-DET-{split}", root / split, root]

    for candidate in candidates:
        if (candidate / "images").is_dir() and (candidate / "annotations").is_dir():
            return candidate

    raise FileNotFoundError(
        f"Could not find VisDrone DET split {split!r} under {root}. Expected images/ and annotations/ directories."
    )


def load_image_size(image_path: Path) -> tuple[int, int]:
    frame = cv2.imread(str(image_path))
    if frame is None:
        raise ValueError(f"Unable to read image: {image_path}")
    height, width = frame.shape[:2]
    return width, height


def convert_annotation_file(annotation_path: Path, *, image_width: int, image_height: int) -> list[str]:
    converted: list[str] = []
    for line in annotation_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        yolo_line = convert_annotation_line_to_yolo(
            line,
            image_width=image_width,
            image_height=image_height,
        )
        if yolo_line is not None:
            converted.append(yolo_line)
    return converted


def write_dataset_yaml(
    output_root: str | Path,
    splits: Sequence[str] = ("train", "val"),
) -> Path:
    output_path = Path(output_root)
    yaml_path = output_path / "visdrone_person.yaml"
    lines = ["path: ."]
    if "train" in splits:
        lines.append("train: images/train")
    if "val" in splits:
        lines.append("val: images/val")
    lines.extend(["names:", "  0: person", ""])
    yaml_path.write_text("\n".join(lines), encoding="utf-8")
    return yaml_path


def available_splits(visdrone_root: str | Path, splits: Sequence[str]) -> list[str]:
    resolved: list[str] = []
    for split in splits:
        try:
            resolve_split_root(visdrone_root, split)
        except FileNotFoundError:
            continue
        resolved.append(split)
    if not resolved:
        raise FileNotFoundError(
            f"Could not find any requested VisDrone DET splits under {Path(visdrone_root)}: {', '.join(splits)}"
        )
    return resolved
def materialize_image(image_path: Path, destination_path: Path, copy_mode: str) -> None:
    if copy_mode == "copy":
        shutil.copy2(image_path, destination_path)
        return
    if destination_path.exists() or destination_path.is_symlink():
        destination_path.unlink()
    destination_path.symlink_to(image_path.resolve())


def prepare_split(split_root: Path, output_root: Path, split: str, *, copy_mode: str) -> dict[str, int]:
    images_dir = split_root / "images"
    annotations_dir = split_root / "annotations"
    output_images_dir = output_root / "images" / split
    output_labels_dir = output_root / "labels" / split
    output_images_dir.mkdir(parents=True, exist_ok=True)
    output_labels_dir.mkdir(parents=True, exist_ok=True)

    image_count = 0
    label_count = 0

    for image_path in sorted(images_dir.glob("*.jpg")):
        annotation_path = annotations_dir / f"{image_path.stem}.txt"
        if not annotation_path.exists():
            raise FileNotFoundError(f"Missing annotation file for {image_path.name}: {annotation_path}")

        image_width, image_height = load_image_size(image_path)
        converted_lines = convert_annotation_file(
            annotation_path,
            image_width=image_width,
            image_height=image_height,
        )

        materialize_image(image_path, output_images_dir / image_path.name, copy_mode)
        (output_labels_dir / f"{image_path.stem}.txt").write_text(
            "\n".join(converted_lines) + ("\n" if converted_lines else ""),
            encoding="utf-8",
        )

        image_count += 1
        label_count += 1

    return {"images": image_count, "labels": label_count}


def prepare_visdrone_person_dataset(
    visdrone_root: str | Path,
    output_root: str | Path,
    splits: Sequence[str] = ("train", "val"),
    copy_mode: str = "copy",
) -> dict[str, dict[str, int] | str]:
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)
    resolved_splits = available_splits(visdrone_root, splits)

    results: dict[str, dict[str, int] | str] = {}
    for split in resolved_splits:
        split_root = resolve_split_root(visdrone_root, split)
        results[split] = prepare_split(split_root, output_path, split, copy_mode=copy_mode)

    yaml_path = write_dataset_yaml(output_path, resolved_splits)
    results["dataset_yaml"] = str(yaml_path)
    return results


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    results = prepare_visdrone_person_dataset(
        visdrone_root=args.visdrone_root,
        output_root=args.output_root,
        copy_mode=args.copy_mode,
    )

    print(f"Prepared YOLO dataset at {Path(args.output_root).resolve()}")
    for split in available_splits(args.visdrone_root, ("train", "val")):
        split_result = results[split]
        print(f"{split}: {split_result['images']} images, {split_result['labels']} label files")
    print(f"dataset_yaml: {results['dataset_yaml']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())