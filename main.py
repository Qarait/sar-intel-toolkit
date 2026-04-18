import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import cv2
import yaml

from detector import PersonDetector
from fusion import create_alert, estimate_target_position
from planner import generate_grid
from telemetry import TelemetrySimulator



def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)



def parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)



def ensure_parent_dir(file_path: str) -> None:
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)



def run(config_path: str = "config.yaml") -> None:
    config = load_config(config_path)

    search_area = config["search_area"]
    mission = config["mission"]
    video_cfg = config["video"]
    detector_cfg = config["detector"]
    camera_cfg = config["camera"]
    output_cfg = config["output"]

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

    telemetry = TelemetrySimulator(
        waypoints=waypoints,
        speed_mps=float(mission["drone_speed_mps"]),
    )

    detector = PersonDetector(
        model_path=str(detector_cfg["model"]),
        confidence_threshold=float(detector_cfg["confidence_threshold"]),
    )

    video_path = video_cfg["path"]
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
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

        t_seconds = frame_idx / fps
        event_time = mission_start + timedelta(seconds=t_seconds)
        drone_lat, drone_lon = telemetry.position_at(t_seconds)

        detections = detector.detect(frame)
        for detection in detections:
            target_lat, target_lon = estimate_target_position(
                drone_lat=drone_lat,
                drone_lon=drone_lon,
                bbox=detection["bbox"],
                frame_shape=frame.shape,
                altitude_m=float(mission["altitude_m"]),
                horizontal_fov_deg=float(camera_cfg["horizontal_fov_deg"]),
                vertical_fov_deg=float(camera_cfg["vertical_fov_deg"]),
            )
            alert = create_alert(
                event_time=event_time,
                lat=target_lat,
                lon=target_lon,
                confidence=detection["confidence"],
            )
            alerts.append(alert)
            print("ALERT:", json.dumps(alert))

        frame_idx += 1

    cap.release()

    alerts_path = output_cfg["alerts_path"]
    ensure_parent_dir(alerts_path)
    with open(alerts_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

    print(f"Saved {len(waypoints)} waypoints -> {waypoints_path}")
    print(f"Saved {len(alerts)} alerts -> {alerts_path}")



def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SAR-INTEL TOOLKIT MVP")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config file")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    run(args.config)
