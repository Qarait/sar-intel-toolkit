import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple


METERS_PER_DEGREE_LAT = 111_320.0
REPLAY_FIELDS = ("lat", "lon", "altitude_m", "yaw_deg", "pitch_deg", "roll_deg")


@dataclass(frozen=True)
class TelemetryState:
    lat: float
    lon: float
    altitude_m: float
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0



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
        raise ValueError(
            f"Cannot project offsets from origin_lat={origin_lat!r}; longitude conversion is unstable near the poles."
        )
    lon = origin_lon + (east_m / meters_per_lon)
    return lat, lon



def offset_latlon(lat: float, lon: float, east_m: float, north_m: float) -> Tuple[float, float]:
    """Apply a local meter offset to a latitude/longitude pair."""
    return _local_m_to_latlon(east_m, north_m, lat, lon)


def parse_utc_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp and normalize it to UTC."""
    ts = value.strip()
    if not ts:
        raise ValueError("Telemetry timestamp is empty; expected an ISO 8601 UTC value such as 2026-04-17T19:30:00Z.")

    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class TelemetrySimulator:
    """Interpolate drone position along a waypoint path at fixed speed."""

    def __init__(self, waypoints: Sequence[Dict[str, float]], speed_mps: float) -> None:
        if len(waypoints) < 2:
            raise ValueError(
                f"TelemetrySimulator requires at least two waypoints, got {len(waypoints)}."
            )
        if speed_mps <= 0:
            raise ValueError(f"mission.drone_speed_mps must be > 0, got {speed_mps!r}.")

        self.waypoints = list(waypoints)
        self.speed_mps = float(speed_mps)
        self.origin_lat = float(self.waypoints[0]["lat"])
        self.origin_lon = float(self.waypoints[0]["lon"])
        self.default_altitude_m = float(self.waypoints[0].get("alt", 0.0))

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

    def state_at(self, timestamp_seconds: float, event_time: Optional[datetime] = None) -> TelemetryState:
        """Return a telemetry state dictionary compatible with replay mode."""
        lat, lon = self.position_at(timestamp_seconds)
        return TelemetryState(
            lat=float(lat),
            lon=float(lon),
            altitude_m=float(self.default_altitude_m),
        )


class TelemetryReplay:
    """Replay timestamped drone telemetry from CSV and interpolate states by time."""

    required_columns = ("timestamp", "lat", "lon", "altitude_m", "yaw_deg", "pitch_deg", "roll_deg")

    def __init__(self, csv_path: str) -> None:
        self.csv_path = Path(csv_path)
        self.rows = self._load_csv(self.csv_path)
        if not self.rows:
            raise ValueError(
                f"Telemetry replay file {csv_path!r} contains no data rows after the header."
            )
        self.rows.sort(key=lambda row: row["timestamp"])
        self.start_time = self.rows[0]["timestamp"]
        self.end_time = self.rows[-1]["timestamp"]

    def _load_csv(self, csv_path: Path) -> List[Dict[str, object]]:
        if not csv_path.exists():
            raise FileNotFoundError(
                f"telemetry.replay_path={str(csv_path)!r} does not exist or is not accessible."
            )

        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError(
                    f"Telemetry replay file {str(csv_path)!r} is missing a header row."
                )

            missing = [name for name in self.required_columns if name not in reader.fieldnames]
            if missing:
                raise ValueError(
                    "Telemetry replay file is missing required columns: "
                    f"{', '.join(missing)}. Expected columns: {', '.join(self.required_columns)}."
                )

            rows: List[Dict[str, object]] = []
            for line_number, row in enumerate(reader, start=2):
                try:
                    parsed: Dict[str, object] = {
                        "timestamp": parse_utc_timestamp(str(row["timestamp"])),
                    }
                    for field in REPLAY_FIELDS:
                        parsed[field] = float(row[field])
                    rows.append(parsed)
                except Exception as exc:
                    raise ValueError(
                        f"Invalid telemetry row {line_number} in {str(csv_path)!r}: {exc}"
                    ) from exc

        return rows

    @staticmethod
    def _as_state(row: Mapping[str, object]) -> TelemetryState:
        return TelemetryState(
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            altitude_m=float(row["altitude_m"]),
            yaw_deg=float(row["yaw_deg"]),
            pitch_deg=float(row["pitch_deg"]),
            roll_deg=float(row["roll_deg"]),
        )

    @staticmethod
    def _lerp(a: float, b: float, ratio: float) -> float:
        return a + ratio * (b - a)

    def _target_time(self, timestamp_seconds: float, event_time: Optional[datetime]) -> datetime:
        if event_time is not None:
            if event_time.tzinfo is None:
                return event_time.replace(tzinfo=timezone.utc)
            return event_time.astimezone(timezone.utc)
        return self.start_time + timedelta(seconds=float(timestamp_seconds))

    def state_at(self, timestamp_seconds: float, event_time: Optional[datetime] = None) -> TelemetryState:
        """Return interpolated telemetry at the requested video/event time.

        If the requested time is outside the replay log, the state is clamped to
        the first or last telemetry row. This keeps short demo logs safe to run
        against longer videos without crashing the pipeline.
        """
        target = self._target_time(timestamp_seconds, event_time)

        if len(self.rows) == 1 or target <= self.start_time:
            return self._as_state(self.rows[0])
        if target >= self.end_time:
            return self._as_state(self.rows[-1])

        for i in range(len(self.rows) - 1):
            left = self.rows[i]
            right = self.rows[i + 1]
            left_time = left["timestamp"]
            right_time = right["timestamp"]

            if left_time <= target <= right_time:
                span = (right_time - left_time).total_seconds()
                if span <= 0:
                    return self._as_state(right)

                ratio = (target - left_time).total_seconds() / span
                return TelemetryState(
                    lat=self._lerp(float(left["lat"]), float(right["lat"]), ratio),
                    lon=self._lerp(float(left["lon"]), float(right["lon"]), ratio),
                    altitude_m=self._lerp(float(left["altitude_m"]), float(right["altitude_m"]), ratio),
                    yaw_deg=self._lerp(float(left["yaw_deg"]), float(right["yaw_deg"]), ratio),
                    pitch_deg=self._lerp(float(left["pitch_deg"]), float(right["pitch_deg"]), ratio),
                    roll_deg=self._lerp(float(left["roll_deg"]), float(right["roll_deg"]), ratio),
                )

        return self._as_state(self.rows[-1])
