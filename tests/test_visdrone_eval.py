import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "evaluate_visdrone_det.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("evaluate_visdrone_det", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_xywh_to_xyxy_converts_expected_box() -> None:
    module = _load_module()

    assert module.xywh_to_xyxy([10, 20, 30, 40]) == [10.0, 20.0, 40.0, 60.0]


def test_parse_visdrone_annotation_file_keeps_categories_1_and_2_only(tmp_path) -> None:
    module = _load_module()
    annotation_path = tmp_path / "sample.txt"
    annotation_path.write_text(
        "10,20,30,40,1,1,0,0\n"
        "15,25,35,45,1,2,0,0\n",
        encoding="utf-8",
    )

    assert module.parse_visdrone_annotation_file(annotation_path) == [
        [10.0, 20.0, 40.0, 60.0],
        [15.0, 25.0, 50.0, 70.0],
    ]


def test_parse_visdrone_annotation_file_ignores_category_0_and_11(tmp_path) -> None:
    module = _load_module()
    annotation_path = tmp_path / "sample.txt"
    annotation_path.write_text(
        "10,20,30,40,1,0,0,0\n"
        "15,25,35,45,1,11,0,0\n"
        "20,30,40,50,1,1,0,0\n",
        encoding="utf-8",
    )

    assert module.parse_visdrone_annotation_file(annotation_path) == [
        [20.0, 30.0, 60.0, 80.0],
    ]


def test_bbox_iou_returns_one_for_identical_boxes() -> None:
    module = _load_module()

    assert module.bbox_iou([10.0, 10.0, 20.0, 20.0], [10.0, 10.0, 20.0, 20.0]) == 1.0


def test_match_detections_to_ground_truth_counts_tp_fp_fn() -> None:
    module = _load_module()
    detections = [
        {"confidence": 0.9, "bbox": [10.0, 10.0, 30.0, 30.0]},
        {"confidence": 0.8, "bbox": [40.0, 40.0, 46.0, 46.0]},
        {"confidence": 0.3, "bbox": [70.0, 70.0, 80.0, 80.0]},
    ]
    gt_boxes = [
        [10.0, 10.0, 30.0, 30.0],
        [40.0, 40.0, 50.0, 50.0],
    ]

    assert module.match_detections_to_ground_truth(detections, gt_boxes, 0.5) == (1, 2, 1)


def test_compute_metrics_handles_zero_denominators_safely() -> None:
    module = _load_module()

    assert module.compute_metrics(0, 0, 0) == {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }


def test_parse_sweep_thresholds_parses_and_sorts_unique_values() -> None:
    module = _load_module()

    assert module.parse_sweep_thresholds("0.50,0.10,0.25,0.25") == [0.10, 0.25, 0.50]


