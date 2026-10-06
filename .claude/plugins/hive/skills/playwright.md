---
name: hive:playwright
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

# `/hive:playwright` — Playwright E2E 테스트 생성 및 실행

**담당 모델:** Sonnet (구현) + Haiku (스텁 생성)

---

## 역할

모든 개발 Wave가 완료된 후, PLAN.md와 ARCHITECTURE.md를 기반으로 주요 사용자 시나리오를 커버하는 Playwright E2E 테스트를 생성하고 실행한다. 모든 테스트가 통과할 때까지 앱 버그 또는 테스트 오류를 수정한다.

---

## 사전 조건 확인

다음 세 가지를 순서대로 확인한다.

**1. Wave 완료 여부 확인**

`PLAN.md`의 모든 Wave 완료 기준 체크박스가 `[x]`인지 확인한다 (`python3 scripts/hive_progress.py --json`의 `completed_waves == total_waves`).
- 완료되지 않은 Wave가 있으면 즉시 중단하고 다음 메시지를 출력한다:
  > "아직 완료되지 않은 Wave가 있습니다. `/hive:execute`로 남은 Wave를 먼저 완료해주세요."

**2. 실행 정보 확인** — PLAN.md "공통 규약"(없으면 ARCHITECTURE.md "실행 환경")에서 가져온다:
- 테스트 명령(`test_cmd`), 앱 실행 명령, E2E 도구
- 없으면 프로젝트 파일로 판단하고 PLAN.md 공통 규약에 기록한다:
  - Node: `package.json`의 `start`/`dev`/`serve`, `@playwright/test`
  - Python: `requirements.txt`/`pyproject.toml` + 앱 진입점(예: `uvicorn app.main:app`), `pytest-playwright`
  - `Makefile`의 `run`/`start`/`dev`

**3. Playwright 설치 여부 확인** — **프로젝트 환경** 기준 (전역 `pip`/`playwright` 를 쓰지 않는다):
```bash
# Node.js
npx playwright --version
# Python (프로젝트 venv)
.venv/bin/python -c "import playwright, pytest_playwright"
```

---

## 1단계: Playwright 설치 (미설치 시)

**Node.js 프로젝트:**
```bash
npm install -D @playwright/test
npx playwright install chromium
```

**Python 프로젝트** (venv 경로는 공통 규약 기준):
```bash
.venv/bin/pip install pytest-playwright      # uv 사용 시: uv pip install --python .venv pytest-playwright
.venv/bin/playwright install chromium
```
설치한 패키지는 requirements(dev) 파일에 추가한다.

---

## 2단계: 테스트 시나리오 도출

`REQUIREMENTS.md`의 핵심 사용자 흐름과 `PLAN.md` 완료 기준에서 시나리오를 뽑는다. 앱에 해당하는 것만 포함한다:

| 시나리오 | 포함 조건 |
|---------|------|
| **Happy Path** | 항상 — 핵심 사용자 흐름 처음부터 끝까지 |
| **CRUD / 상태 변경** | 생성·수정·상태 전이 기능이 있을 때 |
| **에러 상태** | 항상 — 잘못된 입력, 거부되는 전이, 404 |
| **Auth Flow** | 로그인/권한이 있을 때만 (무인증 앱이면 "N/A — 인증 없음"으로 기록) |
| **AI/LLM 기능** | LLM 호출이 있을 때만 |

---

## 3단계: 테스트 파일 생성

Sonnet 에이전트가 테스트를 작성한다 (작업이 많으면 `/hive:execute`와 같은 규칙으로 디스패치: 자기 파일만 쓰고, 커밋·WORKLOG 수정 금지).

**파일 구조:** `tests/e2e/` 아래 흐름별 파일 (`test_core_flow.py` / `core-flow.spec.ts` 등). 이미 Wave 중에 만든 E2E 가 있으면 빠진 시나리오만 추가한다.

**공통 규칙:**
- 서버는 테스트가 직접 띄우고 끝나면 내린다: 빈 포트 + 임시 DB/설정 + 준비될 때까지 대기 + 종료. 실제 데이터 경로를 쓰지 않는다.
- 상태를 바꾸는 동작 뒤에는 결과(배지·행·응답)를 기다린 다음 단언한다 (`expect(...).to_have_text`, `page.expect_response`). 고정 `sleep` 금지.
- 선택자는 `data-testid` → ARIA → 텍스트 순.

