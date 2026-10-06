# HIVE 5-Minute Walkthrough

이 문서는 HIVE 워크플로우를 **빈 디렉토리에서 첫 구현 Wave까지**
5분 안에 체험하는 가이드다. 실제 코드를 작성하기보다 명령 시퀀스를
머리에 새기는 게 목적.

> 가상의 예시 프로젝트: **Todo REST API** (FastAPI). 다른 어떤 도메인도
> 같은 단계로 진행한다.

---

## Setup

```bash
# 1. 빈 디렉토리에 들어간다
mkdir my-todo-api && cd my-todo-api
git init

# 2. HIVE 하네스를 설치 (멱등; 기존 파일은 보호됨)
git clone https://github.com/JaewooShin80/hive.git /tmp/hive
/tmp/hive/install.sh --target .

# 3. 첫 커밋
git add . && git commit -m "chore: bootstrap HIVE harness"

# 4. Claude Code 진입
claude
```

상태바에 `HIVE | opus-4-7 | wave -/-` 가 보이면 정상.

---

## Step 1 — Architecture Discovery (~1 min)

```
> /hive:discover
```

Advisor(Opus)가 개방형 질문 4-6개를 던진다 (사용자/규모/제약/배포 환경 등).
답하면 `ARCHITECTURE.md`와 `WORKLOG.md`가 생성된다.

**기대 결과물**
- `ARCHITECTURE.md` — 선택된 스택 (e.g. FastAPI + SQLite + pydantic)
- `WORKLOG.md` — 작업 시작 시각 + 첫 결정사항

---

## Step 2 — Wave Plan (~1 min)

```
> /hive:plan "todo API: CRUD + auth, single-user"
```

Advisor가 Wave 단위로 분해한 `PLAN.md`를 만든다. 각 Wave는 TDD 가능한
크기로 나뉘며 의존 그래프가 명시된다.

**기대 결과물 (예시)**
- Wave 1: 도메인 모델 + 마이그레이션
- Wave 2: CRUD 엔드포인트
- Wave 3: 인증 미들웨어
- Wave 4: 배포 설정

---

## Step 3 — Execute Wave 1 (~2 min)

```
> /hive:execute
```

Opus가 Haiku에게 보일러플레이트를, Sonnet에게 비즈니스 로직과
TDD 테스트를 병렬 디스패치한다. 끝나면 자동으로 `git commit`.

이어서 보안 검토를 자동/수동 호출:

```
> /hive:security
```

OWASP / AI-LLM / API / 시크릿 4영역을 스캔하고 치명적 이슈는 즉시 수정한다.

---

## Cleanup / 다음 단계

| 상황 | 명령 |
|---|---|
| 다음 Wave 진행 | `/hive:execute` |
| 버그 발생 | `/hive:debug "<증상>"` |
| 결정 변경 / 옵션 비교 | `/hive:compare` → `/hive:adr new` |
| 컨텍스트 50% 초과 | `/compact` |
| 작업 중단 후 재개 | 다음 세션에서 `/hive:worklog resume` |
| 의존성 마이그레이션 | `/hive:migrate "Pydantic v1 -> v2"` |
| 동작 보존 리팩토링 | `/hive:refactor <module>` |
| Wave 단위 롤백 | `/hive:rollback wave 3` |

---

## 추가 학습 자료

- 전체 명령 인덱스: `.claude/plugins/hive/SKILLS.md` (자동 갱신)
- Karpathy 4 원칙 + Context 50% 룰: 루트 `CLAUDE.md`
- 변경 이력: 루트 `CHANGELOG.md`
- 인젝션 가드 / 서브에이전트 표준: `.claude/plugins/hive/_shared/agent-dispatch.md`

문제가 생기면:

```
> /hive:debug "<증상>"
```

(추측 디버깅 금지 — 4단계 RCA가 강제된다.)
