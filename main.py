import argparse
import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import cv2
import yaml

from detector import Detection, PersonDetector
from fusion import create_alert, estimate_target_position_with_mode
from geojson_export import write_tracks_geojson
from mission_profiles import apply_mission_profile
from planner import generate_grid
from telemetry import TelemetryReplay, TelemetrySimulator
from tracker import SimpleTracker


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VideoMetadata:
    fps: float
    width: int
    height: int
    frame_count: int


@dataclass(frozen=True)
class RunSummary:
    frames_processed: int
    alerts_count: int
    confirmed_tracks_count: int
    geojson_features_count: int
    telemetry_mode: str
    geotagging_mode: str
    tracking_motion_model: str


def load_config(config_path: str) -> Dict[str, Any]:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Config file {config_path!r} was not found. Provide a valid --config path."
        ) from exc
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Config file {config_path!r} is not valid YAML: {exc}"
        ) from exc

    if not isinstance(loaded, dict):
        raise ValueError(
            f"Config file {config_path!r} must contain a top-level mapping/object."
        )

    return loaded


def parse_utc(ts: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"Invalid UTC timestamp {ts!r}. Expected an ISO 8601 value such as 2026-04-17T19:30:00Z."
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def ensure_parent_dir(file_path: str) -> None:
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)


def read_video_metadata(cap: cv2.VideoCapture) -> VideoMetadata:
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        logger.warning(
            "Could not read FPS from video metadata; defaulting to 30.0 FPS. "
            "Alert timestamps may be approximate."
        )
        fps = 30.0

    return VideoMetadata(
        fps=float(fps),
        width=int(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0.0)),
        height=int(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0.0)),
        frame_count=int(round(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)),
    )


def format_run_summary(summary: RunSummary) -> str:
    return "\n".join(
        [
            "Run summary",
            "-----------",
            f"Frames processed: {summary.frames_processed}",
            f"Alerts: {summary.alerts_count}",
            f"Confirmed tracks: {summary.confirmed_tracks_count}",
            f"GeoJSON features: {summary.geojson_features_count}",
            f"Telemetry mode: {summary.telemetry_mode}",
            f"Geotagging mode: {summary.geotagging_mode}",
            f"Tracking motion model: {summary.tracking_motion_model}",
        ]
    )


def resolve_run_manifest_path(alerts_path: str) -> str:
    return str(Path(alerts_path).resolve().parent / "run_manifest.json")


def write_run_manifest(run_manifest: Dict[str, Any], alerts_path: str) -> str:
    run_manifest_path = Path(resolve_run_manifest_path(alerts_path))
    run_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    run_manifest_path.write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    if not run_manifest_path.exists():
        raise RuntimeError(
            f"Failed to write run manifest to {str(run_manifest_path)!r}."
        )
    return str(run_manifest_path)


