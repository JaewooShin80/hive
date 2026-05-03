---
name: aifab:migrate
description: Dependency/framework migration
argument-hint: <from -> to>
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:migrate` — 의존성 및 프레임워크 마이그레이션

**담당 모델:** Advisor (Opus) + Sonnet (구현) + Haiku (codemod 적용)
**선행:** /aifab:map-codebase (영향 범위 파악 권장)
**연계:** /aifab:plan (마이그레이션 Wave), /aifab:execute (점진적 적용), /aifab:debug (회귀)

---

## 역할

라이브러리·프레임워크·런타임의 버전 업그레이드 또는 교체를 안전하게 수행한다. Breaking change 분석 → 영향 범위 스캔 → Wave 단위 점진 적용 → 검증의 흐름을 반복하며, 마이그레이션 전후 상태를 Git으로 명확히 분리한다.

---

## 사용 사례

- Pydantic v1 → v2
- React 17 → 18
- Django 4.x → 5.x
- Python 3.11 → 3.12
- SQLAlchemy 1.x → 2.x
- Node 18 → 20
- 라이브러리 교체 (e.g., `requests` → `httpx`)

---

## 사용 방법

```
/aifab:migrate <라이브러리> <from버전> <to버전>
/aifab:migrate pydantic v1 v2
/aifab:migrate react 17 18
/aifab:migrate requests httpx        # 라이브러리 교체
```

---

## 프로세스

### Step 1: 마이그레이션 대상 명확화

사용자에게 다음을 확인한다:

1. **대상:** 라이브러리/프레임워크 이름, `from` 버전, `to` 버전 (또는 교체 대상)
2. **범위:** 모노레포의 경우 특정 패키지만인지, 전체인지
3. **제약:** 마감일, 다운타임 허용 여부, 병렬 실행 가능 여부

---

### Step 2: Breaking Changes 분석

#### 2-1. 공식 마이그레이션 가이드 검색 (WebSearch)

다음 쿼리 패턴으로 공식 가이드를 자동 수집한다:

```
"<library> migration guide <from> to <to>"
"<library> changelog breaking changes <to>"
"<library> upgrade guide"
```

수집된 breaking change를 **심각도**별로 분류한다:

| 심각도 | 기준 |
|--------|------|
| Critical | API 시그니처 변경, 동작 역전, 제거된 기능 |
| Major | Deprecated 경고 → 오류로 격상, 기본값 변경 |
| Minor | 새 경고 추가, 타입 정밀도 향상 |

#### 2-2. 코드베이스 영향 범위 스캔

Bash `grep`으로 deprecated API 사용 위치를 탐색한다:

```bash
# 예시: Pydantic v1 → v2
grep -rn "@validator\|\.dict()\|\.parse_obj\|orm_mode" --include="*.py" .

# 예시: React 17 → 18
grep -rn "ReactDOM.render\|unmountComponentAtNode\|unstable_batchedUpdates" --include="*.tsx" --include="*.ts" .
```

**출력:** 영향 받는 파일 목록 (경로 + 라인 수 + 사용 패턴)

---

### Step 3: 마이그레이션 전략 선택

분석 결과를 기반으로 Advisor가 전략을 권고한다:

| 전략 | 적용 조건 | 위험도 |
|------|-----------|--------|
| **빅뱅** | 소규모 코드베이스 (<50개 파일), 호환 레이어 없음 | 높음 |
| **점진 (Wave)** | 대규모, side-by-side 실행 가능, 모듈 경계 명확 | 낮음 |
| **자동 Codemod** | 기계적 변환 비율 높음, 공식 codemod 도구 존재 | 낮음 |

전략 선택 후 사용자 승인을 받는다.

---

### Step 4: 회귀 안전망 확보

마이그레이션 시작 전 테스트 커버리지를 점검한다:

1. 현재 테스트 실행 후 통과율 기록 (베이스라인)
2. 커버리지가 **60% 미만**이면 다음 경고 출력:

   > "⚠ 테스트 커버리지가 부족합니다. 마이그레이션 전 핵심 경로 테스트 보강을 권장합니다. 계속 진행할까요?"

3. 사용자가 수락 시 핵심 경로 smoke test를 먼저 작성한다 (`/aifab:execute` 위임 가능).

---

### Step 5: Codemod 도구 탐지 및 활용

사용 가능한 codemod 도구를 자동 탐지하고 제안한다:

**JavaScript / TypeScript:**
- `jscodeshift` — 일반 JS/TS AST 변환
- `@next/codemod` — Next.js 버전 업그레이드
- `react-codemod` — React 마이그레이션

**Python:**
- `libcst` — 의미를 보존하는 Python AST 변환
- `bowler` — Python 리팩터링 도구
- `pyupgrade` — Python 버전 문법 자동 업그레이드
- `bump-pydantic` — Pydantic v1 → v2 전용 codemod

탐지 명령 예시:

```bash
which jscodeshift bump-pydantic pyupgrade 2>/dev/null
npx jscodeshift --version 2>/dev/null
```

사용 가능한 도구를 목록화하고, 각 변환 패턴에 어떤 도구를 쓸지 매핑한다.

---

### Step 6: Wave 단위 적용

모듈 경계 기준으로 Wave를 구성한다. 각 Wave는 독립적으로 테스트 가능해야 한다.

**에이전트 역할 분리:**

- **Haiku** — 기계적 변환
  - import 경로 변경
  - deprecated API → new API 1:1 치환
  - 설정 파일 포맷 변경
  - Codemod 스크립트 실행 및 결과 검토

- **Sonnet** — 의미적 변경
  - 로직 흐름이 달라지는 API 변경 (예: Pydantic `@validator` → `@field_validator` 시그니처 변경)
  - 비동기/동기 전환이 수반되는 변경
  - 타입 시스템 심화 적용
  - 테스트 로직 수정

**Wave 적용 순서:**

1. 의존성이 없는 유틸리티/공통 모듈부터 시작
2. 서비스/비즈니스 레이어
3. API 레이어 및 엔드포인트
4. 테스트 코드 업데이트

---

### Step 7: Wave별 즉시 검증

각 Wave 적용 직후 테스트를 실행한다:

```bash
# Wave 적용 후 즉시 실행
pytest <변경된_모듈_경로> -v --tb=short   # Python
npx jest <변경된_모듈_경로> --verbose      # JS/TS
```

- 테스트 실패 시 **해당 Wave에서 즉시 중단** → `/aifab:debug`로 회귀 원인 분석
- 통과 시 다음 Wave로 진행

---

### Step 8: 의존성 버전 커밋 분리

```
# 1. 의존성 파일만 먼저 커밋
git add requirements.txt pyproject.toml package.json package-lock.json
git commit -m "chore(deps): bump <library> from <from> to <to>"

