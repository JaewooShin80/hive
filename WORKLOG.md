# WORKLOG — AI-Fab Harness Hardening (v2.2.0)

> 작업일지. 각 Wave 시작/종료, 결정, 이슈, 재개 지점을 시간순으로 기록.

---

## 2026-06-23 — 마일스톤 v2.2.0 착수

**컨텍스트:** 직전에 statusline 2-line Powerline 작업 완료(commit `75d44d8`, GitHub+GitLab 푸시 완료). 이어서 하네스 고도화 리서치 진행.

**리서치 산출물:**
- 현재 AI-Fab 스킬 인벤토리 (16 스킬, 6 카테고리, `_shared/` 5종 표준)
- 2025–2026 하네스 트렌드 (Ralph / Anthropic 3-agent / Compound / SDD / Aider / Superpowers / GSD 등)
- 입증된 메타 패턴 22종 매트릭스
- 입증된 실패 모드 6종 (Reflexion / multi-agent 토큰 폭발 / fan-out 한계 / context drift / SlopCodeBench / SDK auto-compact 단독)

**의사결정 (사용자 컨펌):**
- 진행 노선: **A(Hooks) → B(Feature List + Evaluator)**
- GSD hooks 9종 보존, AI-Fab은 `aifab-*` 네임스페이스로 병행
- 글로벌(보안) + 프로젝트(워크플로우) 분리 설치
- 이 작업 자체를 ROADMAP v2.2.0으로 dogfooding

**작성 파일:**
- ROADMAP.md (Phase 1: Wave 1-3, Phase 2: Wave 4-6)
- PLAN.md (6 Wave 상세 + 검증 기준)
- WORKLOG.md (이 파일)

**다음 액션:** Wave 1 — 글로벌 보안/제어 hooks 구현
- `~/.claude/hooks/aifab-secret-guard.js`
- `~/.claude/hooks/aifab-bash-guard.js`
- `~/.claude/hooks/aifab-ctx-guard.js`

**현재 Wave:** 1 (착수 직전)

---

## 2026-06-23 — Wave 1 진입

**조정 사항 (RULE 1 가정 명시):**
- 3개 hook 모두 `.js`로 변경 — Bash + node embedded JSON 파싱은 escape 취약. GSD가 동일 패턴 따름.
- `aifab-ctx-guard`는 **Stop → PostToolUse**로 변경. Stop hook은 사용자 advisory 메커니즘 깨끗하지 않음. PostToolUse의 `additionalContext` 출력이 표준.
- 브릿지 파일 `/tmp/aifab-ctx-{session_id}.json` 신설 (GSD `/tmp/claude-ctx-*` 와 분리). aifab-status.py가 동시 작성. → ctx-guard가 GSD statusline 없이도 독립 동작.
- 임계값: GSD가 35% remaining(=65% used)에서 fire. AI-Fab은 **50% used** (CLAUDE.md RULE 5 준수). GSD보다 먼저 fire → 보완.

---

## 2026-06-23 — Wave 1 완료

**산출물 (모두 작성·검증 완료):**
- `~/.claude/hooks/aifab-secret-guard.js` — PreToolUse(Write/Edit) 시크릿 가드
- `~/.claude/hooks/aifab-bash-guard.js` — PreToolUse(Bash) 위험 명령 가드
- `~/.claude/hooks/aifab-ctx-guard.js` — PostToolUse 컨텍스트 50% RULE 5 가드
- `scripts/aifab-status.py` + 글로벌 사본 — `write_ctx_bridge()` 함수 추가, `main()`에서 호출. path-traversal 거부, OSError 무음 처리

**스모크 테스트 결과 (12/12 통과):**
- secret-guard: ghp_ 토큰 차단 / `.env` 경로 차단 / `.env.example` 허용 / clean 허용
- bash-guard: `rm -rf /` 차단 / `git push --force` 차단 / `--force-with-lease` 허용 / `ls -la` 허용
- ctx-guard: bridge 없으면 무음 / 65% warning / 75% critical / 30% 무음 / `../etc/passwd` session_id 거부
- E2E: aifab-status.py가 `remaining=30` 입력 받아 bridge에 `used_pct=71.86` 기록 → ctx-guard가 동일 파일 읽어 84% (auto-compact 보정 후) critical 메시지 emit

**다음 액션:** Wave 1 commit → settings.json 등록은 Wave 3에서 일괄 처리 (현재 hooks는 작성만 되어 있고 등록 전이라 실 환경 영향 없음).

**다음 Wave:** Wave 2 — 프로젝트 워크플로우 hooks (worklog-auto, session-start, wave-gate)

**보안 검토 (`/aifab:security wave 1`):**
- ❌ 치명적: 0 / ⚠️ 경고: 1 / ℹ️ 정보: 3 / ✅ 통과: 10
- **Verdict:** APPROVE_WITH_NITS — Wave 1 그대로 통과
- **Wave 3 deferred (사용자 결정 B):**
  - `aifab-secret-guard.js:88` stderr preview 10자 → 4자로 단축 (Low-risk secret leak in transcript log)
  - `aifab-bash-guard.js:52` 동일 — command preview 길이 검토
  - `aifab-status.py:write_ctx_bridge` Windows 금지 문자(`:*?<>|`) 가드 강화 (선택)

---

## 2026-06-24 — Wave 2 시작

**RULE 1 확정 (사용자 컨펌):**
- A: 3개 모두 `.js`로 통일 (`.sh` 폐기) — Windows 호환 + escape 안전 (Wave 1 결정과 일관)
- B: 글로벌(`~/.claude/hooks/`) + 프로젝트(`.claude/hooks/`) 양쪽 미러 — Wave 1 패턴 유지

**작업 목록 (1차 Sonnet → 사용자 지시로 Opus 재실행, 최종 Opus 감사 통과):**
- [x] [Opus] `aifab-worklog-auto.js` — PostToolUse(Edit|Write|MultiEdit) → WORKLOG.md "## 자동 기록" append
- [x] [Opus] `aifab-session-start.js` — SessionStart → 현재 Wave + 진척% 출력
- [x] [Opus] `aifab-wave-gate.js` — PostToolUse(Bash[git commit]) → /aifab:security 안내

**Opus 감사 결정사항:** 3개 hook 모두 Sonnet 구현이 스펙 통과 → byte-identical 유지 (rewrite 불필요).

**스모크 테스트 결과 (15/15 통과):**
- worklog-auto 5/5: 섹션 append / 섹션 자동 생성 / self-edit 차단 / no-worklog 무음 / 외부경로 차단
- session-start 4/4: 실프로젝트 Wave 2/6 16% / 비-AI-Fab dir 무음 / 모든 Wave 완료 / 부분 33%
- wave-gate 6/6: double-quoted / single-quoted / heredoc / 일반 feat 무시 / 비-commit 무시 / 실패 commit 무시

**산출물 (글로벌 + 프로젝트 byte-identical 미러):**
- `~/.claude/hooks/aifab-worklog-auto.js` (3151 B)
- `~/.claude/hooks/aifab-session-start.js` (3460 B)
- `~/.claude/hooks/aifab-wave-gate.js` (2725 B)
- `D:\lap\26..05-aifab\.claude\hooks\aifab-*.js` (동일 3개)

**상태:** 완료 ✓

**다음 액션:** Wave 2 commit → Wave 3 (settings.json 등록 + docs + e2e). 현재는 등록 전이라 hooks가 실 환경에 작용하지 않음.

**다음 Wave:** Wave 3 — 등록 + 문서 + 통합 테스트 (`_shared/hooks.md`, CLAUDE.md Hooks 섹션, 5개 e2e 시나리오)
