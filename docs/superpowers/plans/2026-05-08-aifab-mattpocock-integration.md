# AIFAB + mattpocock/skills 통합 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mattpocock/skills의 4개 스킬(grill, grill-me, caveman, diagnose)을 AIFAB 하네스에 추가하여 전처리(정렬·언어·디버깅) 레이어를 통합한다.

**Architecture:** 기존 16개 AIFAB 스킬은 변경 없이 유지하고, 새 스킬 4개를 동일한 디렉토리에 추가한다. SKILLS.md와 CLAUDE.md에 새 카테고리와 커맨드 항목을 추가하여 문서화를 완성한다.

**Tech Stack:** Markdown 스킬 파일, YAML frontmatter (AIFAB v2 표준)

---

### Task 1: `/aifab:grill` 스킬 파일 생성

**Files:**
- Create: `.claude/plugins/aifab/skills/grill.md`

- [ ] **Step 1: 파일 생성**

`.claude/plugins/aifab/skills/grill.md` 를 아래 내용으로 생성한다:

```markdown
---
name: aifab:grill
description: Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates CONTEXT.md and ADRs inline as decisions crystallise. Use before /aifab:discover when requirements are fuzzy or when the user wants to stress-test a plan.
argument-hint: [<topic>]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# `/aifab:grill` — 요구사항 정렬 인터뷰

**담당 모델:** Advisor (claude-opus-4-7) — 도메인 이해 및 용어 정제

---

## 역할

구현 시작 전, 계획의 모든 측면을 인터뷰로 탐색하여 공유된 이해에 도달한다. 용어가 확정되면 `CONTEXT.md`를 즉시 업데이트하고, 중요한 결정은 ADR로 기록한다.

---

## 실행 방법

```
/aifab:grill              # 현재 컨텍스트 기반 인터뷰
/aifab:grill <topic>      # 특정 주제에 집중한 인터뷰
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
- 다음 추천 단계 (`/aifab:discover` 또는 `/aifab:plan`)

---

## CONTEXT.md vs WORKLOG.md 구분

| | CONTEXT.md | WORKLOG.md |
|--|------------|------------|
| 목적 | 도메인 언어 공유 | 작업 이력 추적 |
| 업데이트 | 용어 확정 시 | Wave 시작/종료 시 |
| 대상 | 도메인 전문가도 읽음 | 개발팀 내부용 |
```

- [ ] **Step 2: 파일 존재 확인**

```bash
ls -la /Users/jaybee/lab/AIFAB-harness/.claude/plugins/aifab/skills/grill.md
```
Expected: 파일이 존재하고 크기가 0보다 큼

- [ ] **Step 3: frontmatter 유효성 확인**

```bash
head -10 /Users/jaybee/lab/AIFAB-harness/.claude/plugins/aifab/skills/grill.md
```
Expected: `---`, `name: aifab:grill`, `description:` 가 포함된 YAML frontmatter

- [ ] **Step 4: 커밋**

```bash
git add .claude/plugins/aifab/skills/grill.md
git commit -m "feat(skills): add /aifab:grill (mattpocock grill-with-docs)"
```

---

### Task 2: `/aifab:grill-me` 스킬 파일 생성

**Files:**
- Create: `.claude/plugins/aifab/skills/grill-me.md`

- [ ] **Step 1: 파일 생성**

`.claude/plugins/aifab/skills/grill-me.md` 를 아래 내용으로 생성한다:

```markdown
---
name: aifab:grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test an idea or plan without codebase context. For code-aware sessions with CONTEXT.md updates, use /aifab:grill instead.
argument-hint: [<topic>]
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
---

# `/aifab:grill-me` — 아이디어 인터뷰

**담당 모델:** Advisor (claude-opus-4-7)

---

## 역할

코드베이스와 무관하게, 아이디어나 플랜에 대해 모든 측면을 인터뷰로 탐색하여 공유된 이해에 도달한다. `CONTEXT.md` 참조 없음. 기술 결정 전 아이디어 검증에 적합하다.

---

## `/aifab:grill` 과의 차이

