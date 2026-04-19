from telemetry import TelemetryReplay, TelemetryState


def test_telemetry_replay_interpolates_and_clamps(tmp_path) -> None:
    csv_path = tmp_path / "telemetry.csv"
    csv_path.write_text(
        "timestamp,lat,lon,altitude_m,yaw_deg,pitch_deg,roll_deg\n"
        "2026-04-17T19:30:00Z,43.649000,-79.381000,60.0,90.0,0.0,0.0\n"
        "2026-04-17T19:30:02Z,43.650000,-79.380000,80.0,110.0,4.0,2.0\n",
        encoding="utf-8",
    )

    replay = TelemetryReplay(str(csv_path))

    before_start = replay.state_at(-1.0)
    halfway = replay.state_at(1.0)
    after_end = replay.state_at(5.0)

    assert before_start == TelemetryState(
        lat=43.649,
        lon=-79.381,
        altitude_m=60.0,
        yaw_deg=90.0,
        pitch_deg=0.0,
        roll_deg=0.0,
    )
    assert halfway == TelemetryState(
        lat=43.6495,
        lon=-79.3805,
        altitude_m=70.0,
        yaw_deg=100.0,
        pitch_deg=2.0,
        roll_deg=1.0,
    )
    assert after_end == TelemetryState(
        lat=43.65,
        lon=-79.38,
        altitude_m=80.0,
        yaw_deg=110.0,
        pitch_deg=4.0,
        roll_deg=2.0,
    )


def test_telemetry_replay_requires_expected_columns(tmp_path) -> None:
    csv_path = tmp_path / "telemetry.csv"
    csv_path.write_text(
        "timestamp,lat,lon,altitude_m\n"
        "2026-04-17T19:30:00Z,43.649000,-79.381000,60.0\n",
        encoding="utf-8",
    )

    try:
        TelemetryReplay(str(csv_path))
    except ValueError as exc:
        assert "missing required columns" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing telemetry columns")