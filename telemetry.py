import math
from typing import Dict, List, Sequence, Tuple


METERS_PER_DEGREE_LAT = 111_320.0



def _meters_per_degree_lon(at_lat: float) -> float:
    return METERS_PER_DEGREE_LAT * math.cos(math.radians(at_lat))



def _latlon_to_local_m(lat: float, lon: float, origin_lat: float, origin_lon: float) -> Tuple[float, float]:
    north_m = (lat - origin_lat) * METERS_PER_DEGREE_LAT
    east_m = (lon - origin_lon) * _meters_per_degree_lon(origin_lat)
    return east_m, north_m



def _local_m_to_latlon(east_m: float, north_m: float, origin_lat: float, origin_lon: float) -> Tuple[float, float]:
    lat = origin_lat + (north_m / METERS_PER_DEGREE_LAT)
    meters_per_lon = _meters_per_degree_lon(origin_lat)
    if abs(meters_per_lon) < 1e-9:
        raise ValueError("Longitude conversion is unstable near the poles.")
    lon = origin_lon + (east_m / meters_per_lon)
    return lat, lon



def offset_latlon(lat: float, lon: float, east_m: float, north_m: float) -> Tuple[float, float]:
    """Apply a local meter offset to a latitude/longitude pair."""
    return _local_m_to_latlon(east_m, north_m, lat, lon)


class TelemetrySimulator:
    """Interpolate drone position along a waypoint path at fixed speed."""

    def __init__(self, waypoints: Sequence[Dict[str, float]], speed_mps: float) -> None:
        if len(waypoints) < 2:
            raise ValueError("TelemetrySimulator requires at least two waypoints.")
        if speed_mps <= 0:
            raise ValueError("Drone speed must be positive.")

        self.waypoints = list(waypoints)
        self.speed_mps = float(speed_mps)
        self.origin_lat = float(self.waypoints[0]["lat"])
        self.origin_lon = float(self.waypoints[0]["lon"])

        self.xy_points: List[Tuple[float, float]] = [
            _latlon_to_local_m(
                lat=float(point["lat"]),
                lon=float(point["lon"]),
                origin_lat=self.origin_lat,
                origin_lon=self.origin_lon,
            )
            for point in self.waypoints
        ]

        self.segment_lengths: List[float] = []
        self.cumulative_lengths: List[float] = [0.0]

        total = 0.0
        for i in range(len(self.xy_points) - 1):
            x1, y1 = self.xy_points[i]
            x2, y2 = self.xy_points[i + 1]
            dist = math.hypot(x2 - x1, y2 - y1)
            self.segment_lengths.append(dist)
            total += dist
            self.cumulative_lengths.append(total)

        self.total_distance_m = total

    def position_at(self, timestamp_seconds: float) -> Tuple[float, float]:
        if timestamp_seconds <= 0:
            return float(self.waypoints[0]["lat"]), float(self.waypoints[0]["lon"])

        travel_distance = min(timestamp_seconds * self.speed_mps, self.total_distance_m)

        for i, seg_len in enumerate(self.segment_lengths):
            start_dist = self.cumulative_lengths[i]
            end_dist = self.cumulative_lengths[i + 1]
            if travel_distance <= end_dist or i == len(self.segment_lengths) - 1:
                if seg_len == 0:
                    x, y = self.xy_points[i + 1]
                else:
                    ratio = (travel_distance - start_dist) / seg_len
                    x1, y1 = self.xy_points[i]
                    x2, y2 = self.xy_points[i + 1]
                    x = x1 + ratio * (x2 - x1)
                    y = y1 + ratio * (y2 - y1)
                return _local_m_to_latlon(x, y, self.origin_lat, self.origin_lon)

        return float(self.waypoints[-1]["lat"]), float(self.waypoints[-1]["lon"])
