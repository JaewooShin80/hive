#!/usr/bin/env node
// hive-install.js — cross-platform HIVE installer core (macOS / Linux / Windows).
// Called by install.sh (bash) and install.ps1 (PowerShell); all logic lives here.
//
// Layout written under <base> (= <target>/.claude, or ~/.claude with --global):
//   commands/hive/*.md   slash commands (/hive:*), ../_shared links → absolute
//   hive/_shared/*.md    shared standards (outside commands/ so they are not loaded as commands)
//   hive/SKILLS.md
//   hooks/hive-*.js
//   workflows/*.js        saved Claude Code workflows (e.g. hive-wave, used by /hive:execute)
//   settings.json         additive merge: env, hooks, statusLine (`node "<abs>"` = shell-neutral)
// Scripts go to <target>/scripts (project) or ~/.claude/scripts/hive (global).

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const SRC = path.resolve(__dirname, "..");
const PLUGIN_SRC = path.join(SRC, ".claude", "plugins", "hive");
const HOOKS_SRC = path.join(SRC, ".claude", "hooks");
const WORKFLOWS_SRC = path.join(SRC, ".claude", "workflows");
const TEMPLATE_SETTINGS = path.join(SRC, ".claude", "settings.json");
const SCRIPTS = ["hive-status.js", "hive-status.py", "hive_progress.py", "gen_feature_list.py"];

// [event, matcher|null, file] — mirrors _shared/hooks.md
const HOOKS = [
  ["PreToolUse", "Write|Edit", "hive-secret-guard.js"],
  ["PreToolUse", "Bash", "hive-bash-guard.js"],
  ["PostToolUse", "Bash|Edit|Write|MultiEdit|Agent|Task", "hive-ctx-guard.js"],
  ["PostToolUse", "Edit|Write|MultiEdit", "hive-worklog-auto.js"],
  ["PostToolUse", "Bash", "hive-wave-gate.js"],
  ["SessionStart", null, "hive-session-start.js"],
];

const PINNED_MODEL = /claude-(opus|sonnet|haiku|fable)-\d/;
// pre-rename (AI-Fab) artifacts migrated on install
const LEGACY_HOOK = /aifab-(secret-guard|bash-guard|ctx-guard|worklog-auto|session-start|wave-gate)\.js/;

const USAGE = `Usage: install.sh [OPTIONS]      (Windows: .\\install.ps1 [OPTIONS])

Install HIVE harness into a project, or user-wide with --global.

OPTIONS:
  --target DIR    Install into DIR (default: current directory)
  --global        Install user-wide into ~/.claude (all projects) instead of a project
  --copy          Accepted for compatibility (files are always copied)
  --dry-run       Show what would be done without making changes
  -h, --help      Show this help

Behavior:
  - Skills      → <base>/commands/hive/*.md   (/hive:* commands)
  - Shared docs → <base>/hive/_shared/
  - Hooks       → <base>/hooks/hive-*.js, registered in settings.json
  - statusLine  → node "<scripts>/hive-status.js"
  - settings.json is merged additively (existing keys/values win); CLAUDE.md is never overwritten

Requires: node (hooks, installer), python3/python/py -3 (statusline, progress)
`;

function parseArgs(argv) {
  const opts = { target: process.cwd(), global: false, dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--target") {
      if (!argv[i + 1]) fail("--target requires a directory", 2);
      opts.target = argv[++i];
    } else if (a === "--global") opts.global = true;
    else if (a === "--copy") continue;
    else if (a === "--dry-run") opts.dryRun = true;
    else if (a === "-h" || a === "--help") {
      process.stdout.write(USAGE);
      process.exit(0);
    } else {
      process.stderr.write(`error: unknown flag: ${a}\n${USAGE}`);
      process.exit(2);
    }
  }
  return opts;
}

function fail(msg, code) {
  process.stderr.write(`error: ${msg}\n`);
  process.exit(code);
}

const posix = (p) => p.split(path.sep).join("/");
const nodeCmd = (p) => `node "${posix(p)}"`;

