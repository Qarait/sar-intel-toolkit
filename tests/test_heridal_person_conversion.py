import importlib.util
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "prepare_heridal_person_yolo.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("prepare_heridal_person_yolo", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_image(path: Path, size=(100, 50)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=(20, 40, 60)).save(path)


def test_converts_voc_xml_annotations_to_person_yolo(tmp_path):
    module = _load_module()
    root = tmp_path / "HERIDAL"
    _write_image(root / "images" / "frame001.jpg")
    (root / "annotations").mkdir()
    (root / "annotations" / "frame001.xml").write_text(
        """<annotation><object><name>person</name><bndbox><xmin>10</xmin><ymin>5</ymin><xmax>30</xmax><ymax>25</ymax></bndbox></object></annotation>""",
        encoding="utf-8",
    )

    result = module.convert_dataset(root, tmp_path / "out", copy_mode="copy")

    label = (tmp_path / "out" / "labels" / "train" / "frame001.txt").read_text(encoding="utf-8").strip()
    assert label == "0 0.200000 0.300000 0.200000 0.400000"
    assert result["images"] == 1
    assert result["boxes"] == 1
    assert (tmp_path / "out" / "images" / "train" / "frame001.jpg").exists()
    assert "train: images/train" in (tmp_path / "out" / "heridal_person.yaml").read_text(encoding="utf-8")


def test_converts_csv_annotations_to_person_yolo(tmp_path):
    module = _load_module()
    root = tmp_path / "HERIDAL"
    _write_image(root / "images" / "frame002.jpg", size=(200, 100))
    (root / "annotations").mkdir()
    (root / "annotations" / "annotations.csv").write_text(
        "filename,xmin,ymin,xmax,ymax,class\nframe002.jpg,50,20,90,60,person\n",
        encoding="utf-8",
    )

    module.convert_dataset(root, tmp_path / "out", copy_mode="copy")

    label = (tmp_path / "out" / "labels" / "train" / "frame002.txt").read_text(encoding="utf-8").strip()
    assert label == "0 0.350000 0.400000 0.200000 0.400000"


def test_cli_requires_known_layout(tmp_path):
    root = tmp_path / "bad"
    (root / "images").mkdir(parents=True)
    output = tmp_path / "out"

    result = subprocess.run(
        [sys.executable, "scripts/prepare_heridal_person_yolo.py", "--heridal-root", str(root), "--output-root", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Expected annotations" in result.stderr