# AI-Fab 개발 워크플로우

AI-Fab 프로젝트 전용 Claude Code 개발 워크플로우. Andrej Karpathy의 4원칙과 Opus-Sonnet-Haiku 멀티에이전트 오케스트레이션을 결합하여 일관성 있는 고품질 코드를 생성한다.

---

## 설치

사용 패턴에 따라 3가지 방법 중 선택.

### 방법 A: 새 프로젝트 템플릿으로 사용 (권장)

새 AI-Fab 프로젝트를 시작할 때:

```bash
# 1. AIFAB-harness 복제
git clone https://github.com/JaewooShin80/aifab.git my-new-project
cd my-new-project

# 2. 기존 git 히스토리 제거 후 새로 시작
rm -rf .git
git init
git add .
git commit -m "chore: initial AI-Fab setup"

# 3. Claude Code 실행
claude
```

`/aifab:discover` 명령으로 바로 시작.

### 방법 B: 기존 프로젝트에 적용

이미 존재하는 프로젝트에 AI-Fab 워크플로우를 추가:

```bash
# 기존 프로젝트 디렉토리에서
cd my-existing-project

# AIFAB-harness 파일을 임시 디렉토리에 복제
git clone https://github.com/JaewooShin80/aifab.git /tmp/aifab

# 필요 파일 복사 (기존 CLAUDE.md/settings.json 보존 주의)
cp -r /tmp/aifab/.claude .
cp -r /tmp/aifab/scripts .
chmod +x scripts/aifab-status.sh

# CLAUDE.md가 이미 있으면 머지, 없으면 복사
[ -f CLAUDE.md ] || cp /tmp/aifab/CLAUDE.md .

# settings.json도 같은 방식 (기존 설정과 머지 필요할 수 있음)
[ -f settings.json ] || cp /tmp/aifab/settings.json .

rm -rf /tmp/aifab
```

기존 `CLAUDE.md`/`settings.json`이 있으면 수동 머지 필요.

### 방법 C: 전역 스킬로 설치 (모든 프로젝트에서 사용)

`/aifab:*` 명령어를 모든 프로젝트에서 사용하려면:

```bash
# AIFAB-harness 복제
git clone https://github.com/JaewooShin80/aifab.git ~/.local/share/aifab-harness

# 스킬을 Claude Code 전역 플러그인 디렉토리에 심볼릭 링크
mkdir -p ~/.claude/plugins
ln -s ~/.local/share/aifab-harness/.claude/plugins/aifab ~/.claude/plugins/aifab

# 상태바 스크립트도 전역에서 접근 가능하게
chmod +x ~/.local/share/aifab-harness/scripts/aifab-status.sh
```

각 프로젝트마다 `CLAUDE.md`만 복사하거나, 전역 `~/.claude/CLAUDE.md`에 AI-Fab 규칙 추가.

---

## 사전 요구사항

| 도구 | 용도 | 필수/선택 |
|------|------|----------|
| Claude Code CLI | 모든 명령 실행 | 필수 |
| `git` | 버전 관리 / 워크트리 | 필수 |
| `bash` | 상태바 스크립트 | 필수 |
| `python3` | 사용량 통계 파싱 | 선택 (없으면 사용량 바차트만 비활성) |
| `node` / `npm` | Playwright (E2E 테스트) | 선택 (E2E 사용 시) |
| `@openai/codex` CLI | 교차 AI 검증 | 선택 (codex-review 사용 시) |

### Claude Code 인증

```bash
# Claude Pro/Team 구독자
claude login

# 또는 API 키 사용
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 선택 도구 설치

```bash
# Playwright (방법 A에서 자동 설치되지만 미리 설치 가능)
npm install -D @playwright/test
npx playwright install chromium

# OpenAI Codex CLI (codex-review 사용 시)
npm install -g @openai/codex
codex login
```

---

## 설치 확인

설치 후 다음 명령으로 정상 동작 확인:

```bash
# 1. 상태바 스크립트 동작 확인
bash scripts/aifab-status.sh
# 기대 출력: [AI-Fab] | model: opus-4-7 | wave: -/- | ctx --
#           5h   [----------] 0%  |  7day [----------] --%

