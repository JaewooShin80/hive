---
name: hive:grill
description: Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates CONTEXT.md and ADRs inline as decisions crystallise. Use before /hive:discover when requirements are fuzzy or when the user wants to stress-test a plan.
argument-hint: [<topic>]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# `/hive:grill` — 요구사항 정렬 인터뷰

**담당 모델:** Advisor (opus) — 도메인 이해 및 용어 정제

---

## 역할

구현 시작 전, 계획의 모든 측면을 인터뷰로 탐색하여 공유된 이해에 도달한다. 용어가 확정되면 `CONTEXT.md`를 즉시 업데이트하고, 중요한 결정은 ADR로 기록한다.

---

## 실행 방법

```
/hive:grill              # 현재 컨텍스트 기반 인터뷰
/hive:grill <topic>      # 특정 주제에 집중한 인터뷰
```

---

## 프로세스

### 1단계: 코드베이스 및 문서 탐색

- 프로젝트 루트의 `CONTEXT.md`가 있으면 읽어 기존 도메인 언어를 파악한다.
- `docs/adr/`가 있으면 관련 ADR을 확인한다.
- `ARCHITECTURE.md`가 있으면 기술 스택을 파악한다.
- 질문으로 답할 수 있는 것은 코드베이스 탐색으로 먼저 답한다.

### 2단계: 인터뷰 진행

한 번에 하나의 질문만 한다. 각 질문에 추천 답변을 제시한다.

**용어 충돌 처리:** 사용자가 `CONTEXT.md`의 기존 용어와 충돌하는 표현을 쓰면 즉시 지적한다.
> "현재 glossary에서 'cancellation'은 X를 의미하는데, 방금 Y의 의미로 쓰신 것 같습니다 — 어느 쪽인가요?"

**모호한 언어 정제:** 과부하된 용어가 등장하면 정확한 표준 용어를 제안한다.
> "'account'라고 하셨는데 — Customer인가요, User인가요? 두 개는 다른 개념입니다."

**코드 교차 검증:** 사용자가 동작 방식을 설명하면 코드가 동의하는지 확인한다. 모순이 있으면 표면화한다.

**구체적 시나리오:** 도메인 관계를 논의할 때 엣지 케이스를 탐색하는 시나리오를 제시한다.

### 3단계: CONTEXT.md 실시간 업데이트

용어가 확정되는 즉시 `CONTEXT.md`를 업데이트한다. 배치로 모으지 않는다.

**CONTEXT.md가 없으면:** 첫 번째 용어 확정 시 루트에 생성한다.

```markdown
# [프로젝트명] Context

## Language

**[용어]**: [정의]
_Avoid_: [피해야 할 표현들]

## Relationships

- [관계 설명]

## Flagged ambiguities

- [해소된 모호성 기록]
```

도메인 전문가에게 의미 있는 용어만 포함한다. 구현 세부사항은 포함하지 않는다.

### 4단계: ADR 선택적 생성

다음 세 가지 모두 해당할 때만 ADR을 제안한다:

1. **되돌리기 어려움** — 나중에 바꾸는 비용이 의미 있을 때
2. **맥락 없이 놀라움** — 미래의 독자가 "왜 이렇게 했지?"라고 의아할 때
3. **실제 트레이드오프** — 진짜 대안이 있었고 특정 이유로 선택했을 때

세 가지 중 하나라도 빠지면 ADR을 건너뛴다.

ADR 경로: `docs/adr/NNNN-<slug>.md`

### 5단계: 인터뷰 완료

모든 주요 결정이 해소되면 다음을 요약한다:

- 확정된 용어 목록
- 생성/업데이트된 문서
- 다음 추천 단계 (`/hive:discover` 또는 `/hive:plan`)

---

## CONTEXT.md vs WORKLOG.md 구분

| | CONTEXT.md | WORKLOG.md |
|--|------------|------------|
| 목적 | 도메인 언어 공유 | 작업 이력 추적 |
| 업데이트 | 용어 확정 시 | Wave 시작/종료 시 |
| 대상 | 도메인 전문가도 읽음 | 개발팀 내부용 |
