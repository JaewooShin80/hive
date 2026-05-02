# Shared: Output Format Standards

모든 `/aifab:*` 스킬이 따르는 출력 형식 규칙.

## Verdict (판정 표준)

스킬이 사용자에게 결과를 보고할 때 명확한 verdict 사용:

| Verdict | 의미 | 후속 동작 |
|---------|------|----------|
| `✅ PASS` | 모든 기준 충족 | 다음 단계 진행 |
| `⚠ PASS_WITH_WARNINGS` | 통과했으나 권고사항 있음 | 사용자 확인 후 진행 |
| `❌ FAIL` | 차단 사유 발견 | 수정 후 재실행 |
| `🔄 RETRY` | 일시적 실패, 재시도 권장 | 자동 재시도 또는 사용자 확인 |
| `⏸ DEFERRED` | 작업 보류 (의존성 등) | WORKLOG에 기록 후 다음 |

## Status (상태 표준)

진행 중 상태 보고:

```
🔵 PENDING       — 대기 중
🟡 IN_PROGRESS   — 진행 중
🟢 COMPLETED     — 완료
🔴 BLOCKED       — 차단
⚫ SKIPPED       — 건너뜀
```

이모지 미지원 환경 fallback:
```
[ ] PENDING
[~] IN_PROGRESS
[x] COMPLETED
[!] BLOCKED
[-] SKIPPED
```

## Severity (심각도 표준)

이슈 보고 시 일관된 4단계:

| 표시 | 의미 | 처리 |
|------|------|------|
| `🔴 CRITICAL` | 즉시 차단 | 자동 수정 또는 즉시 stop |
| `🟠 HIGH` | 다음 단계 전 수정 필요 | 사용자 확인 후 수정 |
| `🟡 MEDIUM` | 권장 수정 | 다음 Wave 또는 별도 이슈 |
| `🔵 LOW` | 개선 의견 | 무시해도 무방 |

## 표준 보고 구조

스킬 종료 시 다음 구조로 요약:

```markdown
# /aifab:<skill> 실행 결과

## Verdict
<✅/⚠/❌> <한 줄 요약>

## 변경사항
- 추가: <count> 파일
- 수정: <count> 파일
- 삭제: <count> 파일

## 발견된 이슈
- 🔴 CRITICAL: <count>
- 🟠 HIGH: <count>
- 🟡 MEDIUM: <count>
- 🔵 LOW: <count>

## 다음 액션
1. <구체적 다음 명령>
2. <또는 다음 단계 안내>

## WORKLOG 갱신
- 현재 단계: <updated>
- 마지막 업데이트: <timestamp>
```

## 에러 메시지 형식

```
❌ <ERROR_CODE>: <한 줄 요약>

원인:
<상세 설명>

해결 방법:
1. <구체적 액션 1>
2. <구체적 액션 2>

참고:
- 관련 문서: <path or url>
- 관련 스킬: /aifab:<related-skill>
```

ERROR_CODE 네이밍:
- `MISSING_FILE`: 필수 파일 없음
- `INVALID_STATE`: 비정상 상태
- `UNMET_DEPENDENCY`: 의존성 미충족
- `CONTEXT_OVERFLOW`: Context 50% 초과
- `TOOL_NOT_FOUND`: 외부 도구 미설치
- `BRANCH_PROTECTED`: 보호된 브랜치 직접 작업
- `DIRTY_WORKTREE`: 미커밋 변경 존재
- `TEST_FAILED`: 테스트 실패
- `SECURITY_VIOLATION`: 보안 위반 발견

## 진행 표시

장기 작업 (>10초)은 진행 표시:

```
[3/10] Wave 3 실행 중... (Sonnet × 2 병렬)
  ✓ tests/test_auth.py (28 tests)
  ✓ app/auth/jwt.py (180 LOC)
  ⠋ app/middleware/auth.py (작성 중...)
```

## 한국어/영어 혼용 규칙

- **명령어/식별자**: 영어 (`/aifab:execute`, `Wave 3`, `OWASP`)
- **설명/내러티브**: 한국어 (사용자 친화)
- **에러 코드**: 영어 (검색 가능성)
- **변수명/함수명**: 코드 컨벤션 따름 (보통 영어)

## 표/리스트 표준

표는 작은 컬럼은 우측, 텍스트는 좌측 정렬:
```markdown
| 항목 | 카운트 | 비율 |
|------|------:|-----:|
| 추가 | 12 | 60% |
| 수정 | 8 | 40% |
```

리스트는 `-` 사용 (asterisk `*` 금지). 들여쓰기 2칸:
```markdown
- 항목 1
  - 하위 항목
- 항목 2
```

## 코드 블록 언어 명시

```markdown
\`\`\`python
def foo(): pass
\`\`\`

\`\`\`bash
ls -la
\`\`\`

\`\`\`json
{"key": "value"}
\`\`\`
```

언어 미상이면 `text`. 빈 코드 블록 금지.

## 침묵의 원칙

- 상태 변경 없이 끝나면 출력 최소화
- "작업을 완료했습니다" 같은 잡소리 금지
- Verdict + 다음 액션이면 충분
