from __future__ import annotations

import argparse
import json
import struct
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ASSET_PATH = ROOT / "site" / "assets" / "review_queue.json"
THUMBNAIL_DIR = ROOT / "site" / "assets" / "review-candidates"

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


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _write_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    rows = bytearray()
    stride = width * 3
    for y in range(height):
        rows.append(0)
        start = y * stride
        rows.extend(pixels[start : start + stride])

    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    data += _chunk(b"IDAT", zlib.compress(bytes(rows), 9))
    data += _chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _set_pixel(pixels: bytearray, width: int, height: int, x: int, y: int, color: tuple[int, int, int]) -> None:
    if 0 <= x < width and 0 <= y < height:
        index = (y * width + x) * 3
        pixels[index : index + 3] = bytes(color)


def _fill_rect(
    pixels: bytearray,
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    for y in range(max(0, y0), min(height, y1)):
        for x in range(max(0, x0), min(width, x1)):
            _set_pixel(pixels, width, height, x, y, color)


def _draw_thumbnail(path: Path, candidate: dict[str, Any], index: int) -> None:
    width, height = 640, 360
    pixels = bytearray(width * height * 3)
    seed = sum(candidate["tracklet_id"].encode("utf-8")) + index * 97

    for y in range(height):
        for x in range(width):
            texture = (x * 13 + y * 7 + seed) % 29
            band = ((x // 46) + (y // 38) + index) % 5
            base = 28 + band * 6 + texture // 4
            green = 58 + ((x + seed) % 37) + band * 4
            blue = 62 + ((y * 2 + seed) % 43)
            if (x + y + seed) % 97 < 7:
                green += 24
                blue += 10
            pos = (y * width + x) * 3
            pixels[pos : pos + 3] = bytes((min(base, 88), min(green, 132), min(blue, 126)))

    # Simulated flight-imagery structure: terrain bands, tracks, and faint scan grid.
    for offset in range(-180, width, 92):
        for step in range(20):
            _fill_rect(pixels, width, height, offset + step * 9, 70 + step * 3, offset + step * 9 + 5, 76 + step * 3, (76, 104, 94))
    for y in range(0, height, 40):
        for x in range(width):
            if x % 3 == 0:
                _set_pixel(pixels, width, height, x, y, (58, 100, 108))
    for x in range(0, width, 40):
        for y in range(height):
            if y % 3 == 0:
                _set_pixel(pixels, width, height, x, y, (58, 100, 108))

    bbox = candidate["frame_preview"]["bbox_percent"]
    cx = int((bbox["left"] + bbox["width"] / 2) / 100 * width)
    cy = int((bbox["top"] + bbox["height"] / 2) / 100 * height)
    _fill_rect(pixels, width, height, cx - 3, cy - 3, cx + 4, cy + 4, (206, 232, 156))

    _write_png(path, width, height, pixels)


def _candidate_with_thumbnail(candidate: dict[str, Any], index: int) -> dict[str, Any]:
    copied = json.loads(json.dumps(candidate))
    filename = f"{copied['tracklet_id']}.png"
    copied["frame_preview"]["image"] = f"assets/review-candidates/{filename}"
    return copied


def build_payload() -> dict[str, Any]:
    candidates = [
        _candidate_with_thumbnail(candidate, index)
        for index, candidate in enumerate(CANDIDATES, start=1)
    ]
    candidates = sorted(candidates, key=lambda item: float(item["review_priority"]), reverse=True)
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


def write_thumbnails() -> None:
    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    for index, candidate in enumerate(CANDIDATES, start=1):
        _draw_thumbnail(THUMBNAIL_DIR / f"{candidate['tracklet_id']}.png", candidate, index)


def write_asset(path: Path = ASSET_PATH) -> None:
    write_thumbnails()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(build_payload()), encoding="utf-8")


def check_thumbnails(payload: dict[str, Any]) -> bool:
    ok = True
    for candidate in payload["candidates"]:
        image_path = candidate["frame_preview"].get("image")
        if not image_path:
            print(f"Missing frame preview image for {candidate['tracklet_id']}")
            ok = False
            continue
        path = ROOT / "site" / image_path
        if not path.exists():
            print(f"Missing frame preview image asset: {path}")
            ok = False
    return ok


def check_asset(path: Path = ASSET_PATH) -> bool:
    expected_payload = build_payload()
    expected = canonical_json(expected_payload)
    if not path.exists():
        print(f"Missing public review queue asset: {path}")
        return False
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        print(f"Public review queue asset is out of date: {path}")
        return False
    if not check_thumbnails(expected_payload):
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
    print(f"Wrote public review thumbnail assets: {THUMBNAIL_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())