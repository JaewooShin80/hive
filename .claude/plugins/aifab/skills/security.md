---
name: aifab:security
description: 4-domain security review (OWASP/AI-LLM/API/secrets)
argument-hint: [wave <N>]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:security` — 4개 도메인 보안 검토

**담당 모델:** Advisor (claude-opus-4-7) — 보안 판단은 높은 정확성이 요구되는 작업

---

## 역할

Advisor로서 코드베이스를 OWASP Top 10, AI/LLM 보안, API 보안, 시크릿 관리 4개 도메인에 걸쳐 감사한다. 발견된 이슈는 파일:라인 참조와 함께 보고하고, 치명적 이슈는 즉시 수정한다.

---

## 실행 방법

- **자동 실행:** `/aifab:execute` Wave 완료 후 자동으로 실행 권장됨
- **전체 스캔:** `/aifab:security` — 전체 코드베이스 스캔
- **Wave 한정 스캔:** `/aifab:security wave N` — Wave N의 변경 사항만 스캔 (`git diff` 기반)

---

## 1단계: 스캔 범위 결정

1. 인수가 `wave N` 형태이면 다음 명령으로 변경 파일 목록을 가져온다:
   ```bash
   git diff HEAD~1 --name-only
   ```
   해당 파일만 스캔 대상으로 한다. 스캔 범위를 `Wave N`으로 기록한다.

2. 인수가 없으면 프로젝트 전체 소스 파일을 스캔 대상으로 한다. 스캔 범위를 `전체`로 기록한다.

3. `ARCHITECTURE.md`가 존재하면 읽어 기술 스택과 프레임워크를 파악한다. 프레임워크별 취약점 패턴이 달라지므로 반드시 확인한다.

---

## 2단계: Domain 1 — OWASP Top 10 스캔

각 항목을 grep 또는 파일 읽기로 직접 확인한다.

### SQL Injection
다음 패턴을 검색한다:
- `f"SELECT`, `f'SELECT` — f-string 내 SQL
- `"SELECT * FROM" +`, `'SELECT * FROM' +` — 문자열 연결 SQL
- `cursor.execute(query)` — 파라미터 없이 변수를 직접 실행
- `cursor.execute(f"`, `cursor.execute(f'` — f-string SQL 실행

안전한 패턴 (무시): `cursor.execute("...", (param,))`, ORM 쿼리빌더 사용

### XSS (Cross-Site Scripting)
- `dangerouslySetInnerHTML` — React에서 비위생화 HTML 삽입
- `innerHTML =` — DOM에 직접 HTML 삽입
- 템플릿에서 `{{ variable | safe }}` 또는 `|safe` 필터 사용

### CSRF
- 상태 변경 폼(POST/PUT/DELETE)에 CSRF 토큰 없음
- `Set-Cookie`에 `SameSite` 속성 누락
- FastAPI/Flask에서 CSRF 미들웨어 부재

### IDOR (Insecure Direct Object Reference)
- `GET /users/{id}`, `GET /items/{id}` 등 ID 기반 라우트에서 소유권 검증 없음
- `current_user.id == resource.owner_id` 또는 이에 상응하는 검증이 없는 경우

### Broken Authentication
- 보호된 라우트에 `@login_required`, `@auth_required`, `Depends(get_current_user)` 등 인증 데코레이터 누락
- JWT 토큰 서명 검증 없이 디코딩만 수행

### Sensitive Data Exposure
- API 응답에 `password`, `hashed_password`, `secret` 필드 포함
- HTTPS 미강제 (HTTP 직접 허용 설정)
- 에러 응답에 스택 트레이스 노출

---

## 3단계: Domain 2 — AI/LLM 보안 스캔

### Prompt Injection
다음 패턴을 검색한다:
- `f"...{user_input}..."` — 사용자 입력이 시스템 프롬프트에 직접 삽입
- `prompt = system_prompt + user_message` — 시스템 지시와 사용자 입력 미분리
- `messages=[{"role": "system", "content": f"...{user_data}..."}]` — 시스템 메시지에 사용자 데이터 삽입

안전한 패턴: 사용자 입력을 `role: user` 메시지로 분리, 입력 위생화 후 사용

### System Prompt Exposure
- `/debug`, `/admin`, `/prompt` 등 시스템 프롬프트 내용을 반환하는 엔드포인트
- `system_prompt`를 API 응답에 포함하는 코드

### Output Validation
- LLM 출력을 `eval()`, `exec()` 로 직접 실행
- LLM 출력을 위생화 없이 DB에 저장하거나 HTML에 직접 렌더링
- LLM 응답 파싱 시 예외 처리 누락

### Rate Limiting on LLM Calls
- LLM API를 호출하는 엔드포인트에 `@rate_limit`, `slowapi`, `RateLimiter` 등 레이트 리밋 부재
- 인증 없이 LLM 호출을 트리거할 수 있는 공개 엔드포인트

### Token Limit Attacks
- 사용자 입력 길이 제한 없음 (`len(user_input) > MAX_LENGTH` 검증 부재)
- 대용량 파일 업로드를 제한 없이 LLM 컨텍스트에 삽입

---

## 4단계: Domain 3 — API 보안 스캔

### JWT Validation
다음을 확인한다:
- `exp` (만료), `iss` (발급자), `aud` (대상) 클레임 검증 여부
- `algorithms=["none"]` 또는 알고리즘 미지정 — `alg: none` 공격 취약
- `jwt.decode()` 호출에 `options={"verify_signature": False}` 설정

안전한 패턴: `jwt.decode(token, key, algorithms=["HS256"], options={"require": ["exp", "iss"]})`