// Resolve the deepest existing ancestor so not-yet-created paths are checked too.
function realpathLoose(p) {
  let cur = path.resolve(p);
  const rest = [];
  while (!fs.existsSync(cur)) {
    rest.unshift(path.basename(cur));
    const parent = path.dirname(cur);
    if (parent === cur) break;
    cur = parent;
  }
  return path.join(fs.realpathSync(cur), ...rest);
}

function insideSource(p) {
  const real = realpathLoose(p);
  const src = fs.realpathSync(SRC);
  return real === src || real.startsWith(src + path.sep);
}

function detectPython() {
  for (const [cmd, ...pre] of [["python3"], ["python"], ["py", "-3"]]) {
    const r = spawnSync(cmd, [...pre, "--version"], { encoding: "utf8" });
    if (!r.error && r.status === 0 && /Python 3/.test(r.stdout + r.stderr)) {
      return [cmd, ...pre].join(" ");
    }
  }
  return null;
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const dry = opts.dryRun;
  const say = (m) => process.stdout.write((dry ? "[dry-run] " : "") + m + "\n");

  let target = null;
  let base;
  let scriptsDir;
  if (opts.global) {
    base = path.join(os.homedir(), ".claude");
    scriptsDir = path.join(base, "scripts", "hive");
  } else {
    target = path.resolve(opts.target);
    if (fs.existsSync(target) && fs.realpathSync(target) === fs.realpathSync(SRC)) {
      fail(`target equals harness source (${target}); choose a different --target`, 4);
    }
    base = path.join(target, ".claude");
    scriptsDir = path.join(target, "scripts");
  }
  const cmdDir = path.join(base, "commands", "hive");
  const sharedRoot = path.join(base, "hive");
  const hooksDir = path.join(base, "hooks");
  const workflowsDir = path.join(base, "workflows");
  const settingsPath = path.join(base, "settings.json");

  for (const p of [cmdDir, sharedRoot, hooksDir, workflowsDir, scriptsDir, settingsPath]) {
    if (insideSource(p)) {
      fail(
        `${p} resolves into the harness source (${SRC}), e.g. via a symlink. ` +
          "Remove that link first; the installer will not overwrite the source.",
        5,
      );
    }
  }

  say(`→ source: ${SRC}`);
  say(`→ base:   ${base}`);

  const mkdir = (d) => dry || fs.mkdirSync(d, { recursive: true });
  const write = (f, data) => dry || fs.writeFileSync(f, data, "utf8");
  const copy = (from, to) => dry || fs.copyFileSync(from, to);

  // 1. scripts
  mkdir(scriptsDir);
  for (const name of SCRIPTS) copy(path.join(SRC, "scripts", name), path.join(scriptsDir, name));
  say(`  scripts → ${scriptsDir}`);

  // 2. shared docs + SKILLS.md (outside commands/)
  const sharedDir = path.join(sharedRoot, "_shared");
  mkdir(sharedDir);
  for (const f of fs.readdirSync(path.join(PLUGIN_SRC, "_shared"))) {
    copy(path.join(PLUGIN_SRC, "_shared", f), path.join(sharedDir, f));
  }
  copy(path.join(PLUGIN_SRC, "SKILLS.md"), path.join(sharedRoot, "SKILLS.md"));
  say(`  shared docs → ${sharedRoot}`);

  // 3. skills as commands, with links/paths rewritten to the installed locations
  const python = detectPython();
  if (!python) say("  ! python3/python/py not found — statusline and /hive:progress need Python 3");
  mkdir(cmdDir);
  const skills = fs.readdirSync(path.join(PLUGIN_SRC, "skills")).filter((f) => f.endsWith(".md"));
  for (const f of skills) {
    let text = fs.readFileSync(path.join(PLUGIN_SRC, "skills", f), "utf8");
    text = text.split("](../_shared/").join(`](${posix(sharedDir)}/`);
    text = text.split("](../SKILLS.md)").join(`](${posix(path.join(sharedRoot, "SKILLS.md"))})`);
    for (const name of SCRIPTS.filter((n) => n.endsWith(".py"))) {
      const installed = posix(path.join(scriptsDir, name));
      text = text.split(`python3 scripts/${name}`).join(`${python || "python3"} "${installed}"`);
    }
    write(path.join(cmdDir, f), text);
  }
  say(`  ${skills.length} skills → ${cmdDir}`);

  // 4. hooks
  mkdir(hooksDir);
  for (const [, , file] of HOOKS) copy(path.join(HOOKS_SRC, file), path.join(hooksDir, file));
  say(`  ${HOOKS.length} hooks → ${hooksDir}`);

  // 4b. saved workflows (Claude Code reads <base>/workflows/*.js)
  mkdir(workflowsDir);
  const workflows = fs.readdirSync(WORKFLOWS_SRC).filter((f) => f.endsWith(".js"));
  for (const f of workflows) copy(path.join(WORKFLOWS_SRC, f), path.join(workflowsDir, f));
  say(`  ${workflows.length} workflows → ${workflowsDir}`);

  // 5. CLAUDE.md (project only, never overwritten)
  if (target) {
    const claudeMd = path.join(target, "CLAUDE.md");
    if (fs.existsSync(claudeMd)) say("  CLAUDE.md already present — preserved");
    else {
      copy(path.join(SRC, "CLAUDE.md"), claudeMd);
      say("  installed CLAUDE.md");
    }
  }

  // 6. settings.json additive merge
  const template = JSON.parse(fs.readFileSync(TEMPLATE_SETTINGS, "utf8"));
  let settings;
  if (fs.existsSync(settingsPath)) {
    settings = JSON.parse(fs.readFileSync(settingsPath, "utf8"));
  } else if (target) {
    settings = { ...template };
    delete settings.hooks;
    delete settings.statusLine;
  } else {
    settings = {};
  }

  settings.env = settings.env || {};
  // migrate pre-rename AIFAB_* env vars (user values win)
  for (const k of Object.keys(settings.env)) {
    if (!k.startsWith("AIFAB_")) continue;
    const renamed = "HIVE_" + k.slice("AIFAB_".length);
    if (!(renamed in settings.env)) settings.env[renamed] = settings.env[k];
    delete settings.env[k];
  }
  for (const [k, v] of Object.entries(template.env || {})) {
    if (k.startsWith("HIVE_") && !(k in settings.env)) settings.env[k] = v;
  }

  settings.hooks = settings.hooks || {};
  // drop hook entries pointing at pre-rename aifab-*.js files
  for (const event of Object.keys(settings.hooks)) {
    settings.hooks[event] = settings.hooks[event].filter(
      (entry) => !(entry.hooks || []).some((h) => LEGACY_HOOK.test(h.command || "")),
    );
    if (!settings.hooks[event].length) delete settings.hooks[event];
  }
  const registered = JSON.stringify(settings.hooks);
  for (const [event, matcher, file] of HOOKS) {
    if (registered.includes(file)) continue;
    const entry = { hooks: [{ type: "command", command: nodeCmd(path.join(hooksDir, file)) }] };
    if (matcher) entry.matcher = matcher;
    (settings.hooks[event] = settings.hooks[event] || []).push(entry);
  }

  const statusCmd = nodeCmd(path.join(scriptsDir, "hive-status.js"));
  const current = settings.statusLine && settings.statusLine.command;
  if (!current || current.includes("hive-status") || current.includes("aifab-status")) {
    settings.statusLine = { type: "command", command: statusCmd };
  } else {
    say(`  statusLine already set ("${current}") — preserved`);
  }

  mkdir(base);
  write(settingsPath, JSON.stringify(settings, null, 2) + "\n");
  say(`  settings merged → ${settingsPath}`);

  const pinned = [settings.model, ...Object.values(settings.env)].filter(
    (v) => typeof v === "string" && PINNED_MODEL.test(v),
  );
  if (pinned.length) {
    say(`  ! pinned model id(s) ${pinned.join(", ")} — use aliases (opus/sonnet/haiku) to auto-track the latest models`);
  }

  const legacyCmds = path.join(base, "commands", "aifab");
  if (fs.existsSync(legacyCmds)) {
    say(`  ! old ${posix(legacyCmds)} still provides /aifab:* commands — delete it after checking (renamed to /hive:*)`);
  }

  say("");
  say("✓ HIVE harness installed. Restart Claude Code, then try /hive:discover");
}

main();
