---
name: aifab:compare
description: Use when facing a multi-option technical decision and needing a structured trade-off analysis. Triggers on /aifab:compare command. Use when selecting libraries, architecture patterns, frameworks, design patterns, or algorithms and wanting a weighted decision matrix with recommendation.
---

# `/aifab:compare` — N-옵션 의사결정 트레이드오프 매트릭스

**담당 모델:** Advisor (Opus) — 옵션 분석 및 추천
**선행:** /aifab:discover, /aifab:plan (결정 시점에서 호출)
**연계:** /aifab:adr (결정 자동 기록)

---

## 역할

Advisor로서 기술적 의사결정이 필요한 상황에서 옵션을 체계적으로 비교하고, 트레이드오프 매트릭스를 작성하여 컨텍스트에 맞는 권장 옵션을 제시한다. 최종 결정권은 항상 사용자에게 있다.

---

## 사용 사례

- 라이브러리 선택 (예: SQLAlchemy vs Tortoise ORM vs raw SQL)
- 아키텍처 패턴 (모노리스 vs 마이크로서비스)
- 디자인 결정 (REST vs GraphQL)
- 프레임워크 비교 (FastAPI vs Litestar)
- 알고리즘 선택 (B-tree vs LSM-tree)

---

## 명령어

```
/aifab:compare <topic>                    # 대화형으로 옵션 입력 받음
/aifab:compare <topic> --options "A,B,C"  # 옵션 직접 지정
```

---

## Step 1: 비교 주제 명확화

`--options`가 제공된 경우에도 아래 세 항목을 반드시 확인한다 (이미 명확한 항목은 건너뜀):

1. **결정 범위** — 단일 모듈 / 서비스 레이어 / 전체 아키텍처
2. **되돌리기 비용** — 쉬움(라이브러리 교체 가능) / 어려움(아키텍처 전환 필요)
3. **우선순위** — 이 결정에서 가장 중요한 제약 조건 (성능, 개발 속도, 팀 경험 등)

---

## Step 2: 옵션 식별

사용자 제시 옵션에 Advisor가 누락된 유력 후보를 추가 제안한다.

- 최소 2개, 최대 5개 (4개 이상은 분석 부담을 사용자에게 사전 고지)
- 실질적으로 선택 가능한 옵션만 포함
- 확정 전 목록을 사용자에게 제시하고 승인 받기

---

## Step 3: 평가 기준 정의

결정 유형에 맞게 기준을 선정하고 사용자가 추가/제거 가능.

**일반 기준:** 성능, 학습곡선, 커뮤니티, 라이센스, 유지보수성

**도메인 특화 기준 (예시):**
- 라이브러리: 타입 안전성, 마이그레이션 지원, 테스트 용이성
- 아키텍처: 배포 복잡도, 팀 규모 적합성, 확장성
- API 설계: 클라이언트 유연성, 스키마 관리, 캐싱 지원
- 알고리즘: 시간/공간 복잡도, 구현 복잡도

---

## Step 4: 트레이드오프 매트릭스 작성

**점수 기준 (1–5):** 1=부적합, 3=보통, 5=매우 우수
**각 셀: 점수 + 한 줄 근거를 반드시 함께 작성**

```
| 기준       | 가중치 | FastAPI           | Litestar          | Flask          |
|------------|:------:|:-----------------:|:-----------------:|:--------------:|
| 성능       |   3    | 5 (async 우수)    | 5 (가장 빠름)     | 2 (sync 기본)  |
| 생태계     |   5    | 5 (가장 큼)       | 2 (초기 단계)     | 5 (오래됨)     |
| 학습곡선   |   4    | 3 (Pydantic 학습) | 3 (새 패턴 필요)  | 5 (단순)       |
| 가중 합계  |        | **49**            | **35**            | **47**         |
```

가중 합계 = Σ(점수 × 가중치)

---

## Step 5: 가중치 적용 (선택적)

사용자에게 기준별 중요도(1–5) 설정 여부를 묻는다. 기본값은 모든 기준 동일 가중치(3). 설정 시 매트릭스를 업데이트하고 가중 합계를 재계산한다.

---

## Step 6: 추천 + 근거

가중 합계 최고 옵션을 권장하며 다음을 제시한다:

- **추천 이유 3~5가지** — 각 이유를 특정 기준·프로젝트 컨텍스트와 연결
- **차순위 옵션과의 결정적 차이** — 2가지 핵심 포인트
- **주의 문구** — "이 추천은 매트릭스 점수 기준이며, 팀 경험 등 컨텍스트에 따라 다른 선택이 더 적합할 수 있습니다."

---

## Step 7: 사용자에게 최종 결정 위임

매트릭스 추천은 참고 자료다. 사용자에게 선택을 위임하며, 팀 기존 경험·시간 제약·향후 확장 계획을 추가 고려 요소로 안내한다.

---

## Step 8: 결정 기록 및 산출물 생성

사용자가 최종 옵션을 선택하면 아래 작업을 수행한다.

**8-1. 비교 보고서 저장** — `docs/decisions/compare-<topic>.md`
- 결정 요약 (선택 옵션, 비교 대상, 결정 범위, 되돌리기 비용)
- 전체 트레이드오프 매트릭스
- 선택 근거 및 검토된 대안

**8-2. WORKLOG.md 업데이트** — "주요 결정사항" 섹션에 한 줄 요약 추가:
```
- [YYYY-MM-DD] <topic> 결정: [선택된 옵션] 채택 (근거: [핵심 이유 1줄])
```

**8-3. ADR 기록 권장** — 되돌리기 비용이 높은 아키텍처 결정이면 `/aifab:adr` 호출을 안내한다.

---

## 금지 사항

- ❌ "베스트"라며 단정적 추천 — 트레이드오프는 항상 컨텍스트 의존
- ❌ 5개 초과 옵션 동시 비교 — 분석 마비(analysis paralysis) 유발
- ❌ 정량 점수만 제시하고 정성 근거 누락 — 근거 없는 숫자는 신뢰 불가

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
