import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "train_visdrone_person.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("train_visdrone_person", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_training_metadata_includes_dataset_manifest_hash(tmp_path):
    module = _load_module()
    dataset_yaml = tmp_path / "combined_person.yaml"
    dataset_yaml.write_text("train: images/train\n", encoding="utf-8")
    dataset_manifest = tmp_path / "combined_manifest.json"
    dataset_manifest.write_text(json.dumps({"summary": {"images": 12}}), encoding="utf-8")

    metadata = module.build_training_metadata(
        dataset_yaml=dataset_yaml,
        dataset_manifest=dataset_manifest,
        model="yolo26n.pt",
        epochs=50,
        imgsz=640,
        batch=-1,
        project="runs/visdrone_person",
        name="exp1",
        best_path=Path("runs/visdrone_person/exp1/weights/best.pt"),
        save_dir=Path("runs/visdrone_person/exp1"),
        status="planned",
    )

    assert metadata["type"] == "sar-intel-training-metadata"
    assert metadata["dataset"]["yaml_sha256"]
    assert metadata["dataset"]["manifest_sha256"]
    assert metadata["dataset"]["manifest_payload"]["summary"]["images"] == 12
    assert metadata["training"]["epochs"] == 50
    assert metadata["outputs"]["best_path"].endswith("best.pt")


def test_write_training_metadata_creates_parent_directory(tmp_path):
    module = _load_module()
    output = tmp_path / "nested" / "training_metadata.json"

    module.write_training_metadata({"type": "sar-intel-training-metadata"}, output)

    assert json.loads(output.read_text(encoding="utf-8"))["type"] == "sar-intel-training-metadata"


def test_cli_metadata_only_writes_metadata_without_training(tmp_path):
    dataset_yaml = tmp_path / "combined_person.yaml"
    dataset_yaml.write_text("train: images/train\n", encoding="utf-8")
    dataset_manifest = tmp_path / "combined_manifest.json"
    dataset_manifest.write_text(json.dumps({"summary": {"images": 1}}), encoding="utf-8")
    metadata_output = tmp_path / "training_metadata.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/train_visdrone_person.py",
            "--data",
            str(dataset_yaml),
            "--dataset-manifest",
            str(dataset_manifest),
            "--metadata-output",
            str(metadata_output),
            "--metadata-only",
            "--name",
            "dry-run",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    metadata = json.loads(metadata_output.read_text(encoding="utf-8"))
    assert metadata["status"] == "metadata_only"
    assert metadata["training"]["name"] == "dry-run"
    assert "training_metadata" in result.stdout