# 2. Claude Code에서 스킬 인식 확인
claude
> /aifab:
# 자동완성 목록에 11개 스킬이 보여야 함:
# discover, plan, execute, security, playwright, uat, worklog,
# debug, map-codebase, worktree, codex-review
```

---

## 빠른 시작

```bash
# 0. 기존 코드베이스 분석 (brownfield 시작 시)
/aifab:map-codebase

# 1. 새 프로젝트 시작
/aifab:discover

# 2. 개발 플랜 작성
/aifab:plan

# 3. Wave 실행 (반복)
/aifab:execute

# 3-1. 병렬 진행 (선택)
/aifab:worktree create wave-3
/aifab:execute --parallel 3,4,5

# 3-2. 디버깅 (필요 시)
/aifab:debug "<증상 설명>"

# 4. 보안 검토 (각 Wave 완료 후)
/aifab:security

# 4-1. 교차 AI 검증 (선택)
/aifab:codex-review

# 5. E2E 테스트 (전체 개발 완료 후)
/aifab:playwright

# 6. UAT
/aifab:uat

# 작업 중단 후 재시작
/aifab:worklog resume

# === v2 추가 명령 ===

# 결정 시점에 옵션 비교
/aifab:compare "ORM 선택"

# 큰 결정은 ADR로 기록
/aifab:adr new "Pydantic v2 채택"

# 동작 보존 리팩토링
/aifab:refactor "<대상 모듈>"

# 의존성 마이그레이션
/aifab:migrate "Pydantic v1 -> v2"

# Wave 단위 롤백
/aifab:rollback wave 3
```

---

## 워크플로우 개요

```
[brownfield] /aifab:map-codebase  → 4-병렬 매퍼로 코드베이스 분석
                ↓
/aifab:discover
    ↓  개방형 질문 → 아키텍처 선택 (스택 제약 없음)
/aifab:plan
    ↓  Advisor(Opus)가 Wave 분해 → PLAN.md 작성
/aifab:execute  ← 반복 (Wave별, 워크트리로 병렬 가능)
    ↓  Advisor → Sonnet/Haiku 병렬 실행 → Advisor 검토
    ↳ [버그 발생] /aifab:debug → 4단계 RCA
/aifab:security  ← 각 Wave 완료 후
    ↓  OWASP / AI-LLM / API / 시크릿 4영역 자동 검토
    ↳ [선택] /aifab:codex-review → OpenAI 교차 검증
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

### `/aifab:debug` — 체계적 디버깅 (4단계 RCA)

추측 디버깅 금지. **가설 → 증거 → 검증 → 수정** 4단계 강제.

```bash
/aifab:debug "<증상 설명>"
/aifab:debug session              # 진행 중인 세션 재개
/aifab:debug history              # 과거 세션 목록
```

`DEBUG-SESSION.md`에 가설별 검증 결과 기록. 재발 방지 회고 포함.

---

### `/aifab:map-codebase` — 4-병렬 매퍼 분석

기존 코드베이스에 진입할 때 4개 매퍼 에이전트(Sonnet)를 병렬 실행:

| 매퍼 | 산출물 |
|------|--------|
| Tech Stack | `docs/codebase-map/01-TECH.md` |
| Architecture | `docs/codebase-map/02-ARCH.md` |
| Quality | `docs/codebase-map/03-QUALITY.md` |
| Concerns | `docs/codebase-map/04-CONCERNS.md` |

종합 SUMMARY와 권장 진입 전략 자동 생성.

---

### `/aifab:worktree` — 병렬 Wave 워크스페이스

독립 Wave를 git worktree로 분리해 동시 진행:

```bash
/aifab:worktree list
/aifab:worktree create wave-3
/aifab:worktree merge wave-3
/aifab:worktree status
```

`/aifab:execute --parallel 3,4,5`로 여러 Wave 동시 실행. 충돌 가능성 자동 검사.

---

