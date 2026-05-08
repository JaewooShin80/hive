---
description: 웹개발보안 + AI/LLM + 인프라 보안 가이드 기반 코드 점검 및 조치 (63개 항목)
allowed-tools: [Bash, Read, Glob, Grep, Write, Edit, Agent]
---

# Security Audit Skill — 웹/API + AI/LLM + 인프라 보안 점검

프로젝트 코드를 대상으로 **웹/API 보안 가이드 43개 항목** + **AI/LLM 보안 가이드 20개 항목**을 점검하고, 결과 보고서를 생성합니다.

> **기준 문서**: 정부 소프트웨어 개발보안 가이드(행정안전부) + AI/LLM 개발보안 가이드라인 v1.1.0 + CLOUD_DOCKER 보안 규격

---

## 실행 순서

### Step 1: 프로젝트 구조 파악

프로젝트의 기술 스택과 구조를 먼저 파악합니다.

- `package.json` (프론트엔드/백엔드) → 프레임워크, 보안 패키지 확인
- 서버 진입점 → 미들웨어 구성 확인
- 라우트 파일 → 인증/인가 적용 확인
- `.env`, `.env.example` → 시크릿 관리 확인
- `.gitignore` → 민감 파일 제외 확인
- `Dockerfile`, `docker-compose*.yml` → 컨테이너 보안 확인
- `nginx/nginx.conf` 또는 웹서버 설정 → 프록시 보안 확인

### Step 2: 웹/API 보안 점검 (43개 항목)

아래 체크리스트를 코드 기반으로 점검합니다. 각 항목에 대해 **양호/미흡/해당없음** 판정과 근거를 기록합니다.

#### 카테고리 1: 입/출력 값 검증 부재

| # | 점검 항목 | 중요도 | 정부 매핑 | 점검 방법 |
|---|----------|--------|----------|----------|
| 1-1 | XSS/CSRF 공격 가능성 | 중요 | SR1-5, SR1-6 | localStorage에 토큰 저장 여부, httpOnly 쿠키 사용 여부, CSRF 토큰/헤더 검증 미들웨어 존재 여부, CSP 헤더 설정 확인 |
| 1-2 | SQL/Command Injection | 중요 | SR1-1 | parameterized query 사용 여부 (문자열 결합 SQL 검색), eval()/exec() 사용 여부, ORM 사용 시 raw query 검색 |
| 1-3 | 파라미터/히든필드 조작 | 중요 | SR1-9, SR1-8 | 입력값 검증 미들웨어 존재 여부, enum/whitelist 검증 (특히 role, status 등), URL 파라미터 타입 검증 |
| 1-4 | XXE/File Inclusion | 중요 | SR1-2 | XML 파서 사용 여부, 외부 엔티티 비활성화 설정 확인 |
| 1-5 | 미검증 리다이렉트/포워드 | 일반 | SR1-7 | 사용자 입력 기반 redirect/forward 코드 검색 |

#### 카테고리 2: 취약한 파일처리

| # | 점검 항목 | 중요도 | 정부 매핑 | 점검 방법 |
|---|----------|--------|----------|----------|
| 2-1 | 악성코드파일 업로드 | 중요 | SR1-10 | 확장자 whitelist, MIME 타입 검증, magic bytes 검증, 파일 크기 제한, 업로드 경로 격리, 바이러스 스캔 |
| 2-2 | 중요 정보 파일 다운로드 | 중요 | SR1-10 | 경로 조작(path traversal) 방어, 다운로드 권한 확인 |

#### 카테고리 3: 취약한 접근통제 관리