def format_utc(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_git_commit(repo_dir: Optional[Path] = None) -> str:
    target_dir = repo_dir or Path(__file__).resolve().parent
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=target_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

    commit = result.stdout.strip()
    return commit or "unknown"


def build_run_manifest(
    *,
    mission_start: datetime,
    config_path: str,
    video_path: str,
    video_fps: float,
    video_width: int,
    video_height: int,
    telemetry_mode: str,
    detector_model: str,
    tracking_motion_model: str,
    geotagging_mode: str,
    alerts_count: int,
    tracks_count: int,
    geojson_features_count: int,
    git_commit: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "run_id": format_utc(mission_start),
        "git_commit": git_commit or "unknown",
        "config_path": config_path,
        "video_path": video_path,
        "video_fps": round(float(video_fps), 3),
        "video_width": int(video_width),
        "video_height": int(video_height),
        "telemetry_mode": telemetry_mode,
        "detector_model": detector_model,
        "tracking_motion_model": tracking_motion_model,
        "geotagging_mode": geotagging_mode,
        "alerts_count": int(alerts_count),
        "tracks_count": int(tracks_count),
        "geojson_features_count": int(geojson_features_count),
    }


def build_telemetry(config: Dict[str, Any], waypoints: Any) -> Union[TelemetrySimulator, TelemetryReplay]:
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
            raise ValueError(
                "telemetry.mode='replay' requires telemetry.replay_path to point to a CSV telemetry log."
            )
        return TelemetryReplay(str(replay_path))

    raise ValueError(
        f"Unsupported telemetry.mode={mode!r}. Expected 'simulated' or 'replay'."
    )


def run(config_path: str = "config.yaml") -> RunSummary:
    raw_config = load_config(config_path)
    config = apply_mission_profile(raw_config)
    profile = config.get("resolved_mission_profile")
    if profile:
        print(f"Mission profile: {profile}")

    search_area = config["search_area"]
    mission = config["mission"]
    video_cfg = config["video"]
    detector_cfg = config["detector"]
    camera_cfg = config["camera"]
    output_cfg = config["output"]
    tracking_cfg = config.get("tracking", {})
    scoring_cfg = config.get("track_scoring", {})
    geojson_cfg = config.get("geojson", {})
    geotagging_cfg = config.get("geotagging", {})
    telemetry_cfg = config.get("telemetry", {})

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
            motion_model=str(tracking_cfg.get("motion_model", "none")),
            kalman_config=tracking_cfg.get("kalman", {}),
        )

    video_path = str(video_cfg["path"])
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(
            f"Failed to open video.path={video_path!r}. Check that the file exists and is readable by OpenCV."
        )

    video_metadata = read_video_metadata(cap)
    frame_stride = max(1, int(video_cfg.get("frame_stride", 1)))
    mission_start = parse_utc(str(video_cfg["start_time_utc"]))
    telemetry_mode = str(telemetry_cfg.get("mode", "simulated")).lower()
    tracking_motion_model = str(tracking_cfg.get("motion_model", "none")).lower()
    detector_model = str(detector_cfg["model"])

    alerts: List[Dict[str, Any]] = []
    tracks: List[Dict[str, Any]] = []
    geojson_features_count = 0
    frame_idx = 0
    frames_processed = 0
    geotag_mode = str(geotagging_cfg.get("mode", "nadir"))
    geotag_target_point = str(geotagging_cfg.get("target_point", "bbox_center"))
    include_geotag_metadata = bool(geotagging_cfg.get("include_geotag_metadata", False))

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % frame_stride != 0:
            frame_idx += 1
            continue

        frames_processed += 1

        # frame_idx is the absolute source-video frame index, so frame_idx / fps remains correct even when frame_stride skips processing some frames.
        t_seconds = frame_idx / video_metadata.fps
        event_time = mission_start + timedelta(seconds=t_seconds)
        drone_state = telemetry.state_at(t_seconds, event_time)
        drone_lat = drone_state.lat
        drone_lon = drone_state.lon
        altitude_m = drone_state.altitude_m
        yaw_deg = drone_state.yaw_deg

        raw_detections: List[Detection] = detector.detect(frame)
        detections: List[Dict[str, Any]] = []

        for detection in raw_detections:
            target_lat, target_lon = estimate_target_position_with_mode(
                drone_lat=drone_lat,
                drone_lon=drone_lon,
                bbox=detection.bbox,
                frame_shape=frame.shape,
                altitude_m=altitude_m,
                horizontal_fov_deg=float(camera_cfg["horizontal_fov_deg"]),
                vertical_fov_deg=float(camera_cfg["vertical_fov_deg"]),
                mode=geotag_mode,
                yaw_deg=yaw_deg,
                target_point=geotag_target_point,
            )
            enriched_detection = {
                "confidence": detection.confidence,
                "bbox": list(detection.bbox),
                "lat": target_lat,
                "lon": target_lon,
            }
            if include_geotag_metadata:
                enriched_detection["geotag_mode"] = geotag_mode
                enriched_detection["geotag_yaw_deg"] = yaw_deg
                enriched_detection["geotag_target_point"] = geotag_target_point
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
            logger.info("Alert generated: %s", json.dumps(alert))

        frame_idx += 1

    cap.release()

    alerts_path = output_cfg["alerts_path"]
    ensure_parent_dir(alerts_path)
    with open(alerts_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

    if tracker is not None:
        tracks = tracker.confirmed_tracks(
            fps=video_metadata.fps,
            frame_stride=frame_stride,
            scoring_config=scoring_cfg if scoring_cfg else None,
        )
        tracks_path = output_cfg.get("tracks_path", "output/tracks.json")
        ensure_parent_dir(tracks_path)
        with open(tracks_path, "w", encoding="utf-8") as f:
            json.dump(tracks, f, indent=2)
        logger.info("Saved %d confirmed tracks to %s", len(tracks), tracks_path)

        if bool(geojson_cfg.get("enabled", False)):
            geojson_path = str(geojson_cfg.get("tracks_path", "output/tracks.geojson"))
            geojson_fc = write_tracks_geojson(tracks, geojson_path, config=geojson_cfg)
            geojson_features_count = len(geojson_fc["features"])
            logger.info(
                "Saved %d GeoJSON track features to %s",
                len(geojson_fc["features"]),
                geojson_path,
            )

    run_manifest = build_run_manifest(
        mission_start=mission_start,
        config_path=config_path,
        video_path=video_path,
        video_fps=video_metadata.fps,
        video_width=video_metadata.width,
        video_height=video_metadata.height,
        telemetry_mode=telemetry_mode,
        detector_model=detector_model,
        tracking_motion_model=tracking_motion_model,
        geotagging_mode=geotag_mode,
        alerts_count=len(alerts),
        tracks_count=len(tracks),
        geojson_features_count=geojson_features_count,
        git_commit=resolve_git_commit(),
    )
    run_manifest_path = write_run_manifest(run_manifest, alerts_path)
    logger.info("Saved run manifest to %s", run_manifest_path)

    logger.info("Saved %d waypoints to %s", len(waypoints), waypoints_path)
    logger.info("Saved %d alerts to %s", len(alerts), alerts_path)

    return RunSummary(
        frames_processed=frames_processed,
        alerts_count=len(alerts),
        confirmed_tracks_count=len(tracks),
        geojson_features_count=geojson_features_count,
        telemetry_mode=telemetry_mode,
        geotagging_mode=geotag_mode,
        tracking_motion_model=tracking_motion_model,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SAR-INTEL TOOLKIT")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config file")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a short run summary after processing completes",
    )
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    summary = run(args.config)
    if args.summary:
        print(format_run_summary(summary))
