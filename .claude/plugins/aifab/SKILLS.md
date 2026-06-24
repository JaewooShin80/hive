# AI-Fab Skills Index

AI-Fab 워크플로우의 모든 스킬과 의존성 그래프.

## 스킬 카테고리

### 🗣️ 정렬/언어 (4) — mattpocock 통합
구현 전 요구사항 정렬, 도메인 언어 확립, 토큰 효율화.

| 명령어 | 역할 |
|--------|------|
| `/aifab:grill` | 구현 전 인터뷰 + CONTEXT.md / ADR 실시간 업데이트 |
| `/aifab:grill-me` | 코드 무관 아이디어/플랜 인터뷰 |
| `/aifab:caveman` | 토큰 75% 절감 초압축 모드 |
| `/aifab:diagnose` | 재현→최소화→가설→계측→수정→회귀테스트 디버깅 루프 |

### 🎯 핵심 워크플로우 (7)
프로젝트 시작부터 완료까지의 표준 흐름.

| 명령어 | 단계 | 역할 |
|--------|------|------|
| `/aifab:discover` | 시작 | 아키텍처 결정 (제약 없음, 질문 합성) |
| `/aifab:plan` | 계획 | Wave 분해, PLAN.md 작성 |
| `/aifab:execute` | 구현 | Opus→Sonnet/Haiku 병렬 오케스트레이션 |
| `/aifab:security` | 검증 | OWASP/AI-LLM/API/시크릿 4영역 |
| `/aifab:playwright` | 검증 | E2E UI 테스트 |
| `/aifab:uat` | 검증 | 사용자 인수 테스트 |
| `/aifab:worklog` | 추적 | 작업일지 + 재시작 |

### 🔧 보조 도구 (4)
필요 시 호출하는 보조 스킬.

| 명령어 | 역할 |
|--------|------|
| `/aifab:debug` | 4단계 RCA 디버깅 |
| `/aifab:map-codebase` | 4-병렬 매퍼 분석 (brownfield) |
| `/aifab:worktree` | 병렬 Wave git worktree |
| `/aifab:codex-review` | OpenAI Codex 교차 검증 |

### ⚙️ 코드 조작 (3) — v2 추가
기존 코드의 안전한 변경.

| 명령어 | 역할 |
|--------|------|
| `/aifab:refactor` | 동작 보존 리팩토링 |
| `/aifab:migrate` | 의존성/프레임워크 마이그레이션 |
| `/aifab:rollback` | Wave 단위 안전한 되돌리기 |

### 🤔 결정/비교 (2) — v2 추가
의사결정 지원.

| 명령어 | 역할 |
|--------|------|
| `/aifab:compare` | 옵션 N개 비교 + 추천 |
| `/aifab:adr` | Architecture Decision Records |

**총 20 스킬.**

---

## 의존성 그래프

```
/aifab:grill  →  /aifab:discover  →  /aifab:plan  →  /aifab:execute
(선택적 전처리)

                ┌──────────────────────────┐
                │    /aifab:map-codebase   │ (brownfield 시작)
                └──────────────┬───────────┘
                               ↓
┌──────────────────────────────────────────────────────────┐
│  /aifab:discover  →  /aifab:plan  →  /aifab:execute     │
│        ↓                  ↓               ↓              │
│   ARCHITECTURE.md     PLAN.md        WORKLOG.md update   │
└──────────────────────────────┬───────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ↓                      ↓                      ↓
 /aifab:security      /aifab:playwright        /aifab:uat
        │                      │                      │
        ↓                      ↓                      ↓
   (Wave 별 자동)        (전체 후 1회)         (UAT 결과 수집)

↑↓ 모든 단계에서 호출 가능:
   /aifab:worklog (상태 추적)
   /aifab:debug (이슈 발생 시)
   /aifab:worktree (병렬 진행)
   /aifab:codex-review (선택적 검증)
   /aifab:refactor (안정 후 개선)
   /aifab:migrate (의존성 변경)
   /aifab:rollback (롤백)
   /aifab:compare (결정 시점)
   /aifab:adr (결정 기록)
```

