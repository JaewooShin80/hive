---
name: aifab:adr
description: Manage Architecture Decision Records (Michael Nygard format)
argument-hint: <new|list|show|supersede|accept> [args]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# /aifab:adr — Architecture Decision Records 관리 스킬

**담당 모델:** Advisor (Opus) — 의사결정 문서화
**선행:** /aifab:compare (비교 결과를 ADR로) 또는 직접 결정 발생 시
**연계:** /aifab:worklog (결정사항 자동 링크)

---

## 개념

ADR(Architecture Decision Record)은 중요한 아키텍처 결정의 컨텍스트, 결정 내용, 결과를 시간순으로 기록하는 가벼운 문서. 미래의 자신과 팀원이 "왜 이렇게 했는가?"를 답할 수 있게 한다.

---

## 명령어별 동작

### `/aifab:adr new <title>` — 새 ADR 생성

**절차:**

1. 제목을 인수로 받는다 (예: `/aifab:adr new "Pydantic v2 채택"`)
2. `docs/adr/*.md`를 스캔하여 다음 번호를 자동 부여한다 (4자리 zero-padding, 0001부터 시작)
3. 사용자에게 4개 섹션 정보를 순서대로 수집한다:
   - **Context**: 어떤 상황에서, 왜 이 결정이 필요한가?
   - **Decision**: 무엇을 하기로 했는가? (명확하고 단정적으로)
   - **Consequences**: 긍정적/부정적 결과 모두 명시
   - **Alternatives Considered**: 검토한 대안과 미채택 이유
   - `/aifab:compare` 결과가 있으면 자동 인용한다
4. `docs/adr/NNNN-<slug>.md`를 생성한다 (제목에서 slug 자동 생성)
5. `WORKLOG.md`의 "주요 결정사항" 테이블에 한 줄 추가 + ADR 링크
6. `docs/adr/README.md` 인덱스 파일을 갱신한다
7. git commit (Standards/git-commit.md 참조)

---

### `/aifab:adr list` — 목록 표시

1. `docs/adr/*.md`를 스캔한다
2. 각 파일의 Status, Date, 제목을 읽는다
3. 번호 순으로 정렬하여 표시한다

**출력 형식:**
```
# ADR 목록

| # | 제목 | Status | 날짜 |
|---|------|--------|------|
| 0001 | Pydantic v2 채택 | Accepted | 2026-05-02 |
| 0002 | REST API 채택 | Superseded by 0005 | 2026-05-03 |
```

---

### `/aifab:adr show <number>` — 특정 ADR 표시

1. 번호에 해당하는 `docs/adr/NNNN-*.md` 파일을 찾는다
2. 전체 내용을 출력한다
3. 파일이 없으면 "ADR-NNNN을 찾을 수 없습니다." 안내

---

### `/aifab:adr supersede <old> <new>` — 이전 결정 대체

1. `<old>` 번호 ADR의 Status를 `Superseded by ADR-<new>`로 변경한다
2. `<new>` 번호 ADR의 Status를 `Accepted`로 설정한다
3. 두 문서에 양방향 링크를 추가한다:
   - 이전 ADR: `Superseded by: [ADR-NNNN](NNNN-xxx.md)`
   - 새 ADR: `Supersedes: [ADR-MMMM](MMMM-yyy.md)`
4. 이전 결정은 **절대 삭제하지 않는다** — 히스토리 보존 필수
5. `docs/adr/README.md` 인덱스 갱신
6. git commit

---

### `/aifab:adr accept <number>` — 상태 전환

1. 해당 번호 ADR의 Status를 `Proposed` → `Accepted`로 변경한다
2. Date 필드를 오늘 날짜로 갱신한다
3. `docs/adr/README.md` 인덱스 갱신
4. git commit

---

## ADR 파일 형식 (Michael Nygard 형식)

```markdown
# ADR-NNNN: <결정 제목>

* Status: Proposed | Accepted | Deprecated | Superseded by ADR-XXXX
* Date: YYYY-MM-DD
* Deciders: <결정 참여자, 보통 Claude + 사용자>
* Related Wave: <Wave 번호 또는 N/A>

## Context (배경)
어떤 상황에서, 왜 이 결정이 필요한가?
관련된 제약, 과거의 시도, 현재의 문제점.

## Decision (결정)
무엇을 하기로 했는가?
명확하고 단정적으로. 모호한 표현 금지.

## Consequences (결과)
이 결정으로 어떤 것이 좋아지고, 어떤 것이 나빠지는가?
긍정적/부정적 결과를 모두 명시.

## Alternatives Considered (검토한 대안)
다른 어떤 옵션을 검토했고 왜 채택하지 않았는가?
(선택) /aifab:compare 결과 링크.

## References (참고 자료)
관련 문서, RFC, 기사, 토론 링크.
```

---

## 인덱스 자동 갱신 (`docs/adr/README.md`)

모든 ADR 생성/변경 시 아래 형식으로 인덱스를 갱신한다.

```markdown
# Architecture Decision Records

| # | 제목 | Status | 날짜 |
|---|------|--------|------|
| [0001](0001-xxx.md) | Pydantic v2 채택 | Accepted | 2026-05-02 |
| [0002](0002-yyy.md) | REST API 채택 | Superseded by 0005 | 2026-05-03 |
```

---

## 번호 부여 규칙

- 0001부터 시작, 4자리 zero-padding
- 결번 없음 — deprecated/superseded여도 번호 유지
- 새 ADR은 현재 최대 번호 + 1

---

## Anti-patterns

- ADR을 사후 작성하지 않는다 — 결정 시점에 함께 작성
- "최선", "좋은", "적절한" 같은 모호한 단어 사용 금지
- Consequences에 긍정적 결과만 적지 않는다 — 부정적 결과 필수
- 사소한 결정에 ADR을 남발하지 않는다 — 코드 주석 또는 PR 설명으로 대체

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

스킬 인덱스: [`SKILLS.md`](../SKILLS.md)
