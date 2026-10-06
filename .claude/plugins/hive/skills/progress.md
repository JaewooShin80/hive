---
name: hive:progress
description: Display project progress dashboard — milestone, phase progression, wave completion percentages, current position, and next recommended command. Reads PLAN.md checkboxes (ROADMAP.md optional).
allowed-tools:
  - Bash
  - Read
---

# `/hive:progress` — 진척률 대시보드

**담당 모델:** 없음 — Python 헬퍼가 계산, 출력만 표시

---

## 역할

ROADMAP.md와 PLAN.md를 읽어 마일스톤 진행률, Phase별 진척, 현재 위치, 다음 추천 명령어를 한 번에 표시한다.

---

## 동작

1. `PLAN.md` 부재 시 안내 후 중단:
   > "PLAN.md 없음. `/hive:plan`으로 Wave 플랜을 먼저 만드세요."

   `ROADMAP.md`는 선택이다. 없으면 Phase 없이 Wave 진척과 기능 검증 수만 보여준다. 진척의 원천은 PLAN.md 각 Wave의 완료 기준 체크박스다.

2. 헬퍼 스크립트 실행:

```bash
python3 scripts/hive_progress.py
```

> Windows에서 `python3`가 없으면 `python` 또는 `py -3`로 실행한다.

3. 출력 결과를 그대로 사용자에게 표시.

4. 다음 추천 명령어 표시:
   - 현재 Phase에 미완료 Wave 있음 → `/hive:execute`
   - 현재 Phase 완료, 다음 Phase 있음 → `/hive:plan phase N`
   - 모든 Phase 완료 → `/hive:milestone audit`
   - ROADMAP 없이 모든 Wave 완료 → `/hive:playwright` → `/hive:uat`

---

## 출력 예시

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏷  마일스톤: v1.0.0  (시작 2026-05-08, 8일 경과)

📊 전체 진척: 5/12 Wave (42%)

Phase 1: 인증            ████████████  3/3   ✅
Phase 2: 데이터 모델      ██████░░░░░░  2/4   🟡 ← 현재
Phase 3: API 노출         ░░░░░░░░░░░░  0/5   ⬜

📍 현재 위치: Phase 2 (데이터 모델)
🎯 다음 명령어: /hive:execute
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 주의사항

- 이 스킬은 LLM 추론 없이 Python 헬퍼 실행 결과만 표시한다 (예측 불가능성 제거)
- 헬퍼가 종료 코드 2를 반환하면 ROADMAP/PLAN 부재 안내
