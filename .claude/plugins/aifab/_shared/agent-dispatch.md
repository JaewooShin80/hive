# Shared: Sub-Agent Dispatch Protocol

Advisor(Opus)가 Sonnet/Haiku 서브에이전트를 디스패치할 때 사용하는 표준 프롬프트 구조.

## 핵심 원칙

1. **Fresh context**: 매 호출마다 새 에이전트. 이전 대화 의존 금지.
2. **Self-contained prompt**: 에이전트가 외부 문서 검색 없이 작업 가능하도록 모든 컨텍스트 포함.
3. **Explicit success criteria**: WHAT을 정의, HOW는 위임.
4. **Status protocol**: 표준 응답 포맷 강제 (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED).

## 표준 프롬프트 템플릿

```markdown
# Task: <한 줄 요약>

## Project Context (이 작업이 어디에 속하는지)
- Project: <project name from WORKLOG>
- Architecture: <ARCHITECTURE.md 1-2줄 요약>
- Current Wave: Wave <N> — <wave title>
- This Task의 위치: Wave 내 <X>/<Y>번째

## Task Specification
<구체적으로 무엇을 해야 하는지>

## Inputs (필요한 모든 컨텍스트 포함)
- 관련 파일 내용:
  ```
  <file content embedded>
  ```
- 의존성:
  - <prior task가 만든 결과물 경로 + 주요 시그니처>

## Constraints
- 코딩 스타일: <project convention>
- 사용 가능 라이브러리: <list>
- 금지 사항: <e.g., 새 의존성 추가 금지>

## Karpathy Compliance (필수 준수)
- 추측 코드 금지 (요청된 것만)
- 새 추상화 금지 (단일 용도면 직접 작성)
- 작업 외 코드 수정 금지
- 가정이 필요하면 BLOCKED로 응답하고 명시

## TDD 요구사항 (해당 시)
- [ ] 실패하는 테스트 먼저 작성: <test file path>
- [ ] 테스트가 실제로 실패하는지 확인 (`pytest <path>::<test>`)
- [ ] 최소 구현으로 테스트 통과
- [ ] 리팩토링 (중복 제거 등)

## Success Criteria
- [ ] <측정 가능한 기준 1>
- [ ] <측정 가능한 기준 2>
- [ ] 모든 테스트 통과 (`<test command>`)
- [ ] 보안 기본 (시크릿 하드코딩 없음, 입력 검증)

## Expected Outputs
1. 변경/생성된 파일 목록
2. 테스트 결과 (pass/fail 수)
3. 자체 검토 결과 (Karpathy 4원칙 준수 여부)
4. 우려사항 (있을 시)

## Response Format (반드시 준수)

마지막에 다음 중 하나로 응답:

**DONE**
- 작업 완료. 모든 success criteria 충족.

**DONE_WITH_CONCERNS**
- 작업은 완료했으나 다음 우려가 있음:
  - <우려 1>
  - <우려 2>

**NEEDS_CONTEXT**
- 다음 정보가 부족하여 작업 불가:
  - <필요한 정보 1>

**BLOCKED**
- 다음 이유로 작업 불가:
  - <차단 사유>
  - 제안하는 해결 방향: <suggestion>
```

## 작업 유형별 변형

### Haiku (보일러플레이트) 디스패치
- 추가: "이 작업은 패턴 반복이므로 창의적 판단 불필요. 정확한 구조만 따르세요."
- 추가: "기존 파일 <path>를 참고 패턴으로 사용하세요." (있을 시)

### Sonnet (로직) 디스패치
- 추가: "TDD 사이클 강제. 테스트 없는 코드는 거부됨."
- 추가: "엣지 케이스 명시적 처리 (null, empty, 경계값)."

### Sonnet (리뷰) 디스패치
- 다른 에이전트가 작성한 코드를 검토할 때:
- "당신은 이 코드를 처음 봅니다. fresh eyes로 평가하세요."
- "spec 부합 / 코드 품질 두 단계로 평가하세요."

## 병렬 디스패치 (Agent 도구 다중 호출)

독립적인 task는 동일 메시지에서 여러 Agent 호출:

```
[Agent 1] Haiku → 모델 클래스 생성
[Agent 2] Haiku → API 라우터 스캐폴딩
[Agent 3] Sonnet → 비즈니스 로직 + 테스트
```

조건:
- task 간 의존성 없음
- 동일 파일 수정 안 함
- 결과를 Advisor가 통합 검토

## 응답 처리 매트릭스

| 응답 | Advisor 동작 |
|------|-------------|
| DONE | 다음 task 진행 또는 검토 단계로 |
| DONE_WITH_CONCERNS | 우려사항 평가 → 재작업 또는 다음 진행 |
| NEEDS_CONTEXT | 누락 정보 제공하고 동일 모델로 재디스패치 |
| BLOCKED | 차단 사유 분석. context 문제면 보강 후 재디스패치. 더 강한 모델 필요 시 Sonnet→Opus 승격. 작업 자체가 불가하면 PLAN.md 수정. |

## 비용 절약 가이드

- 보일러플레이트는 무조건 Haiku
- 단순 변환(json↔yaml, 형식 변경)은 Haiku
- 비즈니스 로직, 알고리즘, 통합은 Sonnet
- 아키텍처 결정, 코드 리뷰, 디버깅 가설은 Opus(Advisor)
- Opus를 일반 구현에 쓰지 말 것 (60배 비쌈)
