import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np


METERS_PER_DEGREE_LAT = 111_320.0


def _format_utc(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _bbox_iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = [float(v) for v in a]
    bx1, by1, bx2, by2 = [float(v) for v in b]

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter_area

    if union <= 0.0:
        return 0.0
    return inter_area / union


def _meters_per_degree_lon(at_lat: float) -> float:
    return METERS_PER_DEGREE_LAT * math.cos(math.radians(at_lat))


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Small-area lat/lon distance approximation in meters."""
    mean_lat = (lat1 + lat2) / 2.0
    north_m = (lat2 - lat1) * METERS_PER_DEGREE_LAT
    east_m = (lon2 - lon1) * _meters_per_degree_lon(mean_lat)
    return math.hypot(east_m, north_m)


def _bbox_to_xywh(bbox: Sequence[float]) -> Tuple[float, float, float, float]:
    x1, y1, x2, y2 = [float(v) for v in bbox]
    w = max(0.0, x2 - x1)
    h = max(0.0, y2 - y1)
    cx = x1 + (w / 2.0)
    cy = y1 + (h / 2.0)
    return cx, cy, w, h


def _xywh_to_bbox(cx: float, cy: float, w: float, h: float) -> List[float]:
    half_w = max(0.0, float(w)) / 2.0
    half_h = max(0.0, float(h)) / 2.0
    return [float(cx) - half_w, float(cy) - half_h, float(cx) + half_w, float(cy) + half_h]


class KalmanBBoxFilter:
    def __init__(
        self,
        bbox: Sequence[float],
        process_noise: float = 1.0,
        measurement_noise: float = 10.0,
        initial_uncertainty: float = 100.0,
    ) -> None:
        cx, cy, w, h = _bbox_to_xywh(bbox)
        self.state = np.array([[cx], [cy], [w], [h], [0.0], [0.0], [0.0], [0.0]], dtype=float)
        self.covariance = np.eye(8, dtype=float) * float(initial_uncertainty)
        self.process_noise = float(process_noise)
        self.measurement_noise = float(measurement_noise)
        self.measurement_matrix = np.zeros((4, 8), dtype=float)
        self.measurement_matrix[0, 0] = 1.0
        self.measurement_matrix[1, 1] = 1.0
        self.measurement_matrix[2, 2] = 1.0
        self.measurement_matrix[3, 3] = 1.0

    def predict(self, dt: float = 1.0) -> None:
        transition = np.eye(8, dtype=float)
        transition[0, 4] = dt
        transition[1, 5] = dt
        transition[2, 6] = dt
        transition[3, 7] = dt

        process_cov = np.eye(8, dtype=float) * self.process_noise
        self.state = transition @ self.state
        self.covariance = transition @ self.covariance @ transition.T + process_cov

    def update(self, bbox: Sequence[float]) -> None:
        cx, cy, w, h = _bbox_to_xywh(bbox)
        measurement = np.array([[cx], [cy], [w], [h]], dtype=float)
        measurement_cov = np.eye(4, dtype=float) * self.measurement_noise

        innovation = measurement - (self.measurement_matrix @ self.state)
        innovation_cov = self.measurement_matrix @ self.covariance @ self.measurement_matrix.T + measurement_cov
        kalman_gain = self.covariance @ self.measurement_matrix.T @ np.linalg.inv(innovation_cov)

        self.state = self.state + (kalman_gain @ innovation)
        identity = np.eye(8, dtype=float)
        self.covariance = (identity - (kalman_gain @ self.measurement_matrix)) @ self.covariance

    def predicted_bbox(self) -> List[float]:
        cx, cy, w, h = self.state[:4, 0]
        return _xywh_to_bbox(cx, cy, w, h)


@dataclass
class Track:
    track_id: int
    bbox: List[float]
    first_frame: int
    last_frame: int
    first_seen: datetime
    last_seen: datetime
    hits: int = 0
    confidence_sum: float = 0.0
    max_confidence: float = 0.0
    weighted_lat_sum: float = 0.0
    weighted_lon_sum: float = 0.0
    confidence_weight_sum: float = 0.0
    last_lat: float = 0.0
    last_lon: float = 0.0
    missed_frames: int = 0
    max_consecutive_misses: int = 0
    motion_model: str = "none"
    kalman_filter: Optional[KalmanBBoxFilter] = None
    predicted_bbox_cache: Optional[List[float]] = None
    representative_bbox: List[float] = field(default_factory=list)

    def predict(self, dt: float = 1.0) -> None:
        if self.kalman_filter is None:
            return
        self.kalman_filter.predict(dt=dt)
        self.predicted_bbox_cache = self.kalman_filter.predicted_bbox()

    def update(self, detection: Dict[str, Any], frame_idx: int, event_time: datetime) -> None:
        confidence = float(detection["confidence"])
        lat = float(detection["lat"])
        lon = float(detection["lon"])
        bbox = [float(v) for v in detection["bbox"]]

        if self.kalman_filter is not None:
            self.kalman_filter.update(bbox)
            self.predicted_bbox_cache = self.kalman_filter.predicted_bbox()

        self.bbox = bbox
        self.last_frame = int(frame_idx)
        self.last_seen = event_time
        self.hits += 1
        self.confidence_sum += confidence
        self.max_confidence = max(self.max_confidence, confidence)
        self.weighted_lat_sum += lat * confidence
        self.weighted_lon_sum += lon * confidence
        self.confidence_weight_sum += confidence
        self.last_lat = lat
        self.last_lon = lon
        self.missed_frames = 0

        if not self.representative_bbox or confidence >= self.max_confidence:
            self.representative_bbox = bbox

    def mark_missed(self) -> None:
        self.missed_frames += 1
        self.max_consecutive_misses = max(self.max_consecutive_misses, self.missed_frames)

    @property
    def mean_confidence(self) -> float:
        if self.hits <= 0:
            return 0.0
        return self.confidence_sum / self.hits

    @property
    def mean_lat(self) -> float:
        if self.confidence_weight_sum <= 0.0:
            return self.last_lat
        return self.weighted_lat_sum / self.confidence_weight_sum

    @property
    def mean_lon(self) -> float:
        if self.confidence_weight_sum <= 0.0:
            return self.last_lon
        return self.weighted_lon_sum / self.confidence_weight_sum

    def to_summary(self) -> Dict[str, Any]:
        summary = {
            "track_id": self.track_id,
            "type": "possible_person_track",
            "first_seen": _format_utc(self.first_seen),
            "last_seen": _format_utc(self.last_seen),
            "first_frame": self.first_frame,
            "last_frame": self.last_frame,
            "hits": self.hits,
            "lat": round(float(self.mean_lat), 7),
            "lon": round(float(self.mean_lon), 7),
            "max_confidence": round(float(self.max_confidence), 4),
            "mean_confidence": round(float(self.mean_confidence), 4),
            "representative_bbox": [round(float(v), 2) for v in self.representative_bbox],
        }
        if self.motion_model == "kalman":
            summary["motion_model"] = "kalman"
            summary["missed_frames"] = self.missed_frames
            summary["max_consecutive_misses"] = self.max_consecutive_misses
        return summary


def _compute_track_scoring(
    track: "Track",
    fps: float,
    frame_stride: int,
    scoring_config: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute confidence-weighted scoring fields for a confirmed track."""
    duration_seconds = (track.last_frame - track.first_frame) / fps
    expected_processed_frames = math.floor((track.last_frame - track.first_frame) / max(1, frame_stride)) + 1
    detection_density = min(1.0, max(0.0, track.hits / expected_processed_frames))

    weights = scoring_config.get("weights", {})
    w_mean = float(weights.get("mean_confidence", 0.55))
    w_max = float(weights.get("max_confidence", 0.25))
    w_density = float(weights.get("detection_density", 0.20))

    track_score = min(1.0, max(0.0,
        w_mean * track.mean_confidence
        + w_max * track.max_confidence
        + w_density * detection_density
    ))

    high_t = float(scoring_config.get("high_confidence_threshold", 0.80))
    possible_t = float(scoring_config.get("possible_confidence_threshold", 0.55))

    if track_score >= high_t:
        track_class = "high_confidence_person"
    elif track_score >= possible_t:
        track_class = "possible_person"
    else:
        track_class = "marginal_person"

    return {
        "duration_seconds": round(duration_seconds, 3),
        "detection_density": round(detection_density, 4),
        "track_score": round(track_score, 4),
        "track_class": track_class,
    }


class SimpleTracker:
    """Lightweight tracker/deduplicator for MVP video detections.

    This is deliberately small and dependency-free. It links detections across frames using
    image-space overlap plus GPS proximity, then emits one confirmed summary per track.
    """

    def __init__(
        self,
        iou_threshold: float = 0.25,
        max_frame_gap: int = 10,
        max_position_distance_m: float = 12.0,
        min_hits: int = 3,
        motion_model: str = "none",
        kalman_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.iou_threshold = float(iou_threshold)
        self.max_frame_gap = int(max_frame_gap)
        self.max_position_distance_m = float(max_position_distance_m)
        self.min_hits = int(min_hits)
        normalized_motion_model = str(motion_model or "none").lower()
        if normalized_motion_model not in {"none", "kalman"}:
            raise ValueError(
                f"Unsupported tracking.motion_model={motion_model!r}. Expected 'none' or 'kalman'."
            )
        self.motion_model = normalized_motion_model
        self.kalman_config = dict(kalman_config or {})
        self.tracks: Dict[int, Track] = {}
        self._next_track_id = 1

    def _new_track(self, detection: Dict[str, Any], frame_idx: int, event_time: datetime) -> Track:
        kalman_filter = None
        if self.motion_model == "kalman":
            kalman_filter = KalmanBBoxFilter(
                bbox=detection["bbox"],
                process_noise=float(self.kalman_config.get("process_noise", 1.0)),
                measurement_noise=float(self.kalman_config.get("measurement_noise", 10.0)),
                initial_uncertainty=float(self.kalman_config.get("initial_uncertainty", 100.0)),
            )
        track = Track(
            track_id=self._next_track_id,
            bbox=[float(v) for v in detection["bbox"]],
            first_frame=int(frame_idx),
            last_frame=int(frame_idx),
            first_seen=event_time,
            last_seen=event_time,
            motion_model=self.motion_model,
            kalman_filter=kalman_filter,
        )
        self._next_track_id += 1
        track.update(detection, frame_idx, event_time)
        self.tracks[track.track_id] = track
        return track

    def _score_candidate(self, track: Track, detection: Dict[str, Any], frame_idx: int) -> Optional[float]:
        frame_gap = int(frame_idx) - track.last_frame
        if frame_gap < 0 or frame_gap > self.max_frame_gap:
            return None

        candidate_bbox = track.predicted_bbox_cache if track.predicted_bbox_cache is not None else track.bbox
        iou = _bbox_iou(candidate_bbox, detection["bbox"])
        distance = _distance_m(
            track.last_lat,
            track.last_lon,
            float(detection["lat"]),
            float(detection["lon"]),
        )

        position_score = 0.0
        if self.max_position_distance_m > 0.0:
            position_score = max(0.0, 1.0 - (distance / self.max_position_distance_m))

        # Accept either stable image overlap or close geotag proximity.
        if iou < self.iou_threshold and distance > self.max_position_distance_m:
            return None

        # IoU is most reliable when available; proximity helps when boxes jitter.
        recency_bonus = max(0.0, 1.0 - (frame_gap / max(1, self.max_frame_gap))) * 0.05
        return (2.0 * iou) + position_score + recency_bonus

    def update(
        self,
        detections: List[Dict[str, Any]],
        frame_idx: int,
        event_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        if event_time is None:
            if detections:
                ts_str = str(detections[0].get("timestamp", ""))
                event_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).astimezone(timezone.utc)
            else:
                event_time = datetime.now(timezone.utc)

        if self.motion_model == "kalman":
            for track in self.tracks.values():
                if 0 <= (frame_idx - track.last_frame) <= self.max_frame_gap:
                    track.predict(dt=1.0)

        assigned_tracks: Set[int] = set()
        enriched: List[Dict[str, Any]] = []

        # Greedy matching is enough for the MVP and keeps the implementation transparent.
        for detection in sorted(detections, key=lambda d: float(d["confidence"]), reverse=True):
            best_track: Optional[Track] = None
            best_score: Optional[float] = None

            for track in self.tracks.values():
                if track.track_id in assigned_tracks:
                    continue

                score = self._score_candidate(track, detection, frame_idx)
                if score is None:
                    continue

                if best_score is None or score > best_score:
                    best_score = score
                    best_track = track

            if best_track is None:
                best_track = self._new_track(detection, frame_idx, event_time)
            else:
                best_track.update(detection, frame_idx, event_time)

            assigned_tracks.add(best_track.track_id)
            enriched_detection = dict(detection)
            enriched_detection["track_id"] = best_track.track_id
            enriched.append(enriched_detection)

        for track in self.tracks.values():
            if track.track_id in assigned_tracks:
                continue
            frame_gap = int(frame_idx) - track.last_frame
            if 0 < frame_gap <= self.max_frame_gap:
                track.mark_missed()

        return enriched

    def confirmed_tracks(
        self,
        fps: float = 30.0,
        frame_stride: int = 1,
        scoring_config: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        summaries = []
        for track in self.tracks.values():
            if track.hits < self.min_hits:
                continue
            summary = track.to_summary()
            if scoring_config is not None and scoring_config.get("enabled", True):
                scoring_fields = _compute_track_scoring(track, fps, frame_stride, scoring_config)
                summary["duration_seconds"] = scoring_fields["duration_seconds"]
                summary["detection_density"] = scoring_fields["detection_density"]
                summary["track_score"] = scoring_fields["track_score"]
                summary["track_class"] = scoring_fields["track_class"]
            summaries.append(summary)
        summaries.sort(key=lambda item: (item["first_frame"], item["track_id"]))
        return summaries