| | `/aifab:grill-me` | `/aifab:grill` |
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
```

- [ ] **Step 2: 파일 존재 확인**

```bash
ls -la /Users/jaybee/lab/AIFAB-harness/.claude/plugins/aifab/skills/grill-me.md
```
Expected: 파일이 존재하고 크기가 0보다 큼

- [ ] **Step 3: 커밋**

```bash
git add .claude/plugins/aifab/skills/grill-me.md
git commit -m "feat(skills): add /aifab:grill-me (mattpocock grill-me)"
```

---

### Task 3: `/aifab:caveman` 스킬 파일 생성

**Files:**
- Create: `.claude/plugins/aifab/skills/caveman.md`

- [ ] **Step 1: 파일 생성**

`.claude/plugins/aifab/skills/caveman.md` 를 아래 내용으로 생성한다:

```markdown
---
name: aifab:caveman
description: >
  Ultra-compressed communication mode. Cuts token usage ~75% by dropping
  filler, articles, and pleasantries while keeping full technical accuracy.
  Activated by /aifab:caveman, "caveman mode", "talk like caveman", "less tokens", "be brief".
  Stays active until user says "stop caveman" or "normal mode".
allowed-tools: []
---

# `/aifab:caveman` — 초압축 통신 모드

---

## 활성화

이 스킬이 호출되면 즉시 caveman 모드로 전환한다.

---

## 규칙

**제거 대상:** 관사(a/an/the), 군더더기(just/really/basically/actually/simply), 인사말(sure/certainly/of course/happy to), 헤징 표현, 접속사

**유지 대상:** 기술 용어(정확하게), 코드 블록(그대로), 에러 메시지(그대로 인용)

**단축:** DB/auth/config/req/res/fn/impl. 짧은 동의어 사용(big not extensive, fix not "implement a solution for"). 인과는 화살표(X → Y).

**패턴:** `[대상] [동작] [이유]. [다음 단계].`

**금지:** "Sure! I'd be happy to help you with that."
**허용:** "Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"

---

## 지속성

한번 활성화되면 세션 내내 유지. 해제: "stop caveman" 또는 "normal mode".

---

## 예외 (일시 중단 후 재개)

