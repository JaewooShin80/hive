#!/usr/bin/env node
// hive-worklog-auto.js — PostToolUse hook
// Auto-appends an entry to WORKLOG.md whenever the user edits/writes a file.
//
// Matchers: Edit | Write | MultiEdit
// Section: ## 자동 기록 (created at file end if absent).
// Guards: skip WORKLOG.md self-edit, outside-cwd, .git/, no WORKLOG.md in cwd.
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

    const toolName = data.tool_name || "";
    if (["Edit", "Write", "MultiEdit"].indexOf(toolName) === -1) {
      process.exit(0);
    }

    const filePath = (data.tool_input || {}).file_path;
    if (!filePath || typeof filePath !== "string") {
      process.exit(0);
    }

    const cwd = (typeof data.cwd === "string" && data.cwd) ? data.cwd : process.cwd();

    const resolvedFile = path.resolve(filePath);
    const resolvedCwd = path.resolve(cwd);

    // Path traversal / outside-cwd guard
    const rel = path.relative(resolvedCwd, resolvedFile);
    if (!rel || rel.startsWith("..") || path.isAbsolute(rel)) {
      process.exit(0);
    }

    // Skip .git/ noise
    if (rel.startsWith(".git" + path.sep) || rel === ".git") {
      process.exit(0);
    }

    // Skip WORKLOG.md self-edit (infinite loop guard)
    if (path.basename(resolvedFile) === WORKLOG_NAME &&
        path.dirname(resolvedFile) === resolvedCwd) {
      process.exit(0);
    }

    // Check WORKLOG.md exists in cwd
    const worklogPath = path.join(resolvedCwd, WORKLOG_NAME);
    if (!fs.existsSync(worklogPath)) {
      process.exit(0);
    }

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
