#!/usr/bin/env node
// hive-status.js — cross-platform statusLine launcher (macOS / Linux / Windows)
// Pipes stdin JSON to hive-status.py using the first available Python 3:
//   python3 → python → py -3 (Windows launcher)
// Shell-neutral: works from bash, Git Bash, cmd and PowerShell.

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const script = path.join(__dirname, "hive-status.py");
const candidates = [["python3"], ["python"], ["py", "-3"]];

let input = "";
try {
  input = fs.readFileSync(0, "utf8");
} catch (_) {
  // no stdin — let the python side handle the empty payload
}

for (const [cmd, ...pre] of candidates) {
  const r = spawnSync(cmd, [...pre, script, ...process.argv.slice(2)], {
    input,
    encoding: "utf8",
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  // ENOENT = not installed; 9009 = Windows Store "python" stub
  if (r.error || r.status === 9009) continue;
  process.stdout.write(r.stdout || "");
  if (r.stderr) process.stderr.write(r.stderr);
  process.exit(r.status === null ? 1 : r.status);
}

process.stdout.write("HIVE (python3 not found)");
