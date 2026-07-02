from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from os import PathLike
from typing import Any, Iterable, Literal, Mapping

ReviewStatus = Literal["confirmed", "rejected", "uncertain"]
ReviewLogPath = str | PathLike[str]

SUPPORTED_REVIEW_STATUSES: set[str] = {"confirmed", "rejected", "uncertain"}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


@dataclass(frozen=True)
class ReviewDecision:
    tracklet_id: str
    status: ReviewStatus
    reviewer: str
    decided_at: datetime = field(default_factory=_utc_now)
    note: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.tracklet_id:
            raise ValueError("tracklet_id is required")
        if self.status not in SUPPORTED_REVIEW_STATUSES:
            raise ValueError(f"Unsupported review status: {self.status}")
        if not self.reviewer:
            raise ValueError("reviewer is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "tracklet_id": self.tracklet_id,
            "status": self.status,
            "reviewer": self.reviewer,
            "decided_at": _format_timestamp(self.decided_at),
        }
        if self.note is not None:
            record["note"] = self.note
        if self.confidence is not None:
            record["confidence"] = self.confidence
        return record

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> ReviewDecision:
        return cls(
            tracklet_id=str(record["tracklet_id"]),
            status=record["status"],
            reviewer=str(record["reviewer"]),
            decided_at=_parse_timestamp(str(record["decided_at"])),
            note=record.get("note"),
            confidence=record.get("confidence"),
        )


def serialize_review_decisions(decisions: Iterable[ReviewDecision]) -> list[dict[str, Any]]:
    return [decision.to_record() for decision in sorted(decisions, key=lambda item: item.decided_at)]


def append_review_decision_jsonl(path: ReviewLogPath, decision: ReviewDecision) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision.to_record(), sort_keys=True))
        handle.write("\n")


def load_review_decisions_jsonl(path: ReviewLogPath) -> list[ReviewDecision]:
    decisions: list[ReviewDecision] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                decisions.append(ReviewDecision.from_record(json.loads(stripped)))
    return decisions


def apply_review_decisions(
    queue: Iterable[Mapping[str, Any]],
    decisions: Iterable[ReviewDecision],
) -> list[dict[str, Any]]:
    latest_by_tracklet: dict[str, ReviewDecision] = {}
    for decision in decisions:
        current = latest_by_tracklet.get(decision.tracklet_id)
        if current is None or decision.decided_at >= current.decided_at:
            latest_by_tracklet[decision.tracklet_id] = decision

    merged: list[dict[str, Any]] = []
    for item in queue:
        record = dict(item)
        decision = latest_by_tracklet.get(str(record.get("tracklet_id", "")))
        if decision is not None:
            record["status"] = decision.status
            record["review"] = decision.to_record()
        merged.append(record)
    return merged