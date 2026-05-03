---
name: aifab:playwright
description: E2E UI test generation with Playwright
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:playwright` — Playwright E2E 테스트 생성 및 실행

**담당 모델:** Sonnet (구현) + Haiku (스텁 생성)

---

## 역할

모든 개발 Wave가 완료된 후, PLAN.md와 ARCHITECTURE.md를 기반으로 주요 사용자 시나리오를 커버하는 Playwright E2E 테스트를 생성하고 실행한다. 모든 테스트가 통과할 때까지 앱 버그 또는 테스트 오류를 수정한다.

---

## 사전 조건 확인

다음 세 가지를 순서대로 확인한다.

**1. Wave 완료 여부 확인**

`WORKLOG.md`를 읽어 PLAN.md의 모든 Wave가 `[x]`로 표시되어 있는지 확인한다.
- 완료되지 않은 Wave가 있으면 즉시 중단하고 다음 메시지를 출력한다:
  > "아직 완료되지 않은 Wave가 있습니다. `/aifab:execute`로 남은 Wave를 먼저 완료해주세요."

**2. 앱 실행 가능 여부 확인**

`package.json` 또는 `Makefile`에서 앱 시작 스크립트를 확인한다.
- `package.json`: `"start"`, `"dev"`, `"serve"` 스크립트 중 하나가 있어야 한다.
- `Makefile`: `make run`, `make start`, `make dev` 타겟이 있어야 한다.
- 시작 방법을 찾지 못하면: ARCHITECTURE.md에서 실행 명령을 추론한다.

**3. Playwright 설치 여부 확인**

```bash
# Node.js 프로젝트
npx playwright --version

# Python 프로젝트
pip show playwright
```

---

## 1단계: Playwright 설치 (미설치 시)

**Node.js 프로젝트:**
```bash
npm install -D @playwright/test
npx playwright install chromium
```

**Python 프로젝트:**
```bash
pip install playwright
playwright install chromium
```

---

## 2단계: 테스트 시나리오 도출

`PLAN.md`와 `ARCHITECTURE.md`를 읽어 주요 사용자 여정을 추출한다. 각 Wave의 기능을 기반으로 아래 최소 시나리오를 반드시 포함한다.

| 시나리오 | 설명 |
|---------|------|
| **Happy Path** | 핵심 사용자 흐름 처음부터 끝까지 |
| **Auth Flow** | 로그인, 로그아웃, 인증이 필요한 라우트 접근 시도 |
| **CRUD 작업** | 주요 엔티티의 생성, 조회, 수정, 삭제 |
| **에러 상태** | 잘못된 입력, 404 페이지, 네트워크 오류 |
| **AI/LLM 기능** | (해당 시) 입력 → 응답 흐름, 스트리밍 포함 |

---

## 3단계: 테스트 파일 생성

**Haiku 에이전트**가 테스트 스텁을 생성하고, **Sonnet 에이전트**가 실제 테스트 로직을 구현한다.

**파일 구조:**
```
tests/e2e/
├── auth.spec.ts       (또는 .py)
├── core-flow.spec.ts
├── crud.spec.ts
└── error-states.spec.ts
```

**TypeScript 테스트 템플릿:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('<기능명>', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('<시나리오명>', async ({ page }) => {
    // Arrange
    // Act
    // Assert
    await expect(page.locator('[data-testid="..."]')).toBeVisible();
  });
});
```

**Python 테스트 템플릿:**
```python
import pytest
from playwright.sync_api import Page, expect

def test_scenario_name(page: Page):
    # Arrange
    page.goto("http://localhost:3000")
    # Act
    # Assert
    expect(page.locator('[data-testid="..."]')).to_be_visible()
```

**Playwright 설정 파일 (`playwright.config.ts`) 생성 — 없을 경우:**
```typescript
import { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
  },
};

export default config;
```

---

## 4단계: 앱 실행 후 테스트 수행

1. 사전 조건 확인에서 파악한 시작 명령으로 앱을 백그라운드에서 실행한다:
   ```bash
   # 예시 (실제 명령은 ARCHITECTURE.md 기준으로 결정)
   npm run dev &
   # 또는
   make run &
   ```

2. 앱이 준비될 때까지 잠시 대기한 후 테스트를 실행한다:
   ```bash
   # Node.js
   npx playwright test --reporter=html

   # Python
   playwright test
   ```

---

## 5단계: 실패 처리

각 실패한 테스트에 대해 다음 절차를 반복한다:

1. **Playwright가 자동으로 스크린샷을 캡처**한다 (설정에 `screenshot: 'only-on-failure'` 포함 시).
2. **Sonnet 에이전트**가 실패 원인을 분석한다:
   - **앱 버그인 경우:** 앱 코드를 수정하고 해당 테스트만 재실행한다.
     ```bash
     npx playwright test tests/e2e/auth.spec.ts --reporter=html
     ```
   - **테스트 문제인 경우 (셀렉터/어설션 오류):** 테스트 코드를 수정하고 재실행한다.
3. 모든 테스트가 통과할 때까지 반복한다.

---

## 6단계: 리포트 생성 및 완료 처리

모든 테스트가 통과하면:

1. 결과 요약을 출력한다:
   ```
   ✓ N개 테스트 통과, 0개 실패
   ```

2. HTML 리포트를 `tests/e2e/report.html`에 저장한다:
   ```bash
   npx playwright show-report
   ```

3. `WORKLOG.md`에 다음 내용을 추가한다:
   ```markdown
   ## [YYYY-MM-DD] Playwright E2E 테스트 완료
   - 총 테스트 수: N개
   - 결과: 전체 통과
   - 커버된 시나리오: Happy Path, Auth Flow, CRUD, 에러 상태
   - 리포트 위치: tests/e2e/report.html
   ```

4. 다음 메시지를 출력한다:
   > "E2E 테스트 통과! `/aifab:uat`로 사용자 인수 테스트를 진행하세요."

---

## 주의사항

- 테스트 선택자는 `data-testid` 속성을 우선 사용한다. 없으면 ARIA 역할(`role=`, `aria-label=`)을 사용하고, CSS 클래스 선택은 최후 수단으로만 사용한다.
- 각 테스트는 독립적으로 실행 가능해야 한다 (테스트 간 상태 공유 금지).
- 앱이 시작되는 데 시간이 걸릴 경우, `waitForSelector` 또는 `waitForURL`로 준비 상태를 확인한다.
- Python 프로젝트는 `pytest-playwright` 플러그인 사용을 권장한다:
  ```bash
  pip install pytest-playwright
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
