import math
from datetime import datetime, timezone
from typing import Dict, Sequence, Tuple

from telemetry import offset_latlon



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
    frame_h, frame_w = int(frame_shape[0]), int(frame_shape[1])
    x1, y1, x2, y2 = [float(v) for v in bbox]

    center_x = (x1 + x2) / 2.0
    center_y = (y1 + y2) / 2.0

    normalized_x = (center_x - (frame_w / 2.0)) / (frame_w / 2.0)
    normalized_y = (center_y - (frame_h / 2.0)) / (frame_h / 2.0)

    half_ground_width_m = altitude_m * math.tan(math.radians(horizontal_fov_deg / 2.0))
    half_ground_height_m = altitude_m * math.tan(math.radians(vertical_fov_deg / 2.0))

    east_offset_m = normalized_x * half_ground_width_m
    north_offset_m = -normalized_y * half_ground_height_m

    return offset_latlon(drone_lat, drone_lon, east_offset_m, north_offset_m)



def create_alert(event_time: datetime, lat: float, lon: float, confidence: float) -> Dict[str, object]:
    return {
        "timestamp": event_time.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z"),
        "lat": round(float(lat), 7),
        "lon": round(float(lon), 7),
        "confidence": round(float(confidence), 4),
        "type": "possible_person",
    }
