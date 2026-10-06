#!/usr/bin/env node
// hive-worklog-auto.js — PostToolUse hook
// Auto-appends an entry to WORKLOG.md whenever the user edits/writes a file.
//
// Matchers: Edit | Write | MultiEdit
// Section: ## 자동 기록 (created at file end if absent).
// Guards: skip WORKLOG.md self-edit, .git/, and files with no WORKLOG.md up to their git root.
// Exit code: always 0 (advisory, never blocks).

const fs = require("fs");
const path = require("path");

const SECTION_HEADER = "## 자동 기록";
const WORKLOG_NAME = "WORKLOG.md";

function zeroPad(n) {
  return String(n).padStart(2, "0");
}

function formatNow() {
  const d = new Date();
  return d.getFullYear() + "-" +
    zeroPad(d.getMonth() + 1) + "-" +
    zeroPad(d.getDate()) + " " +
    zeroPad(d.getHours()) + ":" +
    zeroPad(d.getMinutes());
}

let input = "";
const stdinTimeout = setTimeout(function() { process.exit(0); }, 5000);
process.stdin.setEncoding("utf8");
process.stdin.on("data", function(c) { input += c; });
process.stdin.on("end", function() {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    // Global copy steps aside when the project registers the same hook (no double runs).
    try { if (require("./hive-hook-dedupe")(data.cwd || process.cwd(), __filename)) process.exit(0); } catch (_) {}

    const toolName = data.tool_name || "";
    if (["Edit", "Write", "MultiEdit"].indexOf(toolName) === -1) {
      process.exit(0);
    }

    const filePath = (data.tool_input || {}).file_path;
    if (!filePath || typeof filePath !== "string") {
      process.exit(0);
    }

    const resolvedFile = path.resolve(filePath);

    // Project root = nearest ancestor of the edited file that has WORKLOG.md,
    // searching up to (and including) the first directory with a .git entry.
    // Works when the session was opened in another folder than the project.
    let projectRoot = null;
    let dir = path.dirname(resolvedFile);
    for (;;) {
      if (fs.existsSync(path.join(dir, WORKLOG_NAME))) { projectRoot = dir; break; }
      const parent = path.dirname(dir);
      if (fs.existsSync(path.join(dir, ".git")) || parent === dir) break;
      dir = parent;
    }
    if (!projectRoot) {
      process.exit(0);
    }

    const rel = path.relative(projectRoot, resolvedFile);
    if (!rel || rel.startsWith("..") || path.isAbsolute(rel)) {
      process.exit(0);
    }

    // Skip .git/ noise
    if (rel.startsWith(".git" + path.sep) || rel === ".git") {
      process.exit(0);
    }

    // Skip WORKLOG.md self-edit (infinite loop guard)
    if (rel === WORKLOG_NAME) {
      process.exit(0);
    }

    const worklogPath = path.join(projectRoot, WORKLOG_NAME);

    // Normalise separators to forward-slash (cross-platform)
    const relFwd = rel.split(path.sep).join("/");
    const entry = "- " + formatNow() + " " + relFwd;
    const existing = fs.readFileSync(worklogPath, "utf8");

    if (existing.indexOf(SECTION_HEADER) !== -1) {
      // Section exists: append at file end
      const tail = existing.charAt(existing.length - 1) === String.fromCharCode(10) ? "" : String.fromCharCode(10);
      fs.appendFileSync(worklogPath, tail + entry + String.fromCharCode(10));
    } else {
      // Section missing: create at file end
      const tail = existing.charAt(existing.length - 1) === String.fromCharCode(10) ? "" : String.fromCharCode(10);
      fs.appendFileSync(worklogPath, tail + String.fromCharCode(10) + SECTION_HEADER + String.fromCharCode(10) + String.fromCharCode(10) + entry + String.fromCharCode(10));
    }

    process.exit(0);
  } catch (_) {
    process.exit(0);
  }
});