def test_parse_sweep_thresholds_rejects_invalid_values() -> None:
    module = _load_module()

    for value in ["-0.1", "1.5", "not-a-number", ""]:
        try:
            module.parse_sweep_thresholds(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {value!r}")


def test_parse_args_accepts_sweep_arguments() -> None:
    module = _load_module()

    args = module.parse_args(
        [
            "--dataset-root",
            "dataset",
            "--sweep",
            "--sweep-thresholds",
            "0.10,0.25,0.50",
        ]
    )

    assert args.dataset_root == "dataset"
    assert args.sweep is True
    assert args.confidence_threshold == 0.25
    assert args.sweep_thresholds == "0.10,0.25,0.50"


def test_parse_args_uses_default_sweep_thresholds() -> None:
    module = _load_module()

    args = module.parse_args([
        "--dataset-root",
        "dataset",
    ])

    assert args.sweep is False
    assert args.sweep_thresholds == "0.10,0.25,0.50"


def test_filter_detections_by_threshold() -> None:
    module = _load_module()

    detections = [
        {"confidence": 0.09, "bbox": [0, 0, 10, 10]},
        {"confidence": 0.25, "bbox": [0, 0, 10, 10]},
        {"confidence": 0.90, "bbox": [0, 0, 10, 10]},
    ]

    filtered = module.filter_detections_by_threshold(detections, 0.25)
    assert [item["confidence"] for item in filtered] == [0.25, 0.90]


def test_summarize_cached_evaluation_uses_same_detections_for_multiple_thresholds() -> None:
    module = _load_module()

    image_records = [
        {
            "image": "sample.jpg",
            "gt_boxes": [[10.0, 10.0, 30.0, 30.0]],
            "detections": [
                {"confidence": 0.20, "bbox": [10.0, 10.0, 30.0, 30.0]},
                {"confidence": 0.90, "bbox": [50.0, 50.0, 70.0, 70.0]},
            ],
        }
    ]

    low = module.summarize_cached_evaluation(
        image_records,
        confidence_threshold=0.10,
        iou_threshold=0.5,
        dataset_root="/tmp/VisDrone2019-DET-val",
        split="val",
        max_images=None,
        model="yolo26n.pt",
    )

    high = module.summarize_cached_evaluation(
        image_records,
        confidence_threshold=0.50,
        iou_threshold=0.5,
        dataset_root="/tmp/VisDrone2019-DET-val",
        split="val",
        max_images=None,
        model="yolo26n.pt",
    )

    assert low["detection_count"] == 2
    assert low["true_positives"] == 1
    assert low["false_positives"] == 1
    assert low["false_negatives"] == 0

    assert high["detection_count"] == 1
    assert high["true_positives"] == 0
    assert high["false_positives"] == 1
    assert high["false_negatives"] == 1


def test_build_validation_manifest_pins_file_list_and_hashes(tmp_path) -> None:
    module = _load_module()
    split_root = tmp_path / "VisDrone2019-DET-val"
    images_dir = split_root / "images"
    annotations_dir = split_root / "annotations"
    images_dir.mkdir(parents=True)
    annotations_dir.mkdir()
    (images_dir / "000002.jpg").write_bytes(b"second-image")
    (annotations_dir / "000002.txt").write_text("2,2,4,4,1,1,0,0\n", encoding="utf-8")
    (images_dir / "000001.jpg").write_bytes(b"first-image")
    (annotations_dir / "000001.txt").write_text("1,1,3,3,1,1,0,0\n", encoding="utf-8")

    manifest = module.build_validation_manifest(tmp_path, "val", max_images=None)

    assert manifest["record_count"] == 2
    assert [record["image"] for record in manifest["records"]] == ["000001.jpg", "000002.jpg"]
    assert manifest["checksum"] == module.compute_manifest_checksum(manifest)
    assert all(len(record["image_sha256"]) == 64 for record in manifest["records"])
    assert all(len(record["annotation_sha256"]) == 64 for record in manifest["records"])

    (images_dir / "000001.jpg").write_bytes(b"other-image")

    try:
        module.validate_manifest_files(manifest, tmp_path, "val")
    except ValueError as exc:
        assert "SHA256 mismatch" in str(exc)
    else:
        raise AssertionError("Expected tampered manifest validation to fail.")


def test_average_precision_rewards_confidence_order_not_threshold_shopping() -> None:
    module = _load_module()
    image_records = [
        {
            "image": "sample-a.jpg",
            "gt_boxes": [[0.0, 0.0, 10.0, 10.0]],
            "detections": [
                {"confidence": 0.90, "bbox": [20.0, 20.0, 30.0, 30.0]},
                {"confidence": 0.80, "bbox": [0.0, 0.0, 10.0, 10.0]},
            ],
        },
        {
            "image": "sample-b.jpg",
            "gt_boxes": [[50.0, 50.0, 60.0, 60.0]],
            "detections": [
                {"confidence": 0.70, "bbox": [50.0, 50.0, 60.0, 60.0]},
            ],
        },
    ]

    pr_curve = module.compute_precision_recall_curve(image_records, iou_threshold=0.5)
    summary = module.summarize_cached_evaluation(
        image_records,
        confidence_threshold=0.10,
        iou_threshold=0.5,
        dataset_root="/tmp/VisDrone2019-DET-val",
        split="val",
        max_images=None,
        model="yolo26n.pt",
    )

    assert abs(pr_curve["average_precision"] - (7 / 12)) < 1e-12
    assert pr_curve["points"] == [
        {"confidence": 0.9, "precision": 0.0, "recall": 0.0, "tp": 0, "fp": 1},
        {"confidence": 0.8, "precision": 0.5, "recall": 0.5, "tp": 1, "fp": 1},
        {"confidence": 0.7, "precision": 2 / 3, "recall": 1.0, "tp": 2, "fp": 1},
    ]
    assert abs(summary["average_precision"] - (7 / 12)) < 1e-12
