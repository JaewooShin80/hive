---
name: aifab:roadmap
description: Manage project roadmap (Phase-level grouping of Waves) and milestone metadata. Subcommands init/add-phase/update. Generates ROADMAP.md as the index above PLAN.md.
argument-hint: [init <semver> | add-phase <name> | update]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# `/aifab:roadmap` — Phase 인덱스 + 마일스톤 메타 관리

**담당 모델:** Advisor (claude-opus-4-7) — 도메인 분해 판단 필요

---

## 역할

ROADMAP.md를 생성·갱신하여 PLAN.md의 Wave를 Phase 단위로 그룹핑한다. 마일스톤(semver) 메타와 Phase별 진행 상태를 추적한다.

---

## 사용 방법

```
/aifab:roadmap                       # 현재 ROADMAP.md 표시 (없으면 안내)
/aifab:roadmap init <semver>         # ROADMAP.md 신규 생성 (예: init v1.0.0)
/aifab:roadmap add-phase <이름>      # Phase 추가
/aifab:roadmap update                # PLAN.md 읽어 Wave 상태 자동 동기화
```

---

## init 동작

1. `ROADMAP.md`가 이미 있으면 안내 후 중단:
   > "ROADMAP.md가 이미 존재합니다. 새 마일스톤은 `/aifab:milestone new` 사용하세요."

2. `ARCHITECTURE.md` 읽어 도메인 파악

3. 사용자 인터뷰로 Phase 분해 (3-5개 권장):
   - "이 마일스톤을 몇 개의 Phase로 나누시겠습니까?"
   - 각 Phase의 이름·목표·예상 Wave 범위 결정

4. ROADMAP.md 생성:

```markdown
# 프로젝트 로드맵

> **마일스톤:** <semver>
> **시작일:** <YYYY-MM-DD (오늘)>
> **상태:** in_progress

## Phase 1: <이름> (Wave 1-N) ⬜ pending

**목표:** <한 줄>

(Wave는 /aifab:plan으로 생성)

## Phase 2: ...
```

5. 다음 명령어 안내:
   > "ROADMAP.md 생성 완료. `/aifab:plan`으로 Phase 1의 Wave를 분해하세요."

---

## add-phase 동작

1. ROADMAP.md 부재 시 안내 후 중단
2. 마지막 Phase 다음에 새 Phase 섹션 추가
3. Wave 범위는 PLAN.md 기준으로 자동 산정 또는 사용자 입력

---

## update 동작

1. `PLAN.md` 읽어 각 Wave의 `[x]` / `[ ]` 상태 파싱
2. 각 Phase의 Wave 항목 체크박스 갱신
3. Phase 상태 자동 결정:
   - 모든 Wave `[x]` → `✅ complete`
   - 일부 `[x]` → `🟡 in_progress`
   - 모두 `[ ]` → `⬜ pending`
4. 갱신 결과 요약:
   > "Phase 1: complete, Phase 2: in_progress (2/4 Wave), Phase 3: pending"

---

## 주의사항

- ROADMAP.md는 사람이 직접 편집해도 무방하지만 `update` 시 형식이 깨지면 경고
- Phase 헤더 형식은 정규식 `## Phase N: <이름> (Wave a-b) <이모지>`로 엄격
- 마일스톤 이름은 semver 권장 (`v1.0.0`)이지만 강제하지 않음
