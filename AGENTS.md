# Codex 지침 — AIFAB 하네스

이 저장소를 코드 작업용 AIFAB 워크플로우 하네스로 사용한다.

## 동작 방식

`/aifab:plan` 같은 Claude slash command는 Codex에서 직접 실행되지 않는다. 대신 `.claude/plugins/aifab/skills/` 아래의 마크다운 파일을 로컬 워크플로우 명세로 읽고, 그 의도를 Codex 작업 절차에 수동으로 적용한다.

코드 작업마다 다음 원칙을 따른다.

1. 작업과 관련된 스킬 파일을 먼저 읽는다.
2. 필요할 때 기대 산출물을 생성하거나 갱신한다.
   - `ARCHITECTURE.md`
   - `PLAN.md`
   - `WORKLOG.md`
   - `CONTEXT.md`
   - `docs/adr/*.md`
3. 사용자 요청과 직접 연결된 외과적 변경만 수행한다.
4. 동작 변경에는 가능한 한 TDD를 적용한다.
5. 수정 후 범위에 맞는 테스트를 실행한다.
6. 마지막 응답에 변경 파일과 검증 결과를 요약한다.

## 명령 매핑

Codex에서는 아래처럼 AIFAB 명령을 해석한다.

| AIFAB 명령 | Codex 동작 |
| --- | --- |
| `/aifab:grill` | 구현 전 요구사항, 도메인 언어, 제약을 정리한다. 필요하면 `CONTEXT.md` 또는 ADR을 갱신한다. |
| `/aifab:discover` | 코드베이스를 조사해 아키텍처, 관례, 위험 요소를 파악한다. |
| `/aifab:map-codebase` | 기존 프로젝트 작업 전에 더 깊게 코드베이스를 스캔한다. |
| `/aifab:plan` | 큰 변경 전에 Wave 스타일의 간결한 구현 계획을 작성한다. |
| `/aifab:execute` | 다음 Wave를 집중적으로 구현한다. |
| `/aifab:security` | 시크릿, 인젝션, 인증/권한, 위험한 기본값을 검토한다. |
| `/aifab:debug` | 원인이 불명확한 실패에 대해 가설 기반 RCA를 수행한다. |
| `/aifab:diagnose` | 재현 가능한 버그는 먼저 재현 루프를 만들고 수정한다. |
| `/aifab:worklog` | 여러 단계에 걸친 작업은 `WORKLOG.md`에 재시작 가능한 상태로 기록한다. |
| `/aifab:compare` | 여러 기술 선택지가 있을 때 트레이드오프 매트릭스로 비교한다. |
| `/aifab:adr` | 중요한 아키텍처 결정은 `docs/adr/` 아래에 기록한다. |
| `/aifab:refactor` | 동작을 보존하고 테스트를 유지하며 넓은 재작성은 피한다. |
| `/aifab:migrate` | 마이그레이션은 Wave로 나누고 호환성 경계를 명확히 한다. |
| `/aifab:rollback` | 사용자가 명시적으로 요청하지 않는 한 파괴적인 git 명령은 실행하지 않는다. |

## 현재 하네스 공백

GSD 스타일 `roadmap`, `progress`, `milestone` 레이어는 현재 `docs/superpowers/` 아래에 명세와 계획만 있고, 실행 가능한 AIFAB 스킬로는 아직 구현되지 않았다. 해당 파일들이 생기기 전까지는 기존 Wave 기반 흐름을 사용한다.

`grill/discover -> plan -> execute -> security -> worklog`

