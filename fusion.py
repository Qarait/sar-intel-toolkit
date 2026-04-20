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
    if not 0.0 < float(horizontal_fov_deg) < 180.0:
        raise ValueError(
            f"horizontal_fov_deg must be between 0 and 180 degrees, got {horizontal_fov_deg!r}."
        )
    if not 0.0 < float(vertical_fov_deg) < 180.0:
        raise ValueError(
            f"vertical_fov_deg must be between 0 and 180 degrees, got {vertical_fov_deg!r}."
        )

    frame_h, frame_w = int(frame_shape[0]), int(frame_shape[1])

    normalized_x = (point_x - (frame_w / 2.0)) / (frame_w / 2.0)
    normalized_y = (point_y - (frame_h / 2.0)) / (frame_h / 2.0)

    half_ground_width_m = altitude_m * math.tan(math.radians(horizontal_fov_deg / 2.0))
    half_ground_height_m = altitude_m * math.tan(math.radians(vertical_fov_deg / 2.0))

    right_m = normalized_x * half_ground_width_m
    forward_m = -normalized_y * half_ground_height_m
    return right_m, forward_m


def _pixel_to_camera_ray(
    point_x: float,
    point_y: float,
    frame_shape: Sequence[int],
    horizontal_fov_deg: float,
    vertical_fov_deg: float,
) -> Tuple[float, float, float]:
    if not 0.0 < float(horizontal_fov_deg) < 180.0:
        raise ValueError(
            f"horizontal_fov_deg must be between 0 and 180 degrees, got {horizontal_fov_deg!r}."
        )
    if not 0.0 < float(vertical_fov_deg) < 180.0:
        raise ValueError(
            f"vertical_fov_deg must be between 0 and 180 degrees, got {vertical_fov_deg!r}."
        )

    frame_h, frame_w = int(frame_shape[0]), int(frame_shape[1])
    normalized_x = (point_x - (frame_w / 2.0)) / (frame_w / 2.0)
    normalized_y = (point_y - (frame_h / 2.0)) / (frame_h / 2.0)

    right = normalized_x * math.tan(math.radians(horizontal_fov_deg / 2.0))
    forward = -normalized_y * math.tan(math.radians(vertical_fov_deg / 2.0))
    down = 1.0

    norm = math.sqrt((right * right) + (forward * forward) + (down * down))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("Could not build a valid camera ray from the image point and field of view.")

    return right / norm, forward / norm, down / norm


def _rotate_body_to_world(right_m: float, forward_m: float, yaw_deg: float) -> Tuple[float, float]:
    yaw_rad = math.radians(yaw_deg)
    east_m = (forward_m * math.sin(yaw_rad)) + (right_m * math.cos(yaw_rad))
    north_m = (forward_m * math.cos(yaw_rad)) - (right_m * math.sin(yaw_rad))
    return east_m, north_m


def _rotation_matrix_yaw_pitch_roll(
    yaw_deg: float,
    pitch_deg: float,
    roll_deg: float,
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]:
    yaw_rad = math.radians(yaw_deg)
    pitch_rad = math.radians(pitch_deg)
    roll_rad = math.radians(-roll_deg)

    c_yaw = math.cos(yaw_rad)
    s_yaw = math.sin(yaw_rad)
    c_pitch = math.cos(pitch_rad)
    s_pitch = math.sin(pitch_rad)
    c_roll = math.cos(roll_rad)
    s_roll = math.sin(roll_rad)

    base = (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, -1.0),
    )
    rotate_pitch = (
        (1.0, 0.0, 0.0),
        (0.0, c_pitch, -s_pitch),
        (0.0, s_pitch, c_pitch),
    )
    rotate_roll = (
        (c_roll, 0.0, s_roll),
        (0.0, 1.0, 0.0),
        (-s_roll, 0.0, c_roll),
    )
    rotate_yaw = (
        (c_yaw, s_yaw, 0.0),
        (-s_yaw, c_yaw, 0.0),
        (0.0, 0.0, 1.0),
    )

    def matmul(
        left: Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]],
        right: Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]],
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]:
        return tuple(
            tuple(sum(left[row][idx] * right[idx][col] for idx in range(3)) for col in range(3))
            for row in range(3)
        )

    return matmul(rotate_yaw, matmul(rotate_roll, matmul(rotate_pitch, base)))


def _intersect_ray_with_ground(
    altitude_m: float,
    ray_world: Tuple[float, float, float],
) -> Tuple[float, float]:
    if not math.isfinite(float(altitude_m)) or float(altitude_m) <= 0.0:
        raise ValueError(
            f"pose_aware_flat_ground requires altitude_m > 0, got {altitude_m!r}."
        )

    east_dir, north_dir, up_dir = ray_world
    if up_dir >= -1e-9:
        raise ValueError(
            "pose_aware_flat_ground ray does not intersect the flat ground plane below the drone. "
            "Check the attitude convention or use a nadir-based mode."
        )

    scale = float(altitude_m) / (-up_dir)
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError(
            "pose_aware_flat_ground produced an invalid ground intersection scale."
        )

    return east_dir * scale, north_dir * scale


def estimate_target_position_pose_aware(
    drone_lat: float,
    drone_lon: float,
    bbox: Sequence[float],
    frame_shape: Sequence[int],
    altitude_m: float,
    horizontal_fov_deg: float,
    vertical_fov_deg: float,
    yaw_deg: float,
    pitch_deg: float,
    roll_deg: float,
    target_point: str,
) -> Tuple[float, float]:
    point_x, point_y = _select_bbox_point(bbox, target_point)
    ray_camera = _pixel_to_camera_ray(
        point_x=point_x,
        point_y=point_y,
        frame_shape=frame_shape,
        horizontal_fov_deg=horizontal_fov_deg,
        vertical_fov_deg=vertical_fov_deg,
    )
    rotation = _rotation_matrix_yaw_pitch_roll(
        yaw_deg=yaw_deg,
        pitch_deg=pitch_deg,
        roll_deg=roll_deg,
    )
    ray_world = tuple(
        sum(rotation[row][col] * ray_camera[col] for col in range(3))
        for row in range(3)
    )
    east_offset_m, north_offset_m = _intersect_ray_with_ground(
        altitude_m=altitude_m,
        ray_world=(float(ray_world[0]), float(ray_world[1]), float(ray_world[2])),
    )
    return offset_latlon(drone_lat, drone_lon, east_offset_m, north_offset_m)


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
    pitch_deg: float = 0.0,
    roll_deg: float = 0.0,
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
    elif mode == "pose_aware_flat_ground":
        return estimate_target_position_pose_aware(
            drone_lat=drone_lat,
            drone_lon=drone_lon,
            bbox=bbox,
            frame_shape=frame_shape,
            altitude_m=altitude_m,
            horizontal_fov_deg=horizontal_fov_deg,
            vertical_fov_deg=vertical_fov_deg,
            yaw_deg=yaw_deg,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
            target_point=target_point,
        )
    else:
        raise ValueError(
            "Unsupported geotagging.mode="
            f"{mode!r}. Expected 'nadir', 'heading_aware_nadir', or 'pose_aware_flat_ground'."
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
