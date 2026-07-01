from dataclasses import dataclass
from math import prod
from typing import Iterable


@dataclass(frozen=True)
class SearchCell:
    cell_id: str
    center_lat: float
    center_lon: float
    planted_target: bool = False


@dataclass(frozen=True)
class CoveragePass:
    cell_id: str
    altitude_m: float
    recall_estimate: float
    detected: bool = False


def _clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def estimate_cell_confidence(cell: SearchCell, passes: Iterable[CoveragePass]) -> dict[str, object]:
    matching_passes = [item for item in passes if item.cell_id == cell.cell_id]
    miss_probability = (
        prod(1.0 - _clamp_probability(item.recall_estimate) for item in matching_passes)
        if matching_passes
        else 1.0
    )
    confidence = 1.0 - miss_probability
    planted_miss = cell.planted_target and not any(item.detected for item in matching_passes)
    confidence_class = "uncertain" if miss_probability >= 0.50 or planted_miss else "covered"
    return {
        "cell_id": cell.cell_id,
        "center_lat": cell.center_lat,
        "center_lon": cell.center_lon,
        "pass_count": len(matching_passes),
        "miss_probability": round(miss_probability, 12),
        "confidence": round(confidence, 12),
        "class": confidence_class,
        "planted_miss": planted_miss,
    }


def rank_uncertain_cells(
    cells: Iterable[SearchCell],
    passes: Iterable[CoveragePass],
) -> list[dict[str, object]]:
    pass_list = list(passes)
    estimates = [estimate_cell_confidence(cell, pass_list) for cell in cells]
    return sorted(estimates, key=lambda item: float(item["miss_probability"]), reverse=True)