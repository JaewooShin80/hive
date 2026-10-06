# PLAN — v2.2.0 HIVE Harness Hardening

> 6 Wave, 2 Phase. ROADMAP.md의 Phase 1(Wave 1-3) + Phase 2(Wave 4-6).
> 각 Wave 종료 시 `git commit` + (Wave 1-3은) `/hive:security` 실행.
> Wave 완료 마킹: 체크리스트 `[x]`.

---

## Wave 1: 글로벌 보안/제어 hooks

**목표:** `~/.claude/hooks/`에 모든 프로젝트가 공유할 안전장치 3종 추가.

**산출물:**
- [x] `hive-secret-guard.js` — PreToolUse(Write|Edit), 시크릿 패턴(`ghp_/gho_/ghs_/glpat-/AKIA/sk-ant-/sk_live_/xox/PEM`) + 경로(`.env/*.key/*.pem/credentials`) 차단(exit 2). `.env.example` 등 allowlist 적용.
- [x] `hive-bash-guard.js` — PreToolUse(Bash), `rm -rf /|git push --force|chmod 777|curl|sh|dd of=/dev/|mkfs|fork bomb` 차단(exit 2). `--force-with-lease`는 허용.
- [x] `hive-ctx-guard.js` — **PostToolUse**(Stop→변경, RULE 1), 자체 브릿지 `/tmp/hive-ctx-{session_id}.json` 사용(GSD `/tmp/claude-ctx-*` fallback). 50% used → warning, 70% → critical. debounce 8 calls, stale 60s.
- [x] `hive-status.py` — bridge writer `write_ctx_bridge()` 추가, `main()`에서 ctx_pct 계산 직후 호출. path-traversal 가드 포함.

**검증:**
- [x] secret-guard: `ghp_` 토큰 content → exit 2, `.env` 경로 → exit 2, `.env.example` → exit 0, clean → exit 0 (4/4)
- [x] bash-guard: `rm -rf /` → exit 2, `git push --force` → exit 2, `--force-with-lease` → exit 0, `ls -la` → exit 0 (4/4)
- [x] ctx-guard: <50% → 무출력, 65% → warning JSON, 75% → critical JSON, path-traversal → 무시 (4/4)
- [x] E2E: hive-status.py가 bridge 작성 → ctx-guard가 동일 파일 consume → 84% critical 메시지 emit
- [x] GSD hook과 네임스페이스 분리(`/tmp/hive-ctx-*` vs `/tmp/claude-ctx-*`) → 충돌 없음

**커밋:** `feat(hooks): add global safety hooks (secret/bash/ctx) + bridge writer`

---

## Wave 2: 프로젝트 워크플로우 hooks

**목표:** `.claude/hooks/`에 HIVE 워크플로우 강제 hook 3종.

**산출물:**
- [x] `hive-worklog-auto.js` — PostToolUse(Edit|Write|MultiEdit), WORKLOG.md "## 자동 기록" 섹션에 `{date} {file}` append (RULE 1: .sh → .js 통일, Windows 호환)
- [x] `hive-session-start.js` — SessionStart, ROADMAP/PLAN/WORKLOG 존재 시 현재 Wave + 진척% 출력 (RULE 1: .sh → .js 통일)
- [x] `hive-wave-gate.js` — PostToolUse(Bash[git commit]), 커밋 메시지에 `feat(wave-N)` 포함 시 "다음: `/hive:security wave N`" 알림

**검증 (15/15 통과):**
- [x] worklog-auto: 섹션 존재시 append (1) / 섹션 없으면 생성 (2) / WORKLOG.md self-edit 차단 (3) / WORKLOG.md 없는 cwd 무음 (4) / cwd 밖 경로 차단 (5)
- [x] session-start: 실제 프로젝트 Wave 2/6 16% 출력 (1) / 비-HIVE dir 무음 (2) / 모든 Wave 완료 메시지 (3) / 부분 진척 Wave 2/3 33% (4)
- [x] wave-gate: double-quoted (1) / single-quoted (2) / heredoc (3) / 일반 feat 무시 (4) / 비-commit 무시 (5) / 실패 commit 무시 (6)
- [x] 글로벌(`~/.claude/hooks/`)과 프로젝트(`.claude/hooks/`) 양쪽 byte-identical 미러 확인

**커밋:** `feat(hooks): add project workflow hooks (worklog/session/wave-gate)`

---

## Wave 3: 등록 + 문서 + 통합 테스트

**목표:** settings.json 등록, `_shared/hooks.md` 작성, e2e 시나리오 통과.

**산출물:**
- [x] `~/.claude/settings.json` hooks 블록에 hive-* 6개 추가 (GSD 보존)
- [x] `.claude/plugins/hive/_shared/hooks.md` — 각 hook 역할/exit code/비활성 방법
- [x] CLAUDE.md "## Hooks" 섹션 추가, `_shared/hooks.md` 링크

**검증 (5개 e2e 시나리오 통과):**
- [x] (1) `.env`에 secret 쓰기 시도 → 차단 (exit 2)
- [x] (2) `rm -rf /` 시도 → 차단 (exit 2)
- [x] (3) 신규 세션 → SessionStart hook이 Wave 3 / 6 출력
- [x] (4) Edit 후 WORKLOG.md auto-append 확인 (L81 substring 매칭 info-level 이슈 라이브 검출)
- [x] (5) ctx 78% → PostToolUse(ctx-guard) critical advisory (실제 세션에서 자체 검증)

