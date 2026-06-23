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
