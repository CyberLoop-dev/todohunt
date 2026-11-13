#!/usr/bin/env python3
"""todohunt: find every TODO / FIXME / HACK in a codebase, with optional git age."""
import argparse
import json
import os
import re
import subprocess
import sys
import time

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
             "build", ".next", ".idea", ".vscode"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz",
            ".tar", ".woff", ".woff2", ".ttf", ".mp4", ".mp3", ".lock", ".pyc",
            ".so", ".exe", ".bin", ".min.js", ".map"}
COLORS = {"FIXME": "\033[91m", "HACK": "\033[95m", "XXX": "\033[93m", "TODO": "\033[96m"}
RESET = "\033[0m"


def make_regex(tags):
    return re.compile(r"(?:#|//|/\*|<!--|--|;)\s*(" + "|".join(tags) + r")\b[:\s(]*(.*)")


def is_text(path):
    try:
        with open(path, "rb") as f:
            return b"\0" not in f.read(2048)
    except OSError:
        return False


def find_hits(root, rx):
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if any(name.endswith(e) for e in SKIP_EXT):
                continue
            full = os.path.join(dirpath, name)
            if not is_text(full):
                continue
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            try:
                with open(full, encoding="utf-8", errors="replace") as f:
                    for n, line in enumerate(f, 1):
                        m = rx.search(line)
                        if m:
                            text = m.group(2).strip().rstrip("*/").rstrip("-->").strip()
                            hits.append({"file": rel, "line": n, "tag": m.group(1),
                                         "text": text[:120], "age_days": None})
            except OSError:
                continue
    return hits


def add_ages(root, hits):
    now = time.time()
    by_file = {}
    for h in hits:
        by_file.setdefault(h["file"], []).append(h)
    for rel, items in by_file.items():
        try:
            out = subprocess.run(["git", "-C", root, "blame", "--line-porcelain", "--", rel],
                                 capture_output=True, text=True, check=True).stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        times, cur = {}, None
        for line in out.splitlines():
            m = re.match(r"^[0-9a-f]{40} \d+ (\d+)", line)
            if m:
                cur = int(m.group(1))
            elif line.startswith("author-time ") and cur is not None:
                times[cur] = int(line.split()[1])
        for h in items:
            if h["line"] in times:
                h["age_days"] = int((now - times[h["line"]]) // 86400)


def fmt_age(d):
    if d is None:
        return "   -"
    if d < 60:
        return f"{d}d"
    if d < 730:
        return f"{d // 30}mo"
    return f"{d // 365}y"


def main():
    ap = argparse.ArgumentParser(description="Find TODO/FIXME/HACK comments.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--tags", nargs="+", default=["TODO", "FIXME", "HACK", "XXX"])
    ap.add_argument("--age", action="store_true", help="add git blame age (slower)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--max", type=int, help="exit 1 if more than N items are found")
    a = ap.parse_args()

    root = os.path.abspath(a.path)
    hits = find_hits(root, make_regex([t.upper() for t in a.tags]))
    if a.age:
        add_ages(root, hits)
        hits.sort(key=lambda h: -(h["age_days"] or -1))

    if a.json:
        print(json.dumps(hits, indent=2, ensure_ascii=False))
    else:
        groups = {}
        for h in hits:
            groups.setdefault(h["tag"], []).append(h)
        for tag in sorted(groups, key=lambda t: -len(groups[t])):
            print(f"\n{COLORS.get(tag, '')}{tag}{RESET}  ({len(groups[tag])})")
            for h in groups[tag]:
                age = f"{fmt_age(h['age_days']):>5}  " if a.age else ""
                print(f"  {age}{h['file']}:{h['line']}  {h['text']}")
        print(f"\n{len(hits)} item(s) found")

    if a.max is not None and len(hits) > a.max:
        sys.exit(1)


if __name__ == "__main__":
    main()
