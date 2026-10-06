#!/usr/bin/env node
// hive-session-start.js — SessionStart hook
// Prints current Wave + progress when a new session begins in an HIVE project.
//
// Detects HIVE: checks for ROADMAP.md + PLAN.md + WORKLOG.md in cwd.
// Parses PLAN.md Wave headers and checkboxes to compute progress.
// Emits hookSpecificOutput JSON to stdout. Always exits 0.
//
// Security: only reads inside cwd, rejects root/empty cwd, 1 MB PLAN.md cap.

const fs = require("fs");
const path = require("path");

const MAX_PLAN_SIZE = 1024 * 1024; // 1 MB

/** Return all RegExp matches in text as an array (uses matchAll). */
function allMatches(re, text) {
  return Array.from(text.matchAll(re));
}

let input = "";
const stdinTimeout = setTimeout(() => process.exit(0), 5000);
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    // Use raw cwd for fs.join; also works on Windows with backslash paths
    const raw = data.cwd || process.cwd();

    // Path safety: reject empty or root/drive-root cwd
    if (!raw || raw === "/" || /^[A-Za-z]:[\\/]?$/.test(raw)) {
      process.exit(0);
    }

    // Check 3 sentinel files; if any missing, not an HIVE project
    for (const f of ["ROADMAP.md", "PLAN.md", "WORKLOG.md"]) {
      if (!fs.existsSync(path.join(raw, f))) process.exit(0);
    }

    // File size guard on PLAN.md
    const planPath = path.join(raw, "PLAN.md");
    if (fs.statSync(planPath).size > MAX_PLAN_SIZE) process.exit(0);

    const planText = fs.readFileSync(planPath, "utf8");

    // Find all Wave header positions
    const headerMatches = allMatches(/^## Wave (\d+):\s*(.+)$/gm, planText);
    if (headerMatches.length === 0) process.exit(0);

    const waves = headerMatches.map((m) => ({
      num: parseInt(m[1], 10),
      title: m[2].trim(),
      start: m.index,
    }));

    // Slice each Wave block and count checkboxes
    for (let i = 0; i < waves.length; i++) {
      const block = planText.slice(
        waves[i].start,
        i + 1 < waves.length ? waves[i + 1].start : planText.length
      );
      waves[i].checked = (block.match(/^- \[x\] /gm) || []).length;
      waves[i].unchecked = (block.match(/^- \[ \] /gm) || []).length;
    }

    const totalWaves = waves.length;
    const completedWaves = waves.filter((w) => w.checked > 0 && w.unchecked === 0).length;
    const pct = Math.floor((completedWaves / totalWaves) * 100);

    const cur = waves.find((w) => w.unchecked > 0);

    let msg;
    if (!cur) {
      msg = "[HIVE] 모든 Wave 완료 (" + totalWaves + "/" + totalWaves + ", 100%). "
           + "다음: /hive:milestone complete";
    } else {
      const waveTotal = cur.checked + cur.unchecked;
      const wavePct = Math.floor((cur.checked / waveTotal) * 100);
      msg = "[HIVE] 현재 Wave: " + cur.num + " / " + totalWaves + " — "
           + "Wave " + cur.num + ": " + cur.title
           + " (" + cur.checked + "/" + waveTotal + " 완료, " + wavePct + "%). "
           + "전체 진척: " + completedWaves + "/" + totalWaves + " Wave 완료 (" + pct + "%). "
           + "다음: /hive:execute";
    }

    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "SessionStart",
          additionalContext: msg,
        },
      })
    );
    process.exit(0);
  } catch (_) {
    process.exit(0);
  }
});
