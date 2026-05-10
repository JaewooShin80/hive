# Design: AIFAB Phase·로드맵·마일스톤·진척률 매니지먼트 통합

**날짜:** 2026-05-08
**상태:** 승인됨
**범위:** AIFAB v2.0 → v2.1 (Phase 레이어 + 진척률 + 마일스톤 추가)

---

## 목표

AIFAB 하네스에 GSD 스타일 매니지먼트 레이어(Phase, ROADMAP, 진척률, 마일스톤)를 추가하되, Wave 단위 실행 정체성과 기존 산출물(PLAN.md, WORKLOG.md, ARCHITECTURE.md)을 그대로 유지한다. ROADMAP.md가 없는 프로젝트와의 역호환을 보장한다.

---

## 결정 사항

| 항목 | 결정 |
|------|------|
| 산출물 구조 | ROADMAP.md (Phase 인덱스) + PLAN.md (Wave 상세, 기존) |
| 책임 분리 | `/aifab:roadmap`이 Phase 결정, `/aifab:plan`이 Phase 내 Wave 분해 |
| 진척률 표시 | 상태바 통합 + `/aifab:progress` 대시보드 둘 다 |
| 마일스톤 식별 | semver (`v1.0.0`) — git tag로 영구 기록 |
| 추가 산출물 | 최소 — 백로그·REQ-ID 제외 |
| 구현 깊이 | 스킬 + Python 헬퍼 (B안) |
| 역호환 | ROADMAP.md 부재 시 기존 동작 유지 |

---

## 신규 산출물

### `ROADMAP.md`

프로젝트 루트에 위치. Phase 인덱스 + 마일스톤 메타 + Wave 상태 동기화.

```markdown
# 프로젝트 로드맵

> **마일스톤:** v1.0.0
> **시작일:** 2026-05-08
> **상태:** in_progress

## Phase 1: 인증 (Wave 1-3) ✅ complete

**목표:** 사용자 가입·로그인·세션 관리

- [x] Wave 1: User 모델 및 JWT
- [x] Wave 2: 회원가입 / 로그인 API
- [x] Wave 3: 세션 미들웨어

## Phase 2: 데이터 모델 (Wave 4-7) 🟡 in_progress

**목표:** 핵심 비즈니스 엔티티 정의

- [x] Wave 4: User Schema
- [x] Wave 5: Post Schema
- [ ] Wave 6: Comment Schema  ← 현재
- [ ] Wave 7: Migration

## Phase 3: API 노출 (Wave 8-12) ⬜ pending

**목표:** REST API 엔드포인트 + OpenAPI 문서

- [ ] Wave 8-12: ...
```

**규칙:**
- Phase 헤더: `## Phase N: <이름> (Wave a-b) <상태이모지>`
- 상태 이모지: `✅ complete`, `🟡 in_progress`, `⬜ pending`
- Wave 항목은 PLAN.md와 번호로 연결

### `MILESTONE-LOG.md` (선택적)

마일스톤 종료 회고. `/aifab:milestone complete`가 인터뷰로 작성.

---

## 신규 스킬 (3개)

### `/aifab:roadmap`

| 인자 | 동작 |
|------|------|
| `(없음)` | 현재 ROADMAP.md 표시. 없으면 안내 후 종료 |
| `init <마일스톤>` | ROADMAP.md 생성 (Phase 분해 인터뷰 포함). 예: `init v1.0.0` |
| `add-phase <이름>` | 신규 Phase 추가 |
| `update` | PLAN.md 읽어 Wave 상태를 ROADMAP.md에 동기화 |

**담당 모델:** Advisor (Opus) — `init`/`add-phase`는 도메인 분해 판단 필요
**산출물:** `ROADMAP.md`

### `/aifab:progress`

인자 없음. 한 번 호출에 풀 대시보드:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏷  마일스톤: v1.0.0  (시작 2026-05-08, 8일 경과)

📊 전체 진척: 5/12 Wave (42%)

Phase 1: 인증            ████████████  3/3   ✅
Phase 2: 데이터 모델      ██████░░░░░░  2/4   🟡 ← 현재
Phase 3: API 노출         ░░░░░░░░░░░░  0/5   ⬜

📍 현재 위치: Phase 2 / Wave 6 (Comment Schema)
🎯 다음 명령어: /aifab:execute
⏱  예상 남은: 7 Wave (~3.5일)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**담당 모델:** 없음 — Python 헬퍼가 계산
**의존:** `scripts/aifab-progress.py`

### `/aifab:milestone`

| 인자 | 동작 |
|------|------|
| `(없음)` | 현재 마일스톤 상태 표시 |
| `new <semver>` | 새 마일스톤 시작. ROADMAP.md 갱신 |
| `complete` | 모든 Phase 완료 확인 → git tag 생성 → 회고 인터뷰 → MILESTONE-LOG.md |
| `audit` | 마일스톤 종료 직전 점검 (테스트·보안·UAT 통과 여부) |

**담당 모델:** Advisor (Opus)
**산출물:** git tag (`v1.0.0`), `MILESTONE-LOG.md` (선택적)

---

## 기존 자산 변경

### `/aifab:plan` 수정 (역호환 유지)

