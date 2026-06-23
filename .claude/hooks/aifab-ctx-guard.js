#!/usr/bin/env node
// aifab-ctx-guard.js — PostToolUse hook
// Enforces CLAUDE.md RULE 5 (컨텍스트 사용률 50% 유지).
// When `used_pct` >= 50, injects an advisory recommending /compact.
//
// Bridge file: /tmp/aifab-ctx-{session_id}.json (written by aifab-status.py).
// Format:
//   { "used_pct": <0–100>, "remaining_percentage": <0–100>, "timestamp": <epoch> }
//
// If GSD bridge file (/tmp/claude-ctx-{session_id}.json) exists, falls back to it
// — keeps single-source-of-truth even when GSD statusline is the one writing it.
//
// Exit code 0 always (advisory, never blocks).

const fs = require("fs");
const os = require("os");
const path = require("path");

const THRESHOLD_USED = 50;     // CLAUDE.md RULE 5
const CRITICAL_USED = 70;      // escalated phrasing past this point
const STALE_SECONDS = 60;
const DEBOUNCE_CALLS = 8;       // GSD uses 5; we're noisier-tolerant since threshold is lower

let input = "";
const stdinTimeout = setTimeout(() => process.exit(0), 5000);
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const sessionId = data.session_id;
    if (!sessionId || /[/\\]|\.\./.test(sessionId)) {
      process.exit(0);
    }

    const tmpDir = os.tmpdir();
    // Prefer aifab's own bridge file; fall back to GSD's if absent.
    const aifabPath = path.join(tmpDir, `aifab-ctx-${sessionId}.json`);
    const gsdPath = path.join(tmpDir, `claude-ctx-${sessionId}.json`);
    const metricsPath = fs.existsSync(aifabPath) ? aifabPath : fs.existsSync(gsdPath) ? gsdPath : null;
    if (!metricsPath) {
      process.exit(0);
    }

    const metrics = JSON.parse(fs.readFileSync(metricsPath, "utf8"));
    const now = Math.floor(Date.now() / 1000);
    if (metrics.timestamp && now - metrics.timestamp > STALE_SECONDS) {
      process.exit(0);
    }

    let usedPct = metrics.used_pct;
    if (typeof usedPct !== "number" && typeof metrics.remaining_percentage === "number") {
      usedPct = 100 - metrics.remaining_percentage;
    }
    if (typeof usedPct !== "number" || usedPct < THRESHOLD_USED) {
      process.exit(0);
    }

    // Debounce per (session, level)
    const warnPath = path.join(tmpDir, `aifab-ctx-${sessionId}-warned.json`);
    let warnData = { callsSinceWarn: 0, lastLevel: null };
    let firstWarn = true;
    if (fs.existsSync(warnPath)) {
      try {
        warnData = JSON.parse(fs.readFileSync(warnPath, "utf8"));
        firstWarn = false;
      } catch (_) {
        /* reset */
      }
    }
    warnData.callsSinceWarn = (warnData.callsSinceWarn || 0) + 1;

    const level = usedPct >= CRITICAL_USED ? "critical" : "warning";
    const escalated = level === "critical" && warnData.lastLevel === "warning";
    if (!firstWarn && warnData.callsSinceWarn < DEBOUNCE_CALLS && !escalated) {
      fs.writeFileSync(warnPath, JSON.stringify(warnData));
      process.exit(0);
    }
    warnData.callsSinceWarn = 0;
    warnData.lastLevel = level;
    fs.writeFileSync(warnPath, JSON.stringify(warnData));

    const msg =
      level === "critical"
        ? `[AI-Fab RULE 5] 컨텍스트 사용률 ${Math.round(usedPct)}% — 임계 (70%↑). ` +
          `현재 진행 중인 작업 단위만 마무리하고, 새 태스크 시작 전 반드시 /compact 실행. ` +
          `WORKLOG.md / feature-list.json 등 외재화된 상태에 진행 사항을 정리하라.`
        : `[AI-Fab RULE 5] 컨텍스트 사용률 ${Math.round(usedPct)}% — CLAUDE.md 50% 임계 초과. ` +
          `다음 태스크 시작 전 /compact 권장. 현재 단위 완료 후 자연 중단점에서 실행.`;

    const output = {
      hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext: msg,
      },
    };
    process.stdout.write(JSON.stringify(output));
    process.exit(0);
  } catch (_) {
    process.exit(0);
  }
});
