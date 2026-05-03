---
name: aifab:codex-review
description: Cross-AI verification via OpenAI Codex CLI
argument-hint: [wave <N>|file <path>|diff <ref>]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:codex-review` — 교차 AI 검증 (OpenAI Codex)

**담당 모델:** Advisor (claude-opus-4-7) — 검토 요청 작성 및 결과 종합
**외부 도구:** OpenAI Codex CLI (`codex`) — 독립적 코드 분석

---

## 목적

Claude(Advisor)가 작성/수정한 코드를 **다른 AI 모델(OpenAI)** 에게 독립적으로 검토받는다. 같은 모델 계열의 맹점을 다른 모델로 교차 검증하여 품질을 한 단계 높인다.

> "Two pairs of (different) eyes are better than one."

---

## 사용 시점

- Wave 완료 후, `git commit` 직전 (선택적 게이트)
- `/aifab:security` 통과 후 추가 검증으로
- 중요한 비즈니스 로직 변경 시
- UAT 직전 최종 검토

---

## 사전 요구사항

OpenAI Codex CLI가 설치되어 있어야 한다:

```bash
# 설치 (한 번만)
npm install -g @openai/codex
# 또는: brew install codex

# 인증
codex login
# 또는 OPENAI_API_KEY 환경변수 설정
```

설치 확인:
```bash
codex --version
```

미설치 시 스킬은 다음 안내:
```
❌ OpenAI Codex CLI가 설치되어 있지 않습니다.
설치: npm install -g @openai/codex
인증: codex login
```

---

## 사용 방법

```
/aifab:codex-review                       # 마지막 commit 변경사항 검토
/aifab:codex-review wave <N>              # 특정 Wave의 변경사항 검토
/aifab:codex-review file <path>           # 특정 파일 검토
/aifab:codex-review diff <ref>            # 특정 git ref 대비 diff 검토
```

---

## 프로세스

### Step 1: 검토 대상 식별

1. 모드별 대상 결정:
   - 기본: `git diff HEAD~1 HEAD`
   - `wave N`: 해당 Wave 커밋들의 누적 diff
   - `file <path>`: 단일 파일 전체
   - `diff <ref>`: `git diff <ref>..HEAD`
2. 변경사항 크기 추정:
   - 1000줄 초과 시 청크 분할 (Codex 컨텍스트 한도 고려)
   - 청크당 한 파일 또는 논리적 그룹 단위

### Step 2: 검토 컨텍스트 준비

Advisor가 Codex에 전달할 프롬프트 작성:

```markdown
# Code Review Request — Independent Verification

## Project Context
- Architecture: <ARCHITECTURE.md 요약 1-2줄>
- Current Wave goal: <PLAN.md에서 현재 Wave 목표>
- Tech stack: <주요 기술>

## Karpathy 4 Principles (Required Adherence)
1. Think Before Coding — assumptions explicit, no guesses
2. Simplicity First — minimum code, no speculative abstractions
3. Surgical Changes — only task-related modifications
4. Goal-Driven Execution — defined success criteria

## Code Under Review
```diff
<git diff 출력>
```

## Review Tasks (provide explicit verdict on each)

1. **Correctness**: Does the code do what it claims to do?
2. **Karpathy Compliance**: Any violations of the 4 principles? Specifically:
   - Speculative code beyond task scope?
   - Unnecessary abstractions?
   - Changes unrelated to the stated goal?
3. **Security**: Any new vulnerabilities introduced?
   - Input validation
   - Authentication/authorization
   - Secret exposure
4. **Edge Cases**: What edge cases are unhandled?
5. **Test Coverage**: Are critical paths tested? Any test that should exist but doesn't?
6. **Performance**: Any obvious inefficiencies (N+1, unbounded loops, etc.)?
7. **Maintainability**: Will this code be hard to change in 6 months?

## Output Format
Respond in this exact structure:

### Verdict
APPROVE / APPROVE_WITH_NITS / REQUEST_CHANGES / REJECT

### Critical Issues (must fix before merge)
- [Issue]: <description> at <file>:<line>

### Important Suggestions (should fix)
- [Suggestion]: ...

### Nits (optional polish)
- [Nit]: ...

