---
name: aifab:map-codebase
description: 4-parallel mappers for codebase analysis
argument-hint: [<path>] [--focus <area>]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Task
---

# `/aifab:map-codebase` — 4-병렬 매퍼 코드베이스 분석

**담당 모델:** Advisor (claude-opus-4-7) — 매퍼 조정 및 종합
**서브에이전트:** Sonnet × 4 — 병렬 매퍼 (각자 독립 영역 분석)

---

## 목적

Brownfield 프로젝트(기존 코드베이스)에 진입할 때, 4개 매퍼 에이전트를 병렬 실행하여 코드베이스를 깊이 이해한다. `/aifab:discover` 또는 `/aifab:plan` 전에 실행하면 정확도가 크게 향상된다.

---

## 사용 방법

```
/aifab:map-codebase                    # 현재 디렉토리 분석
/aifab:map-codebase <path>             # 특정 디렉토리 분석
/aifab:map-codebase --focus <area>     # 특정 영역 집중 분석
```

---

## 4개 병렬 매퍼

각 매퍼는 독립적으로 실행되며, 자신의 영역에 대한 마크다운 보고서를 작성한다. Advisor는 4개 보고서를 받아 SUMMARY를 생성한다.

### Mapper 1: Tech Stack Mapper (기술 스택)

**산출물:** `docs/codebase-map/01-TECH.md`

조사 항목:
- 프로그래밍 언어 및 버전
- 프레임워크 및 주요 라이브러리 (`package.json`, `requirements.txt`, `pyproject.toml`, `go.mod` 등)
- 빌드 도구, 테스트 프레임워크, 린터/포매터
- 데이터베이스, 캐시, 메시지 큐
- 외부 서비스 통합 (API 클라이언트)
- 배포 도구 (Docker, Kubernetes, CI/CD)

### Mapper 2: Architecture Mapper (아키텍처)

**산출물:** `docs/codebase-map/02-ARCH.md`

조사 항목:
- 디렉토리 구조 및 레이어링 (MVC, Clean Architecture, Hexagonal 등)
- 주요 모듈/패키지 및 책임
- 데이터 모델 (DB 스키마, ORM 모델)
- API 엔드포인트 목록 (REST/GraphQL)
- 인증/인가 흐름
- 외부 의존성 그래프
- 핵심 비즈니스 로직 위치

### Mapper 3: Quality Mapper (코드 품질)

**산출물:** `docs/codebase-map/03-QUALITY.md`

조사 항목:
- 테스트 커버리지 현황 (단위/통합/E2E)
- 테스트 프레임워크 및 패턴
- 코드 컨벤션 (네이밍, 폴더링, import 순서)
- 문서화 수준 (docstring, README, ADR)
- TODO/FIXME/HACK 주석 위치
- 복잡한 함수/클래스 (긴 함수, 많은 파라미터)
- 중복 코드 패턴

### Mapper 4: Concerns Mapper (위험/이슈)

**산출물:** `docs/codebase-map/04-CONCERNS.md`

조사 항목:
- 보안 우려 사항 (하드코딩 시크릿, SQL 인젝션 위험 등)
- 성능 핫스팟 (N+1 쿼리, 비효율 알고리즘)
- 기술 부채 표시 (deprecated API 사용, 오래된 의존성)
- 결합도 높은 영역
- 단일 장애점 (Single Point of Failure)
- `git log`로 본 자주 변경되는 핫스팟
- 알려진 버그 또는 이슈 (이슈 트래커, GitHub Issues)

---

## 프로세스

### Step 1: 사전 점검

1. 현재 디렉토리가 git 리포지토리인지 확인
2. 디렉토리 크기 추정 (`find . -type f | wc -l`)
3. 1000개 이상이면 사용자에게 알림: "분석에 시간이 소요될 수 있습니다."
4. `docs/codebase-map/` 디렉토리 생성

### Step 2: 병렬 매퍼 실행

Advisor가 Agent 도구로 4개 매퍼를 **동시에** 실행:

```
Agent 1 (Sonnet) → Mapper 1: Tech Stack
Agent 2 (Sonnet) → Mapper 2: Architecture
Agent 3 (Sonnet) → Mapper 3: Quality
Agent 4 (Sonnet) → Mapper 4: Concerns
```

각 매퍼 프롬프트에는 다음 포함:
- 분석 대상 디렉토리 절대경로
- 자신의 영역에 한정한 조사 항목
- 산출 파일 경로
- "다른 영역은 다루지 말 것" 명시

### Step 3: SUMMARY 생성

4개 매퍼 완료 후, Advisor가 종합:

**산출물:** `docs/codebase-map/00-SUMMARY.md`

```markdown
# Codebase Map Summary
분석 일자: YYYY-MM-DD | 분석 범위: <path>

## 한 줄 요약
<코드베이스를 한 문장으로>

## 주요 발견 사항 (Top 5)
1. ...
2. ...

## 권장 진입 전략
- 새 기능 추가 시: <어디에, 어떤 패턴으로>
- 리팩토링 우선순위: <순서>
- 위험 영역 (조심해서 만질 것): <목록>

## 상세 보고서
- [기술 스택](01-TECH.md)
- [아키텍처](02-ARCH.md)
- [품질](03-QUALITY.md)
- [위험/이슈](04-CONCERNS.md)
```

### Step 4: 후속 단계 안내

분석 완료 후 안내:
```
✅ Codebase 분석 완료. 4개 보고서가 docs/codebase-map/에 생성됨.

다음 단계:
- 새 기능 추가: /aifab:discover (이 분석 결과를 컨텍스트로 사용)
- 리팩토링 계획: /aifab:plan
- 보안 검토: /aifab:security (CONCERNS.md 기반)
```

---

## --focus 옵션

특정 영역만 깊게 보고 싶을 때:
```
/aifab:map-codebase --focus security    # CONCERNS만 더 깊이
/aifab:map-codebase --focus testing     # QUALITY 중 테스트만
/aifab:map-codebase --focus api         # ARCH 중 API만
```

해당 매퍼만 실행하되, 더 상세한 분석 수행.

---

## 통합

- `/aifab:discover`: brownfield일 경우 자동으로 `map-codebase` 실행 권장
- `/aifab:plan`: SUMMARY.md를 컨텍스트로 활용하여 더 정확한 Wave 분해
- `/aifab:security`: CONCERNS.md를 시작점으로 보안 검토
- `/aifab:debug`: ARCH.md를 활용하여 영향 범위 빠르게 파악

---

## 캐싱

매핑 결과는 git에 커밋된다. 이후 `/aifab:map-codebase` 재실행 시:
- 기존 보고서가 1주일 이내면: "캐시된 결과 사용 (rerun으로 재실행)" 안내
- 1주일 초과: 자동 재실행
- `/aifab:map-codebase rerun`: 강제 재분석

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
