---
name: hive:security
description: 5-domain security review (OWASP+Availability/AI-LLM/API/Secrets/Dependencies)
argument-hint: "[wave <N>] [--auto] [--no-commit]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/hive:security` — 5개 도메인 보안 검토

**담당 모델:** Advisor (opus) — 보안 판단은 높은 정확성이 요구되는 작업

---

## 역할

Advisor로서 코드베이스를 OWASP Top 10, AI/LLM 보안, API 보안, 시크릿 관리, 의존성 5개 도메인에 걸쳐 감사한다. 발견된 이슈는 파일:라인 참조와 함께 보고하고, 치명적 이슈는 즉시 수정한다.

---

## 실행 방법

- **자동 실행:** `/hive:execute` Wave 완료 후 자동으로 실행 권장됨
- **전체 스캔:** `/hive:security` — 전체 코드베이스 스캔
- **Wave 한정 스캔:** `/hive:security wave N` — Wave N의 변경 사항만 스캔 (`git diff` 기반)

---

## 0단계: 사전 조건 · 위협 모델 · 적용 도메인

1. 사전 조건 ([`_shared/prerequisites.md`](../_shared/prerequisites.md)): git(CHECK-1), 컨텍스트(CHECK-7). WORKLOG.md·PLAN.md 는 있으면 읽고 없어도 진행한다.
2. **위협 모델**을 정한다 — `REQUIREMENTS.md`(사용자·비기능 요구)와 `ARCHITECTURE.md`(배포·실행 환경)에서:
   - 사용자 유형: 단일 사용자 / 다중 사용자 / 외부 공개
   - 노출 범위: 로컬(127.0.0.1) / 사내망 / 인터넷
   - 다루는 민감정보 (개인정보·결제·비밀)와 NFR (예: "사내망 단독", "개인정보 로컬 저장")
3. **스택 감지 → 적용 도메인 결정**. 해당 없는 항목은 검사하지 않고 리포트에 `N/A (사유)`로 적는다:
   - 로그인/세션/JWT 코드가 없고 위협 모델이 단일 사용자·로컬 → A2·A4·JWT·인증 레이트리밋 = N/A (대신 "바인딩 주소가 127.0.0.1 인가"를 확인)
   - LLM 호출이 없음 → Domain 2 = N/A
   - 언어별 패턴만 쓴다: Python(sqlite3 는 `?`, psycopg 는 `%s`), Jinja2/Django 템플릿, React/Vanilla JS, Node 등
4. 설계상 의도(예: 무인증 단일 사용자 로컬 앱)는 Red Flag 판정 시 그대로 반영한다 — 아래 "Red Flags"의 조건을 따른다.

## 1단계: 스캔 범위 결정

1. 인수가 `wave N` 형태이면 그 Wave 커밋들의 변경 파일만 대상으로 한다 (마지막 커밋만 보는 `HEAD~1`은 쓰지 않는다):
   ```bash
   git log --format=%H --grep="^feat(wave-N)" --grep="(wave-N)" | tail -1   # 가장 오래된 Wave N 커밋
   git diff --name-only <그 커밋>^ HEAD                                        # Wave N 이후 변경 파일
   ```
   커밋을 못 찾으면 전체 스캔으로 전환하고 그 사실을 리포트에 적는다. 스캔 범위를 `Wave N`으로 기록한다.

2. 인수가 없으면 프로젝트 전체 소스 파일을 스캔 대상으로 한다 (`git ls-files`; 의존성·빌드 산출물 제외). 스캔 범위를 `전체`로 기록한다.

3. `ARCHITECTURE.md`가 존재하면 읽어 기술 스택과 프레임워크를 파악한다. 프레임워크별 취약점 패턴이 달라지므로 반드시 확인한다.

---

## 2단계: Domain 1 — OWASP Top 10 스캔

각 항목을 grep 또는 파일 읽기로 직접 확인한다.

### A1. Injection (SQL / NoSQL / OS Command)
검색 패턴:
- `f"SELECT`, `f'SELECT` — f-string 내 SQL
- `"SELECT * FROM" +` — 문자열 연결 SQL
- `cursor.execute(f"` — f-string SQL 실행
- `cursor.execute(query)` — 파라미터 없이 변수 직접 실행

