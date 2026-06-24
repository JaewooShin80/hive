---
name: aifab:evaluate
description: Live feature verification via Playwright MCP. Reads feature-list.json, drives each feature's verify URL/command, updates status (passing/failing/partial). Anthropic 3-agent Evaluator role.
argument-hint: [--wave N] [--feature ID]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# `/aifab:evaluate` — Trajectory Evaluator

**담당 모델:** Advisor (claude-opus-4-7) — Anthropic 3-agent 패턴의 **Evaluator** 역할.

---

## 역할

`feature-list.json`의 각 feature를 **라이브 검증**하여 `status`를 객관적으로 갱신한다.
`/aifab:execute`가 테스트 결과 기반으로 status를 전이하는 것과 달리, `/aifab:evaluate`는
**완성된 산출물을 실제 동작**(브라우저, HTTP, 쉘 등)으로 재확인하여 회귀를 검출한다.

| 스킬 | 시점 | 검증 방식 |
|---|---|---|
| `/aifab:execute` 6-3단계 | Wave 종료 직후 | 테스트 스위트 결과 → status |
| `/aifab:evaluate` | 임의 시점 | 라이브 (Playwright MCP / shell) → status |

---

## 0단계: 컨텍스트 확인

CLAUDE.md RULE 5 (70/80%). 70% 초과 시 `/compact` 권장.

---

## 1단계: 사전 조건

1. `feature-list.json` 존재 확인. 없으면:
   > "feature-list.json이 없습니다. 먼저 `/aifab:plan`을 실행해 feature 목록을 생성해주세요."
2. JSON 파싱. 실패 시 stderr 경고 출력 후 중단 (graceful — non-zero exit).
3. `features` 배열 추출. 빈 배열이면:
   > "feature가 비어 있습니다. PLAN.md success criteria를 feature-list.json에 추가해주세요."

---

## 2단계: 인자 처리

- `--wave N` : `wave == N` entry만 검증 (없으면 전체).
- `--feature ID` : 해당 id만 검증 (다른 인자와 조합 불가).
- 인자 없음: 모든 feature 검증.

---

## 3단계: 검증 실행

각 대상 feature에 대해 다음을 수행한다.

### 3-1. feature.verify 필드 확인

확장 스키마(옵션):

```json
{
  "id": "W2-F1",
  "title": "...",
  "wave": 2,
  "pass_criteria": "...",
  "status": "pending",
  "verify": {
    "type": "url" | "cmd",
    "target": "<URL or shell command>",
    "assert": "<regex or expected substring>"
  }
}
```

`verify` 부재 시: 해당 feature는 **수동 검증 영역** — status 변경 없이 보고만 한다.

### 3-2. type = "url" (Playwright MCP)

1. Playwright MCP를 통해 `target` URL로 navigation.
2. 페이지 콘텐츠를 추출 (DOM textContent 또는 HTML source).
3. `assert` 정규식/substring으로 매칭.
4. **MCP 미가용 시:** `tests/mock-app/evaluate_harness.py` 같은 stub harness로 대체 실행 (오프라인 검증). 결과 동일 포맷.
5. 매치 → `passing` / 불일치 → `failing` / 네트워크 오류 → `partial`.

### 3-3. type = "cmd" (shell)

1. `target` 쉘 명령을 cwd에서 실행.
2. exit code 0 + stdout이 `assert` 매치 → `passing`.
3. exit code !=0 → `failing` / 매치 실패만 → `failing` / 타임아웃(30s) → `partial`.
4. **금지 패턴:** `aifab-bash-guard.js`가 차단하는 명령(`rm -rf /` 등)은 실행 전 검증 거부.

---

## 4단계: status 갱신

1. 갱신 전후 diff를 한 줄씩 보고:
   > "feature {id} ({title}): {old_status} → {new_status}"
2. `feature-list.json`을 들여쓰기 2 spaces + 마지막 newline으로 다시 쓴다.
3. 갱신 요약:
   > "evaluate 완료: {passing}/{total} passing, {failing} failing, {partial} partial"

---

## 5단계: WORKLOG.md 기록

다음 형식으로 append:

```markdown
## [YYYY-MM-DD HH:MM] evaluate 실행
- 범위: --wave N | --feature ID | 전체
- 변동: {N}개 entry status 갱신
- 결과: passing M/T, failing F, partial P
```

---

## 6단계: 다음 작업 안내

- failing 잔존 시:
  > "⚠️ {feature.id} ({feature.title}) failing — 수정 후 `/aifab:evaluate --feature {id}` 재실행 권장."
- 모두 passing:
  > "✅ 모든 feature 통과. `/aifab:milestone complete` 권장."
- partial 잔존:
  > "ℹ️ {feature.id} partial — 환경/인프라 원인 가능. 수동 확인 후 재실행."

---

## verify 필드 추가 가이드 (작성 시점)

`/aifab:plan` 또는 수동 편집 시 `verify`를 추가하면 자동 검증 가능.
없어도 기존 흐름 유지 (graceful).

```json
"verify": { "type": "url", "target": "file:///abs/path/to/page.html", "assert": "OK" }
"verify": { "type": "cmd", "target": "python -c 'import mymod; print(mymod.health())'", "assert": "OK" }
```

---

## 핵심 제약사항

| 규칙 | 설명 |
|------|------|
| **Idempotent** | 동일 입력 → 동일 status. 부수 효과는 feature-list.json + WORKLOG.md 갱신 한정. |
| **Graceful** | feature-list.json/verify 필드 부재 시 안내 후 중단/skip — 기존 프로젝트 무영향. |
| **Bash 가드 통과** | type=cmd는 aifab-bash-guard.js 패턴 위반 시 거부 (이중 가드). |
| **WORKLOG 저널** | 5단계는 생략 불가 — 재개 시 evaluate 이력이 worklog resume에 반영된다. |

---

<!-- AIFAB_V2_STANDARDS -->

## 표준 참조 (AIFAB v2)

이 스킬은 다음 공통 표준을 따른다. 상세 규칙은 각 문서 참조.

| 표준 | 문서 | 역할 |
|------|------|------|
| 사전조건 체크 | [`_shared/prerequisites.md`](../_shared/prerequisites.md) | 스킬 시작 시 git/ARCH/PLAN/WORKLOG/ctx 등 검증 |
| 출력 형식 | [`_shared/output-format.md`](../_shared/output-format.md) | Verdict(✅/⚠/❌) · Severity · 에러 코드 통일 |
| WORKLOG 갱신 | [`_shared/worklog-update.md`](../_shared/worklog-update.md) | 시작/종료/결정사항 기록 표준 절차 |
| 서브 에이전트 호출 | [`_shared/agent-dispatch.md`](../_shared/agent-dispatch.md) | Sonnet/Haiku 디스패치 프롬프트 템플릿 |
| Git 커밋 메시지 | [`_shared/git-commit.md`](../_shared/git-commit.md) | Conventional Commits + 스킬별 자동 메시지 |

Schema: [`_shared/feature-list-schema.md`](../_shared/feature-list-schema.md) — `verify` 옵션 필드 포함.
스킬 인덱스: [`SKILLS.md`](../SKILLS.md)
