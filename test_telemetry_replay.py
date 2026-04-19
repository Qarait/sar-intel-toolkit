from telemetry import TelemetryReplay
from datetime import datetime, timedelta

tr = TelemetryReplay("sample_data/telemetry.csv")
t0 = datetime.fromisoformat("2026-04-17T19:30:00+00:00")
state = tr.state_at(1.0, t0 + timedelta(seconds=1.0))

print(state)

assert "lat" in state
assert "lon" in state
assert "altitude_m" in state
assert abs(state["lon"] - (-79.3809)) < 1e-6

print("telemetry replay smoke test passed")