### What's Good
- <positives observed>
```

### Step 3: Codex 호출

```bash
# Codex CLI 호출 (non-interactive 모드)
codex exec --skip-confirm "$(cat /tmp/aifab-codex-prompt.md)"
```

또는 stdin 파이프:
```bash
cat /tmp/aifab-codex-prompt.md | codex exec --skip-confirm
```

응답을 `/tmp/aifab-codex-response.md`에 저장.

### Step 4: 응답 파싱 및 종합

Advisor가 Codex 응답을 분석:

1. **Verdict 추출**: APPROVE / APPROVE_WITH_NITS / REQUEST_CHANGES / REJECT
2. **이슈 분류**:
   - Critical: 머지 차단 사유
   - Important: 권고
   - Nits: 선택적
3. **Advisor의 메타 검토**: Codex가 지적한 이슈가 실제로 유효한지 평가
   - Codex의 false positive 가능성도 검토
   - Karpathy 원칙에 따라 "Codex 지적이지만 단순성 우선으로 무시"가 가능한 경우 명시

### Step 5: 결과 보고

`docs/codex-reviews/YYYY-MM-DD-wave-<N>.md` 형식으로 저장:

```markdown
# Codex Cross-Review Report
일자: YYYY-MM-DD | 검토 범위: Wave <N> (commit <hash>)
Codex Verdict: APPROVE_WITH_NITS

## Codex 의견 요약
<Codex의 verdict 및 핵심 코멘트>

## Advisor 메타 검토
- 동의: <Codex 지적 중 합당한 것>
- 보류: <Codex 지적이지만 Karpathy 원칙으로 의도적 거부>
- 추가: <Codex가 놓친 이슈를 Advisor가 찾은 경우>

## 조치 항목
- [ ] [Critical] <이슈> — 즉시 수정
- [ ] [Important] <이슈> — 다음 Wave 전 수정
- [Nit] <이슈> — 선택

## 적용 여부
<수정 적용 후 commit hash>
```

WORKLOG.md에 검토 결과 한 줄 기록.

### Step 6: 후속 조치

- **APPROVE**: 다음 단계로 진행
- **APPROVE_WITH_NITS**: nit만 있는 경우 사용자에게 적용 여부 확인
- **REQUEST_CHANGES**: Critical/Important 이슈 수정 → 재검토 (`/aifab:codex-review` 재실행)
- **REJECT**: 작업 재설계 필요. `/aifab:plan`으로 회귀

---

## 비용 관리

Codex 호출은 OpenAI API 비용 발생. 절약 전략:

1. **선택적 사용**: 모든 commit이 아닌 Wave 단위로 호출
2. **diff만 전달**: 전체 파일 대신 변경된 부분만
3. **모델 선택**: `codex --model gpt-5-mini` 같은 옵션으로 가벼운 모델 사용
4. **AIFAB_CODEX_AUTO 환경변수**:
   - `auto`: 모든 Wave 자동 실행
   - `wave`: Wave 완료 시 묻기 (기본값)
   - `manual`: 사용자가 명시적으로 호출 시만
   - `off`: 비활성화

---

## 충돌 시 우선순위

Codex와 Advisor 의견이 충돌할 때:

| 영역 | 우선 |
|------|------|
| 보안 (Codex가 취약점 지적) | **Codex** — 안전 우선 |
| Karpathy 원칙 (Codex가 추상화 추가 권고) | **Advisor** — Karpathy 우선 |
| 스타일/네이밍 | **Advisor** — 프로젝트 일관성 |
| 알고리즘 정확성 | 추가 검증 (둘 다 의심 시 Phase 분석) |

---

## 통합

- `/aifab:execute` 완료 후 자동 호출 옵션 (settings.json에서 활성화)
- `/aifab:security` 통과 후 추가 게이트로 사용
- `/aifab:plan` 단계에서 호출하여 플랜 자체를 검토받기 (실험적)
- UAT 직전 최종 검증으로 사용

---

## 미설치 환경 fallback

Codex CLI 사용 불가 시:
1. 동일한 프롬프트를 사용자에게 출력
2. 사용자가 ChatGPT/Codex Web/다른 AI에 복사하여 검토
3. 결과를 `/tmp/aifab-codex-response.md`에 붙여넣기
4. Advisor가 그 응답을 파싱

이렇게 하여 CLI 없이도 교차 검증 가능.

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
