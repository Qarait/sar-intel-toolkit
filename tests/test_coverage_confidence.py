from coverage_confidence import CoveragePass, SearchCell, estimate_cell_confidence, rank_uncertain_cells


def test_more_passes_reduce_miss_probability():
    cell = SearchCell(cell_id="A1", center_lat=43.0, center_lon=-79.0)
    one_pass = [CoveragePass(cell_id="A1", altitude_m=60.0, recall_estimate=0.30)]
    three_passes = one_pass * 3

    one = estimate_cell_confidence(cell, one_pass)
    three = estimate_cell_confidence(cell, three_passes)

    assert one["miss_probability"] == 0.70
    assert round(three["miss_probability"], 3) == 0.343
    assert three["confidence"] > one["confidence"]


def test_planted_miss_keeps_cell_uncertain():
    cell = SearchCell(cell_id="B2", center_lat=43.0, center_lon=-79.0, planted_target=True)
    passes = [CoveragePass(cell_id="B2", altitude_m=80.0, recall_estimate=0.20, detected=False)]

    result = estimate_cell_confidence(cell, passes)

    assert result["class"] == "uncertain"
    assert result["planted_miss"] is True


def test_rank_uncertain_cells_prioritizes_high_miss_probability():
    cells = [
        SearchCell(cell_id="A", center_lat=0.0, center_lon=0.0),
        SearchCell(cell_id="B", center_lat=0.0, center_lon=1.0),
    ]
    passes = [
        CoveragePass(cell_id="A", altitude_m=50.0, recall_estimate=0.80),
        CoveragePass(cell_id="B", altitude_m=100.0, recall_estimate=0.20),
    ]

    ranked = rank_uncertain_cells(cells, passes)

    assert [item["cell_id"] for item in ranked] == ["B", "A"]