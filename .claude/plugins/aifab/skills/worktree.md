---
name: aifab:worktree
description: Parallel Wave via git worktrees
argument-hint: list|create|switch|merge|remove|status
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:worktree` — 병렬 Wave 워크트리 관리

**담당 모델:** Sonnet (구현) — 단순 git 작업
**연계 스킬:** `/aifab:execute` (병렬 실행 시), `/aifab:plan` (병렬 가능 Wave 식별)

---

## 목적

독립적으로 진행 가능한 Wave를 git worktree로 분리하여 **동시에 개발**한다. 메인 브랜치 오염 없이 여러 기능을 병렬 진행할 수 있다.

---

## 사용 방법

```
/aifab:worktree list                       # 현재 워크트리 목록
/aifab:worktree create <wave-id>           # 특정 Wave용 워크트리 생성
/aifab:worktree switch <wave-id>           # 해당 워크트리로 전환
/aifab:worktree remove <wave-id>           # 워크트리 제거
/aifab:worktree merge <wave-id>            # 워크트리 작업을 메인에 병합
/aifab:worktree status                     # 모든 워크트리의 진행 상황
```

---

## 디렉토리 구조

```
프로젝트 루트/
├── .worktrees/              ← .gitignore에 등록
│   ├── wave-3-auth/         ← Wave 3: 인증 기능
│   ├── wave-4-search/       ← Wave 4: 검색 기능
│   └── wave-5-billing/      ← Wave 5: 결제 기능
├── PLAN.md
└── ...
```

각 워크트리는 독립 브랜치 (`feature/wave-3-auth`)에서 작동한다.

---

## 프로세스

### `/aifab:worktree create <wave-id>`

1. PLAN.md에서 해당 Wave 정보 읽기
2. **의존성 확인**: 이 Wave가 의존하는 Wave가 모두 완료되었는지 검사
   - 미완료 의존성 있으면 거부: "Wave N 미완료. 먼저 진행하세요."
3. **충돌 가능성 검사**: 다른 워크트리와 동일 파일을 수정할 가능성이 있는지 검사
   - PLAN.md의 파일 영향 범위 비교
   - 충돌 가능 시 경고 후 사용자 확인
4. `.worktrees/wave-<id>-<slug>` 경로 결정
5. `.gitignore`에 `.worktrees/` 등록 확인 (없으면 추가)
6. `git worktree add .worktrees/wave-<id>-<slug> -b feature/wave-<id>-<slug>` 실행
7. 새 워크트리에서 의존성 설치 자동 실행:
   - `package.json` → `npm install`
   - `pyproject.toml` → `poetry install` 또는 `pip install -e .`
   - `requirements.txt` → `pip install -r requirements.txt`
8. 베이스라인 테스트 실행 → 통과 확인
9. WORKLOG.md에 워크트리 생성 기록

### `/aifab:worktree switch <wave-id>`

1. 해당 워크트리 경로로 사용자 안내:
   ```
   cd .worktrees/wave-3-auth
   ```
2. (Claude Code 컨텍스트에서) 작업 디렉토리 전환
3. 해당 워크트리의 WORKLOG.md 상태 표시

### `/aifab:worktree status`

모든 워크트리의 현재 상태 표시:
```
ID    Wave  브랜치                  상태       최근 커밋
3     auth  feature/wave-3-auth     in_progress  2시간 전
4     search feature/wave-4-search  ready_to_merge  10분 전
5     billing feature/wave-5-billing  blocked     1일 전
```

### `/aifab:worktree merge <wave-id>`

1. 해당 워크트리의 모든 테스트 통과 확인
2. `/aifab:security` 실행 → 통과 확인
3. 메인 브랜치(또는 통합 브랜치)로 전환
4. `git merge --no-ff feature/wave-<id>-<slug>` 실행
5. 충돌 발생 시:
   - Advisor가 충돌 분석
   - 의미 손실 없는 자동 해결 시도
   - 복잡한 충돌은 사용자에게 위임
6. 머지 성공 → WORKLOG.md 업데이트 → 워크트리 제거 권장

### `/aifab:worktree remove <wave-id>`

1. 해당 워크트리의 미커밋 변경사항 확인
2. 변경사항 있으면 거부: "스태시하거나 커밋 후 제거하세요."
3. `git worktree remove .worktrees/wave-<id>-<slug>` 실행
4. 브랜치도 제거할지 확인 (병합되지 않은 브랜치는 강제 삭제 거부)

---

## /aifab:plan과의 통합

`plan.md` 스킬은 PLAN.md 작성 시 각 Wave에 다음 메타데이터 추가:

```markdown
### Wave 3: 인증 시스템 [Medium]
**목표:** ...
**의존성:** Wave 1 (DB 모델)
**병렬 가능:** ✅ Wave 4(검색), Wave 5(결제)와 동시 진행 가능
**파일 영향 범위:** `app/auth/`, `app/middleware/auth.py`, `tests/auth/`
```

`/aifab:worktree create` 실행 시 이 정보를 활용한다.

---

## /aifab:execute와의 통합

병렬 진행 모드:
```
/aifab:execute --in-worktree wave-3   # 현재 워크트리에서 Wave 3 실행
/aifab:execute --parallel 3,4,5       # Wave 3,4,5를 각 워크트리에서 병렬 실행
```

`--parallel` 옵션은 다음을 자동 수행:
1. 각 Wave별 워크트리 생성 (없으면)
2. 각 워크트리에서 `/aifab:execute <wave-id>` 동시 실행
3. 모든 Wave 완료까지 대기
4. 각 워크트리의 결과 보고

---

## 주의 사항 및 제약

- **단일 빌드 산출물 충돌**: 일부 프로젝트는 빌드 결과물을 공유 디렉토리에 저장. 워크트리별 분리 필요.
- **DB 마이그레이션**: 동시에 진행되는 Wave가 같은 테이블을 변경하면 충돌. PLAN.md의 영향 범위로 사전 차단.
- **포트 충돌**: 각 워크트리가 dev 서버를 띄우면 포트 충돌. `WORKTREE_PORT` 환경변수로 분리.
- **`.env` 파일**: 워크트리는 부모 디렉토리의 `.env`를 자동 상속하지 않음. 필요 시 심볼릭 링크.

---

## 안전 장치

1. **메인 브랜치 보호**: 메인/마스터에서는 직접 작업 금지. 항상 워크트리 사용 권장.
2. **고아 워크트리 청소**: `/aifab:worktree clean` — 메인에 머지된 워크트리 자동 제거.
3. **상태바 통합**: 활성 워크트리 수가 CLI 상태바에 표시 (예: `📊 Wave 3/8 [+2 worktrees]`).
4. **동시 실행 한도**: 기본 3개 워크트리 동시 실행. `AIFAB_MAX_WORKTREES` 환경변수로 조정.

---

## 통합

- `/aifab:plan`: 병렬 가능 Wave 식별 및 메타데이터 작성
- `/aifab:execute --parallel`: 다중 워크트리 동시 실행
- `/aifab:worklog`: 워크트리별 WORKLOG.md 분리 관리
- `/aifab:security`: 머지 전 자동 보안 검토

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
