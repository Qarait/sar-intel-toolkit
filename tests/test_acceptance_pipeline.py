import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from fusion import create_alert, estimate_target_position_with_mode
from geojson_export import tracks_to_feature_collection
from planner import generate_grid
from telemetry import TelemetryReplay
from tracker import SimpleTracker


ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "tests" / "fixtures"
SCHEMAS_DIR = ROOT / "schemas"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(schema_name: str) -> Draft202012Validator:
    schema = _load_json(SCHEMAS_DIR / schema_name)
    return Draft202012Validator(schema)


def test_acceptance_pipeline_attests_readme_claims_without_yolo() -> None:
    waypoints = generate_grid(
        min_lat=43.6490,
        min_lon=-79.3810,
        max_lat=43.6493,
        max_lon=-79.3807,
        altitude_m=60.0,
        lane_spacing_m=15.0,
        forward_step_m=15.0,
    )

    assert len(waypoints) > 0

    replay = TelemetryReplay(str(FIXTURES_DIR / "telemetry_acceptance.csv"))
    mid_state = replay.state_at(1.5)

    assert mid_state.lat is not None
    assert mid_state.lon is not None
    assert mid_state.altitude_m is not None
    assert mid_state.yaw_deg is not None

    bbox = [40.0, 0.0, 60.0, 20.0]
    frame_shape = (100, 100)
    yaw0_lat, yaw0_lon = estimate_target_position_with_mode(
        drone_lat=mid_state.lat,
        drone_lon=mid_state.lon,
        bbox=bbox,
        frame_shape=frame_shape,
        altitude_m=mid_state.altitude_m,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="heading_aware_nadir",
        yaw_deg=0.0,
        target_point="bbox_center",
    )
    yaw90_lat, yaw90_lon = estimate_target_position_with_mode(
        drone_lat=mid_state.lat,
        drone_lon=mid_state.lon,
        bbox=bbox,
        frame_shape=frame_shape,
        altitude_m=mid_state.altitude_m,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="heading_aware_nadir",
        yaw_deg=90.0,
        target_point="bbox_center",
    )

    assert yaw0_lat > mid_state.lat
    assert yaw90_lon > mid_state.lon
    assert abs(yaw0_lat - mid_state.lat) > abs(yaw90_lat - mid_state.lat)
    assert abs(yaw90_lon - mid_state.lon) > abs(yaw0_lon - mid_state.lon)

    tracker = SimpleTracker(
        iou_threshold=0.1,
        max_frame_gap=2,
        max_position_distance_m=25.0,
        min_hits=2,
        motion_model="kalman",
    )

    acceptance_frames = _load_json(FIXTURES_DIR / "detections_acceptance.json")
    alerts = []

    for frame in acceptance_frames:
        frame_idx = int(frame["frame_idx"])
        event_time = datetime.fromisoformat(frame["timestamp"].replace("Z", "+00:00")).astimezone(timezone.utc)
        replay_state = replay.state_at(float(frame_idx), event_time)
        geotagged_detections = []

        for detection in frame["detections"]:
            lat, lon = estimate_target_position_with_mode(
                drone_lat=replay_state.lat,
                drone_lon=replay_state.lon,
                bbox=detection["bbox"],
                frame_shape=frame_shape,
                altitude_m=replay_state.altitude_m,
                horizontal_fov_deg=90.0,
                vertical_fov_deg=90.0,
                mode="heading_aware_nadir",
                yaw_deg=replay_state.yaw_deg,
                target_point="bbox_center",
            )
            geotagged_detections.append(
                {
                    "bbox": detection["bbox"],
                    "confidence": detection["confidence"],
                    "lat": lat,
                    "lon": lon,
                    "timestamp": frame["timestamp"],
                }
            )
            alerts.append(create_alert(event_time, lat, lon, detection["confidence"]))

        tracker.update(geotagged_detections, frame_idx=frame_idx, event_time=event_time)

    tracks = tracker.confirmed_tracks(
        fps=1.0,
        frame_stride=1,
        scoring_config={
            "enabled": True,
            "weights": {
                "mean_confidence": 0.55,
                "max_confidence": 0.25,
                "detection_density": 0.20,
            },
            "high_confidence_threshold": 0.80,
            "possible_confidence_threshold": 0.55,
        },
    )

    assert len(tracks) == 1
    assert tracks[0]["motion_model"] == "kalman"
    assert tracks[0]["max_consecutive_misses"] == 1
    assert tracks[0]["first_frame"] == 0
    assert tracks[0]["last_frame"] == 3

    for required_field in [
        "track_id",
        "type",
        "lat",
        "lon",
        "hits",
        "mean_confidence",
        "max_confidence",
        "duration_seconds",
        "detection_density",
        "track_score",
        "track_class",
    ]:
        assert required_field in tracks[0]

    feature_collection = tracks_to_feature_collection(tracks)

    assert feature_collection["type"] == "FeatureCollection"
    coordinates = feature_collection["features"][0]["geometry"]["coordinates"]
    assert coordinates == [tracks[0]["lon"], tracks[0]["lat"]]
    assert feature_collection["features"][0]["properties"]["heatmap_weight"] is not None

    _validator("alerts.schema.json").validate(alerts)
    _validator("tracks.schema.json").validate(tracks)
    _validator("tracks_geojson.schema.json").validate(feature_collection)

    readme_alert_examples = [
        {
            "timestamp": "2026-04-18T15:00:01Z",
            "lat": 43.6489098,
            "lon": -79.3807224,
            "confidence": 0.9394,
            "type": "possible_person",
        }
    ]
    readme_track_examples = [
        {
            "track_id": 1,
            "type": "possible_person_track",
            "first_seen": "2026-04-18T15:00:00Z",
            "last_seen": "2026-04-18T15:00:03Z",
            "first_frame": 0,
            "last_frame": 80,
            "hits": 78,
            "lat": 43.6489106,
            "lon": -79.380667,
            "max_confidence": 0.956,
            "mean_confidence": 0.8951,
            "representative_bbox": [2669.81, 627.01, 3839.31, 2144.29],
            "duration_seconds": 3.2,
            "detection_density": 0.9625,
            "track_score": 0.9235,
            "track_class": "high_confidence_person",
        }
    ]
    readme_geojson_example = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-79.380667, 43.6489106],
                },
                "properties": {
                    "track_id": 1,
                    "type": "possible_person_track",
                    "track_class": "high_confidence_person",
                    "track_score": 0.9235,
                    "heatmap_weight": 0.9235,
                    "duration_seconds": 3.2,
                    "detection_density": 0.9625,
                    "hits": 78,
                    "mean_confidence": 0.8951,
                    "max_confidence": 0.956,
                    "first_seen": "2026-04-18T15:00:00Z",
                    "last_seen": "2026-04-18T15:00:03Z",
                    "first_frame": 0,
                    "last_frame": 80,
                    "representative_bbox": [2669.81, 627.01, 3839.31, 2144.29],
                },
            }
        ],
    }

    _validator("alerts.schema.json").validate(readme_alert_examples)
    _validator("tracks.schema.json").validate(readme_track_examples)
    _validator("tracks_geojson.schema.json").validate(readme_geojson_example)