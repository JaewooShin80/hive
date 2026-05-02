# Shared: Prerequisites Check Protocol

모든 `/aifab:*` 스킬이 시작 시 수행하는 표준 사전조건 체크.

## 표준 체크 순서

각 스킬은 자신에게 필요한 항목만 선별하여 체크한다.

### CHECK-1: Git 리포지토리
```
git rev-parse --git-dir &>/dev/null
```
실패 시: `❌ Git 리포지토리가 아닙니다. 'git init' 후 다시 시도하세요.`

### CHECK-2: ARCHITECTURE.md 존재
- 사용처: plan, execute, refactor, migrate
- 실패 시: `❌ ARCHITECTURE.md가 없습니다. /aifab:discover를 먼저 실행하세요.`

### CHECK-3: PLAN.md 존재
- 사용처: execute, security, playwright, uat, rollback
- 실패 시: `❌ PLAN.md가 없습니다. /aifab:plan을 먼저 실행하세요.`

### CHECK-4: WORKLOG.md 존재
- 사용처: 거의 모든 스킬
- 실패 시: `❌ WORKLOG.md가 없습니다. /aifab:worklog init <project-name>으로 초기화하세요.`

### CHECK-5: 작업 트리 청결
```
git diff --quiet && git diff --cached --quiet
```
- 사용처: refactor, migrate, rollback, worktree
- 실패 시: `⚠ 미커밋 변경사항이 있습니다. 커밋 또는 stash 후 진행하세요.`

### CHECK-6: 현재 브랜치 보호
- 사용처: execute, refactor, migrate
- 메인 브랜치(main/master)에서 직접 작업 금지
- 실패 시: `⚠ 메인 브랜치에서 직접 작업 중입니다. /aifab:worktree create 권장.`

### CHECK-7: Context 사용량
- 사용처: 모든 스킬 시작 시
- 50% 초과 시: `⚠ Context 50% 초과. /compact 후 다시 시도하세요.`
- 35-49%: 경고만 표시하고 진행

### CHECK-8: 도구 가용성
스킬별 필요 도구 점검:
- playwright: `npx playwright --version` 또는 `playwright --version`
- codex-review: `codex --version`
- map-codebase: `find`, `grep`

미설치 시 설치 명령 안내 후 사용자 확인.

## 스킬별 체크 매트릭스

| 스킬 | git | ARCH | PLAN | WORKLOG | 청결 | 브랜치 | ctx | 도구 |
|------|:---:|:----:|:----:|:-------:|:----:|:------:|:---:|:----:|
| discover | ✓ | - | - | - | - | - | ✓ | - |
| plan | ✓ | ✓ | - | ✓ | - | - | ✓ | - |
| execute | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| security | ✓ | - | - | ✓ | - | - | ✓ | - |
| playwright | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | playwright |
| uat | ✓ | - | ✓ | ✓ | - | - | ✓ | - |
| worklog | ✓ | - | - | - | - | - | - | - |
| debug | ✓ | - | - | ✓ | - | - | ✓ | - |
| map-codebase | ✓ | - | - | - | - | - | ✓ | find/grep |
| worktree | ✓ | - | ✓ | ✓ | ✓ | - | - | - |
| codex-review | ✓ | - | - | ✓ | - | - | ✓ | codex |
| refactor | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| migrate | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ | - |
| rollback | ✓ | - | ✓ | ✓ | ✓ | - | - | - |
| compare | ✓ | - | - | ✓ | - | - | ✓ | - |
| adr | ✓ | - | - | ✓ | - | - | - | - |

## 실패 처리 원칙

- 실패 시 즉시 중단. 부분 진행 금지.
- 사용자에게 정확한 원인 + 다음 액션 제시.
- 자동 복구 가능한 항목(예: WORKLOG.md 자동 init)은 사용자 확인 후 수행.
