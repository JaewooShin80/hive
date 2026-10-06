---
name: hive:roadmap
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

# `/hive:roadmap` — Phase 인덱스 + 마일스톤 메타 관리

**담당 모델:** Advisor (opus) — 도메인 분해 판단 필요

---

## 역할

ROADMAP.md를 생성·갱신하여 PLAN.md의 Wave를 Phase 단위로 그룹핑한다. 마일스톤(semver) 메타와 Phase별 진행 상태를 추적한다.

---

## 사용 방법

```
/hive:roadmap                       # 현재 ROADMAP.md 표시 (없으면 안내)
/hive:roadmap init <semver>         # ROADMAP.md 신규 생성 (예: init v1.0.0)
/hive:roadmap add-phase <이름>      # Phase 추가
/hive:roadmap update                # PLAN.md 읽어 Wave 상태 자동 동기화
```

---

## init 동작

1. `ROADMAP.md`가 이미 있으면 안내 후 중단:
   > "ROADMAP.md가 이미 존재합니다. 새 마일스톤은 `/hive:milestone new` 사용하세요."

2. 도메인 파악: `ARCHITECTURE.md`를 읽는다. 없으면 `REQUIREMENTS.md`를 읽는다. 둘 다 없으면 "먼저 `/hive:spec` 또는 `/hive:discover`를 실행하세요."를 출력하고 중단한다 (권장 순서: spec → discover → milestone/roadmap → plan).

3. Phase 분해 (2-5개 권장) — 질문은 [`_shared/auto-mode.md`](../_shared/auto-mode.md) 규칙으로 묶어서 한 번에 확인받는다 (`--auto`면 추천 분해를 채택):
   - 각 Phase 의 이름·목표를 정한다. Phase 경계는 선택된 아키텍처의 배포 단위를 따른다 (예: SSR 앱을 "API Phase / UI Phase"로 나누지 않는다).
   - Wave 범위는 **추정치**로 적는다. `/hive:plan`이 해당 Phase 를 분해할 때 실제 Wave 번호로 고치고 뒤 Phase 범위를 밀어낸다.

4. ROADMAP.md 생성:

```markdown
# 프로젝트 로드맵

> **마일스톤:** <semver>
> **시작일:** <YYYY-MM-DD (오늘)>
> **상태:** in_progress

## Phase 1: <이름> (Wave 1-N) ⬜ pending

**목표:** <한 줄>

(Wave는 /hive:plan으로 생성)

## Phase 2: ...
```

5. 다음 명령어 안내:
   > "ROADMAP.md 생성 완료. `/hive:plan`으로 Phase 1의 Wave를 분해하세요."

---

## add-phase 동작

1. ROADMAP.md 부재 시 안내 후 중단
2. 마지막 Phase 다음에 새 Phase 섹션 추가
3. Wave 범위는 PLAN.md 기준으로 자동 산정 또는 사용자 입력

---

## update 동작

1. `PLAN.md`의 각 Wave 블록(`## Wave N:` 또는 `### Wave N:`)에서 **완료 기준 체크박스**를 센다. Wave는 체크박스가 1개 이상이고 `[ ]`가 하나도 없을 때 완료다 (`python3 scripts/hive_progress.py --json`과 같은 기준 — `/hive:execute` 6-2가 이 체크박스를 갱신한다).
2. 각 Phase의 Wave 범위 안에서 완료 Wave 수를 집계한다.
3. Phase 상태 자동 결정:
   - 범위의 모든 Wave 완료 → `✅ complete`
   - 일부 Wave 완료 또는 진행 중 → `🟡 in_progress`
   - 모두 `[ ]` → `⬜ pending`
4. 갱신 결과 요약:
   > "Phase 1: complete, Phase 2: in_progress (2/4 Wave), Phase 3: pending"

---

## 주의사항

- ROADMAP.md는 사람이 직접 편집해도 무방하지만 `update` 시 형식이 깨지면 경고
- Phase 헤더 형식은 정규식 `## Phase N: <이름> (Wave a-b) <이모지>`로 엄격
- 마일스톤 이름은 semver 권장 (`v1.0.0`)이지만 강제하지 않음
