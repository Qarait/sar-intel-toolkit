from __future__ import annotations

from typing import Any, Iterable, Mapping

from motion_tracklets import MotionTracklet


def _tracklet_id(tracklet: MotionTracklet, index: int | None = None) -> str:
    existing = getattr(tracklet, "tracklet_id", None)
    if existing is not None:
        return str(existing)
    if index is None:
        return f"motion-{tracklet.start_frame}-{tracklet.end_frame}"
    return f"motion-{index:04d}"


def motion_tracklet_to_record(tracklet: MotionTracklet, *, tracklet_id: str | None = None) -> dict[str, Any]:
    record_id = tracklet_id or _tracklet_id(tracklet)
    return {
        "tracklet_id": record_id,
        "start_frame": tracklet.start_frame,
        "end_frame": tracklet.end_frame,
        "duration": tracklet.duration,
        "score": tracklet.score,
        "displacement": round(tracklet.displacement, 12),
        "candidates": [
            {
                "frame_index": candidate.frame_index,
                "bbox": list(candidate.bbox),
                "centroid": [candidate.centroid[0], candidate.centroid[1]],
                "area": candidate.area,
                "mean_delta": candidate.mean_delta,
            }
            for candidate in tracklet.candidates
        ],
    }


def build_review_queue(
    tracklets: Iterable[MotionTracklet],
    *,
    coverage_by_tracklet: Mapping[str, Mapping[str, float]],
    uncertainty_weight: float = 10.0,
) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for index, tracklet in enumerate(tracklets, start=1):
        tracklet_id = _tracklet_id(tracklet, index)
        record = motion_tracklet_to_record(tracklet, tracklet_id=tracklet_id)
        miss_probability = float(coverage_by_tracklet.get(tracklet_id, {}).get("miss_probability", 0.0))
        priority = float(tracklet.score) + miss_probability * uncertainty_weight
        record.update(
            {
                "coverage_miss_probability": miss_probability,
                "review_priority": round(priority, 12),
                "status": "unreviewed",
            }
        )
        queue.append(record)
    return sorted(queue, key=lambda item: float(item["review_priority"]), reverse=True)