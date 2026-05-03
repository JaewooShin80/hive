---
name: aifab:debug
description: Systematic 4-stage RCA debugging
argument-hint: <symptom>|session|history
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:debug` — 체계적 디버깅 (4단계 RCA)

**담당 모델:** Advisor (claude-opus-4-7) — 가설 수립 및 분석
**서브에이전트:** Sonnet — 가설 검증, 코드 수정

---

## 핵심 원칙

추측으로 디버깅하지 않는다. **가설(Hypothesis) → 증거(Evidence) → 검증(Verification) → 수정(Fix)** 의 4단계를 반드시 따른다.

> "It's not a bug, it's a wrong assumption you haven't verified yet."

---

## 사용 방법

```
/aifab:debug <증상 설명>
/aifab:debug "로그인 후 /dashboard로 리다이렉트 안 됨"
/aifab:debug session              # 진행 중인 디버그 세션 재개
/aifab:debug history              # 과거 디버그 세션 목록
```

---

## 4단계 프로세스

### Phase 1: Reproduce & Isolate (재현 및 격리)

**목표:** 버그를 안정적으로 재현할 수 있는 최소 조건을 찾는다.

1. 사용자에게 질문:
   - 어떤 단계로 발생하는가?
   - 항상 발생하는가, 가끔 발생하는가?
   - 환경(브라우저, OS, 데이터셋)은?
   - 최근 변경사항은?
2. 재현 단계를 `DEBUG-SESSION.md`에 기록
3. 최소 재현 케이스(MRC) 작성:
   - 가능하면 실패하는 테스트로 변환 (TDD 활용)
   - `pytest tests/debug_<issue>.py::test_repro` 같은 명령으로 항상 재현 가능하게

**완료 기준:** "이 명령어를 실행하면 항상 실패한다"는 단일 명령어 보유

---

### Phase 2: Hypothesize (가설 수립)

**목표:** Advisor가 3~5개의 가능한 원인 가설을 작성한다.

1. 코드를 읽고 각 가설을 작성:
   ```markdown
   ## 가설 H1: 세션 쿠키가 SameSite=Strict로 설정되어 리다이렉트 시 누락
   - 증거 필요: 브라우저 DevTools에서 쿠키 속성 확인
   - 검증 방법: response.headers['Set-Cookie'] 확인
   - 가능성: 70%
   ```
2. **각 가설은 반드시 검증 가능해야 함** (검증 불가능한 가설은 제외)
3. 가능성 높은 순으로 정렬
4. `DEBUG-SESSION.md`의 "Hypotheses" 섹션에 기록

**금지 사항:**
- "그냥 코드를 다시 짜자"는 가설은 무효
- 검증 없이 첫 가설로 바로 수정 시도 금지

---

### Phase 3: Verify (증거 수집)

**목표:** 가능성 높은 가설부터 순서대로 검증한다. 각 가설은 명확히 참 or 거짓으로 판명되어야 한다.

각 가설에 대해 Sonnet 서브에이전트 활용:
1. 검증용 로그 추가, breakpoint 삽입, print 디버깅
2. 단위 테스트 작성하여 가설을 시험
3. 결과 기록:
   ```markdown
   ## H1 검증 결과: ❌ 거짓
   증거: 쿠키는 SameSite=Lax로 설정됨. 리다이렉트에 영향 없음.
   다음 가설로 이동.
   ```

**가설이 모두 거짓이라면:** Phase 2로 돌아가 새 가설 수립. 가설 수립 자체가 틀렸다는 뜻.

---

### Phase 4: Fix & Verify (수정 및 검증)

**목표:** 진짜 원인이 확인되면 최소 수정으로 해결한다.

1. **Karpathy 원칙 적용**: 수술적 변경 — 원인과 직접 관련된 코드만 수정
2. 수정 전 실패하던 MRC 테스트가 이제 통과하는지 확인
3. 다른 테스트가 깨지지 않았는지 전체 테스트 실행
4. 보안 영향 검토: 이 수정이 새로운 취약점을 만들지 않는지 확인 (필요 시 `/aifab:security` 실행)
5. `DEBUG-SESSION.md`에 최종 root cause와 수정 내용 기록
6. Git commit: `fix: <component> - <root cause 한 줄 설명>`
7. WORKLOG.md의 "주요 결정사항"에 디버깅 결과 기록

---

## DEBUG-SESSION.md 형식

```markdown
# Debug Session: <이슈 한 줄 설명>
시작: YYYY-MM-DD HH:MM | 상태: <진행중 / 해결 / 보류>

## 증상
<관찰된 현상>

## 재현 단계
1. <단계>
2. <단계>
**MRC 명령어:** `<재현 명령>`

## 영향 범위
- 영향받는 사용자/기능: <범위>
- 심각도: Critical / High / Medium / Low

## 가설 (가능성 순)

### H1: <가설 제목>
- 가능성: <%>
- 검증 방법: <어떻게 시험할 것인가>
- 결과: ⏳ 미검증 / ✅ 참 / ❌ 거짓
- 증거: <검증 후 채움>

### H2: ...

## Root Cause
<검증 완료 후 채움 — 진짜 원인>

## 수정 사항
- 파일: `<path>:<line>`
- 변경: <한 줄 요약>
- Commit: <hash>

## 회고
- 왜 이런 버그가 들어왔는가?
- 재발 방지 조치: <테스트 추가, 가드 추가 등>
```

---

## 세션 관리

`/aifab:debug session`: 진행 중인 `DEBUG-SESSION.md` 표시 → 마지막 단계부터 재개
`/aifab:debug history`: `docs/debug/` 디렉토리의 과거 세션 목록 표시

해결된 세션은 `docs/debug/YYYY-MM-DD-<issue>.md`로 아카이브.

---

## 금지 사항 (Anti-Patterns)

- ❌ 가설 검증 없이 코드 수정
- ❌ "일단 다시 실행해보자" — 비결정적 동작은 그 자체가 가설
- ❌ try/except로 에러 숨기기 (원인 파악 없는 catch)
- ❌ Stack Overflow 답변 그대로 복붙
- ❌ 한 번에 여러 변경 — 한 번에 한 가설씩 검증

---

## 통합

- `/aifab:execute` 도중 테스트 실패 시 자동으로 `/aifab:debug` 진입 권장
- `/aifab:playwright` E2E 실패 시 스크린샷을 증거로 `/aifab:debug` 활용
- `/aifab:uat` 실패 피드백을 디버그 세션의 증상으로 사용

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
