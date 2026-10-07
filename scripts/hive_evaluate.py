#!/usr/bin/env python3
"""Run feature-list.json `verify` checks and update each feature's status.

Fallback for /hive:evaluate when Playwright MCP is not available, usable in any
project (installed next to hive_progress.py).

  type=cmd : run target in the project root; exit 0 and stdout/stderr matching
             `assert` (regex, empty = any) → passing, otherwise failing,
             timeout → partial. Catastrophic commands are refused (failing).
  type=url : http(s) → GET and match the body; file:// or a relative path → read
             the file. Match → passing, no match → failing, network error → partial.
  no verify: manual area — status unchanged, reported as "manual".

Usage: python3 scripts/hive_evaluate.py [--wave N | --feature ID] [--file feature-list.json] [--timeout 30]
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Mirrors the catastrophic patterns of hooks/hive-bash-guard.js.
DANGER = [
    re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)[a-zA-Z]*\s+(/|~|\$HOME)(\s|$|/|\*)"),
    re.compile(r"\bgit\s+push\b[^;&|\n]*\s(--force(?!-with-lease)|-f)(\s|$)"),
    re.compile(r"\bgit\s+reset\s+--hard\b"),
    re.compile(r"\b(curl|wget)\b[^|;&\n]*\|\s*(sudo\s+)?(sh|bash|zsh|ksh)\b"),
    re.compile(r"\b(dd\s+[^|;&\n]*of=/dev/|mkfs\.)"),
    re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:"),
]


def check_cmd(target, pattern, root, timeout):
    if any(p.search(target) for p in DANGER):
        return "failing", "refused: dangerous command"
    try:
        r = subprocess.run(target, shell=True, cwd=root, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "partial", f"timeout after {timeout}s"
    if r.returncode != 0:
        return "failing", f"exit {r.returncode}"
    out = (r.stdout or "") + (r.stderr or "")
    return ("passing", "matched") if re.search(pattern or "", out) else ("failing", "no match")


def check_url(target, pattern, root, timeout):
    if target.startswith(("http://", "https://")):
        try:
            with urllib.request.urlopen(target, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
        except (urllib.error.URLError, OSError) as e:
            return "partial", f"network error: {e}"
    else:
        path = Path(target[len("file://"):]) if target.startswith("file://") else Path(root, target)
        if not path.exists():
            return "failing", f"missing {path}"
        body = path.read_text(encoding="utf-8", errors="replace")
    return ("passing", "matched") if re.search(pattern or "", body) else ("failing", "no match")


def main():
    # Korean/emoji output must not crash on a cp1252 (Windows) console.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="feature-list.json")
    ap.add_argument("--wave", type=int)
    ap.add_argument("--feature")
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()

    fl = Path(args.file)
    if not fl.exists():
        print(f"{fl} 없음. /hive:plan 으로 먼저 생성하세요.", file=sys.stderr)
        sys.exit(2)
    data = json.loads(fl.read_text(encoding="utf-8"))
    root = fl.resolve().parent

    counts = {"passing": 0, "failing": 0, "partial": 0, "manual": 0}
    selected = 0
    for f in data.get("features", []):
        if args.wave is not None and f.get("wave") != args.wave:
            continue
        if args.feature and f.get("id") != args.feature:
            continue
        selected += 1
        v = f.get("verify")
        if not v:
            counts["manual"] += 1
            print(f"feature {f['id']} ({f.get('title', '')}): manual (no verify)")
            continue
        check = check_cmd if v.get("type") == "cmd" else check_url
        status, why = check(v.get("target", ""), v.get("assert", ""), root, args.timeout)
        print(f"feature {f['id']} ({f.get('title', '')}): {f.get('status')} → {status} ({why})")
        f["status"] = status
        counts[status] += 1

    fl.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"evaluate 완료: {counts['passing']}/{selected} passing, {counts['failing']} failing, "
          f"{counts['partial']} partial, {counts['manual']} manual")


if __name__ == "__main__":
    main()
