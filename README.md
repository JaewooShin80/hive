# AI-Fab 개발 워크플로우

AI-Fab 프로젝트 전용 Claude Code 개발 워크플로우. Andrej Karpathy의 4원칙과 Opus-Sonnet-Haiku 멀티에이전트 오케스트레이션을 결합하여 일관성 있는 고품질 코드를 생성한다.

---

## 빠른 시작

```bash
# 1. 새 프로젝트 시작
/aifab:discover

# 2. 개발 플랜 작성
/aifab:plan

# 3. Wave 실행 (반복)
/aifab:execute

# 4. 보안 검토 (각 Wave 완료 후)
/aifab:security

# 5. E2E 테스트 (전체 개발 완료 후)
/aifab:playwright

# 6. UAT
/aifab:uat

# 작업 중단 후 재시작
/aifab:worklog resume
```

---

## 워크플로우 개요

```
/aifab:discover
    ↓  개방형 질문 → 아키텍처 선택 (스택 제약 없음)
/aifab:plan
    ↓  Advisor(Opus)가 Wave 분해 → PLAN.md 작성
/aifab:execute  ← 반복 (Wave별)
    ↓  Advisor → Sonnet/Haiku 병렬 실행 → Advisor 검토
/aifab:security  ← 각 Wave 완료 후
    ↓  OWASP / AI-LLM / API / 시크릿 4영역 자동 검토
/aifab:playwright  ← 전체 개발 완료 후
    ↓  E2E 시나리오 자동 생성 및 실행
/aifab:uat
    ↓  사용자 인수 테스트 → 피드백 수집 → 재작업 루프
```

---

## 명령어 레퍼런스

### `/aifab:discover` — 아키텍처 결정

프로젝트를 시작할 때 가장 먼저 실행한다. 사전에 정해진 스택이 없으며, 질문 답변을 바탕으로 최적 아키텍처를 도출한다.

**입력 방식 (선택):**
- 기능을 자연어로 설명
- 기존 코드베이스 디렉토리 지정
- 요구사항 문서 경로 지정

**출력:**
- `ARCHITECTURE.md` — 선택된 아키텍처 상세
- `WORKLOG.md` — 작업일지 초기화

---

### `/aifab:plan` — Wave 기반 플랜 작성

Advisor(Opus)가 기능을 Wave 단위로 분해하고 `PLAN.md`를 작성한다.

| Wave 크기 | 기준 | 예상 기간 |
|-----------|------|----------|
| Small | 단일 엔드포인트, 독립 컴포넌트 | 0.5~1일 |
| Medium | 기능 묶음, 서비스 레이어 | 1~2일 |
| Large | 크로스 서비스 통합, 외부 API | 2~3일 |

각 Wave는 **TDD 기준** (실패 테스트 → 구현 → 리팩토링)으로 설계된다.

---

### `/aifab:execute` — Wave 실행

멀티에이전트 오케스트레이션의 핵심.

```
Advisor (Opus)
├─ 작업 분해 및 분류
├─ Haiku → 보일러플레이트 생성 (병렬)
│   모델 정의, CRUD 스텁, 설정 파일
├─ Sonnet → 비즈니스 로직 + 테스트 (병렬)
│   TDD Red→Green→Refactor
└─ Advisor 검토 → 통일성/원칙 확인 → 수정
```

완료 시 자동으로 git commit.

---

### `/aifab:security` — 보안 검토

4개 도메인 자동 스캔. 치명적 이슈는 즉시 자동 수정.

| 도메인 | 검토 항목 |
|--------|----------|
| OWASP Top 10 | SQL Injection, XSS, CSRF, IDOR, Broken Auth |
| AI/LLM 보안 | Prompt Injection, 시스템 프롬프트 노출, 출력 검증 |
| API 보안 | JWT 검증, Rate Limiting, CORS 설정 |
| 시크릿 관리 | 하드코딩 키 스캔, .env gitignore, 로그 노출 |

---

### `/aifab:playwright` — E2E UI 테스트

전체 개발 완료 후 실행. PLAN.md 기반으로 주요 사용자 시나리오를 자동 생성하고 실행한다.

