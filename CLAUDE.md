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

- **컨텍스트 창을 항상 50% 미만으로 유지한다.**
- 각 작업 단위(work unit) 완료 후, 컨텍스트 사용량을 확인한다.
- 상태 표시줄의 컨텍스트 % 기준:
  - **35–49%**: 황색 경고 — 다음 태스크 시작 전 /compact 실행을 준비한다.
  - **50% 이상**: 즉각 조치 — 다음 태스크를 시작하기 전에 *반드시* `/compact`를 실행한다.
- **컨텍스트가 50% 이상인 상태에서 새 태스크를 절대 시작하지 않는다.**

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

| 명령어 | 설명 |
|---|---|
| `/aifab:discover` | 프로젝트 구조 및 기존 코드베이스를 분석하여 컨텍스트를 수집한다 |
| `/aifab:plan` | 요구사항을 파악하고 구현 웨이브(wave)로 분해한 실행 계획을 생성한다 |
| `/aifab:execute` | 계획된 웨이브를 순서대로 실행하며 기능을 구현한다 |
| `/aifab:security` | 하드코딩된 시크릿, 취약한 의존성, 보안 결함을 스캔한다 |
| `/aifab:playwright` | Playwright E2E 테스트를 생성하고 실행한다 |
| `/aifab:uat` | 사용자 인수 테스트(UAT) 시나리오를 준비하고 실행한다 |
| `/aifab:worklog` | 완료된 작업, 결정 사항, 변경 이력을 기록한다 |
| `/aifab:debug` | 4단계 RCA(가설→증거→검증→수정)로 체계적 디버깅을 수행한다 |
| `/aifab:map-codebase` | 4-병렬 매퍼(tech/arch/quality/concerns)로 코드베이스를 분석한다 |
| `/aifab:worktree` | git worktree로 병렬 Wave를 동시 진행할 수 있게 한다 |
| `/aifab:codex-review` | OpenAI Codex CLI로 교차 AI 검증을 수행한다 |
| `/aifab:refactor` | 동작 보존 점진 리팩토링 (REFACTOR-LOG.md 작성, 단계별 commit) |
| `/aifab:migrate` | 의존성/프레임워크 마이그레이션 (codemod 활용, Wave 단위 적용) |
| `/aifab:rollback` | Wave 단위 안전한 롤백 (백업 브랜치 자동 생성) |
| `/aifab:compare` | N개 옵션 비교 (트레이드오프 매트릭스 + 추천) |
| `/aifab:adr` | Architecture Decision Records 관리 (Michael Nygard 형식) |

**전체 16 스킬.** 카테고리/의존성 그래프: [`SKILLS.md`](.claude/plugins/aifab/SKILLS.md)
**공통 표준:** [`_shared/`](.claude/plugins/aifab/_shared/) (prerequisites, output-format, worklog-update, agent-dispatch, git-commit)

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
