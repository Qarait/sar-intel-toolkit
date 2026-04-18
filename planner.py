import math
from typing import Dict, List


METERS_PER_DEGREE_LAT = 111_320.0


def meters_to_lat(meters: float) -> float:
    return meters / METERS_PER_DEGREE_LAT



def meters_to_lon(meters: float, at_lat: float) -> float:
    cos_lat = math.cos(math.radians(at_lat))
    if abs(cos_lat) < 1e-9:
        raise ValueError("Longitude conversion is unstable near the poles.")
    return meters / (METERS_PER_DEGREE_LAT * cos_lat)



def _build_row(lat: float, min_lon: float, max_lon: float, altitude_m: float, forward_step_m: float, reverse: bool) -> List[Dict[str, float]]:
    lon_step = meters_to_lon(forward_step_m, lat)
    row_points: List[Dict[str, float]] = []
    lon = min_lon

    while lon <= max_lon + 1e-12:
        row_points.append({
            "lat": lat,
            "lon": lon,
            "alt": altitude_m,
        })
        lon += lon_step

    if not row_points or row_points[-1]["lon"] < max_lon:
        row_points.append({
            "lat": lat,
            "lon": max_lon,
            "alt": altitude_m,
        })

    if reverse:
        row_points.reverse()

    return row_points



def generate_grid(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    altitude_m: float,
    lane_spacing_m: float,
    forward_step_m: float,
) -> List[Dict[str, float]]:
    """Generate a simple lawnmower grid over a small search area."""
    if min_lat >= max_lat or min_lon >= max_lon:
        raise ValueError("Invalid bounding box: min values must be smaller than max values.")
    if altitude_m <= 0:
        raise ValueError("Altitude must be positive.")
    if lane_spacing_m <= 0 or forward_step_m <= 0:
        raise ValueError("Spacing values must be positive.")

    waypoints: List[Dict[str, float]] = []
    row_lat = min_lat
    row_index = 0
    last_row_lat = None

    while row_lat <= max_lat + 1e-12:
        waypoints.extend(
            _build_row(
                lat=row_lat,
                min_lon=min_lon,
                max_lon=max_lon,
                altitude_m=altitude_m,
                forward_step_m=forward_step_m,
                reverse=(row_index % 2 == 1),
            )
        )
        last_row_lat = row_lat
        row_lat += meters_to_lat(lane_spacing_m)
        row_index += 1

    if last_row_lat is not None and last_row_lat < max_lat - 1e-12:
        waypoints.extend(
            _build_row(
                lat=max_lat,
                min_lon=min_lon,
                max_lon=max_lon,
                altitude_m=altitude_m,
                forward_step_m=forward_step_m,
                reverse=(row_index % 2 == 1),
            )
        )

    return waypoints
