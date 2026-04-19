from fusion import estimate_target_position_with_mode
from telemetry import offset_latlon


def test_heading_aware_mode_rotates_forward_offset_into_east_offset() -> None:
    bbox = [40.0, 0.0, 60.0, 20.0]
    frame_shape = (100, 100)

    nadir_lat, nadir_lon = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=bbox,
        frame_shape=frame_shape,
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="nadir",
        yaw_deg=90.0,
        target_point="bbox_center",
    )
    heading_lat, heading_lon = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=bbox,
        frame_shape=frame_shape,
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="heading_aware_nadir",
        yaw_deg=90.0,
        target_point="bbox_center",
    )

    expected_nadir = offset_latlon(43.649, -79.381, east_m=0.0, north_m=80.0)
    expected_heading = offset_latlon(43.649, -79.381, east_m=80.0, north_m=0.0)

    assert abs(nadir_lat - expected_nadir[0]) < 1e-9
    assert abs(nadir_lon - expected_nadir[1]) < 1e-9
    assert abs(heading_lat - expected_heading[0]) < 1e-9
    assert abs(heading_lon - expected_heading[1]) < 1e-9


def test_bottom_center_target_point_changes_projection() -> None:
    center_latlon = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=[40.0, 20.0, 60.0, 80.0],
        frame_shape=(100, 100),
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        target_point="bbox_center",
    )
    bottom_center_latlon = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=[40.0, 20.0, 60.0, 80.0],
        frame_shape=(100, 100),
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        target_point="bbox_bottom_center",
    )

    assert bottom_center_latlon[0] < center_latlon[0]
    assert bottom_center_latlon[1] == center_latlon[1]