- Happy Path, Auth Flow, CRUD, Error States 자동 커버
- 실패 시 스크린샷 캡처 → Sonnet이 수정

---

### `/aifab:uat` — 사용자 인수 테스트

Playwright 통과 후 실행. 사용자가 직접 테스트하고 결과를 입력한다.

- 시나리오별 통과/실패/부분통과 수집
- 실패 시 새 Wave를 PLAN.md에 추가 → 자동 재작업 루프
- 전체 통과 시 `v1.0.0` git tag 생성

---

### `/aifab:worklog` — 작업일지

| 명령어 | 동작 |
|--------|------|
| `/aifab:worklog` | 현재 상태 표시 |
| `/aifab:worklog init <프로젝트명>` | WORKLOG.md 초기화 |
| `/aifab:worklog update` | 최신 git 상태 반영 |
| `/aifab:worklog resume` | **중단된 작업 재시작** (가장 중요) |

---

## CLI 상태바

Claude Code 세션 중 하단에 표시:

```
🏭 AI-Fab | 🤖 opus-4-7 | 📊 Wave 3/8 (37%) | ctx ████░░░░ 42% ⚠
5h  [████████░░] 78%  |  7day [████░░░░░░] 41%
```

| 항목 | 설명 |
|------|------|
| `ctx` 바차트 | Context 창 사용률. 50% 초과 시 즉시 `/compact` |
| `5h` 바차트 | 5시간 롤링 기준 Claude 사용량 |
| `7day` 바차트 | 7일 기준 누적 사용량 |

**Context 경고:** 35~49% ⚠, 50%+ 🔴 (즉시 `/compact` 필요)

---

## 모델 설정

| 모델 | 역할 | 환경변수 |
|------|------|----------|
| `claude-opus-4-7` | Advisor — 플랜, 아키텍처, 검토 | `AIFAB_ADVISOR_MODEL` |
| `claude-sonnet-4-6` | Worker — 로직, 테스트 | `AIFAB_WORKER_MODEL` |
| `claude-haiku-4-5` | Generator — 보일러플레이트 | `AIFAB_BOILERPLATE_MODEL` |

모델 교체: `settings.json`의 환경변수 수정.

---

## 핵심 원칙 (Karpathy 4원칙)

1. **코딩 전 사고** — 가정 명시, 불확실 시 질문, 추측으로 진행 금지
2. **단순성 우선** — 요청된 최소 구현만, 미래 대비 코드 금지
3. **수술적 변경** — 요청과 관련된 코드만 수정
4. **목표 기반 실행** — HOW가 아닌 WHAT 지정, 에이전트가 달성까지 반복

**Context 관리:** 항상 50% 미만 유지. 초과 시 `/compact` 즉시 실행.

---

## 디렉토리 구조

```
AIFAB-harness/
├── CLAUDE.md                    ← 전역 규칙 (Karpathy 원칙)
├── README.md                    ← 이 파일
├── settings.json                ← Claude Code 설정
├── scripts/
│   └── aifab-status.sh         ← CLI 상태바 스크립트
└── .claude/
    └── plugins/aifab/
        └── skills/
            ├── discover.md      ← /aifab:discover
            ├── plan.md          ← /aifab:plan
            ├── execute.md       ← /aifab:execute
            ├── security.md      ← /aifab:security
            ├── playwright.md    ← /aifab:playwright
            ├── uat.md           ← /aifab:uat
            └── worklog.md       ← /aifab:worklog
```

---

## 생성 파일 (프로젝트별)

워크플로우 실행 중 프로젝트 루트에 생성:

| 파일 | 생성 시점 | 내용 |
|------|----------|------|
| `ARCHITECTURE.md` | `/aifab:discover` 완료 | 선택된 아키텍처 상세 |
| `PLAN.md` | `/aifab:plan` 완료 | Wave별 작업 플랜 |
| `WORKLOG.md` | `/aifab:discover` 완료 | 작업일지 |
| `docs/UAT-REPORT.md` | `/aifab:uat` 완료 | UAT 결과 보고서 |