---

## 스킬간 호출 관계

| Caller | Callee | 시점 |
|--------|--------|------|
| `discover` | `worklog init` | 프로젝트 시작 시 자동 |
| `discover` | `map-codebase` | brownfield 감지 시 권장 |
| `plan` | `compare` | 라이브러리 선택 갈림길에서 |
| `plan` | `adr` | 주요 결정 자동 기록 |
| `execute` | `security` | 각 Wave 종료 후 자동 |
| `execute` | `worktree` | --parallel 옵션 시 |
| `execute` | `debug` | 테스트 실패 시 |
| `execute` | `codex-review` | settings 활성화 시 자동 |
| `playwright` | `debug` | E2E 실패 시 |
| `uat` | `plan` | 피드백 반영 새 Wave 추가 |
| `uat` | `execute` | 새 Wave 실행 |
| `refactor` | `plan` | 리팩토링 Wave 분해 |
| `refactor` | `execute` | Wave 적용 |
| `migrate` | `plan` | 마이그레이션 Wave 분해 |
| `rollback` | `worklog update` | 상태 복원 |
| 모든 스킬 | `worklog update` | 시작/종료 시 |
| `grill` | `worklog init` | 프로젝트 시작 시 선택적 |
| `diagnose` | `refactor` | 아키텍처 문제 발견 시 |

---

## 모델 사용 매트릭스

| 스킬 | Advisor (Opus) | Worker (Sonnet) | Generator (Haiku) |
|------|:---:|:---:|:---:|
| discover | ●●● | ○ | - |
| plan | ●●● | ○ | - |
| execute | ●● (조정/검토) | ●●● | ●● |
| security | ●●● | ○ | - |
| playwright | ● | ●●● | ●● |
| uat | ●●● | ○ | - |
| worklog | - | ● | - |
| debug | ●●● | ●● | - |
| map-codebase | ●● (조정) | ●●●× 4 | - |
| worktree | - | ●● | - |
| codex-review | ●●● | ○ | - |
| refactor | ●● | ●●● | - |
| migrate | ●● | ●●● | ●● |
| rollback | ●● | ● | - |
| compare | ●●● | ● | - |
| adr | ●● | ● | - |
| grill | ●●● | - | - |
| grill-me | ●●● | - | - |
| caveman | - | - | - |
| diagnose | - | ●●● | - |

`●●●` 주력 / `●●` 보조 / `●` 가벼운 사용 / `○` 거의 안 씀 / `-` 미사용

---

## 공통 패턴 (`_shared/`)

모든 스킬이 참조하는 공통 프로토콜:

| 파일 | 내용 |
|------|------|
| [`_shared/prerequisites.md`](_shared/prerequisites.md) | 사전조건 체크 매트릭스 |
| [`_shared/worklog-update.md`](_shared/worklog-update.md) | WORKLOG.md 업데이트 표준 |
| [`_shared/agent-dispatch.md`](_shared/agent-dispatch.md) | Sub-agent 디스패치 프롬프트 |
| [`_shared/git-commit.md`](_shared/git-commit.md) | 커밋 메시지 컨벤션 |
| [`_shared/output-format.md`](_shared/output-format.md) | Verdict/Status/Severity 표준 |

각 스킬 파일의 "Prerequisites" 섹션은 `_shared/prerequisites.md`의 해당 행을 참조한다 (DRY).

---

## 토큰 예산

| 카테고리 | 스킬 수 | 평균 토큰 | 합계 |
|----------|--------|---------|------|
| 핵심 워크플로우 | 7 | ~1,600 | ~11,200 |
| 보조 도구 | 4 | ~1,400 | ~5,600 |
| 코드 조작 | 3 | ~1,500 | ~4,500 |
| 결정/비교 | 2 | ~1,200 | ~2,400 |
| 공통 패턴 | 5 | ~1,000 | ~5,000 |
| **총계** | **16+5** | - | **~28,700** |

