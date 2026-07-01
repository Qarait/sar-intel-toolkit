from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_demo_geojson_properties_are_not_rendered_with_html_templates() -> None:
    app_js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")

    assert "<h3>Track ${properties.track_id" not in app_js
    assert "marker.bindPopup(\n        `" not in app_js


def test_public_site_uses_possible_person_and_detection_track_language() -> None:
    index_html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")

    assert "detected persons" not in index_html
    assert "23 confirmed tracks" not in index_html
    assert "possible-person detections" in index_html
    assert "23 confirmed detection tracks" in index_html
