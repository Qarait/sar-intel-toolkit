import numpy as np

from motion_tracklets import build_motion_tracklets, detect_motion_candidates


def _blank(size: int = 24) -> np.ndarray:
    return np.zeros((size, size), dtype=np.uint8)


def _with_square(x: int, y: int, size: int = 3) -> np.ndarray:
    frame = _blank()
    frame[y : y + size, x : x + size] = 255
    return frame


def test_identical_frames_produce_no_motion_candidates() -> None:
    frame = _blank()

    candidates = detect_motion_candidates(frame, frame, frame_index=1, threshold=25, min_area=2)

    assert candidates == []


def test_moving_square_produces_motion_candidate_bbox() -> None:
    previous = _with_square(4, 8)
    current = _with_square(8, 8)

    candidates = detect_motion_candidates(previous, current, frame_index=1, threshold=25, min_area=3)

    assert len(candidates) == 2
    assert candidates[0].frame_index == 1
    assert candidates[0].area == 9
    assert candidates[0].bbox == (4, 8, 6, 10)
    assert candidates[1].bbox == (8, 8, 10, 10)


def test_short_flicker_is_rejected_by_persistence_filter() -> None:
    frames = [_blank(), _with_square(8, 8), _blank(), _blank()]

    tracklets = build_motion_tracklets(
        frames,
        threshold=25,
        min_area=3,
        min_persistence=3,
        max_link_distance=5.0,
    )

    assert tracklets == []


def test_persistent_motion_becomes_scored_tracklet() -> None:
    frames = [
        _with_square(2, 8),
        _with_square(4, 8),
        _with_square(6, 8),
        _with_square(8, 8),
    ]

    tracklets = build_motion_tracklets(
        frames,
        threshold=25,
        min_area=3,
        min_persistence=3,
        max_link_distance=4.0,
    )

    assert len(tracklets) == 1
    tracklet = tracklets[0]
    assert tracklet.start_frame == 1
    assert tracklet.end_frame == 3
    assert tracklet.duration == 3
    assert round(tracklet.displacement, 2) >= 4.0
    assert tracklet.score > 0.0