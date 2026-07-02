import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "combine_person_yolo_datasets.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("combine_person_yolo_datasets", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_dataset(root: Path, name: str, split: str = "train") -> None:
    (root / "images" / split).mkdir(parents=True)
    (root / "labels" / split).mkdir(parents=True)
    (root / "images" / split / f"{name}.jpg").write_bytes(b"image-" + name.encode())
    (root / "labels" / split / f"{name}.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")


def test_combines_sources_with_prefixed_files_and_manifest(tmp_path):
    module = _load_module()
    heridal = tmp_path / "heridal"
    visdrone = tmp_path / "visdrone"
    _write_dataset(heridal, "frame001", "train")
    _write_dataset(visdrone, "frame001", "train")
    _write_dataset(visdrone, "frame002", "val")

    result = module.combine_datasets(
        [("heridal", heridal), ("visdrone", visdrone)],
        tmp_path / "combined",
        copy_mode="copy",
    )

    combined = tmp_path / "combined"
    assert (combined / "images" / "train" / "heridal__frame001.jpg").exists()
    assert (combined / "images" / "train" / "visdrone__frame001.jpg").exists()
    assert (combined / "labels" / "val" / "visdrone__frame002.txt").exists()
    assert "train: images/train" in (combined / "combined_person.yaml").read_text(encoding="utf-8")
    manifest = json.loads((combined / "combined_manifest.json").read_text(encoding="utf-8"))
    assert manifest["summary"]["images"] == 3
    assert manifest["summary"]["labels"] == 3
    assert manifest["sources"][0]["id"] == "heridal"
    assert manifest["sources"][0]["splits"]["train"]["images"] == 1
    assert result["summary"]["images"] == 3


def test_rejects_source_missing_labels(tmp_path):
    module = _load_module()
    source = tmp_path / "bad"
    (source / "images" / "train").mkdir(parents=True)
    (source / "images" / "train" / "sample.jpg").write_bytes(b"image")

    try:
        module.combine_datasets([("bad", source)], tmp_path / "combined")
    except FileNotFoundError as exc:
        assert "labels/train" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_cli_combines_sources(tmp_path):
    heridal = tmp_path / "heridal"
    visdrone = tmp_path / "visdrone"
    _write_dataset(heridal, "a", "train")
    _write_dataset(visdrone, "b", "train")
    output = tmp_path / "combined"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/combine_person_yolo_datasets.py",
            "--source",
            f"heridal={heridal}",
            "--source",
            f"visdrone={visdrone}",
            "--output-root",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert (output / "combined_manifest.json").exists()
    assert "Combined YOLO dataset" in result.stdout