from planner import generate_grid, meters_to_lat, meters_to_lon


def test_generate_grid_uses_lawnmower_pattern_and_preserves_altitude() -> None:
    min_lat = 43.0
    min_lon = -79.0
    max_lat = min_lat + (2 * meters_to_lat(10.0))
    max_lon = min_lon + (2 * meters_to_lon(10.0, min_lat))

    waypoints = generate_grid(
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
        altitude_m=60.0,
        lane_spacing_m=10.0,
        forward_step_m=10.0,
    )

    assert len(waypoints) == 9

    row_one = waypoints[0:3]
    row_two = waypoints[3:6]
    row_three = waypoints[6:9]

    assert [point["alt"] for point in waypoints] == [60.0] * 9
    assert row_one[0]["lon"] < row_one[1]["lon"] < row_one[2]["lon"]
    assert row_two[0]["lon"] > row_two[1]["lon"] > row_two[2]["lon"]
    assert row_three[0]["lon"] < row_three[1]["lon"] < row_three[2]["lon"]
    assert row_one[0]["lat"] < row_two[0]["lat"] < row_three[0]["lat"]


def test_generate_grid_rejects_invalid_bounds() -> None:
    try:
        generate_grid(
            min_lat=43.0,
            min_lon=-79.0,
            max_lat=43.0,
            max_lon=-78.9,
            altitude_m=50.0,
            lane_spacing_m=10.0,
            forward_step_m=10.0,
        )
    except ValueError as exc:
        assert "Invalid bounding box" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid bounds")