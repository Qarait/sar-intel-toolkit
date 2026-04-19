import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import cv2
import yaml

from detector import PersonDetector
from fusion import create_alert, estimate_target_position
from planner import generate_grid
from telemetry import TelemetryReplay, TelemetrySimulator
from tracker import SimpleTracker


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def ensure_parent_dir(file_path: str) -> None:
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)


def build_telemetry(config: Dict[str, Any], waypoints: Any) -> Any:
    mission = config["mission"]
    telemetry_cfg = config.get("telemetry", {}) or {}
    mode = str(telemetry_cfg.get("mode", "simulated")).lower()

    if mode == "simulated":
        return TelemetrySimulator(
            waypoints=waypoints,
            speed_mps=float(mission["drone_speed_mps"]),
        )

    if mode == "replay":
        replay_path = telemetry_cfg.get("replay_path")
        if not replay_path:
            raise ValueError("telemetry.mode is 'replay' but telemetry.replay_path is missing.")
        return TelemetryReplay(str(replay_path))

    raise ValueError(f"Unsupported telemetry.mode: {mode!r}. Use 'simulated' or 'replay'.")


def run(config_path: str = "config.yaml") -> None:
    config = load_config(config_path)

    search_area = config["search_area"]
    mission = config["mission"]
    video_cfg = config["video"]
    detector_cfg = config["detector"]
    camera_cfg = config["camera"]
    output_cfg = config["output"]
    tracking_cfg = config.get("tracking", {})
    scoring_cfg = config.get("track_scoring", {})

    waypoints = generate_grid(
        min_lat=float(search_area["min_lat"]),
        min_lon=float(search_area["min_lon"]),
        max_lat=float(search_area["max_lat"]),
        max_lon=float(search_area["max_lon"]),
        altitude_m=float(mission["altitude_m"]),
        lane_spacing_m=float(mission["lane_spacing_m"]),
        forward_step_m=float(mission["forward_step_m"]),
    )

    waypoints_path = output_cfg["waypoints_path"]
    ensure_parent_dir(waypoints_path)
    with open(waypoints_path, "w", encoding="utf-8") as f:
        json.dump(waypoints, f, indent=2)

    telemetry = build_telemetry(config, waypoints)

    detector = PersonDetector(
        model_path=str(detector_cfg["model"]),
        confidence_threshold=float(detector_cfg["confidence_threshold"]),
    )

    tracker = None
    include_track_id_in_alerts = bool(tracking_cfg.get("include_track_id_in_alerts", False))
    if bool(tracking_cfg.get("enabled", False)):
        tracker = SimpleTracker(
            iou_threshold=float(tracking_cfg.get("iou_threshold", 0.25)),
            max_frame_gap=int(tracking_cfg.get("max_frame_gap", 10)),
            max_position_distance_m=float(tracking_cfg.get("max_position_distance_m", 12.0)),
            min_hits=int(tracking_cfg.get("min_hits", 3)),
        )

    video_path = video_cfg["path"]
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        print("WARNING: Could not read FPS from video metadata; defaulting to 30.0 FPS. Alert timestamps may be approximate.")
        fps = 30.0

    frame_stride = max(1, int(video_cfg.get("frame_stride", 1)))
    mission_start = parse_utc(str(video_cfg["start_time_utc"]))

    alerts = []
    frame_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % frame_stride != 0:
            frame_idx += 1
            continue

        # frame_idx is the absolute source-video frame index, so frame_idx / fps remains correct even when frame_stride skips processing some frames.
        t_seconds = frame_idx / fps
        event_time = mission_start + timedelta(seconds=t_seconds)
        drone_state = telemetry.state_at(t_seconds, event_time)
        drone_lat = float(drone_state["lat"])
        drone_lon = float(drone_state["lon"])
        altitude_m = float(drone_state.get("altitude_m", mission["altitude_m"]))

        raw_detections = detector.detect(frame)
        detections = []

        for detection in raw_detections:
            target_lat, target_lon = estimate_target_position(
                drone_lat=drone_lat,
                drone_lon=drone_lon,
                bbox=detection["bbox"],
                frame_shape=frame.shape,
                altitude_m=altitude_m,
                horizontal_fov_deg=float(camera_cfg["horizontal_fov_deg"]),
                vertical_fov_deg=float(camera_cfg["vertical_fov_deg"]),
            )
            enriched_detection = dict(detection)
            enriched_detection["lat"] = target_lat
            enriched_detection["lon"] = target_lon
            detections.append(enriched_detection)

        if tracker is not None:
            detections = tracker.update(detections, frame_idx, event_time)

        for detection in detections:
            alert = create_alert(
                event_time=event_time,
                lat=detection["lat"],
                lon=detection["lon"],
                confidence=detection["confidence"],
            )
            if tracker is not None and include_track_id_in_alerts:
                alert["track_id"] = int(detection["track_id"])
            alerts.append(alert)
            print("ALERT:", json.dumps(alert))

        frame_idx += 1

    cap.release()

    alerts_path = output_cfg["alerts_path"]
    ensure_parent_dir(alerts_path)
    with open(alerts_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

    if tracker is not None:
        tracks = tracker.confirmed_tracks(
            fps=fps,
            frame_stride=frame_stride,
            scoring_config=scoring_cfg if scoring_cfg else None,
        )
        tracks_path = output_cfg.get("tracks_path", "output/tracks.json")
        ensure_parent_dir(tracks_path)
        with open(tracks_path, "w", encoding="utf-8") as f:
            json.dump(tracks, f, indent=2)
        print(f"Saved {len(tracks)} confirmed tracks -> {tracks_path}")

    print(f"Saved {len(waypoints)} waypoints -> {waypoints_path}")
    print(f"Saved {len(alerts)} alerts -> {alerts_path}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SAR-INTEL TOOLKIT")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config file")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    run(args.config)
