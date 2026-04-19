gitattributes = """# Auto-detect text files and normalize line endings to LF
* text=auto

# Source/text files
*.py text eol=lf
*.txt text eol=lf
*.md text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
*.json text eol=lf
.gitignore text eol=lf
.gitattributes text eol=lf

# Binary files
*.pt binary
*.mp4 binary
*.jpg binary
*.jpeg binary
*.png binary
"""

requirements = """opencv-python>=4.5.0,<5.0.0
numpy>=1.19.0,<2.0.0
ultralytics>=8.0.0,<9.0.0
pyyaml>=5.3.0,<7.0.0
"""

with open(".gitattributes", "w", encoding="utf-8", newline="\n") as f:
    f.write(gitattributes)

with open("requirements.txt", "w", encoding="utf-8", newline="\n") as f:
    f.write(requirements)
