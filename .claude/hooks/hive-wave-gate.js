#!/usr/bin/env node
// hive-wave-gate.js — PostToolUse hook (Bash matcher)
// Detects Wave commits (`feat(wave-N): ...`, any -m/-qm/-am/--message/heredoc form) and emits an advisory
// to run `/hive:security wave N` after a successful Wave commit.
//
// Advisory only — exit code 0 always. Never blocks execution.
// No shell execution, no eval, no file I/O.

let input = "";
const stdinTimeout = setTimeout(() => process.exit(0), 5000);
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);

    // Only act on Bash tool calls
    if (data?.tool_name !== "Bash") {
      process.exit(0);
    }

    const cmd = data?.tool_input?.command || "";

    // Guard: must contain a git commit invocation
    if (!/\bgit\s+commit\b/.test(cmd)) {
      process.exit(0);
    }

    // Guard: commit must have succeeded (exitCode 0 or success truthy)
    const resp = data?.tool_response || {};
    const exitCode = resp.exitCode;
    const success = resp.success;
    // If exitCode is explicitly non-zero, skip. If success is explicitly false, skip.
    if (exitCode !== undefined && exitCode !== 0 && exitCode !== null) {
      process.exit(0);
    }
    if (success !== undefined && success === false) {
      process.exit(0);
    }

    // Find `feat(wave-N)` at the start of a commit message anywhere after `git commit`.
    // Covers -m, -qm/-am (combined flags), --message=, single/double quotes and
    // heredoc bodies (-F - <<EOF) where the subject sits at a line start.
    const afterCommit = cmd.slice(cmd.search(/\bgit\s+commit\b/));
    const waveMatch = afterCommit.match(/(?:^|["'\s=])feat\(wave-(\d+)\)/m);
    if (!waveMatch) {
      process.exit(0);
    }

    const waveNum = waveMatch[1];
    const output = {
      hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext:
          `[HIVE] Wave ${waveNum} 커밋 감지 — 다음: \`/hive:security wave ${waveNum}\` 실행 권장.`,
      },
    };
    process.stdout.write(JSON.stringify(output));
    process.exit(0);
  } catch (_) {
    process.exit(0);
  }
});
