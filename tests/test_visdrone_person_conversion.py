import importlib.util
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "prepare_visdrone_person_yolo.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("prepare_visdrone_person_yolo", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_image(path: Path, width: int, height: int) -> None:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    if not cv2.imwrite(str(path), frame):
        raise AssertionError(f"Failed to write test image: {path}")


def test_category_1_pedestrian_converts_to_person() -> None:
    module = _load_module()

    converted = module.convert_annotation_line_to_yolo(
        "10,20,30,40,1,1,0,0",
        image_width=100,
        image_height=200,
    )

    assert converted == "0 0.250000 0.200000 0.300000 0.200000"


def test_category_2_people_converts_to_person() -> None:
    module = _load_module()

    converted = module.convert_annotation_line_to_yolo(
        "10,20,30,40,1,2,0,0",
        image_width=100,
        image_height=200,
    )

    assert converted == "0 0.250000 0.200000 0.300000 0.200000"


def test_non_person_categories_are_ignored() -> None:
    module = _load_module()

    assert module.convert_annotation_line_to_yolo(
        "10,20,30,40,1,4,0,0",
        image_width=100,
        image_height=200,
    ) is None


def test_invalid_boxes_are_ignored() -> None:
    module = _load_module()

    assert module.convert_annotation_line_to_yolo(
        "10,20,0,40,1,1,0,0",
        image_width=100,
        image_height=200,
    ) is None
    assert module.convert_annotation_line_to_yolo(
        "10,20,30,-1,1,2,0,0",
        image_width=100,
        image_height=200,
    ) is None


def test_xywh_to_normalized_yolo_values_are_correct() -> None:
    module = _load_module()

    normalized = module.xywh_to_yolo(
        x=10.0,
        y=20.0,
        width=30.0,
        height=40.0,
        image_width=100,
        image_height=200,
    )

    assert normalized == [0.25, 0.2, 0.3, 0.2]


def test_generated_dataset_yaml_contains_person_name(tmp_path) -> None:
    module = _load_module()
    output_root = tmp_path / "yolo_person"
    output_root.mkdir()

    yaml_path = module.write_dataset_yaml(output_root)
    contents = yaml_path.read_text(encoding="utf-8")

    assert yaml_path.name == "visdrone_person.yaml"
    assert "names:" in contents
    assert "0: person" in contents
    assert "train: images/train" in contents
    assert "val: images/val" in contents


def test_synthetic_train_val_fixture_produces_expected_yolo_layout(tmp_path) -> None:
    module = _load_module()

    visdrone_root = tmp_path / "visdrone"
    train_root = visdrone_root / "VisDrone2019-DET-train"
    val_root = visdrone_root / "VisDrone2019-DET-val"
    for split_root in (train_root, val_root):
        (split_root / "images").mkdir(parents=True)
        (split_root / "annotations").mkdir(parents=True)

    _write_image(train_root / "images" / "train_sample.jpg", width=100, height=200)
    (train_root / "annotations" / "train_sample.txt").write_text(
        "10,20,30,40,1,1,0,0\n"
        "10,20,30,40,1,4,0,0\n",
        encoding="utf-8",
    )

    _write_image(val_root / "images" / "val_sample.jpg", width=80, height=80)
    (val_root / "annotations" / "val_sample.txt").write_text(
        "8,12,16,20,1,2,0,0\n",
        encoding="utf-8",
    )

    output_root = tmp_path / "prepared"
    result = module.prepare_visdrone_person_dataset(visdrone_root, output_root)

    assert result["train"]["images"] == 1
    assert result["train"]["labels"] == 1
    assert result["val"]["images"] == 1
    assert result["val"]["labels"] == 1

    assert (output_root / "images" / "train" / "train_sample.jpg").exists()
    assert (output_root / "images" / "val" / "val_sample.jpg").exists()

    train_label = (output_root / "labels" / "train" / "train_sample.txt").read_text(encoding="utf-8").strip()
    val_label = (output_root / "labels" / "val" / "val_sample.txt").read_text(encoding="utf-8").strip()

    assert train_label == "0 0.250000 0.200000 0.300000 0.200000"
    assert val_label == "0 0.200000 0.275000 0.200000 0.250000"

    assert (output_root / "visdrone_person.yaml").exists()
    assert result["person_boxes"] == 2
    assert result["skipped_invalid_boxes"] == 0
    assert result["skipped_non_person_boxes"] == 1


def test_missing_required_split_raises_file_not_found(tmp_path) -> None:
    module = _load_module()

    visdrone_root = tmp_path / "visdrone"
    train_root = visdrone_root / "VisDrone2019-DET-train"
    (train_root / "images").mkdir(parents=True)
    (train_root / "annotations").mkdir(parents=True)

    output_root = tmp_path / "prepared"

    try:
        module.prepare_visdrone_person_dataset(visdrone_root, output_root)
    except FileNotFoundError as exc:
        assert "val" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError when a required split is missing")