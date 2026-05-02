# AI-Fab Skills Index

AI-Fab 워크플로우의 모든 스킬과 의존성 그래프.

## 스킬 카테고리

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

**총 16 스킬.**

---

## 의존성 그래프

```
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
