import math
from datetime import datetime, timezone
from typing import Dict, Sequence, Tuple

from telemetry import offset_latlon


def _select_bbox_point(bbox: Sequence[float], target_point: str) -> Tuple[float, float]:
    x1, y1, x2, y2 = [float(v) for v in bbox]
    center_x = (x1 + x2) / 2.0

    if target_point == "bbox_center":
        return center_x, (y1 + y2) / 2.0
    if target_point == "bbox_bottom_center":
        return center_x, y2

    raise ValueError(
        f"Unsupported geotagging.target_point={target_point!r}. Expected 'bbox_center' or 'bbox_bottom_center'."
    )


def _image_offset_to_ground_m(
    point_x: float,
    point_y: float,
    frame_shape: Sequence[int],
    altitude_m: float,
    horizontal_fov_deg: float,
    vertical_fov_deg: float,
) -> Tuple[float, float]:
    frame_h, frame_w = int(frame_shape[0]), int(frame_shape[1])

    normalized_x = (point_x - (frame_w / 2.0)) / (frame_w / 2.0)
    normalized_y = (point_y - (frame_h / 2.0)) / (frame_h / 2.0)

    half_ground_width_m = altitude_m * math.tan(math.radians(horizontal_fov_deg / 2.0))
    half_ground_height_m = altitude_m * math.tan(math.radians(vertical_fov_deg / 2.0))

    right_m = normalized_x * half_ground_width_m
    forward_m = -normalized_y * half_ground_height_m
    return right_m, forward_m


def _rotate_body_to_world(right_m: float, forward_m: float, yaw_deg: float) -> Tuple[float, float]:
    yaw_rad = math.radians(yaw_deg)
    east_m = (forward_m * math.sin(yaw_rad)) + (right_m * math.cos(yaw_rad))
    north_m = (forward_m * math.cos(yaw_rad)) - (right_m * math.sin(yaw_rad))
    return east_m, north_m


def estimate_target_position_with_mode(
    drone_lat: float,
    drone_lon: float,
    bbox: Sequence[float],
    frame_shape: Sequence[int],
    altitude_m: float,
    horizontal_fov_deg: float,
    vertical_fov_deg: float,
    mode: str = "nadir",
    yaw_deg: float = 0.0,
    target_point: str = "bbox_center",
) -> Tuple[float, float]:
    point_x, point_y = _select_bbox_point(bbox, target_point)
    right_m, forward_m = _image_offset_to_ground_m(
        point_x=point_x,
        point_y=point_y,
        frame_shape=frame_shape,
        altitude_m=altitude_m,
        horizontal_fov_deg=horizontal_fov_deg,
        vertical_fov_deg=vertical_fov_deg,
    )

    if mode == "nadir":
        east_offset_m = right_m
        north_offset_m = forward_m
    elif mode == "heading_aware_nadir":
        east_offset_m, north_offset_m = _rotate_body_to_world(right_m, forward_m, yaw_deg)
    else:
        raise ValueError(
            f"Unsupported geotagging.mode={mode!r}. Expected 'nadir' or 'heading_aware_nadir'."
        )

    return offset_latlon(drone_lat, drone_lon, east_offset_m, north_offset_m)



def estimate_target_position(
    drone_lat: float,
    drone_lon: float,
    bbox: Sequence[float],
    frame_shape: Sequence[int],
    altitude_m: float,
    horizontal_fov_deg: float,
    vertical_fov_deg: float,
) -> Tuple[float, float]:
    """Estimate target GPS from image-space offset using a nadir-camera assumption.

    Assumptions are deliberately simple for the MVP:
      - flat ground
      - stabilized camera looking straight down
      - no terrain model or lens distortion correction
    """
    return estimate_target_position_with_mode(
        drone_lat=drone_lat,
        drone_lon=drone_lon,
        bbox=bbox,
        frame_shape=frame_shape,
        altitude_m=altitude_m,
        horizontal_fov_deg=horizontal_fov_deg,
        vertical_fov_deg=vertical_fov_deg,
        mode="nadir",
        yaw_deg=0.0,
        target_point="bbox_center",
    )



def create_alert(event_time: datetime, lat: float, lon: float, confidence: float) -> Dict[str, object]:
    return {
        "timestamp": event_time.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z"),
        "lat": round(float(lat), 7),
        "lon": round(float(lon), 7),
        "confidence": round(float(confidence), 4),
        "type": "possible_person",
    }