| # | 점검 항목 | 중요도 | 정부 매핑 | 점검 방법 |
|---|----------|--------|----------|----------|
| 3-1 | 패스워드 정책 | 중요 | SR2-3 | 최소 길이(8+), 복잡도(대/소/숫자/특수), 이력 관리, 만료 정책, 흔한 비밀번호 사전 체크 |
| 3-2 | 인증 실패 횟수 제한 | 일반 | SR2-2 | 계정 잠금 구현 여부, 잠금이 로그인 플로우에 실제 연동되었는지 확인 |
| 3-3 | 계정 정보 파악 가능성 | 일반 | SR2-1 | 에러 메시지로 사용자 존재 여부 노출 (예: "User not found" vs "Invalid credentials") |
| 3-4 | 관리자 페이지 분리 | 중요 | SR2-4 | 관리자 전용 라우트에 인증+인가 미들웨어 적용 확인 |
| 3-5 | 검색엔진 정보 노출 | 일반 | - | robots.txt 존재 여부, meta noindex 설정 |
| 3-6 | 백업/테스트 파일 존재 | 일반 | SR1-10 | *.backup, test_*.json, *.bak, *.sql 등 민감 파일 검색 |
| 3-7 | 하드코딩 기본 계정 | 중요 | SR2-3 | DB 또는 코드에 사전 생성된 테스트/기본 계정(admin/test 등) 존재 여부, 마이그레이션으로 제거 여부 확인 |

#### 카테고리 4: 취약한 인증 및 세션 관리

| # | 점검 항목 | 중요도 | 정부 매핑 | 점검 방법 |
|---|----------|--------|----------|----------|
| 4-1 | 쿠키 조작 가능성 | 일반 | SR4-1 | httpOnly, secure, sameSite 설정 확인 |
| 4-2 | 세션 재사용/타임아웃 | 일반 | SR4-1 | 로그아웃 시 토큰 무효화, 세션 타임아웃, 토큰 블랙리스트 |
| 4-3 | 접근제어 우회 | 일반 | SR2-4 | JWT 클레임만 신뢰하지 않고 DB 기반 역할 검증 여부 |
| 4-4 | 비인증 중요페이지 접근 | 일반 | SR2-4 | 모든 API에 인증 미들웨어 적용 여부 |
| 4-5 | 일반계정 권한 상승 | 일반 | SR2-4 | RBAC 구현 여부, 역할별 접근 제어 |
| 4-6 | 자기 계정 조작 방지 | 일반 | SR2-4 | 사용자가 자신의 역할 변경·삭제 가능 여부 방어 (자기보호 로직 존재 여부) |

#### 카테고리 5: 중요 정보 저장/전송 처리 미흡

| # | 점검 항목 | 중요도 | 정부 매핑 | 점검 방법 |
|---|----------|--------|----------|----------|
| 5-1 | 소스코드 내 주요정보 노출 | 일반 | SR2-7 | 하드코딩된 시크릿, API 키, 비밀번호 검색, .env.example 기본값 점검 |
| 5-2 | 요청/응답 내 주요정보 | 중요 | SR2-8 | 응답 body에 토큰/비밀번호 포함 여부, HTTPS 강제 여부 |

#### 카테고리 6: 부적절한 오류 처리

| # | 점검 항목 | 중요도 | 정부 매핑 | 점검 방법 |
|---|----------|--------|----------|----------|
| 6-1 | 오류 정보 노출 | 일반 | SR3-1 | 스택트레이스 노출, 내부 경로 노출, DB 에러 원본 노출 |
| 6-2 | 일괄 오류 처리 페이지 | 일반 | SR3-1 | 글로벌 에러 핸들러 존재 여부 |

#### 카테고리 7: 취약한 컴포넌트 구성요소

| # | 점검 항목 | 중요도 | 정부 매핑 | 점검 방법 |
|---|----------|--------|----------|----------|
| 7-1 | 서버 정보 노출 | 일반 | SR3-1 | Health 엔드포인트 정보, X-Powered-By 헤더 |
| 7-2 | 파일 목록화 가능성 | 일반 | - | 디렉토리 리스팅 활성화 여부 |
| 7-3 | 보안 헤더 설정 | 일반 | - | Helmet.js 등 보안 헤더 미들웨어, HSTS, CSP 설정 |
| 7-4 | 취약한 보안설정 | 일반 | SR2-6 | JSON body limit, CORS 설정, 프로덕션 환경 분리 |
| 7-5 | 응답 상태코드 정규화 | 일반 | SR3-1 | 에러 HTTP 상태코드로 내부 정보 유출 방지 (NGINX/앱 레벨에서 에러 응답 일반화 여부), ETag 비활성화 여부 |

