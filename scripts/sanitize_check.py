from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", "__pycache__", ".pytest_cache"}
SELF = Path(__file__).resolve()
PATTERNS = {
    "private absolute path": re.compile(r"/Users/[A-Za-z0-9_.-]+/"),
    "internal IPv4": re.compile(r"\b(?:10|192\.168|172\.(?:1[6-9]|2[0-9]|3[01]))\.[0-9.]+\b"),
    "access token prefix": re.compile(r"\b(?:gho_|ghp_|sk-[A-Za-z0-9])"),
    "credentialed database URL": re.compile(r"(?:postgres|postgresql|mysql)://[^\s:@]+:[^\s@]+@"),
    "private service domain": re.compile(r"[A-Za-z0-9.-]+\.(?:gs-robot|gsbot)\.dev\b"),
}

for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.resolve() == SELF or any(part in EXCLUDED for part in path.parts):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for label, pattern in PATTERNS.items():
        if pattern.search(text):
            print(f"{label}: {path}")
            sys.exit(1)
print("sanitize check passed")
