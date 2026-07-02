import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_PATH = ROOT / "site" / "assets" / "review_queue.json"


def test_public_review_queue_asset_matches_generator() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/build_public_review_queue.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_public_review_queue_asset_is_public_safe_and_review_ready() -> None:
    payload = json.loads(ASSET_PATH.read_text(encoding="utf-8"))

    assert payload["type"] == "sar-intel-public-review-queue"
    assert payload["version"] == 1
    assert payload["safety_note"]
    assert len(payload["candidates"]) >= 3

    priorities = [candidate["review_priority"] for candidate in payload["candidates"]]
    assert priorities == sorted(priorities, reverse=True)

    forbidden_keys = {"lat", "latitude", "lon", "longitude", "gps", "coordinates"}
    serialized = json.dumps(payload).lower()
    for key in forbidden_keys:
        assert f'"{key}"' not in serialized

    for candidate in payload["candidates"]:
        assert candidate["tracklet_id"].startswith("motion-")
        assert candidate["status"] == "unreviewed"
        assert 0.0 <= candidate["coverage_miss_probability"] <= 1.0
        assert candidate["motion_score"] >= 0.0
        preview = candidate["frame_preview"]
        bbox = preview["bbox_percent"]
        assert set(bbox) == {"left", "top", "width", "height"}
        assert all(0 <= bbox[name] <= 100 for name in bbox)
        assert preview["motion_trail_percent"]


def test_public_site_fetches_review_queue_asset_before_fallback() -> None:
    app_js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")

    assert "assets/review_queue.json" in app_js
    assert "fetchPublicReviewQueue" in app_js
    assert "normalizeReviewQueueCandidate" in app_js
    assert "fallbackReviewCandidates" in app_js