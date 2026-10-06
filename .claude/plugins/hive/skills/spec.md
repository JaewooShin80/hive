---
name: hive:spec
description: Use at the very start of a project or feature, before /hive:discover, to turn the user's description into confirmed requirements — users, feature list (Must/Should/Won't), core user flows, screens with text wireframes, and UI conditions. Writes REQUIREMENTS.md. Triggers on /hive:spec.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Bash
  - Skill
  - AskUserQuestion
argument-hint: "[설명 | 요구문서 경로] [--auto]"
---

# `/hive:spec` — 요구사항 · UX/UI 확인

**담당 모델:** Advisor (opus)

---

## 역할

아키텍처를 고르기 전에 "무엇을, 누구를 위해, 어떤 화면으로" 만들지 사용자와 확정한다.
결과는 `REQUIREMENTS.md`이며, `/hive:discover`와 `/hive:plan`의 입력이 된다.

이 스킬은 기술 스택·아키텍처·구현을 다루지 않는다. 그것은 `/hive:discover` 몫이다.

---

## 0단계: 사전 준비

- 질문 방식과 `--auto` 규칙: [`_shared/auto-mode.md`](../_shared/auto-mode.md)
- 현재 폴더가 git 저장소가 아니면 `git init`을 제안한다 (`--auto`면 바로 실행). 이후 모든 단계가 git 을 전제로 한다.

## 1단계: 설명 듣기

`REQUIREMENTS.md`가 이미 있으면 읽고 "기존 요구사항을 수정할까요, 새로 작성할까요?"를 묻는다 (`--auto`: 수정).

입력을 다음 순서로 정한다:
1. **인자에 설명이 있으면** 그것을 설명으로 쓰고 바로 2단계로 간다.
2. **인자나 답에 문서 경로가 있으면** [`_shared/document-input.md`](../_shared/document-input.md)에 따라 읽는다 (docx/xlsx/pptx/hwp 는 `Read`로 못 읽는다). 문서의 기능·비기능 요구를 Must/Should/Won't 로 옮기고, 원문 ID(REQ-01 …)는 기능 목록 `원본` 열에 남긴다. 문서에 이미 답이 있는 2단계 질문은 건너뛴다.
3. 둘 다 없으면 다음을 출력하고 답을 기다린다:
   > "만들고 싶은 것을 자유롭게 설명해 주세요. (요구사항 문서가 있으면 경로를 알려주세요)"

---

### 변경 요구 모드 (기존 코드가 있을 때)

`docs/codebase-map/00-SUMMARY.md`가 있거나 소스 코드가 이미 있는 폴더에서 "기존 앱을 고쳐/보강해" 같은 요청이면 변경 요구 모드로 쓴다:
- 현행 기능은 SUMMARY·02-ARCH 에서 뽑아 `## 현행 기능 (유지)` 표로 적는다 (ID `E1…`, 각 항목은 "회귀 금지" 기준이 된다).
- 이번 요청은 `## 기능 목록`에 `F1…`로 적고 `원본` 열에 `변경 요청` / `04-CONCERNS S2` 처럼 출처를 남긴다.
- 화면은 바뀌는 화면만 와이어프레임을 그린다.

## 2단계: 질문 (묶어서, 불명확한 것만)

설명·문서에서 이미 분명한 항목은 건너뛴다. 불명확한 항목만 `AskUserQuestion` 한 번에 최대 4개씩 묶어 묻는다 (첫 선택지 = 추천안). `--auto`면 묻지 않고 추천안을 "가정 (auto)"로 기록한다.

| 영역 | 질문 예시 |
|---|---|
| 목적 | "이 서비스가 해결하는 문제는 무엇인가요? 성공했다고 판단하는 기준은?" |
| 사용자 | "누가 사용하나요? 사용자 유형이 여러 개면 각각의 권한 차이는?" |
| 기능 목록 | 설명에서 뽑은 기능을 Must / Should / Won't(이번엔 안 함)로 나눠 제시하고 맞는지 확인 |
| 핵심 흐름 | "가장 중요한 사용자 흐름 2~3개를 순서대로 말해 주세요. (예: 가입 → 검색 → 결제)" |
| 화면 | 흐름에서 화면 목록을 도출해 제시하고, 빠진 화면이 있는지 확인 |
| UI 조건 | 플랫폼(웹/모바일/데스크톱), 반응형, 접근성 요구, 기존 디자인 시스템·브랜드 유무 |

