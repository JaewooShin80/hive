---
name: hive:execute
description: Multi-agent Wave execution (Opus + Sonnet/Haiku)
argument-hint: [--parallel <wave-ids>]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
  - Workflow
---

# `/hive:execute` — Wave 멀티에이전트 실행

**담당 모델:** Advisor (opus) — 전체 오케스트레이션 및 검토  
**서브에이전트:** Haiku (보일러플레이트), Sonnet (로직/테스트)

---

## 역할

Advisor로서 현재 Wave를 PLAN.md에서 읽고, 작업을 유형별로 분해하여 Haiku·Sonnet 에이전트에 병렬 디스패치한 뒤, 결과물을 검토·수정하고 Wave를 완료 처리한다.

---

## 0단계: 컨텍스트 윈도우 확인

1. 현재 컨텍스트 사용률을 확인한다.
   - **80% 이상 시:** 다음 메시지를 출력하고 즉시 중단한다 (CLAUDE.md RULE 5):
     > "컨텍스트 사용률이 80% 이상입니다. 먼저 `/compact`를 실행하여 컨텍스트를 압축한 뒤 `/hive:execute`를 다시 실행해주세요."
   - **70–79%:** 경고만 표시하고 진행한다.
   - **70% 미만:** 1단계로 진행한다.

---

## 1단계: 사전 조건 확인

1. `PLAN.md`가 현재 디렉토리에 존재하는지 확인한다.
   - 존재하지 않으면 다음 메시지를 출력하고 즉시 중단한다:
     > "PLAN.md가 없습니다. 먼저 `/hive:plan`을 실행해 개발 플랜을 생성해주세요."

2. `WORKLOG.md`가 현재 디렉토리에 존재하는지 확인한다.
   - 존재하지 않으면 다음 메시지를 출력하고 즉시 중단한다:
     > "WORKLOG.md가 없습니다. 먼저 `/hive:discover`를 실행해 프로젝트를 초기화해주세요."

3. `PLAN.md`를 읽어 현재 Wave를 파악한다. **진행 상태의 원천은 PLAN.md 각 Wave의 완료 기준 체크박스**다 (session-start hook, `/hive:progress`, `/hive:roadmap update`가 같은 값을 읽는다):
   - `## Wave N:` 또는 `### Wave N:` 블록 중 `- [ ]`가 남아 있는 **첫 번째** Wave를 현재 Wave로 선정한다.
   - 모든 Wave의 완료 기준이 `[x]`이면 다음 메시지를 출력하고 즉시 중단한다:
     > "모든 Wave 완료! `/hive:playwright`를 실행하세요."

4. 브랜치를 확인한다 (`_shared/prerequisites.md` CHECK-6):
   - 현재 브랜치가 `main`/`master`이면 `git switch -c hive/wave-N-<slug>`로 작업 브랜치를 만든다 (사용자가 main 작업을 명시적으로 허용한 경우만 예외). 병렬 Wave는 `/hive:worktree`를 쓴다.
   - 미커밋 변경이 있으면 커밋/stash 후 진행하라고 안내하고 중단한다 (CHECK-5).

5. 실행 정보를 확정한다: `root` = `git rev-parse --show-toplevel`, `test_cmd` = PLAN.md "공통 규약"의 테스트 명령 (없으면 프로젝트에서 감지해 PLAN.md 공통 규약에 기록한 뒤 진행).
   - **환경 준비는 Advisor 가 디스패치 전에 한 번 한다**: 공통 규약의 "환경 준비" 명령(venv·의존성·E2E 브라우저 설치 등)을 실행하고 `test_cmd`가 실행되는지(테스트 0개여도 수집 성공) 확인한다. 병렬 에이전트에게 환경 설치를 맡기지 않는다 (동시 설치 충돌).

6. 선정된 현재 Wave 번호와 제목을 확인 메시지로 출력한다:
   > "현재 Wave: Wave N — <제목>. 실행을 시작합니다."

---

## 2단계: Advisor 분석 단계

`PLAN.md`에서 현재 Wave의 상세 내용을 읽고 다음 작업을 수행한다.

### 2-1. 작업 원자 단위 분해

Wave의 목표와 작업 분해 항목을 기반으로 각 작업을 **원자 단위(하나의 파일 또는 단일 책임 함수 수준)**로 나눈다.  
분해 결과를 내부 목록으로 정리한다 (출력 불필요).

### 2-2. 작업 유형 분류