안전 패턴 (무시):
```python
# GOOD — 드라이버별 플레이스홀더: sqlite3 `?`, psycopg/mysql `%s`, SQLAlchemy `:name`
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))         # sqlite3
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))        # psycopg
```

위험 패턴:
```python
# BAD
query = f"SELECT * FROM users WHERE id = '{user_id}'"
cursor.execute(query)
```

### A2. Broken Authentication
검색 패턴:
- 보호된 라우트에 인증 데코레이터 누락 (`@login_required`, `Depends(get_current_user)` 등)
- JWT 서명 검증 없이 디코딩만 수행
- `algorithms=["none"]` 또는 `verify_signature: False`

안전 패턴:
```python
# GOOD
jwt.decode(token, key, algorithms=["HS256"], options={"require": ["exp", "iss"]})

# Session cookie (FastAPI/Starlette)
response.set_cookie("session", token, httponly=True, secure=True, samesite="lax", max_age=86400)
```

### A3. XSS (Cross-Site Scripting)
검색 패턴:
- `dangerouslySetInnerHTML` — React에서 비위생화 HTML 삽입
- `innerHTML =` — DOM에 직접 HTML 삽입
- `{{ variable | safe }}` 또는 `|safe` 필터 (Django/Jinja2)

안전 패턴:
```tsx
// GOOD: React auto-escaping
return <div>{userInput}</div>;

// GOOD: DOMPurify sanitize
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userInput);

// GOOD: Vanilla JS — 사용자 데이터는 textContent 로만
el.textContent = userInput;
```

서버 렌더링(Jinja2/Django): autoescape 가 켜져 있는지(`Environment(autoescape=select_autoescape())`, Starlette `Jinja2Templates` 기본 on) 확인하고 `|safe`·`Markup()` 사용처를 전부 검토한다.

### A4. Broken Access Control (IDOR 포함)
검색 패턴:
- `GET /users/{id}`, `GET /items/{id}` 등 ID 기반 라우트에서 소유권 검증 없음
- `current_user.id == resource.owner_id` 에 상응하는 검증 부재
- DELETE/PUT 엔드포인트에 인증 없음

안전 패턴:
```python
# GOOD
@app.patch('/api/tasks/{task_id}')
async def update_task(task_id: int, current_user=Depends(get_current_user)):
    task = await task_service.find_by_id(task_id)
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
```

### A5. Security Misconfiguration
검색 패턴:
- `allow_origins=["*"]` — 프로덕션 와일드카드 CORS
- 보안 헤더 미설정 (CSP, HSTS, X-Frame-Options)
- `DEBUG=True` 프로덕션 노출
- 스택 트레이스를 사용자에게 직접 반환

안전 패턴:
```python
# GOOD: CORS 제한
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("ALLOWED_ORIGINS", "").split(","))
```

### A6. Sensitive Data Exposure
검색 패턴:
- API 응답에 `password`, `hashed_password`, `secret`, `token` 필드 포함
- HTTPS 미강제 (HTTP 직접 허용 설정)
- 에러 응답에 스택 트레이스 노출

안전 패턴:
```python
# GOOD: sensitive fields 제거
def sanitize_user(user):
    user.pop("password_hash", None)
    user.pop("reset_token", None)
    return user
```

### A7. CSRF
검색 패턴:
- 상태 변경 폼(POST/PUT/DELETE)에 CSRF 토큰 없음
- `Set-Cookie`에 `SameSite` 속성 누락
- CSRF 미들웨어 부재

위협 모델별 판정:
- 쿠키 세션 인증이 있음 → 토큰 또는 SameSite=strict/lax 필수, 없으면 ⚠️ 경고 (민감 작업이면 ❌)
- 무인증 로컬/사내망 앱 → 다른 사이트가 사용자의 브라우저로 `http://127.0.0.1:<port>`에 POST 할 수 있다. `Origin`/`Host` 헤더 검사 미들웨어 또는 JSON 전용 엔드포인트(`Content-Type: application/json` 강제)로 막는다. 없으면 ⚠️ 경고.

