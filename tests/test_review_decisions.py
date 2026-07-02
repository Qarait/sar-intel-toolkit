from datetime import UTC, datetime
from pathlib import Path

import pytest

from review_decisions import (
    ReviewDecision,
    apply_review_decisions,
    append_review_decision_jsonl,
    load_review_decisions_jsonl,
    serialize_review_decisions,
)


def test_review_decision_serializes_to_json_ready_record() -> None:
    decided_at = datetime(2026, 7, 1, 18, 30, tzinfo=UTC)

    decision = ReviewDecision(
        tracklet_id="motion-0001",
        status="confirmed",
        reviewer="operator-a",
        decided_at=decided_at,
        note="Visible moving person near tree line.",
        confidence=0.82,
    )

    assert decision.to_record() == {
        "tracklet_id": "motion-0001",
        "status": "confirmed",
        "reviewer": "operator-a",
        "decided_at": "2026-07-01T18:30:00Z",
        "note": "Visible moving person near tree line.",
        "confidence": 0.82,
    }


def test_review_decision_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="Unsupported review status"):
        ReviewDecision(tracklet_id="motion-0001", status="maybe", reviewer="operator-a")


def test_review_decision_rejects_confidence_outside_unit_interval() -> None:
    with pytest.raises(ValueError, match="confidence"):
        ReviewDecision(tracklet_id="motion-0001", status="confirmed", reviewer="operator-a", confidence=1.2)


def test_apply_review_decisions_merges_latest_status_into_queue_records() -> None:
    queue = [
        {"tracklet_id": "motion-0001", "status": "unreviewed", "review_priority": 10.0},
        {"tracklet_id": "motion-0002", "status": "unreviewed", "review_priority": 9.0},
    ]
    decisions = [
        ReviewDecision(
            tracklet_id="motion-0001",
            status="uncertain",
            reviewer="operator-a",
            decided_at=datetime(2026, 7, 1, 18, 0, tzinfo=UTC),
        ),
        ReviewDecision(
            tracklet_id="motion-0001",
            status="confirmed",
            reviewer="operator-b",
            decided_at=datetime(2026, 7, 1, 18, 5, tzinfo=UTC),
            confidence=0.7,
        ),
    ]

    merged = apply_review_decisions(queue, decisions)

    assert merged[0]["status"] == "confirmed"
    assert merged[0]["review"] == {
        "tracklet_id": "motion-0001",
        "status": "confirmed",
        "reviewer": "operator-b",
        "decided_at": "2026-07-01T18:05:00Z",
        "confidence": 0.7,
    }
    assert merged[1]["status"] == "unreviewed"
    assert "review" not in merged[1]


def test_serialize_review_decisions_orders_append_log_by_decision_time() -> None:
    decisions = [
        ReviewDecision(
            tracklet_id="motion-0002",
            status="rejected",
            reviewer="operator-a",
            decided_at=datetime(2026, 7, 1, 18, 10, tzinfo=UTC),
        ),
        ReviewDecision(
            tracklet_id="motion-0001",
            status="confirmed",
            reviewer="operator-a",
            decided_at=datetime(2026, 7, 1, 18, 0, tzinfo=UTC),
        ),
    ]

    records = serialize_review_decisions(decisions)

    assert [record["tracklet_id"] for record in records] == ["motion-0001", "motion-0002"]


def test_review_decisions_append_and_load_jsonl_log(tmp_path: Path) -> None:
    path = tmp_path / "review-decisions.jsonl"

    append_review_decision_jsonl(
        path,
        ReviewDecision(
            tracklet_id="motion-0001",
            status="confirmed",
            reviewer="operator-a",
            decided_at=datetime(2026, 7, 1, 18, 0, tzinfo=UTC),
            note="Clear movement.",
        ),
    )
    append_review_decision_jsonl(
        path,
        ReviewDecision(
            tracklet_id="motion-0002",
            status="rejected",
            reviewer="operator-a",
            decided_at=datetime(2026, 7, 1, 18, 1, tzinfo=UTC),
        ),
    )

    loaded = load_review_decisions_jsonl(path)

    assert [decision.tracklet_id for decision in loaded] == ["motion-0001", "motion-0002"]
    assert loaded[0].note == "Clear movement."