### `/aifab:codex-review` — 교차 AI 검증

OpenAI Codex CLI로 독립적 코드 리뷰. Karpathy 원칙 준수, 보안, 엣지케이스 등 검증:

```bash
/aifab:codex-review                # 마지막 commit
/aifab:codex-review wave 3         # Wave 3 누적
/aifab:codex-review file <path>    # 특정 파일
```

Verdict: APPROVE / APPROVE_WITH_NITS / REQUEST_CHANGES / REJECT

Codex 미설치 시 사용자가 직접 ChatGPT 등에 복사하는 fallback 지원.

---

### `/aifab:refactor` — 동작 보존 리팩토링

테스트로 회귀 방지하며 점진적으로 구조 개선.

```bash
/aifab:refactor <대상 모듈>
```

- 베이스라인 테스트 통과 확인 → 거부 시 회귀 테스트부터 추가
- Strangler-fig / Branch-by-abstraction 패턴 자동 선택
- 각 단계 5분 이내 (revertable commit)
- `REFACTOR-LOG.md`에 단계별 동작 보존 증거 기록

---

### `/aifab:migrate` — 의존성/프레임워크 마이그레이션

```bash
/aifab:migrate "Pydantic v1 -> v2"
/aifab:migrate "React 17 -> 18"
```

- WebSearch로 공식 마이그레이션 가이드 자동 참조
- grep으로 영향 범위 스캔
- Codemod 도구 자동 탐지 (jscodeshift, libcst, bump-pydantic 등)
- Haiku(기계 변환) + Sonnet(의미 변환) 역할 분리
- 의존성 commit과 코드 commit 분리

---

### `/aifab:rollback` — 안전한 롤백

```bash
/aifab:rollback wave 3        # Wave 3 직전으로
/aifab:rollback commit abc123 # 특정 commit으로
/aifab:rollback last          # 마지막 Wave 취소
/aifab:rollback dry-run       # 영향 분석만
```

- 자동 백업 브랜치 생성 (`backup/pre-rollback-YYYYMMDD-HHMM`)
- 영향 받는 후속 Wave 분석 + 사용자 확인
- revert(권장) / reset / cherry-pick 보존 전략 선택
- 보안 수정 commit 보존 가능

---

### `/aifab:compare` — N-옵션 비교

```bash
/aifab:compare "ORM 선택"
/aifab:compare "API 스타일" --options "REST,GraphQL,tRPC"
```

- 옵션 2~5개 트레이드오프 매트릭스 작성
- 평가 기준 정의 → 점수(1-5) + 가중치
- Advisor 추천 + 차순위와의 결정적 차이
- `docs/decisions/compare-<topic>.md` 보고서 저장
- 큰 결정은 `/aifab:adr` 자동 호출 권장

---

### `/aifab:adr` — Architecture Decision Records

Michael Nygard 형식 의사결정 기록.

```bash
/aifab:adr new "Pydantic v2 채택"
/aifab:adr list
/aifab:adr show 0003
/aifab:adr supersede 0003 0007
```

각 ADR: Status / Context / Decision / Consequences / Alternatives.
`docs/adr/NNNN-<slug>.md` + 자동 인덱스 갱신.

---

## CLI 상태바

Claude Code 세션 중 하단에 2줄 표시. 터미널/폰트 환경에 따라 3가지 스타일 선택 가능.

### 스타일 옵션

`AIFAB_STATUS_STYLE` 환경변수 또는 `settings.json`의 `env`로 설정:

| 스타일 | 출력 예시 | 권장 환경 |
|--------|----------|----------|
| `ascii` (기본값) | `[AI-Fab] \| model: opus-4-7 \| wave: 3/8 (37%) \| ctx ######-- 42% !` | 모든 터미널 (안전) |
| `unicode` | `[AI-Fab] \| model: opus-4-7 \| wave: 3/8 (37%) \| ctx ████░░░░ 42% !` | 박스 문자 지원 폰트 |
| `emoji` | `🏭 AI-Fab \| 🤖 opus-4-7 \| 📊 3/8 (37%) \| ctx ████░░░░ 42% 🔴` | iTerm2, 최신 폰트 |

