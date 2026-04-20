import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_step(label: str, command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"Release verification failed during {label}: {' '.join(command)}")


def main() -> None:
    acceptance_test_path = ROOT / "tests" / "test_acceptance_pipeline.py"
    if not acceptance_test_path.exists():
        raise SystemExit("Release verification failed: tests/test_acceptance_pipeline.py is missing.")

    _run_step("compile", [sys.executable, "-m", "compileall", "."])
    _run_step("unit tests", [sys.executable, "-m", "pytest"])
    _run_step("offline config", [sys.executable, "main.py", "--config", "config.offline.yaml"])
    _run_step("replay config", [sys.executable, "main.py", "--config", "config.replay.yaml"])

    print("SAR-INTEL release verification passed:")
    print("- compile: ok")
    print("- unit tests: ok")
    print("- offline config: ok")
    print("- replay config: ok")
    print("- acceptance pipeline: ok")


if __name__ == "__main__":
    main()