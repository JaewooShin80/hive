#!/usr/bin/env node
// hive-secret-guard.js — PreToolUse(Write|Edit) hook
// Blocks Writes/Edits containing secret patterns or targeting secret file paths.
//
// Exit codes:
//   0: allow (no secret detected, parse error, or fast-path skip)
//   2: block (secret detected — stderr message shown to model)
//
// Behavior: hard block. CLAUDE.md security defaults — secrets must NEVER
// be hardcoded; use environment variables.

const SECRET_PATTERNS = [
  // GitHub / GitLab tokens
  { re: /\bghp_[A-Za-z0-9]{30,}\b/, name: "GitHub PAT (ghp_)" },
  { re: /\bgho_[A-Za-z0-9]{30,}\b/, name: "GitHub OAuth (gho_)" },
  { re: /\bghs_[A-Za-z0-9]{30,}\b/, name: "GitHub Server token (ghs_)" },
  { re: /\bglpat-[A-Za-z0-9_-]{15,}\b/, name: "GitLab PAT (glpat-)" },
  // AWS
  { re: /\bAKIA[0-9A-Z]{16}\b/, name: "AWS Access Key ID (AKIA)" },
  { re: /aws_secret_access_key\s*=\s*['"][^'"\s]{30,}/i, name: "AWS Secret Access Key" },
  // OpenAI / Anthropic / Stripe
  { re: /\bsk-ant-api03-[A-Za-z0-9_-]{20,}\b/, name: "Anthropic API key" },
  { re: /\bsk-[A-Za-z0-9]{40,}\b/, name: "OpenAI-style sk- key" },
  { re: /\bsk_live_[A-Za-z0-9]{20,}\b/, name: "Stripe live key" },
  { re: /\bsk_test_[A-Za-z0-9]{20,}\b/, name: "Stripe test key" },
  // Slack
  { re: /\bxox[bpoa]-[A-Za-z0-9-]{10,}\b/, name: "Slack token" },
  // Private keys
  { re: /-----BEGIN (RSA |EC |DSA |OPENSSH |)?PRIVATE KEY-----/, name: "Private key block" },
  // Generic env-style high-entropy assignment
  { re: /^[A-Z][A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD|API_KEY)\s*=\s*['"]?[A-Za-z0-9+/=_-]{20,}/m, name: "Env-style secret assignment" },
];

const SECRET_PATH_PATTERNS = [
  /(^|[\\/])\.env(\.[A-Za-z0-9_-]+)?$/,            // .env, .env.local, .env.production
  /(^|[\\/])id_(rsa|ed25519|ecdsa|dsa)$/,           // SSH private keys
  /(^|[\\/])[^/\\]+\.(pem|key|p12|pfx|jks|keystore)$/i,
  /(^|[\\/])credentials(\.json|\.yaml|\.yml)?$/i,
  /(^|[\\/])secrets?\.(json|yaml|yml|toml)$/i,
];

// Allow common example/template variants
const PATH_ALLOWLIST = [
  /\.env\.(example|sample|template|dist|test)$/i,
  /\.env\.example\.[A-Za-z0-9_-]+$/i,
];

let input = "";
const stdinTimeout = setTimeout(() => process.exit(0), 5000);
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const ti = data.tool_input || {};
    const filePath = ti.file_path || "";
    // Write tool uses 'content'; Edit uses 'new_string' (and 'old_string'); MultiEdit uses 'edits'
    const candidates = [
      ti.content,
      ti.new_string,
      Array.isArray(ti.edits) ? ti.edits.map((e) => e.new_string || "").join("\n") : "",
    ].filter(Boolean);
    const content = candidates.join("\n");

    // Path-based block (unless allowlisted)
    if (filePath && !PATH_ALLOWLIST.some((re) => re.test(filePath))) {
      for (const re of SECRET_PATH_PATTERNS) {
        if (re.test(filePath)) {
          process.stderr.write(
            `[hive-secret-guard] BLOCKED: '${filePath}' matches a secret file pattern. ` +
              `Secret files must not be written by the agent. ` +
              `Use environment variables (e.g. via process.env or a runtime secret manager) ` +
              `and reference them from code instead.\n`,
          );
          process.exit(2);
        }
      }
    }

    // Content-based block
    if (content) {
      for (const { re, name } of SECRET_PATTERNS) {
        const m = content.match(re);
        if (m) {
          const preview = m[0].slice(0, 10) + "…";
          process.stderr.write(
            `[hive-secret-guard] BLOCKED: ${name} detected in content ("${preview}"). ` +
              `Remove the literal value. Load it from an environment variable instead.\n`,
          );
          process.exit(2);
        }
      }
    }

    process.exit(0);
  } catch (e) {
    // Never block on parse error — fail open for safety of legitimate work
    process.exit(0);
  }
});