**기본값이 `ascii`인 이유:** 이모지/박스 문자는 폰트마다 폭이 달라 정렬이 깨지거나, 일부 폰트에서 미지원으로 깨진 글자가 표시될 수 있음.

### 두 번째 줄 (사용량)

```
5h   [##--------] 12%  |  7day [######----] 41%
```

| 항목 | 설명 |
|------|------|
| `ctx` 바차트 | Context 창 사용률. 50% 초과 시 즉시 `/compact` |
| `5h` 바차트 | 5시간 롤링 기준 Claude 사용량 |
| `7day` 바차트 | 7일 기준 누적 사용량 |

**Context 경고:** 35~49% `!` (warn), 50%+ `!!`/🔴 (즉시 `/compact` 필요)

### 한글/이모지 깨짐 문제 해결

상태바나 출력에서 글자가 깨질 경우:

1. **로케일 확인**: `locale` 명령어로 `LC_ALL=en_US.UTF-8` 또는 `C.UTF-8`인지 확인
2. **`settings.json`에 추가**:
   ```json
   "env": {
     "LC_ALL": "en_US.UTF-8",
     "AIFAB_STATUS_STYLE": "ascii"
   }
   ```
3. **터미널 폰트 확인**: 한글/이모지 미지원 폰트일 경우 D2Coding, Sarasa Mono K, JetBrains Mono 등으로 변경

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
        ├── SKILLS.md             ← 16 스킬 인덱스 + 의존성 그래프
        ├── _shared/              ← 공통 표준 프로토콜
        │   ├── prerequisites.md      (사전조건 매트릭스)
        │   ├── output-format.md      (Verdict/Severity/에러코드)
        │   ├── worklog-update.md     (WORKLOG 갱신 절차)
        │   ├── agent-dispatch.md     (Sub-agent 프롬프트)
        │   └── git-commit.md         (Conventional Commits)
        └── skills/
            ├── discover.md       ← /aifab:discover
            ├── plan.md           ← /aifab:plan
            ├── execute.md        ← /aifab:execute
            ├── security.md       ← /aifab:security
            ├── playwright.md     ← /aifab:playwright
            ├── uat.md            ← /aifab:uat
            ├── worklog.md        ← /aifab:worklog
            ├── debug.md          ← /aifab:debug
            ├── map-codebase.md   ← /aifab:map-codebase
            ├── worktree.md       ← /aifab:worktree
            ├── codex-review.md   ← /aifab:codex-review
            ├── refactor.md       ← /aifab:refactor       (v2)
            ├── migrate.md        ← /aifab:migrate        (v2)
            ├── rollback.md       ← /aifab:rollback       (v2)
            ├── compare.md        ← /aifab:compare        (v2)
            └── adr.md            ← /aifab:adr            (v2)
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
| `DEBUG-SESSION.md` | `/aifab:debug` 진행 중 | 디버그 세션 가설/증거/결과 |
| `docs/codebase-map/*.md` | `/aifab:map-codebase` 완료 | 4-매퍼 분석 보고서 |
| `docs/codex-reviews/*.md` | `/aifab:codex-review` 실행 | Codex 교차 검증 결과 |
| `.worktrees/wave-*/` | `/aifab:worktree create` | 병렬 Wave 작업 디렉토리 |
| `REFACTOR-LOG.md` | `/aifab:refactor` 진행 중 | 리팩토링 단계별 동작 보존 기록 |
| `MIGRATION-PLAN.md`, `MIGRATION-REPORT.md` | `/aifab:migrate` | 마이그레이션 영향 분석 + 결과 |
| `ROLLBACK-LOG.md` | `/aifab:rollback` 실행 | 롤백 시점/사유/영향 |
| `docs/decisions/compare-*.md` | `/aifab:compare` 실행 | 옵션 비교 매트릭스 |
| `docs/adr/NNNN-*.md` | `/aifab:adr new` | Architecture Decision Records |
