from mission_profiles import apply_mission_profile


def test_no_profile_is_noop() -> None:
    cfg = {"detector": {"confidence_threshold": 0.5}}
    resolved = apply_mission_profile(cfg)
    assert resolved == cfg


def test_sar_daylight_profile_applies() -> None:
    cfg = {
        "mission_profile": "sar_daylight",
        "detector": {"confidence_threshold": 0.1},
        "tracking": {"kalman": {"measurement_noise": 99.0}},
        "track_scoring": {"weights": {"mean_confidence": 0.1}},
    }

    resolved = apply_mission_profile(cfg)

    assert resolved["resolved_mission_profile"] == "sar_daylight"
    assert resolved["detector"]["confidence_threshold"] == 0.50
    assert resolved["tracking"]["kalman"]["measurement_noise"] == 10.0
    assert resolved["track_scoring"]["weights"]["mean_confidence"] == 0.55


def test_low_visibility_profile_applies() -> None:
    cfg = {
        "mission_profile": "sar_low_visibility",
        "detector": {"confidence_threshold": 0.5},
        "tracking": {"kalman": {"measurement_noise": 10.0}},
        "track_scoring": {"weights": {"detection_density": 0.2}},
    }

    resolved = apply_mission_profile(cfg)

    assert resolved["detector"]["confidence_threshold"] == 0.40
    assert resolved["tracking"]["kalman"]["measurement_noise"] == 25.0
    assert resolved["track_scoring"]["weights"]["detection_density"] == 0.45


def test_custom_profile_overrides_builtin_style() -> None:
    cfg = {
        "mission_profile": "custom_test",
        "mission_profiles": {
            "custom_test": {
                "detector": {"confidence_threshold": 0.33},
                "tracking": {"kalman": {"measurement_noise": 44.0}},
            }
        },
        "detector": {"confidence_threshold": 0.5},
        "tracking": {"kalman": {"measurement_noise": 10.0}},
    }

    resolved = apply_mission_profile(cfg)

    assert resolved["resolved_mission_profile"] == "custom_test"
    assert resolved["detector"]["confidence_threshold"] == 0.33
    assert resolved["tracking"]["kalman"]["measurement_noise"] == 44.0


def test_unknown_profile_raises() -> None:
    cfg = {"mission_profile": "does_not_exist"}

    try:
        apply_mission_profile(cfg)
    except ValueError as exc:
        assert "Unsupported mission_profile" in str(exc)
    else:
        raise AssertionError("Expected ValueError")