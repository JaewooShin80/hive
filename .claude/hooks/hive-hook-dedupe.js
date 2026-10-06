// hive-hook-dedupe.js — shared helper (not registered as a hook itself).
//
// When HIVE is installed globally (~/.claude/hooks) AND the current project
// registers the same hook in its own .claude/settings(.local).json, Claude Code
// runs both copies: advisories print twice and worklog-auto appends twice.
// The global copy calls this helper and steps aside; the project copy wins.
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

/**
 * @param {string} cwd       project directory from the hook payload
 * @param {string} hookFile  __filename of the calling hook
 * @returns {boolean} true when the caller is the global copy and the project
 *                    registers a hook with the same file name
 */
module.exports = function shadowedByProject(cwd, hookFile) {
  try {
    const globalDir = path.join(os.homedir(), ".claude", "hooks");
    if (path.resolve(path.dirname(hookFile)) !== path.resolve(globalDir)) return false;
    if (!cwd) return false;
    const name = path.basename(hookFile);
    for (const f of ["settings.json", "settings.local.json"]) {
      const p = path.join(cwd, ".claude", f);
      if (fs.existsSync(p) && fs.readFileSync(p, "utf8").includes(name)) return true;
    }
  } catch (_) {
    // never block a hook because of the dedupe check
  }
  return false;
};
