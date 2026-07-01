from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Iterable, Sequence

import cv2
import numpy as np


@dataclass(frozen=True)
class MotionCandidate:
    frame_index: int
    bbox: tuple[int, int, int, int]
    centroid: tuple[float, float]
    area: int
    mean_delta: float


@dataclass(frozen=True)
class MotionTracklet:
    candidates: tuple[MotionCandidate, ...]
    score: float

    @property
    def start_frame(self) -> int:
        return self.candidates[0].frame_index

    @property
    def end_frame(self) -> int:
        return self.candidates[-1].frame_index

    @property
    def duration(self) -> int:
        return len(self.candidates)

    @property
    def displacement(self) -> float:
        start = self.candidates[0].centroid
        end = self.candidates[-1].centroid
        return hypot(end[0] - start[0], end[1] - start[1])


def _as_gray(frame: np.ndarray) -> np.ndarray:
    array = np.asarray(frame)
    if array.ndim == 2:
        return array.astype(np.uint8)
    if array.ndim == 3:
        return cv2.cvtColor(array.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    raise ValueError(f"Expected 2D grayscale or 3D BGR frame, got shape {array.shape!r}")


def _component_candidates(
    delta: np.ndarray,
    frame_index: int,
    min_area: int,
) -> list[MotionCandidate]:
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(delta, connectivity=8)
    candidates: list[MotionCandidate] = []
    for label in range(1, count):
        x, y, width, height, area = stats[label]
        if int(area) < min_area:
            continue
        mask = labels == label
        candidates.append(
            MotionCandidate(
                frame_index=frame_index,
                bbox=(int(x), int(y), int(x + width - 1), int(y + height - 1)),
                centroid=(float(centroids[label][0]), float(centroids[label][1])),
                area=int(area),
                mean_delta=float(delta[mask].mean()),
            )
        )
    return sorted(candidates, key=lambda item: (item.bbox[1], item.bbox[0]))


def detect_motion_candidates(
    previous_frame: np.ndarray,
    current_frame: np.ndarray,
    *,
    frame_index: int,
    threshold: int = 25,
    min_area: int = 4,
) -> list[MotionCandidate]:
    previous_gray = _as_gray(previous_frame)
    current_gray = _as_gray(current_frame)
    if previous_gray.shape != current_gray.shape:
        raise ValueError("Previous and current frames must have the same shape.")

    diff = cv2.absdiff(previous_gray, current_gray)
    _, delta = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    return _component_candidates(delta, frame_index, min_area)


def _appearing_candidates(
    previous_frame: np.ndarray,
    current_frame: np.ndarray,
    *,
    frame_index: int,
    threshold: int,
    min_area: int,
) -> list[MotionCandidate]:
    previous_gray = _as_gray(previous_frame)
    current_gray = _as_gray(current_frame)
    candidates = detect_motion_candidates(
        previous_gray,
        current_gray,
        frame_index=frame_index,
        threshold=threshold,
        min_area=min_area,
    )
    appearing: list[MotionCandidate] = []
    for candidate in candidates:
        x1, y1, x2, y2 = candidate.bbox
        current_mean = float(current_gray[y1 : y2 + 1, x1 : x2 + 1].mean())
        previous_mean = float(previous_gray[y1 : y2 + 1, x1 : x2 + 1].mean())
        if current_mean > previous_mean:
            appearing.append(candidate)
    return appearing


def _distance(a: MotionCandidate, b: MotionCandidate) -> float:
    return hypot(a.centroid[0] - b.centroid[0], a.centroid[1] - b.centroid[1])


def _tracklet_score(candidates: Sequence[MotionCandidate]) -> float:
    if not candidates:
        return 0.0
    displacement = hypot(
        candidates[-1].centroid[0] - candidates[0].centroid[0],
        candidates[-1].centroid[1] - candidates[0].centroid[1],
    )
    mean_area = sum(item.area for item in candidates) / len(candidates)
    return float(len(candidates) + displacement + mean_area / 100.0)


def build_motion_tracklets(
    frames: Iterable[np.ndarray],
    *,
    threshold: int = 25,
    min_area: int = 4,
    min_persistence: int = 3,
    max_link_distance: float = 8.0,
) -> list[MotionTracklet]:
    frame_list = list(frames)
    active_tracks: list[list[MotionCandidate]] = []

    for frame_index in range(1, len(frame_list)):
        candidates = _appearing_candidates(
            frame_list[frame_index - 1],
            frame_list[frame_index],
            frame_index=frame_index,
            threshold=threshold,
            min_area=min_area,
        )
        used_tracks: set[int] = set()
        for candidate in candidates:
            best_track_index = None
            best_distance = max_link_distance
            for track_index, track in enumerate(active_tracks):
                if track_index in used_tracks:
                    continue
                distance = _distance(track[-1], candidate)
                if distance <= best_distance:
                    best_distance = distance
                    best_track_index = track_index
            if best_track_index is None:
                active_tracks.append([candidate])
                used_tracks.add(len(active_tracks) - 1)
            else:
                active_tracks[best_track_index].append(candidate)
                used_tracks.add(best_track_index)

    tracklets = [
        MotionTracklet(candidates=tuple(track), score=_tracklet_score(track))
        for track in active_tracks
        if len(track) >= min_persistence
    ]
    return sorted(tracklets, key=lambda item: item.score, reverse=True)