### A8. 가용성 · 자원 고갈 (DoS)
요청 1건으로 서버가 멈추거나 메모리를 다 쓰면 **❌ 치명적**이다.
검색 패턴:
- 사용자 입력에 쓰이는 정규식의 중첩 반복: `(a+)+`, `(\d+,?)+`, `(x|xy)*` 류 → 실제로 긴 입력(예: 16KB 반복 문자)으로 시간 측정 (> 0.5s 면 ReDoS)
- 업로드 크기 제한 없음, ZIP 기반 문서(docx/xlsx/pptx)의 압축 해제 크기·압축비 검사 없음 (zip bomb)
- 숫자 입력 상·하한 없음 → DB 정수 오버플로(500), 음수 금액 등
- 문자열 길이 상한 없음, 페이지네이션 없는 전체 조회, 무한 루프 가능한 재귀
수정 예:
```python
amount: int = Field(ge=0, le=10**15)                 # 범위
title: str = Field(max_length=200)                    # 길이
text = text[:MAX_LINE]                                # 정규식 입력 길이 제한 + 선형 패턴 사용
check_zip_safety(data, max_total=50 * 2**20, max_ratio=100)   # 압축폭탄
```

---

## 3단계: Domain 2 — AI/LLM 보안 스캔

### Prompt Injection
검색 패턴:
- `f"...{user_input}..."` — 사용자 입력이 시스템 프롬프트에 직접 삽입
- `prompt = system_prompt + user_message` — 시스템 지시와 사용자 입력 미분리
- `messages=[{"role": "system", "content": f"...{user_data}..."}]`

안전 패턴:
```python
# GOOD: 사용자 입력을 role:user 메시지로 분리
messages = [
    {"role": "system", "content": system_prompt},  # 사용자 입력 없음
    {"role": "user", "content": user_input},        # 사용자 입력 분리
]
```

### System Prompt Exposure
검색 패턴:
- `/debug`, `/admin`, `/prompt` 등 시스템 프롬프트를 반환하는 엔드포인트
- `system_prompt`를 API 응답에 포함하는 코드

### Output Validation
검색 패턴:
- LLM 출력을 위생화 없이 DB 저장 또는 HTML 직접 렌더링
- LLM 응답 파싱 시 예외 처리 누락

### LLM Rate Limiting
검색 패턴:
- LLM API 호출 엔드포인트에 레이트 리밋 없음
- 인증 없이 LLM 호출을 트리거할 수 있는 공개 엔드포인트

### Token Limit Attacks
검색 패턴:
- 사용자 입력 길이 제한 없음 (`len(user_input) > MAX_LENGTH` 검증 부재)
- 대용량 파일 업로드를 제한 없이 LLM 컨텍스트에 삽입

---

## 4단계: Domain 3 — API 보안 스캔

### JWT Validation
검색 패턴:
- `exp`, `iss`, `aud` 클레임 검증 여부
- `algorithms=["none"]` — `alg: none` 공격 취약
- `options={"verify_signature": False}`

안전 패턴:
```python
# GOOD
jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"require": ["exp", "iss"]})
```

### Rate Limiting
검색 패턴:
- `/login`, `/register`, `/token` 인증 엔드포인트에 레이트 리밋 없음

안전 패턴:
```python
# GOOD: 인증 엔드포인트 강화
@app.post("/api/auth/login")
@rate_limit(max_calls=10, period=900)  # 15분에 10회
async def login(credentials: LoginRequest): ...
```

### CORS
검색 패턴:
- `allow_origins=["*"]` 또는 `CORS_ORIGIN=*`
- 개발 전용 CORS 설정이 프로덕션 활성화

### Input Validation
검색 패턴:
- Pydantic 모델 없이 `request.json()`, `request.body()` 직접 사용
- 경로 파라미터 타입 검증 없음 (`user_id: str` → `user_id: int` 필요)

안전 패턴:
```python
# GOOD: Pydantic / Zod 스키마 검증
class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: Optional[datetime] = None
```

---

## 5단계: Domain 4 — 시크릿 관리 스캔

### 하드코딩된 시크릿
다음 패턴을 grep으로 검색한다:
```
api_key = "sk-
password = "
SECRET_KEY = "
token = "eyJ
AWS_SECRET = "
DATABASE_URL = "postgresql://user:pass
OPENAI_API_KEY = "
```