분해된 각 작업을 다음 기준으로 분류한다.

**Haiku 작업 (보일러플레이트):**
- Pydantic 모델 / SQLAlchemy 스키마 정의
- CRUD 라우트 스텁 (실제 로직 없이 엔드포인트 뼈대만)
- 설정 파일 / 환경 변수 템플릿
- DB 마이그레이션 파일 (Alembic 등)
- TypeScript 인터페이스 / 타입 선언
- 기본 React 컴포넌트 스텁 (props 정의 + return null 수준)

**Sonnet 작업 (로직/통합):**
- 비즈니스 로직 구현
- 알고리즘 및 복잡한 계산 로직
- 테스트 파일 작성 (TDD — 실패하는 테스트 먼저)
- 서비스 레이어 통합 및 의존성 연결
- 복잡한 컴포넌트 로직 (상태 관리, API 연동)
- 에러 핸들링 및 예외 처리

### 2-3. 의존성 매핑

각 작업 간 의존성을 파악하여 실행 순서를 결정한다.

- **병렬 실행 가능:** 서로 독립적인 Haiku 작업들, 서로 다른 모듈을 다루는 Sonnet 작업들
- **순차 실행 필요:** Haiku 작업(스키마 정의) → Sonnet 작업(비즈니스 로직 구현)
- **TDD 순서 강제:** Sonnet 테스트 작성 → Sonnet 구현 작업 (반드시 이 순서)

### 2-4. 실행 계획 출력

다음 형식으로 실행 계획을 출력한다:

```
[Wave N 실행 계획]

병렬 배치 1 (Haiku):
  - [Haiku-1] <파일명>: <작업 설명>
  - [Haiku-2] <파일명>: <작업 설명>

병렬 배치 2 (Sonnet — 테스트 먼저):
  - [Sonnet-1] tests/<파일명>: 실패하는 테스트 작성

병렬 배치 3 (Sonnet — 구현):
  - [Sonnet-2] <파일명>: 테스트를 통과하는 구현 작성

의존성: Haiku-1 → Sonnet-2, Sonnet-1 → Sonnet-2
```

---

## 3단계: WORKLOG.md Wave 시작 기록

`WORKLOG.md`에 다음 내용을 추가한다:

```markdown
## Wave N 시작 — YYYY-MM-DD HH:MM
- 상태: 진행 중
- 작업 목록:
  - [ ] [Haiku] <작업 설명>
  - [ ] [Sonnet] <테스트 작성 작업 설명>
  - [ ] [Sonnet] <구현 작업 설명>
```

---

## 4단계: 병렬 디스패치 단계

### 4-A. Workflow 도구가 있으면 (Claude Code) — 기본 경로

이 스킬의 실행이 Workflow 사용에 대한 사용자 동의다. 저장된 workflow `hive-wave`(`.claude/workflows/hive-wave.js`)를 호출한다:

```
Workflow({ name: "hive-wave", args: {
  wave: N,
  root: "<git rev-parse --show-toplevel 결과 — 절대경로>",
  test_cmd: "<PLAN.md 공통 규약의 테스트 명령, 예: .venv/bin/pytest -q>",
  batches: [                       // 배치는 순서대로, 배치 안 작업은 동시에
    [ { id: "T1", title: "...", files: ["src/a.py"],
        test: "tests/test_a.py", context: ["PLAN.md Wave N 섹션", "src/db.py:1-40"] } ],
    [ { id: "T2", ..., depends_on: ["T1"] } ]   // 의존 대상만 명시하면 무관한 BLOCKED 에 끌려가지 않음
  ]
}})
```

