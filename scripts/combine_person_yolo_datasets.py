from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SPLITS = ("train", "val")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_source(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("sources must use id=path format")
    source_id, path = value.split("=", 1)
    source_id = source_id.strip()
    if not source_id or any(char in source_id for char in "\\/ :"):
        raise argparse.ArgumentTypeError("source id must be a simple filename-safe token")
    return source_id, Path(path)


def image_files(root: Path, split: str) -> list[Path]:
    directory = root / "images" / split
    if not directory.exists():
        return []
    return sorted(path for path in directory.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)


def validate_source(root: Path, split: str) -> None:
    images_dir = root / "images" / split
    labels_dir = root / "labels" / split
    if images_dir.exists() and not labels_dir.exists():
        raise FileNotFoundError(f"Missing labels/{split} for source: {root}")


def materialize(source: Path, destination: Path, copy_mode: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if copy_mode == "copy":
        shutil.copy2(source, destination)
    elif copy_mode == "symlink":
        if destination.exists():
            destination.unlink()
        destination.symlink_to(source.resolve())
    else:
        raise ValueError("copy_mode must be copy or symlink")


def write_yaml(output_root: Path) -> None:
    (output_root / "combined_person.yaml").write_text(
        "train: images/train\nval: images/val\nnc: 1\nnames: ['person']\n",
        encoding="utf-8",
    )


def combine_datasets(
    sources: Sequence[tuple[str, str | Path]],
    output_root: str | Path,
    *,
    copy_mode: str = "copy",
) -> dict[str, Any]:
    output = Path(output_root)
    source_reports: list[dict[str, Any]] = []
    total_images = 0
    total_labels = 0

    for source_id, source_root_raw in sources:
        source_root = Path(source_root_raw)
        if not source_root.exists():
            raise FileNotFoundError(f"Missing source root: {source_root}")
        source_report: dict[str, Any] = {"id": source_id, "root": str(source_root), "splits": {}}
        for split in SPLITS:
            validate_source(source_root, split)
            split_images = image_files(source_root, split)
            split_report = {"images": 0, "labels": 0, "files": []}
            for image_path in split_images:
                label_path = source_root / "labels" / split / f"{image_path.stem}.txt"
                if not label_path.exists():
                    raise FileNotFoundError(f"Missing label for {image_path.name}: {label_path}")
                prefix = f"{source_id}__{image_path.stem}"
                output_image = output / "images" / split / f"{prefix}{image_path.suffix.lower()}"
                output_label = output / "labels" / split / f"{prefix}.txt"
                materialize(image_path, output_image, copy_mode)
                materialize(label_path, output_label, copy_mode)
                split_report["images"] += 1
                split_report["labels"] += 1
                split_report["files"].append({
                    "image": str(output_image.relative_to(output)),
                    "label": str(output_label.relative_to(output)),
                    "source_image_sha256": sha256_file(image_path),
                    "source_label_sha256": sha256_file(label_path),
                })
            source_report["splits"][split] = split_report
            total_images += split_report["images"]
            total_labels += split_report["labels"]
        source_reports.append(source_report)

    write_yaml(output)
    manifest = {
        "type": "sar-intel-combined-person-yolo-dataset",
        "version": 1,
        "copy_mode": copy_mode,
        "summary": {"sources": len(source_reports), "images": total_images, "labels": total_labels},
        "sources": source_reports,
    }
    (output / "combined_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine prepared person-only YOLO datasets with source-prefixed filenames.")
    parser.add_argument("--source", action="append", required=True, type=parse_source, help="Prepared YOLO source as id=path")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--copy-mode", choices=("copy", "symlink"), default="copy")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = combine_datasets(args.source, args.output_root, copy_mode=args.copy_mode)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Combined YOLO dataset: {manifest['summary']['images']} images from {manifest['summary']['sources']} sources")
    print(f"Manifest: {Path(args.output_root) / 'combined_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())