#### 카테고리 8: 기타

| # | 점검 항목 | 중요도 | 정부 매핑 | 점검 방법 |
|---|----------|--------|----------|----------|
| 8-1 | 의존성 취약점 | 일반 | - | `npm audit` 결과, 알려진 취약 패키지 |
| 8-2 | CI/CD 보안 | 일반 | - | 보안 스캔 자동화, 시크릿 관리 |
| 8-3 | 데이터 보관 정책 | 일반 | 개인정보보호법 | 개인정보·로그 자동 삭제/아카이브 스케줄러 존재 여부, 보관 기간 설정 (로그인 로그 6개월, 감사 로그 2년→아카이브→5년 삭제) |

#### 카테고리 9: 컨테이너/Docker 보안

| # | 점검 항목 | 중요도 | 기준 | 점검 방법 |
|---|----------|--------|------|----------|
| 9-1 | 컨테이너 비루트 실행 | 중요 | CLOUD_DOCKER | Dockerfile에 비루트 사용자(USER appuser) 생성 및 전환 여부 |
| 9-2 | 다단계 빌드 적용 | 일반 | CLOUD_DOCKER | deps→builder→runner 다단계 빌드로 소스코드·빌드 도구 최종 이미지 미포함 여부 |
| 9-3 | 컨테이너 리소스 제한 | 일반 | CLOUD_DOCKER | docker-compose에서 pids_limit, mem_limit 설정 여부 (DoS 방지) |
| 9-4 | 이미지 서명 검증 | 일반 | CLOUD_DOCKER-26 | DOCKER_CONTENT_TRUST=1 환경변수 설정으로 서명된 이미지만 허용 여부 |
| 9-5 | Docker 데몬 감사(auditd) | 일반 | CLOUD_DOCKER-03~08 | auditd 규칙으로 /usr/bin/docker, /var/lib/docker, /etc/docker, docker.service 변조 감지 여부 |
| 9-6 | 환경 파일 보호 | 일반 | CLOUD_DOCKER | .env 파일 read-only 마운트(:ro), 민감 정보 환경변수 외부화 여부 |

#### 카테고리 10: 웹서버(NGINX/Proxy) 보안

| # | 점검 항목 | 중요도 | 기준 | 점검 방법 |
|---|----------|--------|------|----------|
| 10-1 | 서버 버전 정보 숨김 | 중요 | SR3-1 | `server_tokens off` 설정, `Server`·`X-Powered-By` 헤더 제거(`proxy_hide_header`) 여부 |
| 10-2 | HTTP 메서드 제한 | 중요 | SR1-9 | `limit_except GET HEAD POST` 설정으로 비표준 메서드(PUT/DELETE/PATCH 등) 차단 여부 |
| 10-3 | 에러 응답 정규화 | 일반 | SR3-1 | NGINX에서 에러(400/401/403/404/500 등) 응답을 일반화하여 내부 구조 노출 방지 여부 |
| 10-4 | 연결 타임아웃 설정 | 일반 | - | `proxy_read_timeout`, `proxy_connect_timeout` 설정으로 SlowLoris/느린 HTTP DoS 방지 여부 |
| 10-5 | 응답 압축 설정 | 일반 | - | gzip 압축 설정 여부 (트래픽 효율화), 민감 응답(Authorization 헤더 포함 시) 압축 제외 여부 |

### Step 3: AI/LLM 보안 점검 (20개 항목)

> AI/LLM 기능이 없는 프로젝트는 이 섹션을 "해당없음"으로 기록하고 건너뜁니다.

