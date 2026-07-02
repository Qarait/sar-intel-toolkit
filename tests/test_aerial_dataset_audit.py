import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "audit_aerial_datasets.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_aerial_datasets", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_registry_prioritizes_sar_relevant_aerial_person_datasets():
    module = _load_module()

    ids = [dataset["id"] for dataset in module.DATASET_REGISTRY]

    assert ids[:3] == ["heridal", "seadronessee", "visdrone-person"]
    assert all(dataset["task"] == "aerial-person-detection" for dataset in module.DATASET_REGISTRY)
    assert all(dataset["claim_status"] == "candidate-training-source" for dataset in module.DATASET_REGISTRY)


def test_audit_reports_ready_missing_and_blocked_dataset_roots(tmp_path):
    module = _load_module()
    heridal = tmp_path / "HERIDAL"
    (heridal / "images").mkdir(parents=True)
    (heridal / "annotations").mkdir()
    seadrones = tmp_path / "SeaDronesSee"
    seadrones.mkdir()

    report = module.build_dataset_audit(
        {
            "heridal": heridal,
            "seadronessee": seadrones,
            "visdrone-person": tmp_path / "missing-visdrone",
        }
    )

    by_id = {item["id"]: item for item in report["datasets"]}
    assert by_id["heridal"]["status"] == "ready_for_converter"
    assert by_id["seadronessee"]["status"] == "missing_required_paths"
    assert by_id["visdrone-person"]["status"] == "missing_root"
    assert report["summary"]["ready_for_converter"] == 1
    assert report["summary"]["missing_required_paths"] == 1
    assert report["summary"]["missing_root"] == 1


def test_cli_writes_audit_report(tmp_path):
    root = tmp_path / "HERIDAL"
    (root / "images").mkdir(parents=True)
    (root / "annotations").mkdir()
    output = tmp_path / "audit.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_aerial_datasets.py",
            "--dataset-root",
            f"heridal={root}",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["ready_for_converter"] == 1
    assert "Aerial dataset audit" in result.stdout