- `root`·`test_cmd`는 필수다. 워크플로우 에이전트는 세션 cwd(다른 레포일 수 있음)에서 시작하므로 `root`는 반드시 절대경로로 넣는다. `files`·`test`·`context`는 `root` 기준 상대경로.
- 2단계 분해를 그대로 옮긴다. 같은 파일을 건드리는 작업은 하나로 합친다(병렬 작업 간 파일 소유권 충돌 금지). `context`에는 포인터만 넣는다.
- 작업마다 Red(sonnet) → Green(sonnet) 순으로 실행된다. `stub: true`는 스키마·타입 선언처럼 구현과 명확히 분리되는 경우에만 켠다(기본 off — haiku stub 은 범위를 넘기 쉽다).
- 모든 프롬프트에 "커밋 금지 · WORKLOG/PLAN/ROADMAP/feature-list 수정 금지 · 지정 파일만 쓰기"가 자동 포함된다. 커밋과 상태 파일 갱신은 Advisor(6단계)만 한다.
- 각 배치 뒤에 gate(haiku, low effort)가 전체 `test_cmd`와 `git status --porcelain`으로 범위 밖 변경을 검사한다. gate 실패 시 이후 배치는 skip 된다.
- 반환값 `{wave, results, blocked, skipped, gates}`를 5단계 검토의 입력으로 쓴다.
  - `results[].status`: `DONE` · `DONE_WITH_CONCERNS` · `ALREADY_SATISFIED`(이미 구현·기준 충족 — 완료로 취급)
  - `blocked[]`: `{id, stage, notes, files, test_output}` — 사유를 보고 Advisor 가 직접 해결하거나 해당 작업만 다시 디스패치한다.
  - Green 이 `TEST_DEFECT`(테스트 자체 결함)를 반환하면 워크플로우가 Red 를 사유와 함께 1회 재실행한다. 그래도 결함이면 `blocked`.
  - `gates[]`: `{batch, passed, summary, out_of_scope}` — `out_of_scope`가 비어 있지 않으면 범위 밖 수정이므로 검토 후 되돌리거나 반영한다.
- 중단되면 같은 args로 `resumeFromRunId`를 지정해 재개한다.
- 에이전트 수 ≈ 작업×2 + 배치 수. 작업이 4개를 넘으면 Wave 분할을 고려한다.

### 4-B. Workflow 도구가 없으면 (Codex 등) — 대체 경로

Agent 도구를 사용하여 작업을 병렬로 디스패치한다.  
**각 서브에이전트 프롬프트에는 반드시 다음 내용을 포함해야 한다:**

1. **작업 대상 파일 경로** (절대 경로 또는 프로젝트 루트 기준 상대 경로)
2. **맥락 포인터** — 코드를 복사하지 않고 위치만 전달한다 (에이전트가 직접 읽는다):
   - 관련 파일 경로와 라인 범위
   - `PLAN.md`의 해당 Wave 섹션 (`Interfaces` 블록 포함)
   - 앞 배치 결과물의 파일 경로 또는 커밋 해시
3. **기대 출력 형식** (함수 시그니처, 클래스 구조 등)
4. **TDD 지시문** (Sonnet 구현 작업에 한함):
   > "실패하는 테스트를 먼저 작성하고, 구현하고, 테스트가 통과하는지 확인하세요."
5. **공통 안전장치** (4-A의 hive-wave 와 동일):
   - "프로젝트 루트 `<절대경로>`로 cd 한 뒤 작업"
   - "git commit 금지, WORKLOG.md·PLAN.md·ROADMAP.md·feature-list.json 수정 금지 (Advisor 전용)"
   - "지정된 파일만 작성. 다른 작업의 파일·테스트는 실행/수정하지 말고 자기 테스트 파일만 실행"
   - 배치가 끝나면 Advisor 가 전체 테스트와 `git status --porcelain`으로 범위 밖 변경을 확인한 뒤 다음 배치로 간다.

### 배치 1: Haiku 보일러플레이트 (병렬)

```
독립적인 Haiku 작업은 동시에 디스패치한다.

예시 프롬프트 구조:
---
당신은 Haiku 에이전트입니다. 다음 보일러플레이트 작업을 수행하세요.

파일: <경로>
작업: <구체적 설명>

참고 맥락 (직접 읽을 것):
- <관련 파일 경로:라인 범위>
- PLAN.md "Wave N" 섹션

요구사항:
- 실제 비즈니스 로직은 구현하지 않습니다 (스텁 수준 유지)
- 프로젝트의 기존 네이밍 컨벤션을 따릅니다
- 하드코딩된 시크릿은 절대 포함하지 않습니다
---
```

### 배치 2: Sonnet 테스트 작성 (병렬, Haiku 완료 이전에 시작 가능)

```
예시 프롬프트 구조:
---
당신은 Sonnet 에이전트입니다. TDD 방식으로 테스트를 먼저 작성하세요.

파일: tests/<경로>
테스트 대상: <함수/클래스명>

참고 맥락 (직접 읽을 것):
- <관련 파일 경로:라인 범위>
- PLAN.md "Wave N" 섹션 (완료 기준, Interfaces)

요구사항:
- 지금 이 단계에서 테스트는 반드시 실패해야 합니다 (Red 단계)
- 엣지 케이스와 에러 케이스를 포함하세요
- 테스트 파일만 작성하고 구현 파일은 수정하지 마세요
---
```

