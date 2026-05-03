---
name: aifab:plan
description: Wave-based implementation plan creation
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:plan` — Wave 기반 구현 플랜 생성

**담당 모델:** Advisor (claude-opus-4-7) — 높은 판단력이 요구되는 작업

---

## 역할

Advisor로서 프로젝트의 기능 목록을 분석하고, 복잡도에 따라 Wave 크기를 결정하며, 각 Wave에 적절한 에이전트(Sonnet/Haiku)를 배정한 PLAN.md를 생성한다.

---

## 1단계: 사전 조건 확인

1. 현재 디렉토리에서 `ARCHITECTURE.md`가 존재하는지 확인한다.
   - 존재하지 않으면 다음 메시지를 출력하고 즉시 중단한다:
     > "ARCHITECTURE.md가 없습니다. 먼저 `/aifab:discover`를 실행해 아키텍처를 정의해주세요."
2. `ARCHITECTURE.md`를 읽어 기술 스택, 아키텍처 결정사항, 프로젝트 구조를 파악한다.
3. `WORKLOG.md`가 존재하면 읽어 현재 진행 맥락을 파악한다.

---

## 2단계: 기능 목록 수집

사용자에게 다음을 질문한다:

> "개발할 기능 목록을 알려주세요. (직접 나열하거나, 요구사항 문서의 경로를 지정해주세요)"

- **사용자가 기능 목록을 직접 제공한 경우:** 각 기능을 개별 분석한다.
- **사용자가 문서 경로를 제공한 경우:** 해당 파일을 읽고 기능을 추출한다.

---

## 3단계: Wave 크기 결정 기준

각 기능 또는 기능 묶음에 대해 아래 기준으로 Wave 크기를 결정한다.

| Wave 크기 | 적용 기준 | 예상 기간 |
|-----------|-----------|-----------|
| **Small** | 단일 엔드포인트, 독립 컴포넌트, 간단한 CRUD | 0.5~1일 |
| **Medium** | 기능 묶음, 서비스 레이어, 복수 컴포넌트 통합 | 1~2일 |
| **Large** | 복잡한 통합, 크로스 서비스 로직, 외부 API 연동 | 2~3일 |

**판단 원칙:**
- 하나의 Wave는 단일 배포 단위로 완성 가능해야 한다.
- 의존성이 있는 기능은 선행 Wave에 배치한다.
- 불확실성이 높은 기능은 Large로 보수적으로 판단한다.

---

## 4단계: 에이전트 배정

각 Wave 내 작업을 두 에이전트에 분배한다.

**Haiku 에이전트 (보일러플레이트 작업):**
- 모델/스키마 정의
- CRUD 엔드포인트 스캐폴딩
- 설정 파일 생성
- DB 마이그레이션 파일 생성
- 타입/인터페이스 선언

**Sonnet 에이전트 (핵심 로직 작업):**
- 비즈니스 로직 구현
- 알고리즘 및 복잡한 계산 로직
- 테스트 코드 작성 (TDD)
- 컴포넌트/서비스 통합
- 에러 핸들링 및 예외 처리

---

## 5단계: TDD 계획 수립

각 Wave에 대해 TDD 사이클을 명시한다.

- **Red 단계:** 먼저 작성할 실패하는 테스트 목록
- **Green 단계:** 테스트를 통과시키기 위한 최소 구현 범위
- **Refactor 단계:** 구조 개선 및 중복 제거 방향

---

## 6단계: Wave 목록 승인

분석한 Wave 구성을 사용자에게 다음 형식으로 제시한다:

```
[Wave 구성 초안]

Wave 1: <제목> [Small] — 예상 0.5~1일
Wave 2: <제목> [Medium] — 예상 1~2일
Wave 3: <제목> [Large] — 예상 2~3일
...

이 구성으로 PLAN.md를 작성할까요? (수정 사항이 있으면 말씀해주세요)
```

사용자가 승인하면 7단계로 진행한다. 수정 요청이 있으면 반영 후 재제시한다.

---

## 7단계: PLAN.md 작성

승인된 Wave 구성을 바탕으로 프로젝트 루트에 `PLAN.md`를 아래 구조로 작성한다.

```markdown
# AI-Fab 개발 플랜 — <프로젝트명>
생성일: YYYY-MM-DD | 아키텍처: <ARCHITECTURE.md에서 추출한 아키텍처>

## 전체 Wave 목록
| Wave | 제목 | 크기 | 예상 기간 | 담당 에이전트 |
|------|------|------|----------|--------------|
| 1    | <제목> | Small | 0.5~1일 | Haiku + Sonnet |
| 2    | <제목> | Medium | 1~2일 | Haiku + Sonnet |
| 3    | <제목> | Large | 2~3일 | Sonnet 중심 |

---

## Wave 상세

### Wave 1: <제목> [Small]
**목표:** <이 Wave가 달성해야 하는 명확한 목표>

**완료 기준 (Success Criteria):**
- [ ] <구체적이고 검증 가능한 기준 1>
- [ ] <구체적이고 검증 가능한 기준 2>
- [ ] <구체적이고 검증 가능한 기준 3>

**테스트 기준:** <어떤 테스트가 통과해야 이 Wave가 완료되는지>

**TDD 사이클:**
- Red: <먼저 작성할 실패하는 테스트>
- Green: <테스트를 통과시키기 위한 최소 구현>
- Refactor: <완료 후 개선할 구조적 사항>

**작업 분해:**
- Haiku: <구체적인 보일러플레이트 작업 목록>
- Sonnet: <구체적인 비즈니스 로직 작업 목록>

**보안 체크포인트:**
- <이 Wave에서 검토해야 할 보안 항목>

**의존성:** <선행되어야 하는 Wave 또는 없음>

---

### Wave 2: <제목> [Medium]
...
```

---

## 8단계: WORKLOG.md 업데이트

`WORKLOG.md`에 다음 내용을 추가한다:

```markdown
## [YYYY-MM-DD] 플랜 생성 완료
- 총 Wave 수: <N>개
- 예상 전체 기간: <합산 기간>
- Wave 목록:
  - Wave 1: <제목> [Small]
  - Wave 2: <제목> [Medium]
  - ...
```

---

## 9단계: 완료 안내

다음 메시지를 출력한다:

> "플랜 작성 완료. PLAN.md에 <N>개 Wave가 정의되었습니다.
> `/aifab:execute`로 첫 번째 Wave를 시작하세요."

---

## 주의사항

- Wave는 독립적으로 배포 가능한 단위여야 한다.
- 각 완료 기준은 "예/아니오"로 판단할 수 있는 구체적 문장이어야 한다.
- 보안 체크포인트는 ARCHITECTURE.md의 보안 결정사항과 연계한다.
- Wave가 5개를 초과하면 마일스톤 단위로 그룹화를 고려한다.
- 불필요한 Wave 분할은 하지 않는다 — 연관된 작업은 하나의 Wave로 묶는다.

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
