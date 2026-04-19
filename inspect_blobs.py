import subprocess

files = [
    "main.py",
    "planner.py",
    "detector.py",
    "telemetry.py",
    "fusion.py",
    "tracker.py",
    "requirements.txt",
    "README.md",
    ".gitattributes",
]

for name in files:
    try:
        data = subprocess.check_output(["git", "show", f"HEAD:{name}"])
    except subprocess.CalledProcessError:
        print(name, "MISSING")
        continue

    print(name)
    print("  blob LF:", data.count(b"\n"))
    print("  blob CR:", data.count(b"\r"))
    print("  blob first 120:", repr(data[:120]))