| # | 점검 항목 | 중요도 | 점검 방법 |
|---|----------|--------|----------|
| LLM-01 | 클라이언트 내 프롬프트 생성 | 중요 | 시스템 프롬프트가 서버에서 조립되는지, 클라이언트가 system 메시지를 직접 구성하는지 확인 |
| LLM-02 | 프롬프트 인젝션 | 중요 | 특수 토큰 필터링(`<\|endoftext\|>`, `[INST]` 등), 인젝션 패턴 탐지("ignore previous instructions" 등), 입력 새니타이징 |
| LLM-03 | 민감 정보 노출 | 중요 | LLM에 전송되는 데이터에 PII 포함 여부, LLM 응답 필터링 존재 여부, SELECT * 쿼리 |
| LLM-04 | 오류 메시지 출력 | 일반 | AI API 에러가 클라이언트에 원본 노출되는지, 에러 새니타이징 적용 여부 |
| LLM-05 | 모델 서비스 거부 (DoS) | 중요 | AI 엔드포인트 Rate Limiting, 요청 타임아웃, 페이로드 크기 제한, 사용자별 일일 한도 |
| LLM-06 | 취약한 서드파티 소프트웨어 | 중요 | 보안 패키지(helmet, rate-limit 등) 설치 여부, npm audit 결과 |
| LLM-07 | RAG 데이터 오염 | 중요 | RAG/벡터DB 사용 시 데이터 무결성 검증, 입력 새니타이징 |
| LLM-08 | 시크릿 키 노출 | 중요 | API 키 암호화 저장, 환경변수 관리, 기본값(fallback) 제거, Git에 시크릿 포함 여부 |
| LLM-09 | API 매개변수 변조 | 중요 | AI 라우트 입력 검증, 배열/객체 구조 검증, URL 파라미터 타입 검증 |
| LLM-10 | 부적절한 권한 | 중요 | AI 기능 접근 권한, RBAC, DB 기반 권한 확인 (JWT 클레임만 신뢰하지 않는지) |
| LLM-11 | 사용자 동의 절차 누락 | 일반 | 외부 API로 데이터 전송 시 동의, 파괴적 작업 확인 대화상자 |
| LLM-12 | 샌드박스 미적용 | 중요 | eval(), Function(), vm 등 동적 코드 실행 여부, AI 응답 실행 여부 |
| LLM-13 | 모델 내부 악성 페이로드 | 중요 | 로컬 모델 파일 사용 여부, 모델 파일 무결성 검증 |
| LLM-14 | 모델 내 민감 정보 | 일반 | 파인튜닝/자체 학습 시 민감 데이터 포함 여부 |
| LLM-15 | 학습 데이터 오염 | 일반 | 자체 학습 수행 여부, 학습 데이터 검증 |
| LLM-16 | 통신 데이터 무결성/기밀성 | 중요 | HTTPS 사용, CORS 제한, 보안 헤더 |
| LLM-17 | 접근 제어 및 인증 | 중요 | AI 엔드포인트 인증, Rate Limiting, API 키 관리 |
| LLM-18 | 입력 유효성 검증/출력 필터링 | 중요 | 입력 스키마 검증, 출력 새니타이징, 에러 메시지 일반화 |
| LLM-19 | 로그 및 모니터링 | 일반 | AI 요청 로깅, 토큰/비용 추적, 감사 로그, HMAC-SHA256 로그 무결성 서명 여부 |
| LLM-20 | 미정의 취약점 | 일반 | 위 항목 외 추가 발견사항 |

### Step 4: 코드 점검 실행

각 항목별로 아래 패턴을 코드에서 검색합니다:

