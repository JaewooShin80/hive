---
name: hive:grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test an idea or plan without codebase context. For code-aware sessions with CONTEXT.md updates, use /hive:grill instead.
argument-hint: [<topic>]
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
---

# `/hive:grill-me` — 아이디어 인터뷰

**담당 모델:** Advisor (opus)

---

## 역할

코드베이스와 무관하게, 아이디어나 플랜에 대해 모든 측면을 인터뷰로 탐색하여 공유된 이해에 도달한다. `CONTEXT.md` 참조 없음. 기술 결정 전 아이디어 검증에 적합하다.

---

## `/hive:grill` 과의 차이

| | `/hive:grill-me` | `/hive:grill` |
|--|-------------------|-----------------|
| 코드베이스 탐색 | 최소 | 적극적 |
| CONTEXT.md 업데이트 | 없음 | 실시간 업데이트 |
| ADR 생성 | 없음 | 선택적 생성 |
| 사용 시점 | 코드 무관 아이디어 | 구현 직전 정렬 |

---

## 프로세스

질문에 답할 수 있는 것이 있으면 코드베이스 탐색으로 먼저 확인한다.

한 번에 하나의 질문만 한다. 각 질문에 추천 답변을 제시한다. 의사결정 트리의 모든 가지를 해소할 때까지 계속한다.

모든 주요 결정이 해소되면 합의된 내용을 요약한다.
