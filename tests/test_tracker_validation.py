import math

from tracker import KalmanBBoxFilter, SimpleTracker


def test_tracker_ignores_malformed_detections_and_clamps_confidence() -> None:
    tracker = SimpleTracker(
        iou_threshold=0.05,
        max_frame_gap=5,
        max_position_distance_m=50.0,
        min_hits=1,
    )

    detections = [
        {
            "timestamp": "2026-04-18T15:00:00.000Z",
            "lat": 43.65,
            "lon": -79.38,
            "confidence": 1.5,
            "bbox": [100, 100, 200, 300],
        },
        {
            "timestamp": "2026-04-18T15:00:00.000Z",
            "lat": 43.65,
            "lon": -79.38,
            "confidence": 0.9,
            "bbox": [100, 100, 100, 300],
        },
        {
            "timestamp": "2026-04-18T15:00:00.000Z",
            "lat": math.nan,
            "lon": -79.38,
            "confidence": 0.9,
            "bbox": [100, 100, 200, 300],
        },
    ]

    enriched = tracker.update(detections=detections, frame_idx=0)
    tracks = tracker.confirmed_tracks(scoring_config={"enabled": False})

    assert len(enriched) == 1
    assert enriched[0]["confidence"] == 1.0
    assert len(tracks) == 1
    assert tracks[0]["hits"] == 1
    assert tracks[0]["max_confidence"] == 1.0


def test_kalman_predict_ignores_invalid_dt_values() -> None:
    filt = KalmanBBoxFilter([100.0, 100.0, 200.0, 300.0])

    for invalid_dt in [0.0, -1.0, math.nan, math.inf, -math.inf]:
        filt.predict(dt=invalid_dt)

    predicted_bbox = filt.predicted_bbox()

    assert len(predicted_bbox) == 4
    assert all(math.isfinite(value) for value in predicted_bbox)