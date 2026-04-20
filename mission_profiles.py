from copy import deepcopy
from typing import Any, Dict


BUILT_IN_PROFILES: Dict[str, Dict[str, Any]] = {
    "sar_daylight": {
        "detector": {
            "confidence_threshold": 0.50,
        },
        "tracking": {
            "motion_model": "kalman",
            "kalman": {
                "process_noise": 1.0,
                "measurement_noise": 10.0,
                "initial_uncertainty": 100.0,
            },
        },
        "track_scoring": {
            "weights": {
                "mean_confidence": 0.55,
                "max_confidence": 0.25,
                "detection_density": 0.20,
            },
        },
    },
    "sar_low_visibility": {
        "detector": {
            "confidence_threshold": 0.40,
        },
        "tracking": {
            "motion_model": "kalman",
            "kalman": {
                "process_noise": 2.0,
                "measurement_noise": 25.0,
                "initial_uncertainty": 150.0,
            },
        },
        "track_scoring": {
            "weights": {
                "mean_confidence": 0.35,
                "max_confidence": 0.20,
                "detection_density": 0.45,
            },
        },
    },
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)

    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)

    return merged


def apply_mission_profile(config: Dict[str, Any]) -> Dict[str, Any]:
    profile_name = config.get("mission_profile")

    if not profile_name:
        return deepcopy(config)

    custom_profiles = config.get("mission_profiles", {}) or {}

    if profile_name in custom_profiles:
        profile = custom_profiles[profile_name]
    elif profile_name in BUILT_IN_PROFILES:
        profile = BUILT_IN_PROFILES[profile_name]
    else:
        available = sorted(set(BUILT_IN_PROFILES) | set(custom_profiles))
        raise ValueError(
            f"Unsupported mission_profile={profile_name!r}. "
            f"Available profiles: {available}"
        )

    resolved = deep_merge(config, profile)
    resolved["resolved_mission_profile"] = profile_name
    return resolved