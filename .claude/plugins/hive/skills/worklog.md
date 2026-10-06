---
name: hive:worklog
description: Work log for resumable sessions
argument-hint: [init|update|resume]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# /hive:worklog — 작업일지 관리 스킬

## 개요

프로젝트 작업일지(`WORKLOG.md`)를 관리하여 세션 간 작업 상태를 유지한다. 중단된 작업을 정확한 중단 지점부터 재개할 수 있게 한다.

---

## 명령어별 동작

### 기본 (`/hive:worklog`) — 상태 표시

1. 프로젝트 루트의 `WORKLOG.md`를 읽는다
2. 다음 항목을 표시한다:
   - 프로젝트명 및 아키텍처 요약
   - 현재 단계 (discover / plan / execute / security / playwright / uat)
   - 마지막 완료 Wave
   - 다음 작업 (구체적 스텝)
   - 미결 이슈 목록
3. `WORKLOG.md`가 없으면: "WORKLOG.md가 없습니다. `/hive:discover`를 먼저 실행하세요." 라고 안내한다

---

### `/hive:worklog init <project-name>`

1. 아래 형식으로 프로젝트 루트에 `WORKLOG.md`를 생성한다
2. "WORKLOG.md가 생성되었습니다: `<project-name>`" 라고 확인 메시지를 출력한다

**생성 형식:**

```markdown
# HIVE 작업일지 — <프로젝트명>

## 프로젝트 정보
- 시작일: YYYY-MM-DD
- 아키텍처: <선택된 아키텍처 요약>
- 기술 스택: <스택 목록>

## 현재 상태
- 현재 단계: discover
- 마지막 완료 Wave: 없음 - 플랜 단계
- 다음 작업: /hive:plan 실행
- 마지막 업데이트: YYYY-MM-DD

## Wave 진행 현황
진행 상태의 원천은 PLAN.md 각 Wave의 완료 기준 체크박스다 (`/hive:progress`로 확인). 여기에는 체크리스트를 두지 않는다.

## 완료된 Wave 기록
| Wave | 제목 | 완료일 | Git Commit |
|------|------|--------|-----------|

## 주요 결정사항
| 날짜 | 결정 내용 | 이유 |
|------|----------|------|

## 미결 이슈
(없음)

## UAT 결과
- 날짜: 
- 결과: <통과 / 조건부통과 / 실패>
- 피드백:
```

---

### `/hive:worklog update`

1. 현재 `WORKLOG.md`를 읽는다
2. `git log --oneline -10`을 실행하여 최근 커밋을 확인한다
3. `WORKLOG.md`의 "현재 상태" 섹션을 최신 완료 Wave/스텝으로 업데이트한다:
   - `현재 단계` 값 갱신
   - `마지막 완료 Wave` 값 갱신
   - `다음 작업` 값 갱신
   - `마지막 업데이트` 날짜 갱신 (오늘 날짜)
4. Wave가 완료된 경우 (PLAN.md 해당 Wave 완료 기준이 모두 `[x]`):
   - "완료된 Wave 기록" 테이블에 행을 추가한다 (Wave 번호, 제목, 완료일, Git 커밋 해시)
5. 중요한 새 결정사항이 있으면 "주요 결정사항" 테이블에 추가한다

---

### `/hive:worklog resume` — 재개 프로토콜 (가장 중요)

이 명령어는 가장 중요하다. 정확하고 즉각적으로 작업을 재개해야 한다.

**단계별 절차:**

1. `WORKLOG.md`를 읽는다
2. `git log --oneline -10`을 실행하여 실제 Git 상태를 확인한다
3. `feature-list.json`이 존재하면 읽고 JSON 파싱한다 (graceful: 부재·malformed → 무시하고 4단계로 진행 — Wave 4 규약).
4. 교차 검증한다:
   - PLAN.md에서 완료 기준이 모두 `[x]`인 마지막 Wave N 을 찾고, `feat(wave-N)` 커밋이 git log에 존재하는지 확인한다
   - 불일치가 있으면 git log를 우선 기준으로 삼는다
   - feature-list.json이 있으면 마지막 완료 Wave N의 feature entry 상태를 확인한다
