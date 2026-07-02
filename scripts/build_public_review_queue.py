from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ASSET_PATH = ROOT / "site" / "assets" / "review_queue.json"

CANDIDATES: list[dict[str, Any]] = [
    {
        "tracklet_id": "motion-0007",
        "title": "Tree-line motion candidate",
        "frame_range": "frames 184-193",
        "status": "unreviewed",
        "review_priority": 14.6,
        "motion_score": 8.1,
        "coverage_miss_probability": 0.65,
        "evidence": "Persistent small motion against a mostly static background.",
        "location_hint": "northwest grid cell",
        "frame_preview": {
            "bbox_percent": {"left": 28, "top": 36, "width": 22, "height": 30},
            "motion_trail_percent": [
                {"left": 30, "top": 62},
                {"left": 36, "top": 58},
                {"left": 43, "top": 54},
            ],
        },
    },
    {
        "tracklet_id": "motion-0012",
        "title": "Ridge-path uncertainty candidate",
        "frame_range": "frames 241-249",
        "status": "unreviewed",
        "review_priority": 12.2,
        "motion_score": 6.7,
        "coverage_miss_probability": 0.55,
        "evidence": "Lower motion score, but coverage confidence says this cell deserves another human look.",
        "location_hint": "ridge path edge",
        "frame_preview": {
            "bbox_percent": {"left": 56, "top": 24, "width": 18, "height": 24},
            "motion_trail_percent": [
                {"left": 58, "top": 46},
                {"left": 61, "top": 43},
                {"left": 65, "top": 41},
            ],
        },
    },
    {
        "tracklet_id": "motion-0019",
        "title": "Open-field flicker candidate",
        "frame_range": "frames 318-322",
        "status": "unreviewed",
        "review_priority": 8.4,
        "motion_score": 5.9,
        "coverage_miss_probability": 0.25,
        "evidence": "Short-lived motion that remains below confirmation threshold until reviewed.",
        "location_hint": "open field pass",
        "frame_preview": {
            "bbox_percent": {"left": 41, "top": 52, "width": 16, "height": 20},
            "motion_trail_percent": [
                {"left": 43, "top": 70},
                {"left": 47, "top": 68},
                {"left": 50, "top": 66},
            ],
        },
    },
]


def build_payload() -> dict[str, Any]:
    candidates = sorted(CANDIDATES, key=lambda item: float(item["review_priority"]), reverse=True)
    return {
        "type": "sar-intel-public-review-queue",
        "version": 1,
        "generated_from": "scripts/build_public_review_queue.py",
        "source": "sanitized static public demo",
        "safety_note": (
            "Public demo review candidates only. These records do not identify people, do not include original "
            "mission coordinates, and are not operational SAR findings."
        ),
        "candidates": candidates,
    }


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_asset(path: Path = ASSET_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(build_payload()), encoding="utf-8")


def check_asset(path: Path = ASSET_PATH) -> bool:
    expected = canonical_json(build_payload())
    if not path.exists():
        print(f"Missing public review queue asset: {path}")
        return False
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        print(f"Public review queue asset is out of date: {path}")
        return False
    print(f"Public review queue asset is up to date: {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or check the public-safe review queue demo asset.")
    parser.add_argument("--check", action="store_true", help="verify the committed asset matches this generator")
    args = parser.parse_args()

    if args.check:
        return 0 if check_asset() else 1

    write_asset()
    print(f"Wrote public review queue asset: {ASSET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())