### Rate Limiting
- `/login`, `/register`, `/token` 등 인증 엔드포인트에 레이트 리밋 부재
- 반복 호출 가능한 API 엔드포인트에 레이트 리밋 부재

### CORS
- `allow_origins=["*"]` — 프로덕션에서 와일드카드 허용
- `CORS_ORIGIN=*` 환경 변수 설정
- 개발 전용 CORS 설정이 프로덕션에서도 활성화

### HTTP Methods
- DELETE/PUT 엔드포인트에 인증 없음
- `methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"]` — 불필요한 메서드 허용

### Input Validation
- Request body에 Pydantic 모델 또는 스키마 검증 없이 `request.json()`, `request.body()` 직접 사용
- 경로 파라미터 타입 검증 없음 (`user_id: str` → `user_id: int` 필요)

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
```

### 환경 변수 사용 확인
- `os.environ`, `os.getenv`, `python-dotenv`의 `load_dotenv()` 사용 여부 확인
- 시크릿이 코드에 리터럴로 존재하면 즉시 치명적 이슈로 분류

### .env 파일 git 추적 여부
- `.gitignore` 파일에 `.env`, `.env.*`, `.env.local` 포함 여부 확인
- `git ls-files .env` 명령으로 .env가 이미 추적 중인지 확인

### 로그 노출
다음 패턴을 검색한다:
- `print(api_key)`, `print(token)`, `print(password)`
- `logger.debug(api_key)`, `logger.info(secret)`
- `logging.info(f"...{token}...")`

---

## 6단계: 결과 보고

발견 사항을 아래 형식으로 보고한다. 이슈가 없는 섹션도 ✅ 통과로 명시한다.

```markdown
## AI-Fab 보안 검토 결과 — <날짜>
Wave: <N> | 스캔 범위: <전체/Wave N>

### ❌ 치명적 이슈 (즉시 수정 필요)
- [OWASP-SQL] `app/api/users.py:42` — Raw SQL query without parameterization
  현재 코드: `cursor.execute(f"SELECT * FROM users WHERE id={user_id}")`
  수정 필요: `cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))`

### ⚠️ 경고 (이번 Wave 완료 전 수정 권장)
- [API-CORS] `app/main.py:15` — Wildcard CORS origin in non-dev environment

### ℹ️ 정보 (다음 Wave에서 개선 고려)
- [LLM-RATE] `app/api/chat.py:88` — LLM 엔드포인트에 레이트 리밋 없음 (현재 내부 전용이므로 저위험)

### ✅ 통과 항목
- OWASP: 전체 SQL 쿼리에 파라미터화 사용
- JWT: exp/iss/aud 검증 및 알고리즘 고정 확인
- Secret: 모든 시크릿이 환경 변수에서 로드됨
- .gitignore: .env 및 .env.* 포함 확인
```

---

## 7단계: 치명적 이슈 자동 수정

❌ 치명적 이슈가 있으면 다음 절차를 따른다:

1. **코드 수정:** Advisor가 직접 해당 파일을 수정한다. 수정 전 원본 코드를 보고서에 기록한다.

2. **테스트 실행:** 수정된 파일과 관련된 테스트를 실행한다:
   ```bash
   pytest tests/ -k "<관련 모듈명>" -v
   ```
   테스트가 실패하면 수정 사항을 재검토하고 다시 수정한다.

3. **Git 커밋:** 테스트 통과 후 보안 수정을 커밋한다:
   ```bash
   git add <수정된 파일>
   git commit -m "fix(security): <수정 내용 한 줄 요약>"
   ```

---

## 8단계: 경고 처리

⚠️ 경고 항목이 있으면 사용자에게 다음을 질문한다:

> "다음 경고 항목이 발견되었습니다:
> - [항목 목록]
>
> 지금 바로 수정할까요, 아니면 다음 Wave에서 처리할까요?"

사용자가 즉시 수정을 요청하면 7단계와 동일한 절차로 처리한다.

---

## 9단계: WORKLOG.md 업데이트

`WORKLOG.md`에 다음 내용을 추가한다:

```markdown
## [YYYY-MM-DD] 보안 검토 완료
- 스캔 범위: <전체/Wave N>
- 치명적 이슈: <N>건 (모두 즉시 수정 완료)
- 경고: <N>건
- 정보: <N>건
- 통과: <N>개 항목
```

---

## 10단계: 완료 안내

다음 메시지를 출력한다:

> "보안 검토 완료.
> ❌ 치명적: <N>건 수정됨 | ⚠️ 경고: <N>건 | ✅ 통과: <N>개 항목
> 자세한 내용은 위 보고서를 참고하세요."

---

## 심각도 분류 기준

| 심각도 | 기준 | 처리 방법 |
|--------|------|-----------|
| ❌ 치명적 | 데이터 유출, 인증 우회, RCE 가능성 | 즉시 자동 수정 |
| ⚠️ 경고 | 보안 모범 사례 위반, 잠재적 위험 | 사용자 확인 후 수정 |
| ℹ️ 정보 | 개선 권장 사항, 저위험 이슈 | 다음 Wave에서 고려 |

## 주의사항

- 이슈 보고 시 반드시 `파일경로:라인번호` 형식으로 위치를 명시한다.
- 현재 코드와 수정 후 코드를 함께 제시하여 수정 방향을 명확히 한다.
- 프레임워크별 보안 패턴이 다르므로 ARCHITECTURE.md에서 기술 스택을 확인하고 맞춤형으로 스캔한다.
- 오탐(false positive)이 의심되면 해당 컨텍스트를 더 읽어 확인한 후 보고한다.
- 테스트 환경 코드(`tests/`, `*_test.py`)의 하드코딩된 값은 치명적으로 분류하지 않는다.

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
