---
name: aifab:milestone
description: Manage project milestones (semver tags). Subcommands new/complete/audit handle milestone lifecycle from start to git tag. Use new at project start, audit before declaring done, complete to tag.
argument-hint: [new <semver> | complete | audit]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# `/aifab:milestone` — 마일스톤 라이프사이클

**담당 모델:** Advisor (opus) — `complete`/`audit`는 판단 필요

---

## 역할

마일스톤(semver)을 생성·점검·완료한다. 완료 시 git tag를 생성하고 회고를 `MILESTONE-LOG.md`에 기록한다.

---

## 사용 방법

```
/aifab:milestone                # 현재 마일스톤 상태 표시
/aifab:milestone new <semver>   # 새 마일스톤 시작 (예: new v1.0.0)
/aifab:milestone audit          # 종료 직전 점검
/aifab:milestone complete       # 모든 Phase 완료 확인 → git tag → 회고
```

---

## new 동작

1. ROADMAP.md가 이미 있으면 안내 후 중단:
   > "현재 마일스톤이 진행 중입니다. 먼저 `/aifab:milestone complete`로 종료하세요."

2. 인자가 semver 형식인지 검증 (`vN.N.N`)

3. `/aifab:roadmap init <semver>` 호출 권장 메시지 출력:
   > "마일스톤 <semver> 시작 준비. 이제 `/aifab:roadmap init <semver>`로 ROADMAP.md를 생성하세요."

---

## audit 동작

ROADMAP.md를 읽어 다음 항목을 순서대로 점검:

1. **Phase 상태:** 모든 Phase가 `✅ complete`인가
2. **테스트:** 프로젝트에 테스트가 있다면 통과하는가
   ```bash
   # 자동 감지: package.json scripts.test, pytest, go test 등
   ```
3. **보안:** 마지막 Wave 후 `/aifab:security` 또는 `/security-audit` 실행 이력 확인
4. **UAT:** WORKLOG.md에 `/aifab:uat` 통과 기록 있는가
5. **문서:** README.md, CHANGELOG.md 갱신 여부

각 항목에 ✅/⚠️/❌ 표시하고 미완료 항목은 권장 액션 제시.

---

## complete 동작

1. `/aifab:milestone audit` 자동 실행. ❌ 항목 있으면 중단.

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
   > "마일스톤 <semver> 완료. 다음 마일스톤은 `/aifab:milestone new vX.Y.Z`로 시작하세요."

---

## 주의사항

- semver 강제: `vN.N.N` 형식. 다른 형식은 거부
- git tag는 항상 annotated tag (`-a`)로 생성하여 메시지 보존
- `audit`는 비파괴적 (절대 수정 안 함)
- `complete`는 git tag 생성 전 사용자 확인 필수
