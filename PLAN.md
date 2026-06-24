# PLAN — v2.2.0 AI-Fab Harness Hardening

> 6 Wave, 2 Phase. ROADMAP.md의 Phase 1(Wave 1-3) + Phase 2(Wave 4-6).
> 각 Wave 종료 시 `git commit` + (Wave 1-3은) `/aifab:security` 실행.
> Wave 완료 마킹: 체크리스트 `[x]`.

---

## Wave 1: 글로벌 보안/제어 hooks

**목표:** `~/.claude/hooks/`에 모든 프로젝트가 공유할 안전장치 3종 추가.

**산출물:**
- [x] `aifab-secret-guard.js` — PreToolUse(Write|Edit), 시크릿 패턴(`ghp_/gho_/ghs_/glpat-/AKIA/sk-ant-/sk_live_/xox/PEM`) + 경로(`.env/*.key/*.pem/credentials`) 차단(exit 2). `.env.example` 등 allowlist 적용.
- [x] `aifab-bash-guard.js` — PreToolUse(Bash), `rm -rf /|git push --force|chmod 777|curl|sh|dd of=/dev/|mkfs|fork bomb` 차단(exit 2). `--force-with-lease`는 허용.
- [x] `aifab-ctx-guard.js` — **PostToolUse**(Stop→변경, RULE 1), 자체 브릿지 `/tmp/aifab-ctx-{session_id}.json` 사용(GSD `/tmp/claude-ctx-*` fallback). 50% used → warning, 70% → critical. debounce 8 calls, stale 60s.
- [x] `aifab-status.py` — bridge writer `write_ctx_bridge()` 추가, `main()`에서 ctx_pct 계산 직후 호출. path-traversal 가드 포함.

**검증:**
- [x] secret-guard: `ghp_` 토큰 content → exit 2, `.env` 경로 → exit 2, `.env.example` → exit 0, clean → exit 0 (4/4)
- [x] bash-guard: `rm -rf /` → exit 2, `git push --force` → exit 2, `--force-with-lease` → exit 0, `ls -la` → exit 0 (4/4)
- [x] ctx-guard: <50% → 무출력, 65% → warning JSON, 75% → critical JSON, path-traversal → 무시 (4/4)
- [x] E2E: aifab-status.py가 bridge 작성 → ctx-guard가 동일 파일 consume → 84% critical 메시지 emit
- [x] GSD hook과 네임스페이스 분리(`/tmp/aifab-ctx-*` vs `/tmp/claude-ctx-*`) → 충돌 없음

**커밋:** `feat(hooks): add global safety hooks (secret/bash/ctx) + bridge writer`

---

## Wave 2: 프로젝트 워크플로우 hooks

**목표:** `.claude/hooks/`에 AI-Fab 워크플로우 강제 hook 3종.

**산출물:**
- [x] `aifab-worklog-auto.js` — PostToolUse(Edit|Write|MultiEdit), WORKLOG.md "## 자동 기록" 섹션에 `{date} {file}` append (RULE 1: .sh → .js 통일, Windows 호환)
- [x] `aifab-session-start.js` — SessionStart, ROADMAP/PLAN/WORKLOG 존재 시 현재 Wave + 진척% 출력 (RULE 1: .sh → .js 통일)
- [x] `aifab-wave-gate.js` — PostToolUse(Bash[git commit]), 커밋 메시지에 `feat(wave-N)` 포함 시 "다음: `/aifab:security wave N`" 알림

**검증 (15/15 통과):**
- [x] worklog-auto: 섹션 존재시 append (1) / 섹션 없으면 생성 (2) / WORKLOG.md self-edit 차단 (3) / WORKLOG.md 없는 cwd 무음 (4) / cwd 밖 경로 차단 (5)
- [x] session-start: 실제 프로젝트 Wave 2/6 16% 출력 (1) / 비-AI-Fab dir 무음 (2) / 모든 Wave 완료 메시지 (3) / 부분 진척 Wave 2/3 33% (4)
- [x] wave-gate: double-quoted (1) / single-quoted (2) / heredoc (3) / 일반 feat 무시 (4) / 비-commit 무시 (5) / 실패 commit 무시 (6)
- [x] 글로벌(`~/.claude/hooks/`)과 프로젝트(`.claude/hooks/`) 양쪽 byte-identical 미러 확인

**커밋:** `feat(hooks): add project workflow hooks (worklog/session/wave-gate)`

---

## Wave 3: 등록 + 문서 + 통합 테스트

**목표:** settings.json 등록, `_shared/hooks.md` 작성, e2e 시나리오 통과.

