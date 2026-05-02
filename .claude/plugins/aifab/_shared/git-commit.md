# Shared: Git Commit Convention

AI-Fab 프로젝트의 git 커밋 컨벤션. 모든 스킬이 자동/수동 커밋 시 따른다.

## 형식

```
<type>(<scope>): <subject>

<body — optional>

<footer — optional>
```

- type, scope, subject는 영문 (검색/필터 용이)
- body는 한글 가능 (상세 설명, 결정 이유)
- subject 50자 이하, body 줄당 72자 이하

## Type

| Type | 사용 |
|------|------|
| `feat` | 새 기능 추가 |
| `fix` | 버그 수정 |
| `refactor` | 동작 변경 없는 구조 개선 |
| `perf` | 성능 개선 |
| `docs` | 문서만 변경 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드/설정/의존성 |
| `style` | 포맷팅 (코드 동작 변경 없음) |
| `migrate` | 마이그레이션 (`/aifab:migrate` 결과) |
| `security` | 보안 수정 (`/aifab:security` 자동 수정) |
| `revert` | 이전 커밋 되돌리기 (`/aifab:rollback`) |

## Scope (선택)

프로젝트 모듈명 또는 영역. 자주 쓰이는 예:
- `auth`, `api`, `db`, `ui`, `crawler`, `dashboard`
- 스킬 결과: `wave-N` (예: `feat(wave-3): add auth flow`)

## 스킬별 자동 커밋 메시지

### `/aifab:execute` Wave 완료
```
feat(wave-<N>): <wave title from PLAN.md>

- 추가된 파일: <count>
- 변경된 파일: <count>
- 통과 테스트: <count>

WORKLOG: Wave <N> 완료
```

### `/aifab:security` 자동 수정
```
security: fix <issue type> in <file>

- <변경 내용 한 줄>
- OWASP/AI-LLM/API/Secret 중 어느 영역
- 영향: <범위>
```

### `/aifab:debug` Root Cause 수정
```
fix(<scope>): <root cause 한 줄>

증상: <observed symptom>
원인: <verified root cause>
재발 방지: <test added | guard added | etc>

DEBUG-SESSION: <session file path>
```

### `/aifab:refactor` Wave 완료
```
refactor(<scope>): <what changed>

- 동작 변경 없음 (테스트 N/N 통과 유지)
- 개선: <readability | performance | structure>
```

### `/aifab:migrate` 단계 완료
```
migrate(<from>->: <to>): step <N>/<M> — <module>

- <적용된 변경 패턴>
- 회귀 테스트 N/N 통과
```

### `/aifab:rollback`
```
revert: rollback to Wave <N> (<original commit>)

원본 커밋: <hash>
사유: <UAT 실패 | 회귀 발견 | 결정 변경>
영향 받는 Wave: <N+1 ~ M>
```

### `/aifab:adr` 결정 기록
```
docs(adr): ADR-<NNNN> — <decision title>

Status: Proposed | Accepted | Superseded
관련 Wave: <N>
```

## 자동 vs 수동

자동 커밋 (사용자 확인 없음):
- 보안 critical 이슈 자동 수정
- Wave 완료 후 (테스트 통과 + security 통과 시)
- ADR 신규 기록

수동 확인 후 커밋:
- 큰 파일 변경 (>500 LOC)
- 의존성 추가/제거
- 마이그레이션 (실수 시 영향 큼)
- 메인 브랜치 머지

## 금지 사항

- ❌ `--no-verify` (pre-commit hook 우회)
- ❌ `--amend` (이미 push된 커밋)
- ❌ `git push --force` (메인 브랜치 대상)
- ❌ 시크릿(.env, key, password) 포함된 변경
- ❌ subject 끝에 마침표
- ❌ "WIP", "fix stuff", "asdf" 같은 무의미한 메시지

## 검증

커밋 전 자동 체크:
```bash
# .env, *.key, *.pem 패턴 차단
git diff --cached --name-only | grep -E '\.(env|key|pem)$' && {
  echo "❌ 시크릿 파일 staged. 제거 후 다시 시도하세요."
  exit 1
}

# subject 길이
msg=$(git log -1 --pretty=%s)
[[ ${#msg} -gt 50 ]] && echo "⚠ Subject가 50자를 초과합니다."
```

## Co-author 처리

스킬에 의한 자동 변경에는 다음 trailer 추가 (선택):
```
Generated-by: AI-Fab /aifab:<skill> 
```

이를 통해 추후 어떤 스킬이 어떤 커밋을 만들었는지 추적 가능.
