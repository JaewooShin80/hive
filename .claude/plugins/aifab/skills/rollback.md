---
name: aifab:rollback
description: Safe Wave-level rollback with backup
argument-hint: wave <N>|commit <hash>|last|dry-run
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:rollback` — 안전 롤백 (Wave 또는 Commit)

**담당 모델:** Advisor (Opus) — 영향 분석 + Sonnet — 적용
**선행:** WORKLOG.md, PLAN.md 기반
**연계:** /aifab:debug (롤백 후 원인 분석), /aifab:plan (재계획)

---

## 핵심 원칙

롤백은 되돌릴 수 없는 작업이다. **분석 → 확인 → 백업 → 적용** 순서를 반드시 지킨다. 백업 없이 실행하지 않으며, 사용자 확인 없이 force-push하지 않는다.

> "롤백 자체가 실패하면 더 큰 재앙이다. 먼저 저장하고, 그 다음 되돌린다."

---

## 사용 시나리오

- **UAT 실패:** 이전 Wave가 안정적이었으므로 해당 Wave 직전으로 복귀
- **회귀 발견:** 특정 commit 이후 기능이 깨진 경우 원상 복구
- **잘못된 결정:** 설계 오류 발견 후 분기 변경 필요
- **보안 사고 응급 대응:** 취약점이 포함된 커밋을 즉시 제거

---

## 명령어

```
/aifab:rollback wave <N>        — Wave N 직전 상태로 복구
/aifab:rollback commit <hash>   — 특정 commit 시점으로 복구
/aifab:rollback last            — 마지막 완료 Wave 취소
/aifab:rollback dry-run         — 실제 적용 없이 영향 분석만 출력
```

---

## 9단계 프로세스

### Step 1: 롤백 대상 식별

1. 명령어에서 대상 추출:
   - `wave <N>` → WORKLOG.md에서 Wave N 시작 commit hash 탐색
   - `commit <hash>` → 해당 hash를 직접 대상으로 사용
   - `last` → WORKLOG.md에서 가장 최근 `[x]` Wave의 시작 commit 탐색
2. WORKLOG.md와 `git log --oneline` 결과를 교차 확인하여 정확한 hash를 확정한다.
3. 대상 확정 메시지 출력:
   > "롤백 대상: Wave N — <제목> (commit: <hash>)"

---

### Step 2: 영향 분석

Advisor가 다음 항목을 분석한다:

1. **사라지는 변경사항 목록**
   - `git log <hash>..HEAD --oneline` 으로 되돌아갈 commit 나열
   - 각 commit의 파일 변경 요약
2. **영향 받는 후속 Wave**
   - 이미 완료된 Wave N+1, N+2 등이 있다면 명시
   - 예: "Wave 5, 6, 7이 영향 받습니다 (총 <n>개 커밋)"
3. **보존해야 할 commit 식별**
   - 커밋 메시지에서 `security`, `hotfix`, `CVE`, `fix:` 패턴 탐색
   - 보안 수정이나 긴급 패치는 cherry-pick 보존 대상으로 표시

---

### Step 3: 사용자 확인

영향 분석 결과를 요약 출력 후 진행 여부를 묻는다.

```
[롤백 영향 분석]
- 되돌릴 커밋 수: <n>개
- 영향 받는 Wave: Wave <X>, Wave <Y>
- 보존 권장 commit: <hash> (hotfix: ...)
- 롤백 전략: revert (히스토리 보존) / reset (히스토리 제거)

Wave 5~7이 영향 받습니다. 진행하시겠습니까? (y/n)
```

`dry-run` 모드일 경우 여기서 종료. 실제 적용 없이 분석 결과만 출력한다.

사용자가 `n`으로 거부하면 즉시 중단하고 `/aifab:plan` 재계획을 제안한다.

---

### Step 4: 안전 백업

롤백 적용 전 반드시 현재 상태를 보존한다.

```bash
# 현재 HEAD를 백업 브랜치로 저장
git branch backup/pre-rollback-$(date +%Y%m%d-%H%M)

