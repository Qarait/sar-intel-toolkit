from motion_tracklets import MotionCandidate, MotionTracklet
from review_queue import build_review_queue, motion_tracklet_to_record


def _candidate(frame_index: int, x: int, y: int) -> MotionCandidate:
    return MotionCandidate(
        frame_index=frame_index,
        bbox=(x, y, x + 2, y + 2),
        centroid=(float(x + 1), float(y + 1)),
        area=9,
        mean_delta=255.0,
    )


def _tracklet(tracklet_id: str, score: float, start_x: int = 2) -> MotionTracklet:
    base = MotionTracklet(
        candidates=(
            _candidate(1, start_x, 8),
            _candidate(2, start_x + 2, 8),
            _candidate(3, start_x + 4, 8),
        ),
        score=score,
    )
    object.__setattr__(base, "tracklet_id", tracklet_id)
    return base


def test_motion_tracklet_serializes_to_json_ready_record() -> None:
    record = motion_tracklet_to_record(_tracklet("m-1", score=7.5))

    assert record == {
        "tracklet_id": "m-1",
        "start_frame": 1,
        "end_frame": 3,
        "duration": 3,
        "score": 7.5,
        "displacement": 4.0,
        "candidates": [
            {"frame_index": 1, "bbox": [2, 8, 4, 10], "centroid": [3.0, 9.0], "area": 9, "mean_delta": 255.0},
            {"frame_index": 2, "bbox": [4, 8, 6, 10], "centroid": [5.0, 9.0], "area": 9, "mean_delta": 255.0},
            {"frame_index": 3, "bbox": [6, 8, 8, 10], "centroid": [7.0, 9.0], "area": 9, "mean_delta": 255.0},
        ],
    }


def test_review_queue_ranks_uncertainty_before_raw_motion_score() -> None:
    high_motion_low_uncertainty = _tracklet("fast-covered", score=10.0, start_x=2)
    lower_motion_high_uncertainty = _tracklet("slow-uncertain", score=6.0, start_x=10)
    coverage = {
        "fast-covered": {"miss_probability": 0.20},
        "slow-uncertain": {"miss_probability": 0.85},
    }

    queue = build_review_queue(
        [high_motion_low_uncertainty, lower_motion_high_uncertainty],
        coverage_by_tracklet=coverage,
    )

    assert [item["tracklet_id"] for item in queue] == ["slow-uncertain", "fast-covered"]
    assert queue[0]["review_priority"] > queue[1]["review_priority"]
    assert queue[0]["status"] == "unreviewed"


def test_review_queue_defaults_missing_coverage_to_zero_uncertainty() -> None:
    queue = build_review_queue([_tracklet("motion-only", score=4.0)], coverage_by_tracklet={})

    assert queue[0]["tracklet_id"] == "motion-only"
    assert queue[0]["coverage_miss_probability"] == 0.0
    assert queue[0]["review_priority"] == 4.0