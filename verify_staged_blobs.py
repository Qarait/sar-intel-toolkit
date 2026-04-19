import subprocess

for name in ["main.py", "requirements.txt", ".gitattributes"]:
    data = subprocess.check_output(["git", "show", f":{name}"])
    print(name)
    print("  staged LF:", data.count(b"\n"))
    print("  staged CR:", data.count(b"\r"))
    print("  staged lines:", len(data.splitlines()))
    print("  first 120:", repr(data[:120]))