**산출물:**
- [ ] `~/.claude/settings.json` hooks 블록에 aifab-* 6개 추가 (GSD 보존)
- [ ] `.claude/plugins/aifab/_shared/hooks.md` — 각 hook 역할/exit code/비활성 방법
- [ ] CLAUDE.md "## Hooks" 섹션 추가, `_shared/hooks.md` 링크

**검증 (5개 e2e 시나리오):**
- [ ] (1) `.env`에 secret 쓰기 시도 → 차단
- [ ] (2) `rm -rf /` 시도 → 차단
- [ ] (3) 신규 세션 → SessionStart hook이 ROADMAP head 출력
- [ ] (4) Edit 후 WORKLOG.md auto-append 확인
- [ ] (5) ctx 60% 합성 → Stop hook advisory

**커밋:** `feat(hooks): register aifab hooks + docs + e2e tests`
**Phase 1 완료 커밋:** `chore(milestone): Phase 1 complete (Hooks)`

---

## Wave 4: feature-list.json 스키마 + plan 통합

**목표:** PLAN.md와 짝이 되는 외재화 검증 파일 도입.

**산출물:**
- [ ] `.claude/plugins/aifab/_shared/feature-list-schema.md` — JSON 스키마 정의
  ```
  {
    "milestone": "v2.2.0",
    "features": [
      {"id":"W1-F1","title":"secret guard blocks .env","wave":1,
       "pass_criteria":"exit 2 on .env Write","status":"pending"}
    ]
  }
  ```
- [ ] `/aifab:plan` 스킬 갱신: PLAN.md 작성 시 동일 정보로 feature-list.json도 emit
- [ ] `scripts/aifab_progress.py` 확장: feature-list.json 읽어 pass% 계산, dashboard에 추가

**검증:**
- [ ] mock 입력으로 `/aifab:plan` 실행 → PLAN.md + feature-list.json 동시 생성
- [ ] `/aifab:progress` 출력에 "Wave: 3/6 / Features: 12/24 passing" 표시
- [ ] 스키마 위반 JSON은 progress가 detect (graceful fallback)

**커밋:** `feat(plan): emit feature-list.json alongside PLAN.md`

---

## Wave 5: execute/worklog 통합

**목표:** Wave 완료 시 feature status 자동 전이, resume이 둘 다 read.

**산출물:**
- [ ] `/aifab:execute` 갱신: Wave 종료 직전 `feature-list.json` 해당 Wave entry의 status를 테스트 결과 기반으로 갱신 (test pass→passing / fail→failing / skip→partial)
- [ ] `/aifab:worklog resume` 갱신: WORKLOG.md(서술) + feature-list.json(검증) 모두 read → 다음 작업이 "Wave N 미통과 feature 수정" 또는 "Wave N+1 시작" 인지 정확히 추론

**검증:**
- [ ] mock Wave 종료 시뮬레이션 → feature status pending→passing 전이
- [ ] failing feature 1개 남기고 resume → "Wave N의 F2 fix 먼저" 안내
- [ ] 모든 feature passing → "Wave N+1 시작" 안내

**커밋:** `feat(execute,worklog): integrate feature-list.json pass/fail tracking`

---

## Wave 6: Trajectory evaluator + Phase 2 통합 테스트

**목표:** Anthropic 3-agent 패턴의 Evaluator를 AI-Fab에 합성.

**Wave 시작 시점 RULE 1 재확인 (구현 전):**
- [ ] 신규 `/aifab:evaluate` vs `/aifab:playwright` 확장 — 어느 쪽? (현재 가정: 확장. 시작 시 사용자 확인)

**산출물:**
- [ ] Evaluator 스킬: feature-list.json 읽고 → Playwright MCP로 라이브 검증 → status 갱신
- [ ] mock 앱 1개 + mock feature 3개로 e2e 시나리오 (pass→fail→pass 전이 감지)
- [ ] CLAUDE.md 워크플로우 명령어 표 갱신 (gen_skills_index.py 자동 재생성)

**검증:**
- [ ] mock 앱에서 feature A 정상 → status: passing
- [ ] mock 앱 의도적 break → 다음 evaluate 호출 시 status: failing 감지
- [ ] fix 후 재실행 → status: passing 회복
- [ ] Phase 2 전체 e2e: plan → execute → evaluate → worklog resume 사이클 1회 무중단 완료

**커밋:** `feat(evaluate): add trajectory evaluator (Anthropic 3-agent pattern)`
**Phase 2 완료 커밋:** `chore(milestone): Phase 2 complete (Feature List + Evaluator)`
**Milestone 종료:** `/aifab:milestone complete v2.2.0` → git tag v2.2.0
