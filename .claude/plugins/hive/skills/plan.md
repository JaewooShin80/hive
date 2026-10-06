---
name: hive:plan
description: Wave-based implementation plan creation
argument-hint: "[phase N] [--auto]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/hive:plan` — Wave 기반 구현 플랜 생성

**담당 모델:** Advisor (opus) — 높은 판단력이 요구되는 작업

---

## 역할

Advisor로서 프로젝트의 기능 목록을 분석하고, 복잡도에 따라 Wave 크기를 결정하며, 각 Wave에 적절한 에이전트(Sonnet/Haiku)를 배정한 PLAN.md를 생성한다.

---

## 1단계: 사전 조건 확인

1. 현재 디렉토리에서 `ARCHITECTURE.md`가 존재하는지 확인한다.
   - 존재하지 않으면 다음 메시지를 출력하고 즉시 중단한다:
     > "ARCHITECTURE.md가 없습니다. 먼저 `/hive:discover`를 실행해 아키텍처를 정의해주세요."
2. `ARCHITECTURE.md`를 읽어 기술 스택, 아키텍처 결정사항, 프로젝트 구조를 파악한다.
3. `WORKLOG.md`가 존재하면 읽어 현재 진행 맥락을 파악한다.

4. `ROADMAP.md` 존재 여부 확인 (선택적):
   - **있으면:**
     - 인자에 `phase N`이 있으면 해당 Phase의 Wave 범위만 분해 대상으로 한다.
     - 인자가 없으면 첫 `🟡 in_progress` 또는 `⬜ pending` Phase의 Wave 범위만 분해.
     - PLAN.md 헤더에 다음 메타를 추가한다:
       ```markdown
       > **Phase:** N (이름)
       > **Wave 범위:** a-b
       ```
   - **없으면:** 기존 동작 (전체 기능을 단일 Phase로 분해, 메타 추가 없음). 역호환 유지.

5. `PLAN.md`가 이미 있으면 (다음 Phase 플랜 등) **덮어쓰지 않는다**:
   - 기존 Wave 섹션·Interfaces·체크박스는 그대로 두고, 새 Wave를 기존 마지막 번호 다음부터 `## Wave 상세` 끝에 추가한다.
   - `## 전체 Wave 목록` 표에 새 행을 추가한다.
   - 헤더 메타는 `> **Phase:** N (이름)` / `> **Wave 범위:** a-b`를 현재 Phase 로 갱신하고, 바로 아래에 `> **이전 Phase:** 1 (Wave 1-2) 완료` 같은 이력을 한 줄씩 남긴다.
   - 새 Wave의 Consumes 는 이전 Phase 의 Produces 이름을 그대로 쓴다.

6. ROADMAP.md 가 있으면 이번에 분해한 Phase 헤더의 `(Wave a-b)`를 실제 Wave 번호로 고치고, 뒤 Phase 들의 범위를 그만큼 밀어낸다 (roadmap init 의 범위는 추정치다).

7. ROADMAP.md를 갱신해야 하는 경우 (Phase 1 완료 후 Phase 2 plan 호출 등) 마지막 단계에서 사용자에게 `/hive:roadmap update` 실행을 안내한다.

---

## 2단계: 기능 목록 수집

ARCHITECTURE.md 의 "실행 환경"(환경 준비·테스트·실행 명령)을 PLAN.md "공통 규약"으로 그대로 옮긴다. 없으면 프로젝트 파일(requirements.txt, package.json 등)에서 정해 기록한다 — `/hive:execute`가 이 테스트 명령을 `test_cmd`로 쓴다.

`REQUIREMENTS.md`(`/hive:spec` 산출물)가 있으면 그 기능 목록(F1…)을 그대로 사용하고 질문하지 않는다. Must 기능은 모두 Wave에 배정하고, Should 기능은 배정 여부를 6단계 승인 때 확인한다.

없으면 사용자에게 다음을 질문한다:

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

제시 전에 스스로 아래 4항목을 점검하고, 문제가 있으면 바로 고친다 (서브 에이전트 호출 없음):

1. **커버리지:** 요구사항/기능 목록의 각 항목이 어느 Wave에 들어가는지 짚을 수 있는가. 빠진 항목은 Wave에 추가한다.
2. **모호한 줄:** "적절히 처리", "TBD", "엣지 케이스 대응"처럼 아무것도 결정하지 않는 줄을 구체적 기준으로 바꾼다.
3. **이름 일관성:** Wave 간 Interfaces의 함수·타입·파일 이름이 서로 일치하는가.
4. **분량 비율:** 플랜이 요구사항보다 몇 배 길거나 코드 블록이 대부분이면 구현을 대신 쓴 것이다. 시그니처와 테스트 기준만 남긴다.

분석한 Wave 구성을 사용자에게 다음 형식으로 제시한다:

```
[Wave 구성 초안]

Wave 1: <제목> [Small] — 예상 0.5~1일
Wave 2: <제목> [Medium] — 예상 1~2일
Wave 3: <제목> [Large] — 예상 2~3일
...

이 구성으로 PLAN.md를 작성할까요? (수정 사항이 있으면 말씀해주세요)
```