### 배치 3: Sonnet 구현 (Haiku 배치 1 + Sonnet 배치 2 완료 후)

```
예시 프롬프트 구조:
---
당신은 Sonnet 에이전트입니다. 작성된 테스트를 통과하는 구현을 작성하세요.

구현 파일: <경로>
테스트 파일: tests/<경로>

참고 맥락 (직접 읽을 것):
- Haiku 스텁: <파일 경로>
- 테스트: tests/<경로>
- PLAN.md "Wave N" 섹션 (Interfaces)

요구사항:
- 실패하는 테스트를 먼저 확인합니다 (테스트 실행 후 출력 확인)
- 모든 테스트가 통과하도록 최소한의 코드만 작성합니다
- 작업 범위를 벗어나는 추측성 코드를 추가하지 않습니다
- 구현 완료 후 테스트를 다시 실행하여 통과 여부를 확인합니다
---
```

---

## 5단계: Advisor 검토 단계

모든 에이전트가 완료된 후 Advisor가 직접 산출물을 검토한다.  
**이 단계는 생략할 수 없다.**

### 5-1. 코드 통일성 검토

- 파일 전체에 동일한 네이밍 컨벤션이 사용되는가?
- 임포트 스타일, 타입 힌팅, 주석 언어가 일관되는가?
- 기존 코드베이스의 패턴과 충돌하는 부분이 없는가?

### 5-2. Karpathy 원칙 준수 검토

- **추측 코드 없음:** Wave 범위를 벗어난 기능이 추가되지 않았는가?
- **불필요한 추상화 없음:** 지금 당장 필요하지 않은 인터페이스·베이스 클래스·헬퍼가 생성되지 않았는가?
- **수술적 변경:** 작업과 무관한 파일이 수정되지 않았는가?

### 5-3. 보안 기본 원칙 검토

- 하드코딩된 시크릿(API 키, 비밀번호, 토큰)이 없는가?
- 사용자 입력에 대한 유효성 검사가 존재하는가?
- SQL 쿼리에서 파라미터 바인딩을 사용하는가? (직접 문자열 조합 금지)
- 입력 범위·크기 상한이 있는가? (거대 숫자 → 오버플로 500, 긴 문자열·업로드 → 메모리/ReDoS)
- 정규식이 사용자 입력에 대해 선형 시간인가? (중첩 반복 `(a+)+`, `(\d+,?)+` 류 금지)

### 5-4. 부작용·환경 검토

- import 시점 부작용이 없는가? (모듈 레벨에서 DB 파일 생성, 네트워크 호출, 전역 상태 변경)
- 테스트가 실제 데이터 경로(`data/`, 홈 디렉토리)를 건드리지 않고 임시 경로를 쓰는가?
- `gates[].out_of_scope`에 나온 범위 밖 변경을 확인하고 되돌리거나 반영했는가?

### 5-5. 에이전트 가정 환류

`results[].notes`·`blocked[].notes`에서 PLAN에 없던 가정(기본값, None 처리, 오류 코드, 계산식 세부)과 PLAN 내부 모순(예: 보안 체크포인트 ↔ Interfaces)을 모은다.
- 다음 Wave가 의존하는 가정 → PLAN.md 해당 Wave의 `Interfaces`에 확정값으로 반영
- 설계 판단이 담긴 가정 → `/hive:adr`로 기록
- 사용자 판단이 필요한 가정 → WORKLOG "미결 이슈"에 기록

### 5-6. 문제 발견 시 처리

검토 중 문제가 발견되면:
- **Advisor가 직접 파일을 수정한다** (에이전트를 재디스패치하지 않는다)
- 수정 내용을 인라인 주석으로 간략히 기록한다

---

## 6단계: 완료 단계

### 6-1. 전체 테스트 스위트 실행

1단계에서 확정한 `test_cmd`(PLAN.md 공통 규약)로 전체 테스트를 실행한다. hive-wave 의 마지막 gate 결과가 있더라도 Advisor 가 직접 한 번 더 실행해 출력을 확인한다.

- **모든 테스트 통과 시:** 6-2단계로 진행한다.
- **실패 테스트 존재 시:** Advisor가 직접 원인을 분석하고 수정한 뒤 테스트를 재실행한다. 2회 시도 후에도 실패하면:
  > "Wave N 테스트 실패: <실패 테스트명>. 수동 개입이 필요합니다. 오류: <오류 메시지>"  
  출력 후 중단한다.