# 2. 코드 변경은 모듈별로 분리 커밋
git commit -m "migrate(<scope>): <from>→<to> <간략한 변경 내용>"
```

---

### Step 9: 전체 통합 테스트

모든 Wave 완료 후 전체 테스트 스위트를 실행한다:

```bash
pytest --tb=short -q          # Python
npx jest --coverage           # JS/TS
```

베이스라인(Step 4에서 기록)과 통과율을 비교한다. 통과율이 베이스라인 대비 하락하면 회귀로 간주하고 분석한다.

---

### Step 10: 마이그레이션 보고서 작성

`MIGRATION-REPORT.md`를 프로젝트 루트에 생성한다 (구조는 아래 Output 섹션 참조).

---

## 금지 사항

- 마이그레이션과 기능 추가를 동시에 수행하지 않는다 — 변경 원인을 분리해야 회귀 추적이 가능하다.
- 테스트 없이 마이그레이션을 진행하지 않는다 — 최소 smoke test가 없으면 Step 4에서 보강 후 진행한다.
- `requirements.txt` / `package.json`만 수정하고 코드를 미수정한 상태로 커밋하지 않는다.
- 여러 라이브러리를 동시에 마이그레이션하지 않는다 — 한 번에 하나씩 수행한다.

---

## Output

### MIGRATION-PLAN.md

```markdown
# 마이그레이션 플랜 — <library> <from> → <to>

## 요약
- 대상: <library> <from> → <to>
- 전략: <빅뱅 / 점진 / Codemod>
- 영향 파일 수: <N>개
- 예상 Wave 수: <N>개

## Breaking Changes
| 항목 | 심각도 | 영향 파일 |
|------|--------|-----------|
| ...  | Critical / Major / Minor | ... |

## 영향 파일 목록
- `<경로>` — <사용 패턴>

## Wave 계획
| Wave | 대상 모듈 | 담당 | 예상 소요 |
|------|-----------|------|-----------|
| 1    | ...       | Haiku | 30분 |
| 2    | ...       | Sonnet | 1시간 |

## 위험 요소
- <위험 항목 및 대응 방안>
```

### 모듈별 Git Commit

```
migrate(<scope>): pydantic v1→v2 validator 시그니처 변경
migrate(utils): requests→httpx 비동기 전환
chore(deps): bump pydantic from 1.10 to 2.6
```

### MIGRATION-REPORT.md

```markdown
# 마이그레이션 보고서 — <library> <from> → <to>
완료일: YYYY-MM-DD

## 변경된 파일 목록
| 파일 | 변경 유형 | Wave |
|------|-----------|------|
| ...  | import 변경 / 로직 수정 / 삭제 | 1 |

## 테스트 결과
- 베이스라인: <N>개 통과 / <M>개 전체
- 마이그레이션 후: <N'>개 통과 / <M'>개 전체
- 회귀: <없음 / 있으면 목록>

## 미완료 항목
- <남은 deprecated 사용 등>
```

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
