# AIFAB 하네스 워크플로우 가이드

> **기준일**: 2026-05-08
> **버전**: 2.0
> **하네스**: AI-Fab v2 — 20 스킬 (16 AIFAB + 4 mattpocock 통합) + 보안 감사 스킬 + 자동 Hook

---

## 목차

1. [스킬 전체 목록](#스킬-전체-목록)
2. [자동화 Hook](#자동화-hook)
3. [시나리오 1: 새 프로젝트 시작](#시나리오-1-새-프로젝트-시작)
4. [시나리오 2: 기존 프로젝트 리팩토링](#시나리오-2-기존-프로젝트-리팩토링)
5. [두 시나리오 공통 패턴](#두-시나리오-공통-패턴)
6. [보안 스킬 상세 비교](#보안-스킬-상세-비교)
7. [빠른 참조 — 상황별 첫 명령어](#빠른-참조--상황별-첫-명령어)

---

## 스킬 전체 목록

### AI-Fab 워크플로우 스킬 (20개)

#### 정렬/언어 (4개) — mattpocock 통합

| 명령어 | 설명 |
|---|---|
| `/aifab:grill` | 구현 전 1:1 인터뷰로 요구사항 정렬 + CONTEXT.md / ADR 실시간 업데이트 |
| `/aifab:grill-me` | 코드 무관 아이디어/플랜 인터뷰로 공유된 이해 도달 |
| `/aifab:caveman` | 토큰 75% 절감 초압축 모드 (세션 내 지속, "stop caveman"으로 해제) |
| `/aifab:diagnose` | 재현 우선 디버깅 루프 (재현→최소화→가설→계측→수정→회귀테스트) |

#### 핵심 워크플로우 + 보조 도구 + 코드 조작 + 결정 (16개)

| 명령어 | 설명 |
|---|---|
| `/aifab:discover` | 프로젝트 구조 및 기존 코드베이스를 분석하여 컨텍스트를 수집한다 |
| `/aifab:plan` | 요구사항을 파악하고 구현 웨이브(wave)로 분해한 실행 계획을 생성한다 |
| `/aifab:execute` | 계획된 웨이브를 순서대로 실행하며 기능을 구현한다 |
| `/aifab:security` | OWASP/AI-LLM/API/시크릿 4도메인 보안 스캔 및 치명적 이슈 자동 수정 |
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

### 보안 감사 스킬 (전수 점검용)

| 명령어 | 설명 |
|---|---|
| `/security-audit` | 정부 개발보안 가이드 기반 정적 점검 (웹/API 43항목 + AI/LLM 20항목 + Docker 6항목 + NGINX 5항목) |

---

## 자동화 Hook

### PostToolUse — git commit 감지 후 보안 알림 주입

**설정 파일**: `.claude/settings.json`

**동작 방식**:

```
Bash 도구로 git commit 실행
    └─ PostToolUse Hook 발동
    └─ 커맨드에 "git commit" 포함 여부 확인
    └─ 포함 시 → Claude 컨텍스트에 알림 주입:
         "[자동알림] git commit 감지됨. /aifab:security 실행 필요"
    └─ Claude가 즉시 /aifab:security 자동 실행
         ├─ ❌ 치명적 이슈 → 코드 자동 수정 + git commit
         ├─ ⚠️ 경고 → 사용자 확인 후 처리
         └─ ✅ 통과 항목 보고
```

**효과**: Wave마다 개발자가 잊어도 보안 회귀가 즉시 감지됨

---

## 시나리오 1: 새 프로젝트 시작

### 전체 흐름

```
grill-me → grill → compare/adr → plan → [execute → (auto)security] × N
  → playwright → uat → security-audit
```

### 단계별 상세

#### Phase 0a: 아이디어 정렬 (선택)

```
/aifab:grill-me
```
- 코드와 무관한 아이디어·플랜 단계에서 호출
- AI가 의사결정 트리의 모든 가지를 인터뷰로 해소
- 산출물 없음 (대화 기반)

```
/aifab:grill
```
- 구현 직전 도메인 언어와 요구사항을 정렬
- `CONTEXT.md`를 실시간 갱신 (도메인 전문가 공유 언어)
- 중요한 결정은 `docs/adr/`에 자동 기록

---

#### Phase 0b: 방향 설정

```
/aifab:compare
```
- 기술 스택 N개 옵션 비교 (트레이드오프 매트릭스 생성)
- 예: React vs Vue, PostgreSQL vs MongoDB, REST vs GraphQL

```
/aifab:adr
```
- 결정 사항을 Architecture Decision Record(Michael Nygard 형식)로 기록
- 결정의 배경·대안·결과를 문서화하여 나중에 "왜 이렇게 했지?" 방지

---

#### Phase 1: 계획 수립

```
/aifab:plan
```
- 요구사항 분석 → Wave N개로 분해
- 각 Wave에 성공 기준(success criteria) 정의
- `PLAN.md` 생성 (이후 모든 스킬의 기준 문서)

---

#### Phase 2: Wave 반복 실행

각 Wave마다 아래 루프를 반복한다.

```
/aifab:execute          ← Wave N 구현 (TDD: Red → Green → Refactor)
                           └─ git commit 발생
                                └─ [자동 Hook] /aifab:security 알림 주입
                                     └─ Claude가 즉시 보안 스캔 실행
                                          ├─ ❌ 치명적 → 자동 코드 수정 + commit
                                          └─ ⚠️ 경고 → 사용자 확인 후 처리
```

**독립적인 Wave인 경우 (선택)**:

```
/aifab:worktree         ← git worktree로 병렬 Wave 동시 진행
```

**문제 발생 시 (둘 중 선택)**:

```
/aifab:diagnose         ← 재현 가능한 버그
                           재현 루프 → 최소화 → 가설 → 계측 → 수정 → 회귀테스트

/aifab:debug            ← 재현 어려움 / 원인 불명
                           가설 → 증거 → 검증 → 수정 (4단계 RCA)
```

---

#### Phase 3: 교차 검증 (선택)

```
/aifab:codex-review     ← OpenAI Codex로 교차 AI 검증
```
- Claude의 맹점을 다른 AI 관점에서 교차 확인
- 중요한 비즈니스 로직 구현 후 권장

---

#### Phase 4: E2E 및 UAT

```
/aifab:playwright       ← E2E 테스트 생성 및 실행
/aifab:uat              ← 사용자 인수 테스트 시나리오 실행
```

---

#### Phase 5: 최종 감사 및 기록

```
/security-audit         ← 74개 항목 전수 점검
                           └─ docs/SECURITY_AUDIT_REPORT.md 생성
                                (납품·감사·컴플라이언스 증적용)

/aifab:worklog          ← 전체 작업 이력·결정 사항 기록
```

---

## 시나리오 2: 기존 프로젝트 리팩토링

### 전체 흐름

```
discover → map-codebase → grill → security-audit(before)
  → [refactor → (auto)security] × N
    → playwright → security-audit(after)
```

### 단계별 상세

#### Phase 0: 현황 파악 (코딩 전 필수)

```
/aifab:discover
```
- 프로젝트 구조, 의존성, 진입점, 라우트 분석
- 리팩토링 전 컨텍스트를 충분히 확보 (가정 위에서 작업 금지)

```
/aifab:map-codebase
```
- 4개 병렬 매퍼로 코드베이스 전체 분석:
  - `tech` — 기술 스택, 라이브러리 버전
  - `arch` — 아키텍처 레이어, 의존 방향
  - `quality` — 코드 품질, 테스트 커버리지
  - `concerns` — 잠재적 문제, 기술 부채
- 변경 전 스냅샷 확보 (리팩토링 후 비교 기준)

```
/aifab:grill
```
- map-codebase 결과를 바탕으로 기존 도메인 언어를 학습하고, 리팩토링 의도를 정렬
- `CONTEXT.md` 신규 생성 또는 갱신 (기존 코드 용어와 충돌 시 즉시 표면화)
- 리팩토링 범위·경계 결정을 ADR로 기록

---

#### Phase 1: 보안 현황 베이스라인

```
/security-audit
```
- 리팩토링 **전** 현재 보안 상태 점검
- `docs/SECURITY_AUDIT_REPORT_before.md` 저장
- 리팩토링으로 인한 보안 회귀를 나중에 before/after로 비교

---

#### Phase 2: 전략 수립

```
/aifab:compare          ← 리팩토링 방식 비교
                           예: 점진적 vs 일괄, 모노리스 vs 모듈 분리
/aifab:adr              ← 결정 기록
/aifab:plan             ← Wave 단위 계획 수립 (PLAN.md 생성)
```

---

#### Phase 3: 리팩토링 Wave 실행

각 Wave마다 아래 루프를 반복한다.

```
/aifab:refactor         ← Wave N 점진 리팩토링
                           ├─ 변경 전 테스트 통과 확인 (동작 기준선 확보)
                           ├─ 동작 보존하며 코드 변경
                           ├─ 변경 후 테스트 통과 확인
                           ├─ REFACTOR-LOG.md 자동 작성
                           └─ git commit
                                └─ [자동 Hook] /aifab:security 알림 주입
                                     └─ 리팩토링이 보안 회귀 일으켰는지 즉시 확인
```

**의존성·프레임워크 변경이 포함된 경우**:

```
/aifab:migrate          ← codemod 활용, Wave 단위 마이그레이션
                           예: Express 4 → 5, React 17 → 18, CommonJS → ESM
```

**문제 발생 시**:

```
/aifab:diagnose         ← 재현 가능한 동작 변경
                           재현 루프 구축 → 최소화 → 계측 → 수정 → 회귀테스트
/aifab:debug            ← 재현 어려움 / 원인 불명
                           가설 → 증거 → 검증 → 수정 (4단계 RCA)
/aifab:rollback         ← Wave 단위 안전한 롤백 (백업 브랜치 자동 보존)
                           ※ force-push 금지, 백업 브랜치로 항상 복구 가능
```

---

#### Phase 4: 최종 검증

```
/aifab:playwright       ← 기존 E2E 시나리오 전체 재실행
                           (리팩토링 후 사용자 시나리오 동작 여부 확인)

/security-audit         ← 리팩토링 후 보안 점검
                           └─ docs/SECURITY_AUDIT_REPORT_after.md 생성
                                └─ before vs after 비교로 개선 증적 확보

/aifab:worklog          ← 변경 이력·결정 사항·REFACTOR-LOG 기록
```

---

## 두 시나리오 공통 패턴

| 단계 | 새 프로젝트 | 리팩토링 |
|---|---|---|
| **정렬** | `grill-me` (선택) → `grill` | `grill` (map-codebase 후) |
| **진입** | `plan` | `discover` + `map-codebase` |
| **베이스라인** | 없음 | `security-audit` (before) |
| **Wave 실행** | `execute` | `refactor` (또는 `migrate`) |
| **Wave 후 보안** | Hook 자동 → `security` | Hook 자동 → `security` |
| **문제 발생** | `diagnose` (재현 가능) / `debug` (재현 불가) | `diagnose` / `debug` + `rollback` |
| **교차 검증** | `codex-review` (선택) | `codex-review` (선택) |
| **최종 감사** | `security-audit` 1회 | `security-audit` before/after 비교 |
| **기록** | `worklog` + `CONTEXT.md` | `worklog` + REFACTOR-LOG.md + `CONTEXT.md` |
| **상시** | `caveman` (토큰 압박 시) | `caveman` (토큰 압박 시) |

### Wave 루프 — 두 시나리오 공통

```
┌─────────────────────────────────────────────────┐
│              Wave N 실행 루프                    │
│                                                  │
│  execute / refactor                              │
│      └─ TDD (Red → Green → Refactor)             │
│      └─ git commit                               │
│           └─ [자동 Hook] security 알림 주입      │
│                └─ /aifab:security 실행           │
│                     ├─ ❌ 치명적 → 즉시 수정    │
│                     ├─ ⚠️ 경고 → 사용자 확인   │
│                     └─ ✅ 통과 → 다음 Wave      │
└─────────────────────────────────────────────────┘
```

---

## 보안 스킬 상세 비교

| 항목 | `/aifab:security` | `/security-audit` |
|---|---|---|
| **실행 시점** | Wave 완료 후 자동 (Hook) | 프로젝트 시작·종료 시 수동 1회 |
| **점검 기준** | OWASP Top 10 + AI/LLM + API + 시크릿 | 행정안전부 개발보안 가이드 + AI/LLM v1.1.0 |
| **점검 항목** | 4개 도메인 (정성적) | 74개 항목 (체크리스트) |
| **출력** | 즉시 코드 수정 또는 경고 보고 | `docs/SECURITY_AUDIT_REPORT.md` |
| **자동 수정** | ❌ 치명적 이슈는 자동 수정 | 수동 수정 (Phase별 우선순위 제시) |
| **용도** | 개발 중 CI 역할 (회귀 방지) | 납품·감사·컴플라이언스 증적 |
| **소요 시간** | 빠름 (변경 파일 위주) | 느림 (전체 코드베이스 전수 점검) |

---

## 빠른 참조 — 상황별 첫 명령어

| 상황 | 명령어 |
|------|--------|
| 뭘 만들지 모르겠다 | `/aifab:grill-me` |
| 요구사항이 모호하다 | `/aifab:grill` |
| 새 프로젝트 출발 (구조 결정) | `/aifab:discover` |
| 처음 보는 코드베이스 | `/aifab:map-codebase` |
| 두 옵션 사이 결정 | `/aifab:compare` |
| 큰 결정 영구 기록 | `/aifab:adr new` |
| 재현되는 버그/회귀 | `/aifab:diagnose` |
| 가끔 나는 / 원인 불명 버그 | `/aifab:debug` |
| 컨텍스트 50% 도달, 토큰 압박 | `/aifab:caveman` |
| 작업 재개 | `/aifab:worklog resume` |
| 동작 보존 점진 개선 | `/aifab:refactor` |
| 의존성/프레임워크 교체 | `/aifab:migrate` |
| 문제 시 안전한 되돌리기 | `/aifab:rollback` |

---

## 변경 이력

- **v2.0 (2026-05-08)**: mattpocock/skills 4개 통합 (grill, grill-me, caveman, diagnose). 정렬 단계와 재현 우선 디버깅 옵션 추가.
- **v1.0 (2026-05-08)**: 초기 버전 (16 AIFAB 스킬 + security-audit + Hook).

---

*이 문서는 AI-Fab v2 하네스 기준으로 작성되었습니다. 스킬 목록 전체: [`.claude/plugins/aifab/SKILLS.md`](.claude/plugins/aifab/SKILLS.md)*