### 6-2. WORKLOG.md 업데이트

`WORKLOG.md`에서 Wave N 시작 기록을 찾아 다음과 같이 업데이트한다:

```markdown
## Wave N 완료 — YYYY-MM-DD HH:MM
- 상태: 완료 ✓
- 완료된 작업:
  - [x] [Haiku] <작업 설명>
  - [x] [Sonnet] <테스트 작성 작업 설명>
  - [x] [Sonnet] <구현 작업 설명>
- 테스트 결과: <통과한 테스트 수>/<전체 테스트 수> 통과
- 비고: <특이사항 또는 없음>
```

그리고 **PLAN.md의 Wave N 완료 기준 체크박스를 갱신한다** (진행 상태의 원천):
- 테스트로 충족이 확인된 기준 → `- [ ]` → `- [x]`
- 충족되지 않은 기준은 `[ ]`로 둔다 (그러면 다음 `/hive:execute`가 같은 Wave를 다시 고른다).

WORKLOG.md에는 별도의 Wave 체크리스트를 두지 않는다 (이중 관리 금지).

### 6-3. feature-list.json status 전이

프로젝트 루트에 `feature-list.json`이 존재하면 Wave N에 매핑된 모든 feature entry의 `status`를 다음 규칙으로 전이한다. 파일이 없으면 이 단계를 건너뛴다 (기존 프로젝트 backward compat — Wave 4 graceful 규약 준수).

**전이 규칙:**

| 6-1단계 테스트 결과 | feature.status 전이 |
|---|---|
| 모든 테스트 통과 | `pending` → `passing` (Wave 매핑 entry 전부) |
| 일부 실패 후 Advisor 수정으로 통과 | `pending` → `passing` |
| 2회 재시도 후에도 일부 실패 | 실패 영향 entry → `failing`, 나머지 → `passing` |
| Wave 범위에 검증 미작성 영역 있음 | 해당 entry → `partial` |

**절차:**

1. `feature-list.json`을 읽고 JSON으로 파싱한다. `JSONDecodeError`는 `features` 키 무효로 간주하고 6-4단계로 진행한다 (graceful skip).
2. `features` 배열에서 `wave == N`인 entry만 필터한다.
3. 각 entry의 `status` 필드를 위 규칙으로 갱신한다.
4. 갱신된 JSON을 **들여쓰기 2 spaces · 마지막 newline** 으로 다시 쓴다 (Wave 4 schema 규약).
5. 전이 내역을 한 줄 보고한다:
   > "feature-list.json: Wave N — {passing N}개 passing / {failing N}개 failing / {partial N}개 partial"

### 6-4. Git 커밋

다음 형식으로 커밋한다:

```
feat(wave-N): <wave 제목>
```

`git commit -m "feat(wave-N): <wave 제목>"` 형식을 지킨다 (`_shared/git-commit.md`와 동일 — `hive-wave-gate` hook이 이 형식을 감지해 `/hive:security wave N`을 안내한다).

커밋에 포함할 파일: Wave N에서 생성·수정된 모든 파일 + `PLAN.md`(체크박스) + `WORKLOG.md` + (존재 시) `feature-list.json`

### 6-5. 완료 안내 출력

다음 메시지를 출력한다:

> "Wave N 완료! 다음: `/hive:execute` (Wave N+1 시작) 또는 `/hive:security` (보안 검토)"

---

## 핵심 제약사항

| 규칙 | 설명 |
|------|------|
| **순차 제약** | 현재 Wave의 테스트가 전부 통과하기 전까지 다음 Wave를 디스패치하지 않는다 |
| **검토 필수** | 5단계 Advisor 검토는 생략 불가 |
| **TDD 순서** | Sonnet 테스트 작성 → Sonnet 구현 — 이 순서는 절대 역전하지 않는다 |
| **Wave 저널** | WORKLOG.md를 Wave 시작(3단계)과 완료(6-2단계) 양쪽에서 모두 업데이트한다 |
| **컨텍스트 관리** | 0단계에서 80% 이상 시 즉시 중단하고 `/compact` 실행을 요청한다 |
| **직접 수정** | 검토 단계에서 문제 발견 시 에이전트 재디스패치 대신 Advisor가 직접 수정한다 |

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