안전 패턴:
```python
# GOOD
API_KEY = os.getenv("STRIPE_API_KEY")
if not API_KEY:
    raise RuntimeError("STRIPE_API_KEY not configured")
```

### .env 파일 git 추적 여부
`.gitignore`에 반드시 포함되어야 할 항목:
```
.env
.env.local
.env.*.local
*.pem
*.key
```

`git ls-files .env` 명령으로 .env가 이미 추적 중인지 확인한다.

### 로그 노출
다음 패턴을 검색한다:
- `print(api_key)`, `print(token)`, `print(password)`
- `logger.debug(api_key)`, `logging.info(f"...{token}...")`

---

## 6단계: Domain 5 — 의존성 보안 (npm audit / pip-audit)

### 스캔 실행

Node.js 프로젝트:
```bash
npm audit --json 2>/dev/null | head -200
```

Python 프로젝트 — **프로젝트 환경**을 감사한다 (전역 환경이 아니라):
```bash
# 1) 프로젝트 venv 에 pip-audit 가 있으면
.venv/bin/pip-audit -r requirements.txt
# 2) 없으면 설치 없이 일회 실행
uvx pip-audit -r requirements.txt        # 또는: pipx run pip-audit -r requirements.txt
```
- 도구를 하나도 쓸 수 없으면 "의존성 감사: 미실행 (사유)"로 리포트에 적는다. `2>/dev/null`로 오류를 숨기지 않는다.
- `requirements.txt`/`package.json`에 버전 고정이 없으면 ⚠️ 경고 (재현 불가능한 빌드, 감사 결과가 설치 시점마다 달라짐).

### 심각도별 트리아지 기준

```
취약점 발견
├── Critical / High
│   ├── 프로덕션에서 해당 코드 경로가 실행됨?
│   │   ├── YES → 즉시 수정 (업데이트, 패치, 또는 교체)
│   │   └── NO (dev 전용, 미사용 코드) → 곧 수정, 블로커 아님
│   └── 수정 버전이 존재함?
│       ├── YES → 패치 버전으로 업데이트
│       └── NO → 우회책 검토, 의존성 교체 고려, 검토일 설정 후 allowlist
├── Moderate
│   ├── 프로덕션 경로? → 다음 릴리스 사이클에 수정
│   └── dev 전용? → 백로그에 추가
└── Low → 정기 의존성 업데이트 시 수정
```

판단 시 확인 사항:
- 취약한 함수가 실제 코드 경로에서 호출되는가?
- 런타임 의존성인가, dev 전용인가?
- 배포 컨텍스트상 실제 익스플로잇 가능한가?

수정을 미룰 경우, 사유와 검토일을 문서화한다.

---

## 7단계: 결과 보고

발견 사항을 아래 형식으로 보고하고 `docs/security/SECURITY-REVIEW-<YYYY-MM-DD>.md`에 저장한다 (같은 날 재실행이면 덮어쓴다). 이슈가 없는 섹션도 ✅ 통과, 적용하지 않은 섹션은 `N/A (사유)`로 명시한다.

심각도는 [`_shared/output-format.md`](../_shared/output-format.md)와 다음과 같이 대응한다: ❌ 치명적 = CRITICAL/HIGH · ⚠️ 경고 = MEDIUM · ℹ️ 정보 = LOW.

```markdown
## HIVE 보안 검토 결과 — <날짜>
스캔 범위: <전체 | Wave N (커밋 a1b2c3..d4e5f6)> | 위협 모델: <단일 사용자·로컬 | …>

### ❌ 치명적 이슈 (즉시 수정 필요)
- [OWASP-SQL] `app/api/users.py:42` — Raw SQL query without parameterization
  현재 코드: `cursor.execute(f"SELECT * FROM users WHERE id={user_id}")`
  수정 필요: `cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))`

### ⚠️ 경고 (이번 Wave 완료 전 수정 권장)
- [API-CORS] `app/main.py:15` — Wildcard CORS origin in non-dev environment

### ℹ️ 정보 (다음 Wave에서 개선 고려)
- [LLM-RATE] `app/api/chat.py:88` — LLM 엔드포인트에 레이트 리밋 없음 (현재 내부 전용이므로 저위험)

### N/A (적용 안 함)
- AI/LLM: LLM 호출 없음
- A2/A4/JWT: 인증 없음 — 설계상 단일 사용자 로컬 (127.0.0.1 바인딩 확인)

### 요구사항 대비 (NFR)
- NFR-01 사내망 단독: 외부 전송 코드 없음 ✅

### ✅ 통과 항목
- OWASP: 전체 SQL 쿼리에 파라미터화 사용
- JWT: exp/iss/aud 검증 및 알고리즘 고정 확인
- Secret: 모든 시크릿이 환경 변수에서 로드됨
- .gitignore: .env 및 .env.* 포함 확인
- Dependency: Critical/High 취약점 없음
```

