# HIVE Hooks — 표준 참조

> HIVE 하네스가 강제하는 글로벌(보안) + 프로젝트(워크플로우) hooks 6종 정의.
> GSD에 의존하지 않는다 (아래 "GSD와의 관계" 참조).

---

## 개요 매트릭스

| Hook | 이벤트 | 매처 | 분류 | 동작 | Exit 정책 |
|---|---|---|---|---|---|
| hive-secret-guard.js | PreToolUse | Write\|Edit | 글로벌·보안 | 시크릿 토큰/키 패턴 또는 민감 파일 경로 차단 | exit 2 차단 |
| hive-bash-guard.js | PreToolUse | Bash | 글로벌·보안 | 파괴적 쉘 명령(rm -rf /, force push, fork bomb 등) 차단 | exit 2 차단 |
| hive-ctx-guard.js | PostToolUse | Bash\|Edit\|Write\|MultiEdit\|Agent\|Task | 글로벌·제어 | 컨텍스트 사용률 70/80% 경고 emit (RULE 5 강제) | exit 0 advisory |
| hive-worklog-auto.js | PostToolUse | Edit\|Write\|MultiEdit | 프로젝트·워크플로우 | WORKLOG.md `## 자동 기록` 섹션에 편집 경로 자동 append | exit 0 |
| hive-session-start.js | SessionStart | - | 프로젝트·워크플로우 | PLAN.md 파싱해 현재 Wave 위치/진척% 주입 | exit 0 advisory |
| hive-wave-gate.js | PostToolUse | Bash | 프로젝트·워크플로우 | `feat(wave-N)` 커밋 감지 시 보안 리뷰 명령 안내 | exit 0 advisory |

---

## 1. hive-secret-guard.js
- 이벤트: PreToolUse(Write\|Edit)
- 차단 패턴: ghp_ / gho_ / ghs_ / glpat- / AKIA / sk-ant- / sk_live_ / xox / PEM 헤더
- 차단 경로: `.env`, `*.key`, `*.pem`, `credentials`
- Allowlist: `.env.example`, `.env.sample`, `.env.template`
- 일치 시: exit 2 + stderr에 4자 미리보기 (시크릿 노출 최소화)
- 비활성: 호출자 `settings.json` PreToolUse 블록에서 해당 엔트리 주석 처리

## 2. hive-bash-guard.js
- 이벤트: PreToolUse(Bash)
- 차단 패턴: rm -rf /, git push --force, chmod 777, curl … | sh, dd of=/dev/, mkfs, fork bomb (`:(){:|:&};:`)
- 허용: `git push --force-with-lease` (안전 force-push)
- 일치 시: exit 2 + stderr 짧은 사유
- 비활성: settings.json에서 엔트리 제거

## 3. hive-ctx-guard.js
- 이벤트: PostToolUse(Bash\|Edit\|Write\|MultiEdit\|Agent\|Task)
- 동작: `/tmp/hive-ctx-{session_id}.json` (hive-status.py가 작성) 읽고 CLAUDE.md RULE 5 강제
- 임계: 70% used → warning, 80% used → critical
- 출력: `hookSpecificOutput.additionalContext` JSON (advisory)
- Debounce: 8 calls per (session, level), stale 60s
- GSD 브릿지(/tmp/claude-ctx-*)도 fallback으로 read (레거시 호환 — statusLine이 hive-status일 때는 생성되지 않아 미사용)
- 비활성: settings.json에서 엔트리 제거 또는 `/tmp/hive-ctx-*.json` 미작성 시 자동 무음

## 4. hive-worklog-auto.js
- 이벤트: PostToolUse(Edit\|Write\|MultiEdit)
- 동작: cwd에 WORKLOG.md 존재 시 `## 자동 기록` 섹션에 `- YYYY-MM-DD HH:MM <상대경로>` append
- 가드: WORKLOG.md self-edit / cwd 밖 / `.git/` prefix → skip
- 섹션 없으면: 파일 끝에 자동 생성
- 비활성: 프로젝트에 WORKLOG.md 미존재 시 자동 무음, 또는 settings.json 엔트리 제거

## 5. hive-session-start.js
- 이벤트: SessionStart
- 동작: cwd에 PLAN.md 가 있으면 `## Wave N:`/`### Wave N:` 블록의 완료 기준 체크박스를 세어 현재 Wave + 진척% 출력 (ROADMAP.md 는 선택 — 있으면 다음 단계로 milestone 안내)
- 출력: `hookSpecificOutput.additionalContext` JSON
- 가드: 1MB PLAN.md 크기 제한, 루트 cwd 거부
- 3 파일 중 하나라도 없으면 자동 무음 (비-HIVE 프로젝트에서 무해)

## 6. hive-wave-gate.js
- 이벤트: PostToolUse(Bash)
- 동작: `git commit -m "feat(wave-N): …"` 감지 시 `/hive:security wave N` 실행 안내 emit
- 지원 형태: double-quote / single-quote / heredoc (`$(cat <<EOF … EOF)`)
- commit 실패(`exitCode !== 0` 또는 `success === false`)는 무시
- 비활성: settings.json 엔트리 제거 또는 다른 커밋 메시지 사용

---

## GSD와의 관계

HIVE는 GSD hook을 사용하지도, 전제하지도 않는다. 컨텍스트 경고는 `hive-ctx-guard`(70%/80% used, CLAUDE.md RULE 5)가 단독 담당한다.
GSD 원본은 `gsd-build/get-shit-done` → [`open-gsd/gsd-core`](https://github.com/open-gsd/gsd-core) (npm `@opengsd/gsd-core`)로 이전되었다. 병행 설치 시에도 `hive-*` / `/tmp/hive-ctx-*` 네임스페이스로 충돌하지 않는다.

## 일괄 비활성 (개발/디버깅)

`settings.json`(프로젝트 또는 `--global` 설치 시 `~/.claude/settings.json`)의 hooks 블록에서 hive-* 엔트리만 삭제하면 된다. `.claude/hooks/` 파일은 그대로 두고 settings.json 등록만 해제하면 충분.

## 트러블슈팅

| 증상 | 원인 후보 | 진단 |
|---|---|---|
| 합법 `.env.example` 차단 | secret-guard allowlist 누락 | 파일명에 `example/sample/template` 포함 확인 |
| ctx-guard 무음 | 브릿지 파일 미작성 | `/tmp/hive-ctx-{session_id}.json` 존재 + timestamp < 60s 확인 |
| WORKLOG.md append 누락 | cwd 외부 경로 / self-edit | tool_input.file_path가 cwd 하위인지 확인 |
| session-start 무음 | PLAN.md 부재 또는 Wave 헤더/체크박스 없음 | PLAN.md 와 `### Wave N:` 아래 완료 기준 `- [ ]` 확인 |
| wave-gate 미발화 | commit 메시지가 `feat(wave-N)` 시작 아님 | 메시지 첫 줄 prefix 확인 (-m/-qm/-am/--message/heredoc 모두 지원) |

---

**관련 문서:**
- 상위 SKILLS 인덱스: [`../SKILLS.md`](../SKILLS.md)
- CLAUDE.md "## Hooks" 섹션 (프로젝트 루트)
- Wave 1·2·3 산출물 기록: WORKLOG.md