---

## 3단계: 화면 와이어프레임

Must 기능에 해당하는 화면마다 텍스트 와이어프레임을 그린다. 화면에 놓일 요소와 배치만 표현하고, 색·폰트는 다루지 않는다.

```
[로그인]
┌─────────────────────────┐
│ 로고                     │
│ [이메일          ]       │
│ [비밀번호        ]       │
│ (로그인)   비밀번호 찾기  │
└─────────────────────────┘
→ 성공: [대시보드] / 실패: 오류 문구 표시
```

---

## 4단계: 확인

정리본(아래 형식)을 보여주고 묻는다:

> "이 내용으로 확정할까요? 고칠 부분이 있으면 말씀해 주세요."

사용자가 승인할 때까지 수정·재제시한다. 승인 없이 저장하지 않는다 (`--auto`: 자동 승인으로 기록하고 저장).

---

## 5단계: REQUIREMENTS.md 저장

프로젝트 루트에 저장한다.

```markdown
# 요구사항 — <프로젝트명>
작성일: YYYY-MM-DD | 상태: 확정

## 목적
<해결하는 문제 1~2줄> / 성공 기준: <측정 가능한 기준>

## 사용자
| 유형 | 설명 | 권한 |
|---|---|---|

## 기능 목록
| ID | 원본 | 기능 | 우선순위 | 완료 기준 |
|---|---|---|---|---|
| F1 | <REQ-01 / 사용자 설명 / 제안> | <기능> | Must | <예/아니오로 판단 가능한 문장> |
| F2 | ... | <기능> | Should | ... |

## 범위 밖 (Won't)
- <이번에 하지 않는 것>

## 핵심 사용자 흐름
1. <흐름 이름>: <화면 A> → <화면 B> → <결과> (관련 기능: F1, F3)

## 화면
### <화면명> (관련 기능: F1)
<텍스트 와이어프레임>

## UI 조건
- 플랫폼: / 반응형: / 접근성: / 디자인 시스템:

## 미결정 사항
- <사용자가 보류한 질문>

### 가정 (auto)
- <`--auto`로 추천안을 채택한 질문 → 선택 (근거)>  ← --auto 가 아니면 섹션 생략
```

기능 ID(`F1`…)는 이후 `/hive:plan`의 Wave 매핑과 `feature-list.json`에서 그대로 쓰인다.

---

## 6단계: 완료 안내

> "요구사항 확정. REQUIREMENTS.md에 기능 <N>개(Must <a> / Should <b>), 화면 <M>개가 정리되었습니다.
> 다음: `/hive:discover`로 아키텍처를 결정하세요."

---

## 주의사항

- 질문은 묶어서 한 번에 (최대 4개). 앞 답에 따라 달라지는 질문만 다음 왕복으로 미룬다.
- 추측으로 기능을 추가하지 않는다. 사용자가 말하지 않은 기능은 "제안"으로 표시하고 확인받는다.
- 완료 기준은 "예/아니오"로 판단 가능한 문장이어야 한다.

---

<!-- HIVE_V2_STANDARDS -->

## 표준 참조 (HIVE v2)

이 스킬은 다음 공통 표준을 따른다. 상세 규칙은 각 문서 참조.

| 표준 | 문서 | 역할 |
|------|------|------|
| 사전조건 체크 | [`_shared/prerequisites.md`](../_shared/prerequisites.md) | 스킬 시작 시 git/ARCH/PLAN/WORKLOG/ctx 등 검증 |
| 출력 형식 | [`_shared/output-format.md`](../_shared/output-format.md) | Verdict(✅/⚠/❌) · Severity · 에러 코드 통일 |
| WORKLOG 갱신 | [`_shared/worklog-update.md`](../_shared/worklog-update.md) | 시작/종료/결정사항 기록 표준 절차 |
| 서브 에이전트 호출 | [`_shared/agent-dispatch.md`](../_shared/agent-dispatch.md) | Sonnet/Haiku 디스패치 프롬프트 템플릿 |
| Git 커밋 메시지 | [`_shared/git-commit.md`](../_shared/git-commit.md) | Conventional Commits + 스킬별 자동 메시지 |

스킬 인덱스: [`SKILLS.md`](../SKILLS.md)
