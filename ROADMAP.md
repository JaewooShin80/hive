# ROADMAP — AI-Fab Harness Hardening

> **마일스톤:** v2.2.0
> **시작일:** 2026-06-23
> **상태:** in_progress

## 개요

AI-Fab 하네스 자체를 고도화하는 자기-개선 마일스톤. 최신 하네스 트렌드 리서치(2025–2026) 결과 중 입증 강도 "강"인 패턴 두 개(**Hooks 결정론 가드**, **외재화 pass/fail + Trajectory evaluator**)를 적용한다.

**Dogfooding 원칙:** v2.2.0은 AI-Fab의 자체 스킬(plan/execute/security/playwright/worklog/progress)을 사용해 진행한다. 자기 하네스로 자기를 개선하는 검증 사이클.

**전제(보존):**
- 기존 GSD hooks 9종(`gsd-*`)은 그대로 유지. AI-Fab은 `aifab-*` 네임스페이스로 병행
- 글로벌 hooks(`~/.claude/hooks/`)는 모든 프로젝트 공통 안전장치, 프로젝트 hooks(`.claude/hooks/`)는 AI-Fab 워크플로우 강제
- 16개 기존 스킬 동작은 불변. 본 마일스톤은 외곽 인프라(hooks)와 데이터 레이어(feature-list.json) 추가가 핵심

---

## Phase 1: Hooks 정식화 (Wave 1-3) 🟡 in_progress

> CLAUDE.md의 prose 규칙(컨텍스트 50%, 시크릿 금지, TDD)을 결정론 hook으로 강제. Fowler의 "computational sensor" 레이어 도입.

**산출물:**
- 글로벌 보안/제어 hooks 3종
- 프로젝트 워크플로우 hooks 3종
- settings.json hooks 블록 갱신 (GSD 보존)
- `_shared/hooks.md` 신규 문서

**성공 기준:**
- 시크릿 포함 파일 Write가 hook으로 차단(exit 2)
- SessionStart 시 ROADMAP/현재 Wave 자동 표시
- 컨텍스트 50% 초과 시 Stop hook이 `/compact` 안내
- 5개 통합 시나리오 100% 통과

## Phase 2: Feature List + Evaluator (Wave 4-6) ⬜ pending

> 외재화 pass/fail 체크리스트(`feature-list.json`)와 Trajectory 검증기 도입. Anthropic 3-agent 패턴(Planner/Generator/**Evaluator**)을 AI-Fab의 plan/execute/playwright와 합성.

**산출물:**
- `feature-list.json` 스키마 + emit 로직 (`/aifab:plan`)
- 자동 pass/fail 갱신 (`/aifab:execute`)
- WORKLOG + feature-list 이중 read (`/aifab:worklog resume`)
- 신규 `/aifab:evaluate` 스킬 또는 `/aifab:playwright` 확장
- `aifab_progress.py`의 pass% 표시 추가

**성공 기준:**
- `/aifab:plan` 1회 실행 시 PLAN.md + feature-list.json 동시 생성
- Wave 종료 시 feature status 자동 전이(pending → passing/failing)
- evaluator가 mock 시나리오에서 pass→fail→pass 전이 감지
- progress 대시보드에 Wave 진척% + Feature pass% 동시 표시

---

## 진행 추적

- 현재 Wave: 0 (착수 직전)
- 다음 액션: Wave 1 — 글로벌 보안/제어 hooks
- 검증 도구: `/aifab:progress` (이 마일스톤이 자체 검증 케이스)