사용자가 승인하면 7단계로 진행한다. 수정 요청이 있으면 반영 후 재제시한다. `--auto`([`_shared/auto-mode.md`](../_shared/auto-mode.md))면 자동 승인으로 기록하고 진행한다 — Should 기능 포함 여부 같은 판단은 PLAN.md 공통 규약 아래 "가정 (auto)"에 남긴다.

---

## 7단계: PLAN.md 작성

승인된 Wave 구성을 바탕으로 프로젝트 루트에 `PLAN.md`를 아래 구조로 작성한다.

```markdown
# HIVE 개발 플랜 — <프로젝트명>
생성일: YYYY-MM-DD | 아키텍처: <ARCHITECTURE.md에서 추출한 아키텍처>

## 공통 규약
- 프로젝트 루트: <git rev-parse --show-toplevel>
- 환경 준비: <예: uv venv .venv && uv pip install -r requirements.txt / npm ci — ARCHITECTURE.md "실행 환경"에서>
- 테스트 명령 (`test_cmd`): <예: .venv/bin/pytest -q / npm test -->
- 앱 실행: <예: .venv/bin/uvicorn app.main:app --port 8000 / npm run dev>
- 공통 제약: <설정 경로·환경변수·금액 단위 등 모든 Wave 가 지킬 것>
- (기존 코드일 때) 회귀 금지: <docs/codebase-map/00-SUMMARY.md 테스트 기준선, 예: 기존 136 tests 전부 통과 유지>
- (기존 코드일 때) 호환 유지: <ARCHITECTURE.md "변경 범위"의 바뀌면 안 되는 것 — 공개 API 응답 필드, DB 스키마/해시 규칙 등은 추가만 허용>
- (기존 코드일 때) 참조: docs/codebase-map/00-SUMMARY.md, 04-CONCERNS.md, REQUIREMENTS.md `현행 기능 (유지)`

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
**담당 기능:** <REQUIREMENTS.md 기능 ID, 예: F1, F3 — 없으면 생략>

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

**Interfaces:**
- Consumes: <이전 Wave에서 가져다 쓰는 함수·타입·파일 — 정확한 이름/시그니처, 없으면 "없음">
- Produces: <다음 Wave가 의존하는 함수·타입·파일 — 정확한 이름/시그니처>

---

### Wave 2: <제목> [Medium]
...
```

---

## 7-1단계: feature-list.json 생성

`PLAN.md`와 함께 프로젝트 루트에 `feature-list.json`을 만든다. 형식은 [`_shared/feature-list-schema.md`](../_shared/feature-list-schema.md)를 따른다.

직접 추출하지 말고 생성 스크립트를 실행한다:

```bash
python3 scripts/gen_feature_list.py            # milestone 은 ROADMAP.md 에서, 없으면 --milestone vX.Y.Z
```

- 각 Wave의 "완료 기준" 체크박스 1개 = feature 1개. `id`는 `W{wave}-F{idx}`, `status`는 `"pending"`(이미 `[x]`면 `"passing"`).
- `title`·`pass_criteria`는 완료 기준 문장 그대로. REQUIREMENTS.md 기능에서 온 기준은 PLAN 에 미리 `[F3] …`처럼 기능 ID를 붙여 쓴다.
- 파일이 이미 있으면(다음 Phase) **새 id 만 추가**하고 기존 항목의 `status`·`verify`는 보존한다.
- 자동 검증할 수 있는 기준은 PLAN.md 에 ``(verify: `<test_cmd> <테스트 파일>`)``를 붙여 쓴다 → `verify` 필드가 생겨 `/hive:evaluate`가 라이브로 확인한다.

---

## 8단계: WORKLOG.md 업데이트

진행 상태(어느 Wave가 끝났는지)는 **PLAN.md 완료 기준 체크박스만** 원천으로 쓴다. WORKLOG.md에 별도 Wave 체크리스트를 만들지 않는다 (`/hive:execute`, session-start hook, `/hive:progress`, `/hive:roadmap update`가 모두 PLAN.md를 읽는다).

`WORKLOG.md`에 다음 기록만 추가한다:

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
> `/hive:execute`로 첫 번째 Wave를 시작하세요."

---

## 주의사항

- 이 스킬은 계획만 한다 — 구현 코드를 작성하거나 실행하지 않는다. 플랜에는 결정(파일, 시그니처, 테스트 기준, 스펙 값)만 기록하고 함수 본문은 쓰지 않는다.
- Wave는 독립적으로 배포 가능한 단위여야 한다.
- 각 완료 기준은 "예/아니오"로 판단할 수 있는 구체적 문장이어야 한다.
- 보안 체크포인트는 ARCHITECTURE.md의 보안 결정사항과 연계한다.
- Wave가 5개를 초과하면 마일스톤 단위로 그룹화를 고려한다.
- 불필요한 Wave 분할은 하지 않는다 — 연관된 작업은 하나의 Wave로 묶는다.

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
