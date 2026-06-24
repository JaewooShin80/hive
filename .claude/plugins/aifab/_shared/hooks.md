# AI-Fab Hooks — 표준 참조

> AI-Fab 하네스가 강제하는 글로벌(보안) + 프로젝트(워크플로우) hooks 6종 정의.
> GSD hooks(9종)와 네임스페이스(`aifab-*` vs `gsd-*`)로 분리되어 공존한다.

---

## 개요 매트릭스

| Hook | 이벤트 | 매처 | 분류 | 동작 | Exit 정책 |
|---|---|---|---|---|---|
| aifab-secret-guard.js | PreToolUse | Write\|Edit | 글로벌·보안 | 시크릿 토큰/키 패턴 또는 민감 파일 경로 차단 | exit 2 차단 |
| aifab-bash-guard.js | PreToolUse | Bash | 글로벌·보안 | 파괴적 쉘 명령(rm -rf /, force push, fork bomb 등) 차단 | exit 2 차단 |
| aifab-ctx-guard.js | PostToolUse | Bash\|Edit\|Write\|MultiEdit\|Agent\|Task | 글로벌·제어 | 컨텍스트 사용률 50/70% 경고 emit (RULE 5 강제) | exit 0 advisory |
| aifab-worklog-auto.js | PostToolUse | Edit\|Write\|MultiEdit | 프로젝트·워크플로우 | WORKLOG.md `## 자동 기록` 섹션에 편집 경로 자동 append | exit 0 |
| aifab-session-start.js | SessionStart | - | 프로젝트·워크플로우 | PLAN.md 파싱해 현재 Wave 위치/진척% 주입 | exit 0 advisory |
| aifab-wave-gate.js | PostToolUse | Bash | 프로젝트·워크플로우 | `feat(wave-N)` 커밋 감지 시 보안 리뷰 명령 안내 | exit 0 advisory |

---

## 1. aifab-secret-guard.js
- 이벤트: PreToolUse(Write\|Edit)
- 차단 패턴: ghp_ / gho_ / ghs_ / glpat- / AKIA / sk-ant- / sk_live_ / xox / PEM 헤더
- 차단 경로: `.env`, `*.key`, `*.pem`, `credentials`
- Allowlist: `.env.example`, `.env.sample`, `.env.template`
- 일치 시: exit 2 + stderr에 4자 미리보기 (시크릿 노출 최소화)
- 비활성: 호출자 `settings.json` PreToolUse 블록에서 해당 엔트리 주석 처리

## 2. aifab-bash-guard.js
- 이벤트: PreToolUse(Bash)
- 차단 패턴: rm -rf /, git push --force, chmod 777, curl … | sh, dd of=/dev/, mkfs, fork bomb (`:(){:|:&};:`)
- 허용: `git push --force-with-lease` (안전 force-push)
- 일치 시: exit 2 + stderr 짧은 사유
- 비활성: settings.json에서 엔트리 제거

## 3. aifab-ctx-guard.js
- 이벤트: PostToolUse(Bash\|Edit\|Write\|MultiEdit\|Agent\|Task)
- 동작: `/tmp/aifab-ctx-{session_id}.json` (aifab-status.py가 작성) 읽고 CLAUDE.md RULE 5 강제
- 임계: 50% used → warning, 70% used → critical
- 출력: `hookSpecificOutput.additionalContext` JSON (advisory)
- Debounce: 8 calls per (session, level), stale 60s
- GSD 브릿지(/tmp/claude-ctx-*)도 fallback으로 read
- 비활성: settings.json에서 엔트리 제거 또는 `/tmp/aifab-ctx-*.json` 미작성 시 자동 무음

## 4. aifab-worklog-auto.js
- 이벤트: PostToolUse(Edit\|Write\|MultiEdit)
- 동작: cwd에 WORKLOG.md 존재 시 `## 자동 기록` 섹션에 `- YYYY-MM-DD HH:MM <상대경로>` append
- 가드: WORKLOG.md self-edit / cwd 밖 / `.git/` prefix → skip
- 섹션 없으면: 파일 끝에 자동 생성
- 비활성: 프로젝트에 WORKLOG.md 미존재 시 자동 무음, 또는 settings.json 엔트리 제거

## 5. aifab-session-start.js
- 이벤트: SessionStart
- 동작: cwd에 ROADMAP.md + PLAN.md + WORKLOG.md 3개 모두 존재 시 PLAN.md를 파싱해 현재 Wave + 진척% 출력
- 출력: `hookSpecificOutput.additionalContext` JSON
- 가드: 1MB PLAN.md 크기 제한, 루트 cwd 거부
- 3 파일 중 하나라도 없으면 자동 무음 (비-AI-Fab 프로젝트에서 무해)

## 6. aifab-wave-gate.js
- 이벤트: PostToolUse(Bash)
- 동작: `git commit -m "feat(wave-N): …"` 감지 시 `/aifab:security wave N` 실행 안내 emit
- 지원 형태: double-quote / single-quote / heredoc (`$(cat <<EOF … EOF)`)
- commit 실패(`exitCode !== 0` 또는 `success === false`)는 무시
- 비활성: settings.json 엔트리 제거 또는 다른 커밋 메시지 사용

---

## GSD hooks와의 공존

aifab-*는 `aifab-*` 파일명 + `/tmp/aifab-ctx-*` 네임스페이스로 GSD(`gsd-*` / `/tmp/claude-ctx-*`)와 완전 분리된다. 동일 hook 이벤트에 둘 다 등록되면 Claude Code 런타임이 순차 실행하며, exit code 2가 하나라도 발생하면 차단된다.

임계값 충돌 시 정책:
- aifab-ctx-guard: 50% used에서 fire (CLAUDE.md RULE 5)
- gsd-context-monitor: 35% remaining(=65% used)에서 fire
- → aifab가 먼저 fire하여 GSD를 보완하는 관계

## 일괄 비활성 (개발/디버깅)

`~/.claude/settings.json`의 hooks 블록에서 aifab-* 엔트리만 일괄 주석/삭제하면 GSD는 영향 없이 보존된다. 글로벌 + 프로젝트(`.claude/hooks/`) 양쪽 파일은 그대로 두고 settings.json 등록만 해제하면 충분.

## 트러블슈팅

| 증상 | 원인 후보 | 진단 |
|---|---|---|
| 합법 `.env.example` 차단 | secret-guard allowlist 누락 | 파일명에 `example/sample/template` 포함 확인 |
| ctx-guard 무음 | 브릿지 파일 미작성 | `/tmp/aifab-ctx-{session_id}.json` 존재 + timestamp < 60s 확인 |
| WORKLOG.md append 누락 | cwd 외부 경로 / self-edit | tool_input.file_path가 cwd 하위인지 확인 |
| session-start 무음 | 3 sentinel 파일 부재 | ROADMAP.md, PLAN.md, WORKLOG.md 모두 존재 확인 |
| wave-gate 미발화 | commit 메시지가 `feat(wave-N)` 시작 아님 | 첫 라인 prefix 확인 |

---

**관련 문서:**
- 상위 SKILLS 인덱스: [`../SKILLS.md`](../SKILLS.md)
- CLAUDE.md "## Hooks" 섹션 (프로젝트 루트)
- Wave 1·2·3 산출물 기록: WORKLOG.md
