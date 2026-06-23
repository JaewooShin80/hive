#!/usr/bin/env node
// aifab-bash-guard.js — PreToolUse(Bash) hook
// Blocks catastrophic / hard-to-reverse bash commands.
//
// Exit codes:
//   0: allow
//   2: block (stderr → model)
//
// Patterns are intentionally narrow (anchored on flags + targets) to avoid
// false positives on legitimate commands.

const DANGER = [
  // Root / home wipes
  { re: /\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)[a-zA-Z]*\s+\/(\s|$)/, msg: "rm -rf / (root filesystem deletion)" },
  { re: /\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)[a-zA-Z]*\s+(~|\$HOME)(\s|$|\/)/, msg: "rm -rf $HOME" },
  { re: /\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)[a-zA-Z]*\s+\/\*/, msg: "rm -rf /*" },
  // Force push (allows --force-with-lease as safer alternative)
  { re: /\bgit\s+push\s+(?:[^\s]+\s+)*--force(?!-with-lease)(\s|$)/, msg: "git push --force (use --force-with-lease for safer overwrite)" },
  { re: /\bgit\s+push\s+(?:[^\s]+\s+)*-f(\s|$)/, msg: "git push -f (use --force-with-lease for safer overwrite)" },
  // World-writable
  { re: /\bchmod\s+-?R?\s*777\b/, msg: "chmod 777 (world-writable permission)" },
  // Pipe-to-shell from network
  { re: /\bcurl\b[^|;&\n]*\|\s*(sudo\s+)?(sh|bash|zsh|ksh)\b/, msg: "curl | sh (untrusted remote execution)" },
  { re: /\bwget\b[^|;&\n]*-O-?[^|;&\n]*\|\s*(sudo\s+)?(sh|bash|zsh|ksh)\b/, msg: "wget | sh (untrusted remote execution)" },
  // Disk wipes
  { re: /\bdd\s+[^|;&\n]*of=\/dev\/(sd[a-z]|nvme|hd[a-z]|xvd)/, msg: "dd to raw disk device" },
  { re: /\bmkfs\.[a-z0-9]+\s+\/dev\/(sd|nvme|hd|xvd)/, msg: "mkfs on raw disk device" },
  // Redirect to disk device
  { re: />\s*\/dev\/(sd[a-z]|nvme[0-9]|hd[a-z])/, msg: "redirect to raw disk device" },
  // Fork bomb
  { re: /:\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:/, msg: "fork bomb" },
  // History destruction
  { re: /\bgit\s+reflog\s+expire\b[^|;&\n]*--all\b/, msg: "git reflog expire --all (destroys recovery history)" },
];

let input = "";
const stdinTimeout = setTimeout(() => process.exit(0), 5000);
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const cmd = ((data.tool_input || {}).command || "").trim();
    if (!cmd) {
      process.exit(0);
    }

    for (const { re, msg } of DANGER) {
      if (re.test(cmd)) {
        const preview = cmd.length > 200 ? cmd.slice(0, 200) + "…" : cmd;
        process.stderr.write(
          `[aifab-bash-guard] BLOCKED: ${msg}\n` +
            `Command: ${preview}\n` +
            `If this is intentional, the user can run it directly from their terminal ` +
            `(prefix with '!' in the Claude Code prompt) so it is performed under their explicit confirmation.\n`,
        );
        process.exit(2);
      }
    }

    process.exit(0);
  } catch (e) {
    process.exit(0);
  }
});