**커밋:** `feat(hooks): register hive hooks + docs + e2e tests`
**Phase 1 완료 커밋:** `chore(milestone): Phase 1 complete (Hooks)`

---

## Wave 4: feature-list.json 스키마 + plan 통합

**목표:** PLAN.md와 짝이 되는 외재화 검증 파일 도입.

**산출물:**
- [x] `.claude/plugins/hive/_shared/feature-list-schema.md` — JSON 스키마 + status enum + graceful 규약
- [x] `/hive:plan` 스킬 양쪽 미러 갱신 (plugins/hive/skills + commands/hive) — 7-1/7-2 단계 분리, 9단계 메시지 갱신, 8506 bytes byte-identical
- [x] `scripts/hive_progress.py` 확장: FeatureList dataclass + parse_feature_list + short/dashboard/json 출력에 features_passing/features_total

**검증 (3/3 시나리오 통과):**
- [x] mock feature-list.json 4 entry(2 passing) → dashboard "🎯 기능 검증: 2/4 passing (50%)", short "F2/4", json features_passing=2/features_total=4
- [x] feature-list.json 부재 → 기존 동작 (feature 라인/필드 미출력)
- [x] 스키마 위반 graceful: (a) features 비-array → stderr warning + skip / (b) malformed JSON → 동상 / (c) entry 필수필드 누락 → 해당 entry만 skip, 나머지 카운트

**커밋:** `feat(plan): emit feature-list.json alongside PLAN.md`

---

## Wave 5: execute/worklog 통합

**목표:** Wave 완료 시 feature status 자동 전이, resume이 둘 다 read.

**산출물:**
- [x] `/hive:execute` 갱신: 6-3단계 신설 — Wave 종료 시 `feature-list.json`의 Wave 매핑 entry status 전이 (all_pass→passing / some_fail→failing+passing 혼합 / skip→partial), graceful skip 보장. 6-4 commit / 6-5 안내로 리넘버. 양쪽 mirror byte-identical (13108 bytes).
- [x] `/hive:worklog resume` 갱신: feature-list.json도 read → 마지막 Wave entry 중 `failing`/`partial` 잔존 시 분기 a("F<id> 수정 먼저"), 전부 passing이면 분기 b("Wave N+1 시작"). 양쪽 mirror byte-identical (6674 bytes).

**검증 (4/4 시나리오 통과):**
- [x] A: 3-feature(Wave 2×2 pending + Wave 4×1 passing) all_pass → Wave 2 둘 다 passing 전이, Wave 4 미변경 (단순 wave 필터)
- [x] B: 2-feature(Wave 2 둘 다 pending) some_fail → F1 failing / F2 passing, resume 분기 'a' + "Wave 2의 F1 수정 먼저" 메시지
- [x] C: 2-feature(Wave 2 모두 passing) → resume 분기 'b' + "Wave 3 시작" 메시지
- [x] D (backward compat): feature-list.json 부재 → execute 6-3 None 반환(skip), resume 분기 'b' (기본 안내) — Wave 4 graceful 규약 준수

**커밋:** `feat(execute,worklog): integrate feature-list.json pass/fail tracking`

---

## Wave 6: Trajectory evaluator + Phase 2 통합 테스트

**목표:** Anthropic 3-agent 패턴의 Evaluator를 HIVE에 합성.

**Wave 시작 시점 RULE 1 재확인 (구현 전):**
- [x] 신규 `/hive:evaluate` vs `/hive:playwright` 확장 — Q1=A 신규 스킬 채택 (단일 책임, RULE 2). 사용자 컨펌 2026-06-24.

**산출물:**
- [x] Evaluator 스킬 `/hive:evaluate` (3 mirror byte-identical 6031b) — feature-list.json read → verify 필드 따라 url/cmd 라이브 검증 → status (passing/failing/partial) 갱신. graceful skip + bash-guard 이중 가드.
- [x] mock 앱 `tests/mock-app/` — 3 HTML (feature-a/b/c.html) + feature-list.json (3 entry, verify=url) + `evaluate_harness.py` (Playwright MCP fallback stub, file:// + regex)
- [x] CLAUDE.md 워크플로우 명령어 표 갱신 — gen_skills_index.py 자동 재생성으로 16→17 스킬 (`/hive:evaluate` 추가). SKILLS.md mirror 동시 갱신.
- [x] `_shared/feature-list-schema.md`에 옵션 `verify` 객체 정의 추가 (type/target/assert + Wave 6 동작 명세)

**검증 (4/4 통과):**
- [x] (A) 초기 상태 → M-F1/F2/F3 모두 pending→passing 전이 (3/3)
- [x] (B) feature-a.html 마커 BROKEN으로 변경 → re-evaluate → M-F1: passing→failing 검출 (2/3 passing, 1 failing)
- [x] (C) 마커 FEATURE-A-OK 복원 → re-evaluate → M-F1: failing→passing 회복 (3/3 passing)
- [x] (D) 전체 사이클: plan(emit pending) → execute(simulate test pass→passing) → evaluate(live re-verify, 0 diff) → worklog resume(branch=b "Wave N+1 시작") — 무중단 1회 완료

**커밋:** `feat(evaluate): add trajectory evaluator (Anthropic 3-agent pattern)`
**Phase 2 완료 커밋:** `chore(milestone): Phase 2 complete (Feature List + Evaluator)`
**Milestone 종료:** `/hive:milestone complete v2.2.0` → git tag v2.2.0