# WORKLOG.md 스냅샷
cp WORKLOG.md WORKLOG.md.backup
```

백업 브랜치 이름을 사용자에게 안내한다:
> "백업 완료: `backup/pre-rollback-20260501-1430`"

---

### Step 5: 롤백 전략 선택

상황에 따라 전략을 선택한다:

| 전략 | 사용 시점 | 명령어 | 위험도 |
|------|-----------|--------|--------|
| **revert** (권장) | 원격에 이미 push된 경우 | `git revert <range>` | 낮음 — 히스토리 보존 |
| **reset** | 원격 미반영, 로컬 전용 | `git reset --hard <hash>` | 높음 — 히스토리 삭제 |
| **cherry-pick 보존** | 중요 commit만 선별 유지 | `git cherry-pick <hash>` | 낮음 |

기본값은 **revert**. 원격 미반영이 확인된 경우에만 reset을 사용자에게 제안한다.

보안 수정 commit은 무조건 제거하지 않고 cherry-pick 보존 여부를 사용자에게 확인한다.

---

### Step 6: 롤백 적용

Sonnet 서브에이전트가 선택된 전략으로 적용한다.

- **revert:** `git revert <oldest_hash>^..<HEAD> --no-edit`
- **reset:** `git reset --hard <target_hash>`
- **cherry-pick 보존:** reset 후 `git cherry-pick <security_hash>`

적용 중 충돌 발생 시 즉시 중단하고 사용자에게 충돌 파일을 안내한다. 자동 해결을 시도하지 않는다.

---

### Step 7: 복원 후 테스트 실행

롤백이 완료된 상태에서 기존 테스트를 실행하여 정상 작동을 확인한다.

1. 프로젝트의 테스트 명령어 실행 (PLAN.md 또는 package.json 참조)
2. 테스트 통과 시 Step 8로 진행
3. 테스트 실패 시:
   > "롤백 후 테스트 실패. 백업 브랜치(`backup/pre-rollback-...`)로 복구하거나 `/aifab:debug`로 원인을 분석하세요."
   - 자동으로 추가 수정을 시도하지 않는다.

---

### Step 8: WORKLOG.md 갱신

```markdown
## 주요 결정사항
- [ROLLBACK] YYYY-MM-DD HH:MM — Wave <N>으로 롤백
  - 사유: <사용자가 제공한 사유>
  - 영향 받은 Wave: <목록>
  - 백업 브랜치: backup/pre-rollback-<timestamp>
  - 보존된 commit: <hash> (<사유>)
```

롤백된 Wave의 상태를 `[x]` → `[ ]`로 되돌린다.

---

### Step 9: 다음 단계 제안

사용자에게 명확한 선택지를 제시한다:

```
[롤백 완료]
백업: backup/pre-rollback-20260501-1430

다음 단계를 선택하세요:
1. 동일 Wave 수정 후 재시도   → /aifab:execute
2. 다른 접근법으로 재계획     → /aifab:plan
3. 원인 분석 먼저             → /aifab:debug
```

---

## 금지 사항 (Safety Rules)

- ❌ 사용자 확인 없는 force-push — 항상 확인 후 실행
- ❌ 메인 브랜치(main / master) 직접 reset — revert만 허용
- ❌ 백업 없는 롤백 — Step 4는 절대 생략 불가
- ❌ 보안 수정 commit 무조건 제거 — 반드시 cherry-pick 보존 검토
- ❌ 충돌 자동 해결 — 사용자에게 알리고 대기

---

## 산출물

| 파일 | 내용 |
|------|------|
| `ROLLBACK-LOG.md` | 롤백 시점, 사유, 영향 받은 commit 목록, 백업 브랜치명 |
| `WORKLOG.md` | 롤백된 Wave 상태 복원 + 결정사항 기록 |
| `WORKLOG.md.backup` | 롤백 직전 WORKLOG 스냅샷 |
| `backup/pre-rollback-<timestamp>` | 현재 HEAD 보존 브랜치 |

---

## ROLLBACK-LOG.md 형식

```markdown
# Rollback Log

## 롤백 #<N>
- 일시: YYYY-MM-DD HH:MM
- 대상: Wave <N> / commit <hash>
- 사유: <사용자 제공>
- 전략: revert / reset
- 영향 받은 commit:
  - <hash> <메시지>
  - <hash> <메시지>
- 보존된 commit:
  - <hash> <메시지> (cherry-pick)
- 백업 브랜치: backup/pre-rollback-<timestamp>
- 테스트 결과: ✅ 통과 / ❌ 실패
```

---

<!-- AIFAB_V2_STANDARDS -->

## 표준 참조 (AIFAB v2)

이 스킬은 다음 공통 표준을 따른다. 상세 규칙은 각 문서 참조.

| 표준 | 문서 | 역할 |
|------|------|------|
| 사전조건 체크 | [`_shared/prerequisites.md`](../_shared/prerequisites.md) | 스킬 시작 시 git/ARCH/PLAN/WORKLOG/ctx 등 검증 |
| 출력 형식 | [`_shared/output-format.md`](../_shared/output-format.md) | Verdict(✅/⚠/❌) · Severity · 에러 코드 통일 |
| WORKLOG 갱신 | [`_shared/worklog-update.md`](../_shared/worklog-update.md) | 시작/종료/결정사항 기록 표준 절차 |
| 서브 에이전트 호출 | [`_shared/agent-dispatch.md`](../_shared/agent-dispatch.md) | Sonnet/Haiku 디스패치 프롬프트 템플릿 |
| Git 커밋 메시지 | [`_shared/git-commit.md`](../_shared/git-commit.md) | Conventional Commits + 스킬별 자동 메시지 |

스킬 인덱스: [`SKILLS.md`](../SKILLS.md)