---

## 8단계: 치명적 이슈 자동 수정

❌ 치명적 이슈가 있으면 다음 절차를 따른다:

1. **코드 수정:** Advisor가 직접 해당 파일을 수정한다. 수정 전 원본 코드를 보고서에 기록한다.

2. **회귀 테스트 추가 후 전체 테스트 실행:** 취약점을 재현하는 테스트(예: 긴 입력 시간 제한, 거대 금액 422)를 먼저 추가하고, PLAN.md 공통 규약의 테스트 명령(없으면 프로젝트 테스트 명령)으로 **전체** 스위트를 실행한다. 실패하면 수정 사항을 재검토한다.

3. **Git 커밋:** `--no-commit`이 아니면 테스트 통과 후 커밋한다 ([`_shared/git-commit.md`](../_shared/git-commit.md)):
   ```bash
   git add <수정된 파일> <추가한 테스트>
   git commit -m "fix(security): <수정 내용 한 줄 요약>"
   ```
   `--no-commit`이면 수정만 하고 커밋은 호출자(Advisor)에게 맡긴다.

4. **설계 결정이 필요한 수정**(예: 인증 체계 도입)은 자동 수정하지 않는다. 리포트에 선택지와 함께 남기고 사용자 확인을 받는다 (`--auto`면 WORKLOG "미결 이슈"에 기록).

---

## 9단계: 경고 처리

⚠️ 경고 항목이 있으면 사용자에게 다음을 질문한다:

> "다음 경고 항목이 발견되었습니다:
> - [항목 목록]
>
> 지금 바로 수정할까요, 아니면 다음 Wave에서 처리할까요?"

사용자가 즉시 수정을 요청하면 8단계와 동일한 절차로 처리한다.

`--auto`([`_shared/auto-mode.md`](../_shared/auto-mode.md))면 묻지 않는다: 수정 범위가 작고 테스트로 검증 가능한 경고(입력 상한, 보안 헤더, Origin 검사)는 8단계 절차로 수정하고, 나머지는 WORKLOG.md "미결 이슈"에 `[보안] <항목> — <파일:라인>`으로 남긴다.

---

## 10단계: WORKLOG.md 업데이트

`WORKLOG.md`에 다음 내용을 추가한다:

```markdown
## [YYYY-MM-DD] 보안 검토 완료
- 스캔 범위: <전체/Wave N>
- 리포트: docs/security/SECURITY-REVIEW-YYYY-MM-DD.md
- 치명적 이슈: <N>건 (수정 <a>건 / 미수정 <b>건 — 사유)
- 경고: <N>건 (수정 <c>건 / 보류 <d>건 → 미결 이슈)
- 정보: <N>건
- N/A 도메인: <목록>
- 의존성 감사: Critical <N>건 / High <N>건 (또는 미실행 — 사유)
```

---

## 11단계: 완료 안내

다음 메시지를 출력한다:

> "보안 검토 완료.
> ❌ 치명적: <N>건 (수정 <a>) | ⚠️ 경고: <N>건 (수정 <c> / 보류 <d>) | ℹ️ 정보: <N>건 | N/A: <도메인 수>
> 리포트: docs/security/SECURITY-REVIEW-YYYY-MM-DD.md"

---

## 심각도 분류 기준

