import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _clamp01(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, max(0.0, numeric))


def _track_heatmap_weight(track: Dict[str, Any]) -> float:
    if track.get("track_score") is not None:
        return round(_clamp01(track.get("track_score")), 4)
    if track.get("mean_confidence") is not None:
        return round(_clamp01(track.get("mean_confidence")), 4)
    return round(_clamp01(track.get("max_confidence")), 4)


def track_to_feature(track: Dict[str, Any]) -> Dict[str, Any]:
    properties = {
        "track_id": track.get("track_id"),
        "type": track.get("type"),
        "track_class": track.get("track_class"),
        "track_score": track.get("track_score"),
        "heatmap_weight": _track_heatmap_weight(track),
        "duration_seconds": track.get("duration_seconds"),
        "detection_density": track.get("detection_density"),
        "hits": track.get("hits"),
        "mean_confidence": track.get("mean_confidence"),
        "max_confidence": track.get("max_confidence"),
        "first_seen": track.get("first_seen"),
        "last_seen": track.get("last_seen"),
        "first_frame": track.get("first_frame"),
        "last_frame": track.get("last_frame"),
        "representative_bbox": track.get("representative_bbox"),
    }
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(track["lon"]), float(track["lat"])],
        },
        "properties": properties,
    }


def tracks_to_feature_collection(
    tracks: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = config or {}
    min_track_score = float(cfg.get("min_track_score", 0.0))
    include_marginal_tracks = bool(cfg.get("include_marginal_tracks", True))

    features = []
    for track in tracks:
        track_score = float(track.get("track_score", 0.0) or 0.0)
        if min_track_score > 0.0 and track_score < min_track_score:
            continue
        if not include_marginal_tracks and track.get("track_class") == "marginal_person":
            continue
        features.append(track_to_feature(track))

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def write_tracks_geojson(
    tracks: List[Dict[str, Any]],
    output_path: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    feature_collection = tracks_to_feature_collection(tracks, config=config)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(feature_collection, f, indent=2)
    return feature_collection