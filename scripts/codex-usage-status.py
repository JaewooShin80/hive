#!/usr/bin/env python3
"""Print the latest Codex token usage from the local Codex TUI log."""

from __future__ import annotations

import os
import re
from pathlib import Path


DEFAULT_LOG = Path.home() / ".codex" / "log" / "codex-tui.log"
TOKEN_RE = re.compile(r"codex\.turn\.token_usage\.([a-z_]+)=([0-9]+)")
MODEL_RE = re.compile(r"\bmodel=([^\s}:]+)")


def fmt(n: int | None) -> str:
    if n is None:
        return "-"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}m"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def latest_usage(log_path: Path) -> tuple[str | None, dict[str, int]] | None:
    if not log_path.exists():
        return None

    latest_line = None
    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if TOKEN_RE.search(line):
                    latest_line = line
    except OSError:
        return None

    if latest_line is None:
        return None

    usage: dict[str, int] = {}
    for key, value in TOKEN_RE.findall(latest_line):
        usage[key] = int(value)

    model_match = MODEL_RE.search(latest_line)
    model = model_match.group(1) if model_match else None
    return model, usage


def main() -> None:
    log_path = Path(os.environ.get("CODEX_TUI_LOG", DEFAULT_LOG))
    result = latest_usage(log_path)
    if result is None:
        print("Codex usage: -")
        return

    model, usage = result
    model_part = model or "model"
    input_tokens = usage.get("input_tokens")
    cached = usage.get("cached_input_tokens")
    output = usage.get("output_tokens")
    reasoning = usage.get("reasoning_output_tokens")
    total = usage.get("total_tokens")

    print(
        f"Codex {model_part} | "
        f"in {fmt(input_tokens)} cached {fmt(cached)} | "
        f"out {fmt(output)} r {fmt(reasoning)} | "
        f"total {fmt(total)}"
    )


if __name__ == "__main__":
    main()
