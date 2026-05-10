# Design: AIFAB + mattpocock/skills 통합

**날짜:** 2026-05-08  
**상태:** 승인됨  
**범위:** 기존 AIFAB 16개 스킬 유지 + mattpocock 4개 스킬 추가

---

## 목표

mattpocock/skills의 전처리 레이어(정렬·언어·디버깅)를 AIFAB 실행 레이어에 결합하여 단일 통합 워크플로우를 만든다. 산출물 체계는 로컬 파일 기반으로 유지한다.

---

## 결정 사항

| 항목 | 결정 |
|------|------|
| 커맨드 프리픽스 | `/aifab:` (기존 유지) |
| 기존 스킬 처리 | 16개 전부 유지, 추가만 |
| CONTEXT.md 위치 | 프로젝트 루트 |
| 추가 스킬 | grill, grill-me, caveman, diagnose 4개 |
| 통합 방식 | 단순 추가 (기존 스킬 변경 없음) |

---

## 추가 스킬 명세

### `/aifab:grill` (← mattpocock/grill-with-docs)

- **역할:** 구현 전 1:1 인터뷰로 요구사항 정렬. 용어가 확정되면 `CONTEXT.md`를 실시간 업데이트. 중요 결정은 ADR로 기록.
- **담당 모델:** Advisor (claude-opus-4-7)
- **산출물:** `CONTEXT.md` (첫 용어 확정 시 생성), `docs/adr/` (필요 시)
- **사용 시점:** `/aifab:discover` 전, 요구사항이 모호할 때

### `/aifab:grill-me` (← mattpocock/grill-me)

- **역할:** 코드와 무관한 아이디어·플랜을 인터뷰로 구체화. `CONTEXT.md` 참조 없음.
- **담당 모델:** Advisor (claude-opus-4-7)
- **사용 시점:** 기술 결정 전 아이디어 검증

### `/aifab:caveman` (← mattpocock/caveman)

- **역할:** 토큰 75% 절감 초압축 모드. 한번 활성화되면 세션 내내 유지.
- **담당 모델:** — (행동 변경)
- **해제:** "stop caveman" 또는 "normal mode"
- **사용 시점:** 언제든지

### `/aifab:diagnose` (← mattpocock/diagnose)

- **역할:** 재현→최소화→가설→계측→수정→회귀테스트 순서의 디버깅 루프. 재현 가능한 피드백 루프 구축을 최우선으로 한다.
- **담당 모델:** Sonnet (claude-sonnet-4-6)
- **사용 시점:** 버그 재현이 가능할 때 (재현 불가 시 `/aifab:debug` 사용)

---

## `/aifab:debug` vs `/aifab:diagnose` 구분

| | `/aifab:debug` | `/aifab:diagnose` |
|--|----------------|-------------------|
| 접근 | 가설 수립 → 증거 수집 → RCA | 재현 루프 구축 → 최소화 → 계측 |
| 강점 | 재현 어려운 버그, 복잡한 원인 분석 | 재현 가능한 버그, 빠른 피드백 루프 |
| 선택 기준 | 재현 안 됨 / 원인 불명 | 재현 가능 / 느린 디버깅 |

---

## 통합 워크플로우

### 신규 프로젝트

```
/aifab:grill      ← [선택] 요구사항 정렬 (CONTEXT.md 생성)
      ↓
/aifab:discover   ← 아키텍처 결정
      ↓
/aifab:plan       ← Wave 분해 (PLAN.md)
      ↓
/aifab:execute    ← 멀티에이전트 실행
      ↓
/aifab:security   ← 4도메인 보안 검증
```

### 버그 대응

```
재현 가능? → YES → /aifab:diagnose
           → NO  → /aifab:debug
```

### 일상 보조

```
/aifab:caveman    ← 토큰 절감 (언제든 ON)
/aifab:grill-me   ← 아이디어 구체화 (코드 무관)
```

---

## 파일 변경 범위

### 새로 생성 (4개)

```
.claude/plugins/aifab/skills/grill.md
.claude/plugins/aifab/skills/grill-me.md
.claude/plugins/aifab/skills/caveman.md
.claude/plugins/aifab/skills/diagnose.md
```

### 수정 (2개)

```
.claude/plugins/aifab/SKILLS.md   ← "정렬/언어" 카테고리 추가
CLAUDE.md                          ← 커맨드 테이블에 4개 추가
```

### 변경 없음

- 기존 16개 스킬 파일
- `_shared/` 공통 표준
- `settings.json`
- 심볼릭 링크

---

## 프로젝트 사용 시 산출물 (로컬)

```
프로젝트 루트/
├── CONTEXT.md          ← 공유 도메인 언어 (/aifab:grill 이 생성)
├── docs/
│   └── adr/            ← 중요 결정 ADR (/aifab:grill 이 필요 시 생성)
├── PLAN.md             ← 기존
└── WORKLOG.md          ← 기존
```

---

## 제외 항목

- mattpocock의 `/to-prd`, `/to-issues`, `/triage` — GitHub 이슈 의존, 로컬 체계와 불일치
- `/zoom-out`, `/prototype` — 기존 AIFAB 스킬로 커버 가능
- `/improve-codebase-architecture` — `/aifab:refactor`와 역할 중복
