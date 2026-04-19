import json

from geojson_export import track_to_feature, tracks_to_feature_collection, write_tracks_geojson


def test_track_to_feature_uses_geojson_coordinate_order() -> None:
    feature = track_to_feature({
        "track_id": 1,
        "type": "possible_person_track",
        "track_class": "high_confidence_person",
        "track_score": 0.9,
        "duration_seconds": 4.0,
        "detection_density": 1.0,
        "hits": 5,
        "mean_confidence": 0.8,
        "max_confidence": 0.9,
        "first_seen": "2026-04-19T12:00:00Z",
        "last_seen": "2026-04-19T12:00:04Z",
        "first_frame": 0,
        "last_frame": 4,
        "representative_bbox": [1.0, 2.0, 3.0, 4.0],
        "lat": 43.649,
        "lon": -79.381,
    })

    assert feature["geometry"]["coordinates"] == [-79.381, 43.649]
    assert feature["properties"]["heatmap_weight"] == 0.9


def test_tracks_to_feature_collection_filters_tracks_and_writes_file(tmp_path) -> None:
    tracks = [
        {
            "track_id": 1,
            "type": "possible_person_track",
            "track_class": "high_confidence_person",
            "track_score": 0.85,
            "mean_confidence": 0.75,
            "max_confidence": 0.8,
            "lat": 43.649,
            "lon": -79.381,
        },
        {
            "track_id": 2,
            "type": "possible_person_track",
            "track_class": "marginal_person",
            "track_score": 0.4,
            "mean_confidence": 0.4,
            "max_confidence": 0.45,
            "lat": 43.65,
            "lon": -79.38,
        },
    ]

    collection = tracks_to_feature_collection(
        tracks,
        config={"min_track_score": 0.5, "include_marginal_tracks": False},
    )

    assert len(collection["features"]) == 1
    assert collection["features"][0]["properties"]["track_id"] == 1

    output_path = tmp_path / "tracks.geojson"
    write_tracks_geojson(tracks, str(output_path), config={"min_track_score": 0.5, "include_marginal_tracks": False})

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written == collection