- 보안 경고
- 되돌릴 수 없는 작업 확인
- 다단계 순서에서 단편이 오독될 위험
- 사용자가 재질문하거나 명확화 요청
```

- [ ] **Step 2: 파일 존재 확인**

```bash
ls -la /Users/jaybee/lab/AIFAB-harness/.claude/plugins/aifab/skills/caveman.md
```
Expected: 파일이 존재하고 크기가 0보다 큼

- [ ] **Step 3: 커밋**

```bash
git add .claude/plugins/aifab/skills/caveman.md
git commit -m "feat(skills): add /aifab:caveman (mattpocock caveman)"
```

---

### Task 4: `/aifab:diagnose` 스킬 파일 생성

**Files:**
- Create: `.claude/plugins/aifab/skills/diagnose.md`

- [ ] **Step 1: 파일 생성**

`.claude/plugins/aifab/skills/diagnose.md` 를 아래 내용으로 생성한다:

```markdown
---
name: aifab:diagnose
description: Disciplined diagnosis loop for hard bugs and performance regressions. Reproduce → minimise → hypothesise → instrument → fix → regression-test. Use when bug is reproducible. For hard-to-reproduce bugs with unclear cause, use /aifab:debug instead.
argument-hint: <symptom>
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:diagnose` — 재현 우선 디버깅 루프

**담당 모델:** Sonnet (claude-sonnet-4-6) — 재현·계측·수정

---

## `/aifab:debug` 와의 차이

| | `/aifab:diagnose` | `/aifab:debug` |
|--|-------------------|-----------------|
| 접근 | 재현 루프 구축 → 최소화 → 계측 | 가설 수립 → 증거 수집 → RCA |
| 강점 | 재현 가능한 버그, 빠른 피드백 루프 | 재현 어려운 버그, 복잡한 원인 분석 |
| 선택 기준 | 재현 가능 | 재현 안 됨 / 원인 불명 |

---

## Phase 1 — 피드백 루프 구축 (핵심)

**이것이 전부다.** 빠르고 결정적이며 자동 실행 가능한 Pass/Fail 신호가 있으면 버그를 찾을 수 있다. 없으면 코드를 아무리 봐도 해결 안 된다.

여기에 불균형적으로 많은 노력을 쏟는다. 적극적으로, 창의적으로, 포기 없이.

### 피드백 루프 구축 방법 (이 순서로 시도)

1. **실패하는 테스트** — 버그에 닿는 seam에서 unit/integration/e2e 테스트
2. **curl / HTTP 스크립트** — 실행 중인 dev 서버 대상
3. **CLI 호출** — fixture 입력으로 stdout을 known-good 스냅샷과 diff
4. **Playwright 스크립트** — UI 조작, DOM/console/network 어설션
5. **캡처된 트레이스 재생** — 실제 요청/페이로드를 디스크에 저장 후 재생
6. **throwaway 하네스** — 최소한의 시스템 서브셋으로 버그 코드 경로 격리
7. **Property/fuzz 루프** — "가끔 잘못된 출력" 버그라면 1000개 랜덤 입력
8. **이분 하네스** — 두 알려진 상태 사이에서 버그가 나타난다면 `git bisect run`
9. **차분 루프** — 같은 입력을 구버전 vs 신버전으로 실행하고 출력 diff

### 루프 품질 기준

- 더 빠르게 만들 수 있나? (설정 캐시, 무관한 초기화 스킵, 테스트 범위 축소)
- 신호가 더 정확한가? (구체적 증상 어설션, "안 죽었음"이 아닌 것)
- 더 결정적인가? (시간 고정, RNG 시드, 파일시스템 격리, 네트워크 동결)

30초 flaky 루프 < 2초 결정적 루프.

### 루프 없이는 진행 불가

루프를 구축할 수 없으면 명시적으로 중단하고 사용자에게 요청:
- 재현되는 환경 접근권
- 캡처된 아티팩트 (HAR, 로그 덤프, 스크린 녹화)
- 임시 프로덕션 계측 권한

---

## Phase 2 — 재현

루프를 실행한다. 버그가 나타나는 것을 확인한다.

체크리스트:
- [ ] 루프가 사용자가 설명한 **정확한** 실패 모드를 재현하는가 (근처의 다른 실패가 아닌)
- [ ] 여러 번 실행해도 재현되는가 (또는 비결정적 버그라면 충분히 높은 재현율인가)
- [ ] 정확한 증상이 캡처되었는가 (에러 메시지, 잘못된 출력, 느린 타이밍)

---

## Phase 3 — 가설 수립

테스트 전에 **3-5개의 순위가 매겨진 가설**을 생성한다.

각 가설은 반증 가능해야 한다:
> "만약 X가 원인이라면, Y를 변경하면 버그가 사라질 것이다 / Z를 변경하면 더 심해질 것이다."

예측을 서술할 수 없으면 그것은 가설이 아니라 직감이다 — 버린다.

**테스트 전에 순위 목록을 사용자에게 보여준다.** 도메인 지식으로 즉시 재순위가 가능하다. 사용자가 AFK이면 자신의 순위로 진행한다.

---

## Phase 4 — 계측

각 탐침은 Phase 3의 특정 예측에 매핑되어야 한다. **한 번에 변수 하나만 변경한다.**

도구 우선순위:
1. **디버거 / REPL 검사** — 환경이 지원하면. 브레이크포인트 하나가 로그 열 개보다 낫다.
2. **경계에 타겟팅된 로그** — 가설을 구별하는 경계에만
3. "모든 것을 로그하고 grep"은 금지

**모든 디버그 로그에 고유 태그 부착:** `[DEBUG-a4f2]`. 정리는 grep 하나로. 태그 없는 로그는 생존, 태그 있는 로그는 Phase 6에서 제거.

**성능 버그:** 로그 대신 타이밍 하네스/profiler/쿼리 플랜으로 베이스라인 측정 후 이분.

---

## Phase 5 — 수정 + 회귀 테스트

수정 **전에** 회귀 테스트를 작성한다 — 단, 올바른 seam이 있을 때만.

올바른 seam: 테스트가 실제 호출 지점에서 실제 버그 패턴을 실행하는 것.

올바른 seam이 있으면:
1. 최소화된 repro를 그 seam에서 실패하는 테스트로 전환
2. 실패 확인
3. 수정 적용
4. 통과 확인
5. Phase 1 피드백 루프를 원래(최소화 전) 시나리오에 재실행

올바른 seam이 없으면: 그것 자체가 발견이다. 기록하고 넘어간다.

---

## Phase 6 — 정리 + 사후 분석

완료 선언 전 필수:
- [ ] 원본 repro가 더 이상 재현되지 않음 (Phase 1 루프 재실행)
- [ ] 회귀 테스트 통과 (또는 seam 부재 문서화)
- [ ] 모든 `[DEBUG-...]` 계측 제거 (태그로 grep)
- [ ] throwaway 프로토타입 삭제
- [ ] 실제 원인이 된 가설이 커밋/PR 메시지에 기술됨

**그 다음:** "이 버그를 무엇이 예방했을까?" 답이 아키텍처 변경을 포함하면 (좋은 test seam 없음, 얽힌 caller, 숨겨진 결합) `/aifab:refactor`에 구체적 사항과 함께 위임한다. 수정 **후에** 이 추천을 한다.
```

- [ ] **Step 2: 파일 존재 확인**