```bash
# 1. 하드코딩된 시크릿 검색
grep -rn "password\|secret\|api.key\|token" --include="*.js" --include="*.ts" --include="*.env*" | grep -v node_modules | grep -v "\.test\."

# 2. localStorage 사용 검색
grep -rn "localStorage" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" | grep -v node_modules

# 3. eval/exec 사용 검색
grep -rn "eval(\|Function(\|exec(\|execSync(" --include="*.js" --include="*.ts" | grep -v node_modules

# 4. SQL 문자열 결합 검색
grep -rn "SELECT\|INSERT\|UPDATE\|DELETE" --include="*.js" --include="*.ts" | grep -v node_modules | grep "+"

# 5. 에러 원본 노출 검색
grep -rn "error\.message\|err\.message\|error\.stack" --include="*.js" --include="*.ts" | grep -v node_modules | grep "res\."

# 6. CORS 설정 검색
grep -rn "cors\|Access-Control" --include="*.js" --include="*.ts" | grep -v node_modules

# 7. 보안 헤더 검색
grep -rn "helmet\|X-Frame\|Content-Security-Policy\|X-Content-Type" --include="*.js" | grep -v node_modules

# 8. Rate Limiting 검색
grep -rn "rate.limit\|rateLimit\|express-rate-limit" --include="*.js" | grep -v node_modules

# 9. 인증 미들웨어 적용 검색
grep -rn "authenticateToken\|requireAdmin\|adminCheck\|authMiddleware" --include="*.js" | grep -v node_modules

# 10. AI/LLM 특수 토큰 검색
grep -rn "endoftext\|im_start\|im_end\|INST\|injection\|sanitiz" --include="*.js" | grep -v node_modules

# 11. 민감 파일 검색
find . -name "*.backup" -o -name "*.bak" -o -name "test_*" -o -name "*.sql" -o -name "*.db" | grep -v node_modules

# 12. npm audit
cd server && npm audit --json 2>/dev/null | head -50

# 13. 컨테이너 보안 검색 (Docker/Compose)
grep -n "USER\|pids_limit\|mem_limit\|DOCKER_CONTENT_TRUST" Dockerfile docker-compose*.yml 2>/dev/null
grep -n "^FROM\|RUN npm\|RUN pip" Dockerfile 2>/dev/null  # 다단계 빌드 확인

# 14. NGINX 보안 설정 검색
grep -n "server_tokens\|limit_except\|proxy_hide_header\|proxy_read_timeout" nginx/*.conf 2>/dev/null
grep -n "X-Content-Type\|X-Frame\|Strict-Transport" nginx/*.conf 2>/dev/null

# 15. 감사 로그 무결성 검색
grep -rn "HMAC\|createHmac\|signLog\|integrity" --include="*.js" | grep -v node_modules

# 16. 하드코딩 계정 검색
grep -rn "INSERT INTO users\|username.*=.*'" --include="*.js" --include="*.sql" | grep -v node_modules | grep -v "\.test\."
find . -path "*/migrations/*.sql" -exec grep -l "INSERT INTO users" {} \;
```

### Step 5: 결과 보고서 생성

점검 결과를 아래 형식으로 `docs/` 에 보고서를 생성합니다:

```markdown
# [프로젝트명] 보안 점검 결과 보고서

| 구분 | 내용 |
|------|------|
| **시스템명** | [프로젝트명] |
| **점검일** | [YYYY-MM-DD] |
| **점검 기준** | 웹/API 보안 가이드 (43항목) + AI/LLM 보안 가이드 (20항목) |
| **기술 스택** | [프레임워크, DB, AI 서비스 등] |

## 1. 종합 요약

| 구분 | 양호 | 미흡 | 해당없음 | 합계 |
|------|------|------|----------|------|
| 웹/API 보안 | N | N | N | 43 |
| AI/LLM 보안 | N | N | N | 20 |
| **전체** | **N** | **N** | **N** | **63** |

## 2. 웹/API 보안 점검 결과
[각 항목별 판정 + 근거 + 관련 코드 위치]

## 3. AI/LLM 보안 점검 결과
[각 항목별 판정 + 근거 + 관련 코드 위치]

## 4. 미흡 항목 개선 우선순위
[Phase 1: 긴급, Phase 2: 일반, Phase 3: 강화]

## 5. 양호 항목 현황 (유지 필요)
[현재 잘 구현된 보안 조치 목록]
```

### Step 6: 개선 조치 (선택)

사용자가 조치를 요청하면 미흡 항목에 대해 코드 수정을 수행합니다.
우선순위: **중요 > 일반**, **CRITICAL > HIGH > MEDIUM > LOW**

#### 일반적인 조치 패턴

