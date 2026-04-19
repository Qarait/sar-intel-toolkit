from datetime import datetime, timezone

from tracker import SimpleTracker


def test_confirmed_tracks_include_scoring_fields() -> None:
    tracker = SimpleTracker(
        iou_threshold=0.1,
        max_frame_gap=2,
        max_position_distance_m=20.0,
        min_hits=2,
    )
    event_time = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)

    detections_frame_0 = [{
        "bbox": [10.0, 10.0, 30.0, 30.0],
        "lat": 43.6490,
        "lon": -79.3810,
        "confidence": 0.8,
        "timestamp": "2026-04-19T12:00:00Z",
    }]
    detections_frame_1 = [{
        "bbox": [11.0, 10.0, 31.0, 30.0],
        "lat": 43.6491,
        "lon": -79.3811,
        "confidence": 0.6,
        "timestamp": "2026-04-19T12:00:01Z",
    }]

    tracker.update(detections_frame_0, frame_idx=0, event_time=event_time)
    tracker.update(detections_frame_1, frame_idx=1, event_time=event_time)

    summaries = tracker.confirmed_tracks(
        fps=1.0,
        frame_stride=1,
        scoring_config={
            "enabled": True,
            "weights": {
                "mean_confidence": 0.5,
                "max_confidence": 0.25,
                "detection_density": 0.25,
            },
            "high_confidence_threshold": 0.8,
            "possible_confidence_threshold": 0.55,
        },
    )

    assert len(summaries) == 1

    summary = summaries[0]
    assert summary["duration_seconds"] == 1.0
    assert summary["detection_density"] == 1.0
    assert summary["track_score"] == 0.8
    assert summary["track_class"] == "high_confidence_person"
    assert summary["representative_bbox"] == [10.0, 10.0, 30.0, 30.0]


def test_kalman_tracker_emits_motion_metadata() -> None:
    tracker = SimpleTracker(
        iou_threshold=0.1,
        max_frame_gap=2,
        max_position_distance_m=20.0,
        min_hits=2,
        motion_model="kalman",
    )
    event_time = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)

    tracker.update([
        {
            "bbox": [10.0, 10.0, 30.0, 30.0],
            "lat": 43.6490,
            "lon": -79.3810,
            "confidence": 0.8,
            "timestamp": "2026-04-19T12:00:00Z",
        }
    ], frame_idx=0, event_time=event_time)
    tracker.update([
        {
            "bbox": [11.0, 10.0, 31.0, 30.0],
            "lat": 43.6491,
            "lon": -79.3811,
            "confidence": 0.7,
            "timestamp": "2026-04-19T12:00:01Z",
        }
    ], frame_idx=1, event_time=event_time)
    tracker.update([], frame_idx=2, event_time=event_time)

    summaries = tracker.confirmed_tracks(fps=1.0, frame_stride=1, scoring_config={"enabled": False})

    assert len(summaries) == 1
    assert summaries[0]["motion_model"] == "kalman"
    assert summaries[0]["missed_frames"] == 1
    assert summaries[0]["max_consecutive_misses"] == 1