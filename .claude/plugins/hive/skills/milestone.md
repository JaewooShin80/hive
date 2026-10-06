---
name: hive:milestone
description: Manage project milestones (semver tags). Subcommands new/complete/audit handle milestone lifecycle from start to git tag. Use new after /hive:discover (it also creates ROADMAP.md), audit before declaring done, complete to tag.
argument-hint: [new <semver> | complete | audit]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# `/hive:milestone` — 마일스톤 라이프사이클

**담당 모델:** Advisor (opus) — `complete`/`audit`는 판단 필요

---

## 역할

마일스톤(semver)을 생성·점검·완료한다. 완료 시 git tag를 생성하고 회고를 `MILESTONE-LOG.md`에 기록한다.

---

## 사용 방법

```
/hive:milestone                # 현재 마일스톤 상태 표시
/hive:milestone new <semver>   # 새 마일스톤 시작 (예: new v1.0.0)
/hive:milestone audit          # 종료 직전 점검
/hive:milestone complete       # 모든 Phase 완료 확인 → git tag → 회고
```

---

## new 동작

1. ROADMAP.md가 이미 있으면 안내 후 중단:
   > "현재 마일스톤이 진행 중입니다. 먼저 `/hive:milestone complete`로 종료하세요."

2. 인자가 semver 형식인지 검증 (`vN.N.N`)

3. 이어서 ROADMAP.md 를 바로 만든다 — `Skill` 도구로 `hive:roadmap`을 인자 `init <semver>`로 호출한다 (별도 명령을 다시 입력하게 하지 않는다).
   - 권장 순서: `/hive:spec` → `/hive:discover` → **`/hive:milestone new`** → `/hive:plan`. ARCHITECTURE.md(또는 최소한 REQUIREMENTS.md)가 있어야 Phase 를 나눌 수 있다.
   - 둘 다 없으면 "먼저 `/hive:spec`(요구사항) 또는 `/hive:discover`(아키텍처)를 실행하세요."를 출력하고 중단한다.

---

## audit 동작

ROADMAP.md를 읽어 다음 항목을 순서대로 점검:

1. **Phase 상태:** 모든 Phase가 `✅ complete`인가
2. **테스트:** 프로젝트에 테스트가 있다면 통과하는가
   ```bash
   # 자동 감지: package.json scripts.test, pytest, go test 등
   ```
3. **보안:** 마지막 Wave 후 `/hive:security` 또는 `/security-audit` 실행 이력 확인
4. **UAT:** WORKLOG.md에 `/hive:uat` 통과 기록 있는가
5. **문서:** README.md, CHANGELOG.md 갱신 여부

각 항목에 ✅/⚠️/❌ 표시하고 미완료 항목은 권장 액션 제시.

---

## complete 동작

1. `/hive:milestone audit` 자동 실행. ❌ 항목 있으면 중단.

2. 회고 인터뷰 (Advisor):
   - "이 마일스톤에서 가장 잘된 결정은?"
   - "다음에 다르게 했으면 좋았을 부분은?"
   - "다음 마일스톤에 가져갈 결정은?"

3. `MILESTONE-LOG.md` 작성 (없으면 생성, 있으면 추가):

```markdown
## <semver> — <YYYY-MM-DD>

**기간:** <시작> ~ <종료> (N일)
**Phase:** N개 완료
**Wave:** N개 완료

### 잘된 점
- ...

### 개선할 점
- ...

### 다음 마일스톤 인계
- ...
```

4. git tag 생성:

```bash
git tag -a <semver> -m "milestone: <semver>"
```

5. ROADMAP.md를 archive 처리:
   - `archive/ROADMAP-<semver>.md`로 이동
   - 또는 ROADMAP.md 상단에 `> **상태:** complete` 갱신

6. 다음 명령어 안내:
   > "마일스톤 <semver> 완료. 다음 마일스톤은 `/hive:milestone new vX.Y.Z`로 시작하세요."

---

## 주의사항

- semver 강제: `vN.N.N` 형식. 다른 형식은 거부
- git tag는 항상 annotated tag (`-a`)로 생성하여 메시지 보존
- `audit`는 비파괴적 (절대 수정 안 함)
- `complete`는 git tag 생성 전 사용자 확인 필수