CLAUDE.md(1,100) + 스킬 1개 평균 사용 시: ~2,700 토큰 (Context의 1.4%).

---

## 자동 인덱스 (전체 스킬)

> 아래 표는 `scripts/gen_skills_index.py`가 각 스킬 frontmatter의 `description`에서
> 자동 생성한다. 직접 편집하지 말 것 — `python3 scripts/gen_skills_index.py --write SKILLS.md`로 갱신.
> CI는 `--check`로 stale 여부를 검증한다.

<!-- AUTO-INDEX:start -->
| Command | Description |
| --- | --- |
| `/aifab:adr` | Manage Architecture Decision Records (Michael Nygard format) |
| `/aifab:caveman` | Ultra-compressed communication mode. Cuts token usage ~75% by dropping filler, articles, and pleasantries while keeping full technical accuracy. Activated by /aifab:caveman, "caveman mode", "talk like caveman", "less tokens", "be brief". Stays active until user says "stop caveman" or "normal mode". |
| `/aifab:codex-review` | Cross-AI verification via OpenAI Codex CLI |
| `/aifab:compare` | Use when facing a multi-option technical decision and needing a structured trade-off analysis. Triggers on /aifab:compare command. Use when selecting libraries, architecture patterns, frameworks, design patterns, or algorithms and wanting a weighted decision matrix with recommendation. |
| `/aifab:debug` | Systematic 4-stage RCA debugging |
| `/aifab:diagnose` | Disciplined diagnosis loop for hard bugs and performance regressions. Reproduce → minimise → hypothesise → instrument → fix → regression-test. Use when bug is reproducible. For hard-to-reproduce bugs with unclear cause, use /aifab:debug instead. |
| `/aifab:discover` | Use when starting a new project or feature and needing to select the right architecture. Triggers on /aifab:discover command. Use when the user has not yet chosen a tech stack, wants to explore options, or needs a structured discovery session before planning. |
| `/aifab:evaluate` | Live feature verification via Playwright MCP. Reads feature-list.json, drives each feature's verify URL/command, updates status (passing/failing/partial). Anthropic 3-agent Evaluator role. |
| `/aifab:execute` | Multi-agent Wave execution (Opus + Sonnet/Haiku) |
| `/aifab:grill` | Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates CONTEXT.md and ADRs inline as decisions crystallise. Use before /aifab:discover when requirements are fuzzy or when the user wants to stress-test a plan. |
| `/aifab:grill-me` | Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test an idea or plan without codebase context. For code-aware sessions with CONTEXT.md updates, use /aifab:grill instead. |
| `/aifab:map-codebase` | 4-parallel mappers for codebase analysis |
| `/aifab:migrate` | Dependency/framework migration |
| `/aifab:milestone` | Manage project milestones (semver tags). Subcommands new/complete/audit handle milestone lifecycle from start to git tag. Use new at project start, audit before declaring done, complete to tag. |
| `/aifab:plan` | Wave-based implementation plan creation |
| `/aifab:playwright` | E2E UI test generation with Playwright |
| `/aifab:progress` | Display project progress dashboard — milestone, phase progression, wave completion percentages, current position, and next recommended command. Reads ROADMAP.md and PLAN.md. |
| `/aifab:refactor` | Behavior-preserving incremental refactoring |
| `/aifab:roadmap` | Manage project roadmap (Phase-level grouping of Waves) and milestone metadata. Subcommands init/add-phase/update. Generates ROADMAP.md as the index above PLAN.md. |
| `/aifab:rollback` | Safe Wave-level rollback with backup |
| `/aifab:security` | 5-domain security review (OWASP/AI-LLM/API/Secrets/Dependencies) |
| `/aifab:uat` | UAT scenarios + result collection |
| `/aifab:worklog` | Work log for resumable sessions |
| `/aifab:worktree` | Parallel Wave via git worktrees |
<!-- AUTO-INDEX:end -->