**변경 후 동작:**
1. ROADMAP.md 존재 여부 확인
2. **있으면:** 인자로 받은 `<phase-id>` 또는 첫 incomplete Phase의 Wave만 분해. PLAN.md에 `Phase: N` 메타 헤더 추가.
3. **없으면:** 기존 동작 (단일 Phase로 동작) — 역호환

**호출 예:**
```
/aifab:plan                  # ROADMAP 있으면 첫 incomplete Phase, 없으면 기존 동작
/aifab:plan phase 2          # Phase 2의 Wave만 분해
```

**PLAN.md 추가 메타 (ROADMAP 있을 때):**
```markdown
# 개발 플랜

> **Phase:** 2 (데이터 모델)
> **Wave 범위:** 4-7
```

### `scripts/aifab-status.sh` 수정

**변경 전:**
```
[AI-Fab] | model: opus-4-7 | wave: 6/12 | ctx 35%
```

**변경 후 (ROADMAP 있을 때):**
```
[AI-Fab] | model: opus-4-7 | P2/3 W6/12 (50%) | ctx 35%
```

ROADMAP.md 부재 시 기존 표시 유지.

### `scripts/aifab-progress.py` (신규)

진척률 계산 라이브러리 + CLI.

**CLI:**
```
python3 scripts/aifab-progress.py            # 전체 대시보드 (사람 가독)
python3 scripts/aifab-progress.py --short    # 상태바용 한 줄
python3 scripts/aifab-progress.py --json     # 다른 도구 통합용
```

**Public API:**
- `parse_roadmap(path) -> Roadmap`
- `parse_plan(path) -> Plan`
- `compute_progress(roadmap, plan) -> Progress`
- `format_dashboard(progress) -> str`
- `format_short(progress) -> str`

테스트는 `scripts/tests/test_progress.py`에 작성.

### `gen_skills_index.py` 자동 갱신

새 스킬 3개의 frontmatter `description`이 CLAUDE.md / SKILLS.md 테이블에 자동 반영.

---

## 워크플로우 통합

### 신규 프로젝트 흐름 (변경된 부분)

```
/aifab:grill              ← 정렬 (변경 없음)
      ↓
/aifab:discover           ← 아키텍처 (변경 없음)
      ↓
/aifab:milestone new v1.0.0   ⭐ 신규
      ↓
/aifab:roadmap init       ⭐ 신규 — Phase 분해 인터뷰
      ↓
/aifab:plan               ← 자동으로 Phase 1의 Wave만 분해 (수정됨)
      ↓
/aifab:execute  ↻         ← 변경 없음
      ↓
/aifab:progress           ⭐ 신규 — 언제든 위치 확인
      ↓
[Phase 1 완료]
      ↓
/aifab:plan phase 2       ⭐ 다음 Phase
      ↓
... 반복 ...
      ↓
/aifab:milestone audit    ⭐ 종료 전 점검
      ↓
/aifab:milestone complete ⭐ git tag + 회고
```

### 기존 프로젝트 마이그레이션

- ROADMAP.md 부재 시 새 스킬은 안내 후 안전 종료
- `/aifab:plan` 등 기존 스킬은 부재 시 기존 동작 유지
- 기존 PLAN.md 그대로 유지하며 `/aifab:roadmap init`으로 ROADMAP 추가 시 자동 매핑

---

## 파일 변경 범위

### 새로 생성 (4)

```
.claude/plugins/aifab/skills/roadmap.md
.claude/plugins/aifab/skills/progress.md
.claude/plugins/aifab/skills/milestone.md
scripts/aifab-progress.py
```

### 수정 (2)

```
.claude/plugins/aifab/skills/plan.md      ← ROADMAP 참조 로직
scripts/aifab-status.sh                    ← 상태바 Phase·Wave 표시
```

### 자동 갱신 (2)

```
CLAUDE.md
.claude/plugins/aifab/SKILLS.md
```

### 별도 커밋 (1)

```
WORKFLOW.md                                ← 통합 흐름 반영
```

### 신규 테스트 (1)

```
scripts/tests/test_progress.py             ← progress.py 단위 테스트
```

---

## 제외 항목

- 백로그 관리 (BACKLOG.md, `/aifab:backlog`) — Option C 영역
- 요구사항 추적 (REQUIREMENTS.md, REQ-ID) — Option C 영역
- Phase 자동 자동화 hooks — 단순함 우선
- ROADMAP.md를 PLAN.md 안에 통합 — Q1에서 거부됨

---

## 성공 기준

- [ ] ROADMAP.md 있는 프로젝트에서 `/aifab:progress` 출력이 Phase·Wave 진척률을 정확히 표시
- [ ] ROADMAP.md 부재 시 기존 `/aifab:plan` `/aifab:execute` 동작 변경 없음 (역호환)
- [ ] 상태바가 ROADMAP 있을 때 `P*/* W*/*` 형식으로 표시
- [ ] `/aifab:milestone complete`가 git tag를 생성
- [ ] 새 스킬 3개가 `gen_skills_index.py --check` 통과
- [ ] `scripts/tests/test_progress.py` 100% 통과
- [ ] CI 전체 green 유지
