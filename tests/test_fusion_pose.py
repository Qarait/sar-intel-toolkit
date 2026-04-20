import pytest

from fusion import estimate_target_position_with_mode
from telemetry import offset_latlon


def test_pose_aware_zero_attitude_matches_heading_aware_nadir() -> None:
    pose_latlon = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=[40.0, 0.0, 60.0, 20.0],
        frame_shape=(100, 100),
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="pose_aware_flat_ground",
        yaw_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        target_point="bbox_center",
    )
    heading_latlon = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=[40.0, 0.0, 60.0, 20.0],
        frame_shape=(100, 100),
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="heading_aware_nadir",
        yaw_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        target_point="bbox_center",
    )

    assert abs(pose_latlon[0] - heading_latlon[0]) < 1e-9
    assert abs(pose_latlon[1] - heading_latlon[1]) < 1e-9


def test_pose_aware_yaw_90_rotates_offsets_as_expected() -> None:
    pose_latlon = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=[40.0, 0.0, 60.0, 20.0],
        frame_shape=(100, 100),
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="pose_aware_flat_ground",
        yaw_deg=90.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        target_point="bbox_center",
    )

    expected = offset_latlon(43.649, -79.381, east_m=80.0, north_m=0.0)

    assert abs(pose_latlon[0] - expected[0]) < 1e-9
    assert abs(pose_latlon[1] - expected[1]) < 1e-9


def test_pose_aware_roll_changes_output_compared_with_heading_only() -> None:
    heading_only = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=[40.0, 40.0, 60.0, 60.0],
        frame_shape=(100, 100),
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="heading_aware_nadir",
        yaw_deg=45.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        target_point="bbox_center",
    )
    rolled = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=[40.0, 40.0, 60.0, 60.0],
        frame_shape=(100, 100),
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="pose_aware_flat_ground",
        yaw_deg=45.0,
        pitch_deg=0.0,
        roll_deg=10.0,
        target_point="bbox_center",
    )

    assert rolled != heading_only


def test_pose_aware_pitch_changes_output_compared_with_heading_only() -> None:
    heading_only = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=[40.0, 40.0, 60.0, 60.0],
        frame_shape=(100, 100),
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="heading_aware_nadir",
        yaw_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        target_point="bbox_center",
    )
    pitched = estimate_target_position_with_mode(
        drone_lat=43.649,
        drone_lon=-79.381,
        bbox=[40.0, 40.0, 60.0, 60.0],
        frame_shape=(100, 100),
        altitude_m=100.0,
        horizontal_fov_deg=90.0,
        vertical_fov_deg=90.0,
        mode="pose_aware_flat_ground",
        yaw_deg=0.0,
        pitch_deg=15.0,
        roll_deg=0.0,
        target_point="bbox_center",
    )

    assert pitched != heading_only


def test_pose_aware_invalid_altitude_raises() -> None:
    with pytest.raises(ValueError, match="requires altitude_m > 0"):
        estimate_target_position_with_mode(
            drone_lat=43.649,
            drone_lon=-79.381,
            bbox=[40.0, 40.0, 60.0, 60.0],
            frame_shape=(100, 100),
            altitude_m=0.0,
            horizontal_fov_deg=90.0,
            vertical_fov_deg=90.0,
            mode="pose_aware_flat_ground",
            yaw_deg=0.0,
            pitch_deg=0.0,
            roll_deg=0.0,
            target_point="bbox_center",
        )


def test_pose_aware_invalid_fov_raises() -> None:
    with pytest.raises(ValueError, match="must be between 0 and 180 degrees"):
        estimate_target_position_with_mode(
            drone_lat=43.649,
            drone_lon=-79.381,
            bbox=[40.0, 40.0, 60.0, 60.0],
            frame_shape=(100, 100),
            altitude_m=100.0,
            horizontal_fov_deg=0.0,
            vertical_fov_deg=90.0,
            mode="pose_aware_flat_ground",
            yaw_deg=0.0,
            pitch_deg=0.0,
            roll_deg=0.0,
            target_point="bbox_center",
        )


def test_pose_aware_parallel_or_away_ray_is_handled_explicitly() -> None:
    with pytest.raises(ValueError, match="does not intersect the flat ground plane"):
        estimate_target_position_with_mode(
            drone_lat=43.649,
            drone_lon=-79.381,
            bbox=[40.0, 40.0, 60.0, 60.0],
            frame_shape=(100, 100),
            altitude_m=100.0,
            horizontal_fov_deg=90.0,
            vertical_fov_deg=90.0,
            mode="pose_aware_flat_ground",
            yaw_deg=0.0,
            pitch_deg=180.0,
            roll_deg=0.0,
            target_point="bbox_center",
        )