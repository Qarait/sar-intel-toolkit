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


def test_public_site_keeps_simulation_first_framing_in_hero() -> None:
    index_html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")

    assert "Simulation-first humanitarian SAR intelligence" in index_html


def test_public_site_exposes_review_cockpit_without_operational_overclaim() -> None:
    index_html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")

    assert "Human review cockpit" in index_html
    assert "candidate queue" in index_html
    assert "Confirm candidate" in app_js
    assert "Mark uncertain" in app_js
    assert "Reject candidate" in app_js
    assert "assets/review_queue.json" in app_js
    assert "victim found" not in index_html.lower()
    assert "victim found" not in app_js.lower()