```bash
ls -la /Users/jaybee/lab/AIFAB-harness/.claude/plugins/aifab/skills/diagnose.md
```
Expected: 파일이 존재하고 크기가 0보다 큼

- [ ] **Step 3: 커밋**

```bash
git add .claude/plugins/aifab/skills/diagnose.md
git commit -m "feat(skills): add /aifab:diagnose (mattpocock diagnose)"
```

---

### Task 5: SKILLS.md 업데이트

**Files:**
- Modify: `.claude/plugins/aifab/SKILLS.md`

- [ ] **Step 1: "정렬/언어" 카테고리 섹션 추가**

`.claude/plugins/aifab/SKILLS.md` 에서 `## 스킬 카테고리` 섹션을 찾아, `### 🎯 핵심 워크플로우 (7)` 앞에 다음 섹션을 삽입한다:

```markdown
### 🗣️ 정렬/언어 (4) — mattpocock 통합
구현 전 요구사항 정렬, 도메인 언어 확립, 토큰 효율화.

| 명령어 | 역할 |
|--------|------|
| `/aifab:grill` | 구현 전 인터뷰 + CONTEXT.md / ADR 실시간 업데이트 |
| `/aifab:grill-me` | 코드 무관 아이디어/플랜 인터뷰 |
| `/aifab:caveman` | 토큰 75% 절감 초압축 모드 |
| `/aifab:diagnose` | 재현→최소화→가설→계측→수정→회귀테스트 디버깅 루프 |

```

- [ ] **Step 2: 총계 업데이트**

`**총 16 스킬.**` 를 `**총 20 스킬.**` 로 수정한다.

- [ ] **Step 3: 의존성 그래프 업데이트**

의존성 그래프에서 최상단에 다음을 추가한다:

```
/aifab:grill  →  /aifab:discover  →  /aifab:plan  →  /aifab:execute
(선택적 전처리)
```

- [ ] **Step 4: 스킬간 호출 관계 테이블에 추가**

```markdown
| `grill` | `worklog init` | 프로젝트 시작 시 선택적 |
| `diagnose` | `refactor` | 아키텍처 문제 발견 시 |
```

- [ ] **Step 5: 모델 사용 매트릭스에 추가**

```markdown
| grill | ●●● | - | - |
| grill-me | ●●● | - | - |
| caveman | - | - | - |
| diagnose | - | ●●● | - |
```

- [ ] **Step 6: 커밋**

```bash
git add .claude/plugins/aifab/SKILLS.md
git commit -m "docs(skills): add 정렬/언어 category with 4 mattpocock skills"
```

---

### Task 6: CLAUDE.md 업데이트

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 커맨드 테이블에 4개 추가**

`CLAUDE.md`에서 `## AI-Fab Workflow Commands` 섹션의 테이블을 찾아 다음 4개 행을 추가한다:

```markdown
| `/aifab:grill` | 구현 전 1:1 인터뷰로 요구사항 정렬 + CONTEXT.md / ADR 실시간 업데이트 |
| `/aifab:grill-me` | 코드 무관 아이디어/플랜 인터뷰로 공유된 이해 도달 |
| `/aifab:caveman` | 토큰 75% 절감 초압축 모드 (세션 내 지속, "stop caveman"으로 해제) |
| `/aifab:diagnose` | 재현→최소화→가설→계측→수정 순서의 결정적 디버깅 루프 |
```

- [ ] **Step 2: 총계 라인 업데이트**

`**전체 16 스킬.**` 을 `**전체 20 스킬.**` 로 수정한다.

- [ ] **Step 3: 커밋**

```bash
git add CLAUDE.md
git commit -m "docs: add 4 mattpocock skills to command table in CLAUDE.md"
```

---

### Task 7: 심볼릭 링크 갱신 확인

**Files:**
- Verify: `~/.claude/commands/aifab` symlink

- [ ] **Step 1: 심볼릭 링크 대상 확인**

```bash
ls -la ~/.claude/commands/aifab
```
Expected: `.claude/plugins/aifab/skills` 를 가리키는 symlink

- [ ] **Step 2: 새 스킬 파일이 링크를 통해 노출되는지 확인**

```bash
ls ~/.claude/commands/aifab/ | grep -E "grill|caveman|diagnose"
```
Expected: `grill.md`, `grill-me.md`, `caveman.md`, `diagnose.md` 4개 출력

심볼릭 링크는 디렉토리 전체를 참조하므로 별도 갱신 불필요. 파일만 추가하면 자동으로 노출된다.

- [ ] **Step 3: 최종 커밋 확인**

```bash
git log --oneline -6
```
Expected: Task 1~6의 커밋 6개가 순서대로 출력됨
