from tracker import SimpleTracker


def test_kalman_tracker_continues_across_missed_frame() -> None:
    tracker = SimpleTracker(
        iou_threshold=0.05,
        max_frame_gap=5,
        max_position_distance_m=50,
        min_hits=2,
        motion_model="kalman",
        kalman_config={
            "process_noise": 1.0,
            "measurement_noise": 10.0,
            "initial_uncertainty": 100.0,
        },
    )

    detections = [
        {
            "timestamp": "2026-04-18T15:00:00.000Z",
            "frame_idx": 0,
            "lat": 43.65,
            "lon": -79.38,
            "confidence": 0.90,
            "bbox": [100, 100, 200, 300],
        },
        {
            "timestamp": "2026-04-18T15:00:00.040Z",
            "frame_idx": 1,
            "lat": 43.650001,
            "lon": -79.380001,
            "confidence": 0.91,
            "bbox": [110, 100, 210, 300],
        },
        {
            "timestamp": "2026-04-18T15:00:00.120Z",
            "frame_idx": 3,
            "lat": 43.650003,
            "lon": -79.380003,
            "confidence": 0.92,
            "bbox": [130, 100, 230, 300],
        },
    ]

    tracker.update(frame_idx=0, detections=[detections[0]])
    tracker.update(frame_idx=1, detections=[detections[1]])
    tracker.update(frame_idx=2, detections=[])
    tracker.update(frame_idx=3, detections=[detections[2]])

    tracks = tracker.confirmed_tracks(
        fps=25.0,
        frame_stride=1,
        scoring_config={
            "enabled": True,
            "high_confidence_threshold": 0.80,
            "possible_confidence_threshold": 0.55,
            "weights": {
                "mean_confidence": 0.55,
                "max_confidence": 0.25,
                "detection_density": 0.20,
            },
        },
    )

    assert len(tracks) == 1
    assert tracks[0]["hits"] == 3
    assert tracks[0].get("motion_model") == "kalman"
    assert tracks[0].get("max_consecutive_misses", 0) >= 1