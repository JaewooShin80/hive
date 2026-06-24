# feature-list.json — 표준 스키마

> AI-Fab v2.2.0 (Wave 4)에서 도입. `PLAN.md`(서술/계획)와 짝이 되는 **외재화 검증 파일**.
> `/aifab:plan`이 emit, `/aifab:execute`가 update, `/aifab:progress`가 read.

---

## 위치

프로젝트 루트 `./feature-list.json` (PLAN.md와 같은 디렉토리).

## 최상위 구조

```json
{
  "schema_version": "1.0",
  "milestone": "v2.2.0",
  "features": [ ... ]
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `schema_version` | string | yes | 본 스키마 버전. 현재 `"1.0"`. 호환성 깨지는 변경 시 increment. |
| `milestone` | string | yes | ROADMAP.md 또는 PLAN.md의 milestone 식별자 (예: `v2.2.0`). |
| `features` | array<Feature> | yes | feature 객체 배열. 빈 배열 허용. |

## Feature 객체

```json
{
  "id": "W1-F1",
  "title": "secret guard blocks .env",
  "wave": 1,
  "pass_criteria": "exit 2 on .env Write",
  "status": "passing"
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | string | yes | `W{wave}-F{idx}` 형식 권장. 마일스톤 내 unique. |
| `title` | string | yes | feature 한 줄 요약 (PLAN.md success criteria 1줄을 그대로 사용 권장). |
| `wave` | integer | yes | 소속 Wave 번호 (1-based). |
| `pass_criteria` | string | yes | 검증 가능한 단일 문장. "예/아니오" 판단 가능해야 한다. |
| `status` | enum | yes | 아래 status enum 참조. |
| `verify` | object | no | `/aifab:evaluate` 라이브 검증용 (Wave 6). 부재 시 수동 검증 영역 (status 미변경). |

### verify 객체 (옵션 — Wave 6 도입)

```json
"verify": {
  "type": "url",
  "target": "file:///abs/path/to/page.html",
  "assert": "OK"
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `type` | enum | yes | `"url"` (Playwright MCP로 navigate + DOM/HTML fetch) 또는 `"cmd"` (쉘 명령 실행). |
| `target` | string | yes | type=url이면 URL (file://, http://, https://). type=cmd이면 쉘 명령. |
| `assert` | string | yes | 응답/stdout에서 매칭할 정규식 또는 substring. 매치 → `passing`, 불일치 → `failing`. |

`/aifab:evaluate` 동작:
- type=url + 매치 → `passing` / 불일치 → `failing` / 네트워크 오류 → `partial`
- type=cmd + exit 0 + stdout 매치 → `passing` / exit !=0 또는 매치 실패 → `failing` / 30s 타임아웃 → `partial`
- `verify` 부재 → 해당 entry는 status 미변경 (수동 검증 영역, 보고만 함)
- `aifab-bash-guard.js` 차단 패턴(type=cmd)은 실행 전 거부 (이중 가드)

## status enum

| 값 | 의미 | 누가 설정 |
|---|---|---|
| `pending` | 미착수 (PLAN.md 작성 직후 기본값) | `/aifab:plan` |
| `passing` | Wave 종료 시 테스트/검증 통과 | `/aifab:execute`, `/aifab:playwright`, `/aifab:evaluate` (Wave 6) |
| `failing` | 검증 실패 | 동상 |
| `partial` | 부분 통과 (예: 일부 케이스 skip) | 동상 |

`/aifab:progress`는 `passing` 카운트만 분자, 전체를 분모로 사용한다.

## 전체 예제

```json
{
  "schema_version": "1.0",
  "milestone": "v2.2.0",
  "features": [
    {
      "id": "W1-F1",
      "title": "secret guard blocks .env writes",
      "wave": 1,
      "pass_criteria": "PreToolUse(Write) on .env → exit 2",
      "status": "passing"
    },
    {
      "id": "W1-F2",
      "title": "bash guard blocks rm -rf /",
      "wave": 1,
      "pass_criteria": "PreToolUse(Bash) on 'rm -rf /' → exit 2",
      "status": "passing"
    },
    {
      "id": "W4-F1",
      "title": "feature-list.json schema documented",
      "wave": 4,
      "pass_criteria": "_shared/feature-list-schema.md exists with status enum",
      "status": "pending"
    }
  ]
}
```

## 검증 (consumer 측 그레이스풀 규약)

`/aifab:progress` (= `scripts/aifab_progress.py`)는 다음을 그레이스풀하게 처리한다:

| 상태 | 동작 |
|---|---|
| 파일 부재 | Wave 진척만 표시 (기존 동작). feature 라인 미출력. |
| JSON 파싱 실패 | feature 라인 미출력. stderr에 short warning. exit code는 영향 없음. |
| `features` 키 누락 또는 비-array | 동상. |
| 개별 entry 필수 필드 누락 | 해당 entry skip, 나머지로 카운트. stderr에 1줄 경고. |
| `status` 값이 enum 밖 | 해당 entry는 `passing` 카운트에서 제외. |

이 규약 덕분에 **기존 PLAN.md만 있는 프로젝트는 영향 없이** 작동한다 (Wave 4 RULE 1 Q4 결정).

## 향후 확장 (Wave 5/6 예정)

- Wave 5 `/aifab:execute`: Wave 종료 시 해당 Wave의 feature entry status를 테스트 결과 기반으로 갱신.
- Wave 6 `/aifab:evaluate`: Playwright MCP로 라이브 검증 후 status 갱신.

## 관련 문서

- [`../SKILLS.md`](../SKILLS.md) — 스킬 인덱스
- [`./hooks.md`](./hooks.md) — Wave 1·2·3 hooks 표준
- `PLAN.md` Wave 4-6 — 본 스키마 활용 계획
