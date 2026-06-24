# CLAUDE.md — AI-Fab 프로젝트 전역 규칙

이 파일은 AI-Fab 프로젝트 내 모든 Claude Code 인터랙션을 지배하는 전역 규칙 파일이다.
규칙이지 제안이 아니다. 예외 없이 따른다.

---

## RULE 1: Think Before Coding (코딩 전 반드시 사고하라)

- 가정(assumption)을 명시적으로 선언한다. 불확실하면 반드시 질문한다.
- 요청이 여러 해석을 허용할 경우, 하나를 임의로 선택하지 말고 복수의 해석을 제시하고 확인받는다.
- 트레이드오프를 표면화한다. 구현 전에 장단점을 명시한다.
- 잘못된 가정 위에서는 절대 진행하지 않는다.

## RULE 2: Simplicity First (단순함을 최우선으로)

- 문제를 해결하는 최소한의 코드만 작성한다.
- 요청받지 않은 기능, 추측성 코드, 미래를 위한 추상화는 금지한다.
- 단일 용도 코드에는 추상화 레이어를 추가하지 않는다.
- 요청되지 않은 유연성이나 설정 가능성(configurability)을 추가하지 않는다.

## RULE 3: Surgical Changes (외과적 변경만 허용)

- 작업과 무관한 코드는 건드리지 않는다.
- 변경된 모든 줄은 사용자의 요청으로부터 직접 추적 가능해야 한다.
- 기존 코드 스타일을 그대로 따른다.
- 요청받지 않은 한, 기존의 데드 코드(dead code)를 제거하지 않는다.

## RULE 4: Goal-Driven Execution (목표 중심 실행)

- 방법(HOW)이 아니라 목표(WHAT)를 정의한다.
- 성공 기준(success criteria)을 먼저 명시하고 구현을 시작한다.
- 에이전트가 목표를 달성할 때까지 루프를 돌도록 한다. 중간 단계를 과도하게 명령하지 않는다.

---

## RULE 5: Context Management (컨텍스트 창 관리 — 절대 규칙)

- **컨텍스트 창을 항상 80% 미만으로 유지한다.**
- 각 작업 단위(work unit) 완료 후, 컨텍스트 사용량을 확인한다.
- 상태 표시줄의 컨텍스트 % 기준:
  - **70–79%**: 황색 경고 — 다음 태스크 시작 전 /compact 실행을 준비한다.
  - **80% 이상**: 즉각 조치 — 다음 태스크를 시작하기 전에 *반드시* `/compact`를 실행한다.
- **컨텍스트가 80% 이상인 상태에서 새 태스크를 절대 시작하지 않는다.**

---

## Multi-Agent Model Assignment (모델 역할 배정)

| 모델 | 역할 | 담당 업무 |
|---|---|---|
| `claude-opus-4-7` | Advisor | 계획 수립, 아키텍처 결정, 작업 분배, 최종 리뷰 |
| `claude-sonnet-4-6` | Implementer | 일반 기능 구현, 비즈니스 로직, TDD 테스트 작성 |
| `claude-haiku-4-5` | Generator | 보일러플레이트 생성 (CRUD 엔드포인트, 모델 클래스, 설정 파일) |

모델은 `settings.json`의 환경 변수를 통해 교체할 수 있다.

---

## AI-Fab Workflow Commands (워크플로우 명령어)

> 아래 표는 `scripts/gen_skills_index.py`가 각 스킬 frontmatter `description`에서
> 자동 생성한다. 직접 편집하지 말 것 — 새 스킬 추가/변경 후
> `python3 scripts/gen_skills_index.py --write CLAUDE.md`로 갱신한다.
> CI가 `--check`로 stale 여부를 검증한다.

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
| `/aifab:security` | 4-domain security review (OWASP/AI-LLM/API/secrets) |
| `/aifab:uat` | UAT scenarios + result collection |
| `/aifab:worklog` | Work log for resumable sessions |
| `/aifab:worktree` | Parallel Wave via git worktrees |
<!-- AUTO-INDEX:end -->

| `/security-audit` | 정부 개발보안 가이드 기반 정적 점검 (웹/API 43항목 + AI/LLM 20항목 + Docker/NGINX) — `.claude/commands/security-audit.md` |

**전체 16 스킬.** 카테고리/의존성 그래프: [`SKILLS.md`](.claude/plugins/aifab/SKILLS.md)
**공통 표준:** [`_shared/`](.claude/plugins/aifab/_shared/) (prerequisites, output-format, worklog-update, agent-dispatch, git-commit)

---

## Hooks (자동 가드 — v2.2.0 Wave 1-3)

`~/.claude/settings.json`에 등록된 6개의 `aifab-*` hook이 모든 세션에서 자동 실행된다.
GSD hook 9종과 네임스페이스 분리되어 공존한다.

| Hook | Event | 역할 | Exit 정책 |
|---|---|---|---|
| `aifab-secret-guard.js` | PreToolUse(Write\|Edit) | 시크릿 패턴/금지 경로 차단 | exit 2 = block |
| `aifab-bash-guard.js` | PreToolUse(Bash) | `rm -rf /` 등 위험 명령 차단 | exit 2 = block |
| `aifab-ctx-guard.js` | PostToolUse(*) | 컨텍스트 50% RULE 5 가드 | advisory only |
| `aifab-worklog-auto.js` | PostToolUse(Edit\|Write\|MultiEdit) | WORKLOG.md "## 자동 기록" append | advisory |
| `aifab-session-start.js` | SessionStart | 현재 Wave + 진척% 출력 | advisory |
| `aifab-wave-gate.js` | PostToolUse(Bash) | `feat(wave-N)` 커밋 후 `/aifab:security` 안내 | advisory |

상세 동작/비활성화 방법: [`_shared/hooks.md`](.claude/plugins/aifab/_shared/hooks.md)

---

## Security Defaults (보안 기본값 — 비타협적)

- API 키, 비밀번호, 토큰 등 시크릿(secret)을 코드에 하드코딩하는 것은 **절대 금지**한다.
- 모든 시크릿은 환경 변수(environment variables)를 통해 주입한다.
- git 커밋에 시크릿이 포함되지 않도록 한다. 커밋 전 반드시 확인한다.

---

## Development Defaults (개발 기본값)

- **TDD를 항상 따른다**: Red → Green → Refactor 순서를 지킨다.
- 각 기능 또는 웨이브 완료 후 git 커밋을 수행한다.
- 각 웨이브 완료 후 `/aifab:security`를 실행하여 보안 검사를 수행한다.
- 테스트 실패나 버그 발생 시 추측하지 말고 `/aifab:debug`로 4단계 RCA를 수행한다.
- 기존 코드베이스 진입 시 `/aifab:map-codebase`로 먼저 분석한다.
- 독립 가능한 Wave는 `/aifab:worktree`로 병렬 진행을 고려한다.
- 중요 변경 후 `/aifab:codex-review`로 교차 AI 검증을 받을 수 있다.
- 동작 보존 변경은 `/aifab:refactor`로 점진 적용한다 (테스트 없는 코드 리팩토링 금지).
- 의존성/프레임워크 변경은 `/aifab:migrate`로 Wave 단위 적용한다.
- 롤백 필요 시 `/aifab:rollback`을 사용 (force-push 금지, 백업 브랜치 자동 보존).
- 결정 시점에 `/aifab:compare`로 옵션을 비교하고, 큰 결정은 `/aifab:adr`로 기록한다.