**Python 템플릿 (pytest-playwright):**
```python
import os, socket, subprocess, sys, time, urllib.request
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="session")
def server_url(tmp_path_factory):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    env = {**os.environ, "APP_DB": str(tmp_path_factory.mktemp("db") / "e2e.db")}   # 앱의 DB 환경변수 이름으로
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)], env=env)
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try: urllib.request.urlopen(url, timeout=1); break
        except Exception: time.sleep(0.1)
    yield url
    proc.terminate(); proc.wait(timeout=10)

def test_happy_path(page: Page, server_url):
    page.goto(server_url)
    expect(page.get_by_test_id("...")).to_be_visible()
```
(fixture 이름을 `base_url`로 하지 않는다 — pytest-base-url 과 충돌)

**TypeScript 템플릿 (`playwright.config.ts`):**
```typescript
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/e2e',
  use: { baseURL: 'http://127.0.0.1:3000', screenshot: 'on', trace: 'on' },
  webServer: { command: 'npm run start', url: 'http://127.0.0.1:3000', reuseExistingServer: false },
  reporter: [['html', { outputFolder: 'tests/e2e/report', open: 'never' }]],
});
```

---

## 4단계: 테스트 실행 (증거 남기기)

통과한 테스트도 증거를 남긴다 (스크린샷·trace — `/hive:uat`가 재사용).

```bash
# Python
<test_cmd> tests/e2e --screenshot=on --tracing=on --output=tests/e2e/artifacts
# Node (서버는 webServer 설정이 띄운다)
npx playwright test
```

---

## 5단계: 실패 처리

각 실패한 테스트에 대해 다음 절차를 반복한다:

1. 실패 스크린샷·trace(`tests/e2e/artifacts/` 또는 `test-results/`)를 열어 원인을 본다.
2. **앱 버그인 경우:** 앱 코드를 수정하고 해당 테스트만 재실행한 뒤 전체 스위트를 다시 돌린다.
3. **테스트 문제인 경우 (셀렉터/대기/도메인 규칙 위반):** 테스트를 고치고 재실행한다.
4. 2회 이상 같은 테스트가 실패하면 `/hive:debug`로 넘긴다.

---

## 6단계: 리포트 생성 및 완료 처리

모든 테스트가 통과하면:

1. 결과 요약을 출력한다:
   ```
   ✓ N개 테스트 통과, 0개 실패
   ```

2. 증거 위치를 정리한다:
   - Python: `tests/e2e/artifacts/` (테스트별 스크린샷·trace.zip — `playwright show-trace <zip>`로 열람)
   - Node: `tests/e2e/report/index.html` (`npx playwright show-report tests/e2e/report`로 열람)

3. `WORKLOG.md`에 다음 내용을 추가한다:
   ```markdown
   ## [YYYY-MM-DD] Playwright E2E 테스트 완료
   - Playwright: 통과
   - 총 테스트 수: N개
   - 커버된 시나리오: Happy Path, CRUD, 에러 상태 (Auth Flow: N/A — 인증 없음)
   - 증거: tests/e2e/artifacts/ (또는 tests/e2e/report/)
   ```

4. 다음 메시지를 출력한다:
   > "E2E 테스트 통과! `/hive:uat`로 사용자 인수 테스트를 진행하세요."

---

## 주의사항

- 테스트 선택자는 `data-testid` 속성을 우선 사용한다. 없으면 ARIA 역할(`role=`, `aria-label=`)을 사용하고, CSS 클래스 선택은 최후 수단으로만 사용한다.
- 각 테스트는 독립적으로 실행 가능해야 한다 (테스트 간 상태 공유 금지).
- 앱이 시작되는 데 시간이 걸릴 경우, `waitForSelector` 또는 `waitForURL`로 준비 상태를 확인한다.
- Python 프로젝트는 `pytest-playwright` 플러그인을 프로젝트 venv 에 설치해 쓴다 (`playwright test`는 Node 전용 명령이다).

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