**XSS 방어 (localStorage 토큰 제거)**:
- httpOnly 쿠키로 JWT 전환
- localStorage에서 토큰 저장/읽기 코드 제거
- API 클라이언트에 `credentials: 'include'` 추가

**CSRF 방어**:
- Content-Type + X-Requested-With 헤더 검증 미들웨어
- SameSite=Lax 쿠키 설정

**프롬프트 인젝션 방어**:
- 특수 토큰 필터링 미들웨어 (16종)
- 인젝션 패턴 탐지 (12종)
- 서버 측 시스템 프롬프트 조립

**시크릿 관리**:
- 환경변수 필수화 (기본값 제거)
- 서버 시작 시 필수 환경변수 검증
- AES-256-GCM 암호화 저장

**Rate Limiting**:
- login: 5회/15분
- api: 1,000회/15분
- strict (관리자/AI): 200회/15분
- upload: 10회/1시간

**에러 새니타이징**:
- 클라이언트 반환 에러 일반화
- 상세 에러는 서버 로그에만 기록

**보안 헤더 (Helmet.js)**:
- HSTS, X-Content-Type-Options, X-Frame-Options
- CSP 설정 (프로덕션)

**감사 로깅**:
- 관리자 작업 로그 (사용자, 작업, 리소스, IP)
- HMAC-SHA256 로그 무결성 서명
- Winston 구조화 로깅

**컨테이너 보안 (Docker)**:
- Dockerfile에 비루트 사용자 생성: `RUN adduser --disabled-password --uid 1001 appuser && USER appuser`
- 다단계 빌드 적용: `FROM node:20-slim AS deps` → `FROM node:20-slim AS runner`
- docker-compose에 리소스 제한: `pids_limit: 200`, `mem_limit: 2g`
- `DOCKER_CONTENT_TRUST=1` 환경변수 설정
- auditd 규칙으로 Docker 바이너리 감시 (`/usr/bin/docker`, `/var/lib/docker`, `/etc/docker`)
- `.env` 파일 read-only 마운트: `- .env:/app/.env:ro`

**웹서버(NGINX) 보안**:
- `server_tokens off;` — 서버 버전 노출 차단
- `proxy_hide_header X-Powered-By; proxy_hide_header Server;` — 프레임워크 정보 숨김
- `limit_except GET HEAD POST { deny all; }` — 비표준 HTTP 메서드 차단
- `proxy_read_timeout 300s; proxy_connect_timeout 75s;` — 타임아웃 설정
- 에러 응답 일반화: `error_page 400 401 403 404 500 /error.html;`
- `etag off;` (앱 레벨) — 캐시 관련 정보 유출 방지

**데이터 보관 정책**:
- 자동 정리 스케줄러 (node-cron 등): 매일 새벽 자동 실행
- 로그인 로그: 180일(6개월) 보관 후 삭제 — 정보통신망법 준수
- 감사 로그: 730일(2년) 후 아카이브 테이블 이동, 1825일(5년) 후 최종 삭제 — 개인정보보호법 준수
- AI 요청 로그: 180일 보관 후 삭제

---

## 주의사항

1. **점검 범위**: 이 스킬은 코드 레벨 정적 점검입니다. 동적 테스트(침투 테스트)는 별도 수행이 필요합니다.
2. **기술 스택**: Node.js + Express + React 기반으로 작성되었으나, 점검 항목 자체는 기술 스택에 무관합니다. 다른 스택에서는 검색 패턴만 조정하면 됩니다.
3. **AI/LLM 항목**: AI 기능이 없는 프로젝트는 LLM-01~20을 "해당없음"으로 처리합니다.
4. **컨테이너/NGINX 항목**: 컨테이너 미사용 프로젝트는 9-1~9-6, 10-1~10-5를 "해당없음"으로 처리합니다.
5. **보고서**: 결과 보고서는 `docs/SECURITY_AUDIT_REPORT.md` (웹/API) 또는 `docs/LLM_SECURITY_AUDIT.md` (AI/LLM)로 저장합니다.
6. **개선 조치**: 코드 수정은 사용자 확인 후 수행합니다. Phase별 우선순위에 따라 진행합니다.