| 심각도 | 기준 | 처리 방법 |
|--------|------|-----------|
| ❌ 치명적 | 데이터 유출, 인증 우회, RCE 가능성, 하드코딩 시크릿, Critical 의존성 취약점, **요청 1건으로 서버 정지·메모리 고갈(ReDoS·zip bomb·무제한 입력)** | 즉시 자동 수정 |
| ⚠️ 경고 | 보안 모범 사례 위반, 잠재적 위험 | 사용자 확인 후 수정 |
| ℹ️ 정보 | 개선 권장 사항, 저위험 이슈 | 다음 Wave에서 고려 |

---

## Red Flags (즉시 치명적 분류)

- 사용자 입력이 DB 쿼리, 셸 명령, HTML 렌더링에 직접 전달됨
- 소스 코드 또는 커밋 히스토리에 시크릿 존재
- 인증/인가 없는 API 엔드포인트 — **단, 위협 모델이 "단일 사용자·로컬(127.0.0.1)"로 요구사항에 명시돼 있고 바인딩이 127.0.0.1 이면 ℹ️ 정보**로 기록 (0.0.0.0 바인딩·사내망·인터넷 노출이면 치명적)
- 사용자 입력에 대한 지수 시간 정규식(ReDoS), 압축 해제 크기 검사 없는 업로드
- 와일드카드(`*`) CORS 설정
- 인증 엔드포인트에 레이트 리밋 없음
- 사용자에게 스택 트레이스 노출
- Critical/High 알려진 취약점 의존성

---

## Common Rationalizations (합리화 패턴 반박)

| 합리화 | 현실 |
|--------|------|
| "내부 툴이라 보안 안 해도 돼" | 내부 툴도 침해된다. 공격자는 가장 약한 고리를 노린다. |
| "나중에 보안 추가하면 돼" | 보안 레트로핏은 처음부터 구축하는 것보다 10배 어렵다. 지금 추가하라. |
| "아무도 이걸 악용하려 하지 않을 거야" | 자동화된 스캐너가 찾아낸다. 난독화 보안은 보안이 아니다. |
| "프레임워크가 보안을 처리해줘" | 프레임워크는 도구를 제공하지 보장을 하지 않는다. 올바르게 사용해야 한다. |
| "그냥 프로토타입인데" | 프로토타입이 프로덕션이 된다. 처음부터 보안 습관을 들여라. |

---

## 릴리스 전 수동 점검 체크리스트

### Authentication
- [ ] 비밀번호가 bcrypt/scrypt/argon2로 해시됨 (salt rounds ≥ 12)
- [ ] 세션 쿠키가 httpOnly, secure, sameSite 설정됨
- [ ] 로그인 엔드포인트에 레이트 리밋 있음
- [ ] 비밀번호 재설정 토큰이 만료됨

### Authorization
- [ ] 모든 엔드포인트에 사용자 권한 검사 있음
- [ ] 사용자가 자신의 리소스에만 접근 가능
- [ ] 관리자 액션에 관리자 역할 검증 있음

### Input
- [ ] 모든 사용자 입력이 경계에서 검증됨
- [ ] SQL 쿼리가 파라미터화됨
- [ ] HTML 출력이 인코딩/이스케이프됨

### Data
- [ ] 코드 또는 버전 관리에 시크릿 없음
- [ ] API 응답에서 민감한 필드 제외됨
- [ ] 해당 시 PII 저장 암호화됨

### Infrastructure
- [ ] 보안 헤더 설정됨 (CSP, HSTS 등)
- [ ] CORS가 알려진 origin으로 제한됨
- [ ] 의존성 취약점 감사 완료
- [ ] 에러 메시지에 내부 정보 미노출

---

## 주의사항

- 이슈 보고 시 반드시 `파일경로:라인번호` 형식으로 위치를 명시한다.
- 현재 코드와 수정 후 코드를 함께 제시하여 수정 방향을 명확히 한다.
- 프레임워크별 보안 패턴이 다르므로 ARCHITECTURE.md에서 기술 스택을 확인하고 맞춤형으로 스캔한다.
- 오탐(false positive)이 의심되면 해당 컨텍스트를 더 읽어 확인한 후 보고한다.
- 테스트 환경 코드(`tests/`, `*_test.py`)의 하드코딩된 값은 치명적으로 분류하지 않는다.

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
