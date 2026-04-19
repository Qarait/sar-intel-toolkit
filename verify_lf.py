from pathlib import Path

for name in [
    "main.py",
    "planner.py",
    "detector.py",
    "telemetry.py",
    "fusion.py",
    "tracker.py",
    "requirements.txt",
    ".gitattributes",
]:
    data = Path(name).read_bytes()
    print(name)
    print("  working LF:", data.count(b"\n"))
    print("  working CR:", data.count(b"\r"))
    print("  working lines:", len(data.splitlines()))
    print("  first 120:", repr(data[:120]))