5. **분기 안내** (feature-list.json 존재 시 우선 적용):
   - **a. 마지막 Wave N의 feature 중 `failing` 또는 `partial` 잔존 시:**
     > "마지막 완료: Wave N — <제목> (커밋: abc1234)
     > ⚠️ feature-list.json: Wave N에 미통과 feature 잔존 — F<id> (<title>): <status>
     > 다음 작업: Wave N의 F<id> 수정 먼저 — 통과 후 Wave N+1 진입"
   - **b. 마지막 Wave N의 feature 모두 `passing` (또는 feature-list.json 없음):**
     > "마지막 완료: Wave N — <제목> (커밋: abc1234)
     > ✅ feature-list.json: Wave N 모두 passing (또는 미사용)
     > 다음 작업: <WORKLOG.md의 '다음 작업' 필드>"
6. **보고 즉시 해당 작업을 시작한다. 추가 확인 없이 진행한다.**

**예시 출력 (모두 passing):**
```
마지막 완료: Wave 2 — 데이터베이스 스키마 구현 (커밋: f3a8b21)
✅ feature-list.json: Wave 2 모두 passing
다음 작업: Wave 3 시작 — API 엔드포인트 구현 (/hive:execute)
→ Wave 3 실행을 시작합니다...
```

**예시 출력 (failing 잔존):**
```
마지막 완료: Wave 2 — 데이터베이스 스키마 구현 (커밋: f3a8b21)
⚠️ feature-list.json: Wave 2에 미통과 feature 잔존 — F2 (User CRUD endpoint): failing
다음 작업: Wave 2의 F2 수정 먼저 — 통과 후 Wave 3 진입
→ F2 수정에 착수합니다...
```

---

## 교차 검증 규칙

| 상황 | 처리 방법 |
|------|----------|
| WORKLOG.md와 git log 일치 | WORKLOG.md 기준으로 재개 |
| WORKLOG.md가 git보다 앞서 있음 | git log 기준으로 재개, WORKLOG.md 수정 |
| WORKLOG.md가 git보다 뒤처져 있음 | git log 기준으로 WORKLOG.md 업데이트 후 재개 |
| WORKLOG.md 없음 | `/hive:discover` 실행 안내 |

---

## 흔한 실수

- `resume` 후 사용자에게 "어디서부터 시작할까요?" 라고 묻지 않는다 — WORKLOG.md와 git log로 이미 알 수 있다
- `update` 시 날짜를 누락하지 않는다 — 항상 오늘 날짜로 갱신한다
- Wave 완료 체크박스(`[ ]` → `[x]`)를 빠뜨리지 않는다
- 완료된 Wave의 Git 커밋 해시를 반드시 기록한다

---

<!-- HIVE_V2_STANDARDS -->

## 표준 참조 (HIVE v2)

이 스킬은 다음 공통 표준을 따른다. 상세 규칙은 각 문서 참조.

| 표준 | 문서 | 역할 |
|------|------|------|
| 사전조건 체크 | [`_shared/prerequisites.md`](../_shared/prerequisites.md) | 스킬 시작 시 git/ARCH/PLAN/WORKLOG/ctx 등 검증 |
| 출력 형식 | [`_shared/output-format.md`](../_shared/output-format.md) | Verdict(✅/⚠/❌) · Severity · 에러 코드 통일 |
| WORKLOG 갱신 | [`_shared/worklog-update.md`](../_shared/worklog-update.md) | 시작/종료/결정사항 기록 표준 절차 |
| 서브 에이전트 호출 | [`_shared/agent-dispatch.md`](../_shared/agent-dispatch.md) | Sonnet/Haiku 디스패치 프롬프트 템플릿 |
| Git 커밋 메시지 | [`_shared/git-commit.md`](../_shared/git-commit.md) | Conventional Commits + 스킬별 자동 메시지 |

스킬 인덱스: [`SKILLS.md`](../SKILLS.md)

## 자동 기록

- 2026-10-07 08:38 execute.md
