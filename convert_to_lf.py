from pathlib import Path

text_names = {".gitignore", ".gitattributes"}
text_suffixes = {".py", ".txt", ".md", ".yaml", ".yml", ".json"}

for path in Path(".").rglob("*"):
    if ".git" in path.parts:
        continue
    if path.is_dir():
        continue
    if path.name not in text_names and path.suffix not in text_suffixes:
        continue

    data = path.read_bytes()
    if b"\0" in data:
        continue

    text = data.decode("utf-8")

    # Important: explicitly handle CR-only, not just CRLF.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip("\n") + "\n")

    print("rewrote", path)
