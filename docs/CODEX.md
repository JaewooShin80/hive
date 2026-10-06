# Codex에서 HIVE 하네스 사용하기

Codex는 `AGENTS.md`를 통해 이 하네스를 사용할 수 있다.

## 설치

HIVE 동작을 적용하려는 프로젝트에 하네스 파일을 복사한다.

```bash
cp AGENTS.md /path/to/project/
cp -r .claude /path/to/project/
cp -r scripts /path/to/project/
```

대상 프로젝트에 이미 `AGENTS.md`가 있다면 덮어쓰지 말고 HIVE 관련 섹션만 병합한다.

## Codex에 요청하는 방식

Claude slash command 대신 자연어로 요청한다.

```text
HIVE 하네스를 사용해줘. 코드베이스를 파악하고, Wave 계획을 만든 뒤, Wave 1만 구현해줘.
```

기존 기능 작업 예시:

```text
HIVE 방식으로 진행해줘. 코드베이스를 조사하고, 가장 작은 안전한 Wave를 계획한 다음 구현하고, 테스트와 보안 검토까지 해줘.
```

버그 수정 예시:

```text
HIVE diagnose 방식으로 진행해줘. 먼저 버그를 재현하고, 최소 재현을 만든 뒤, 회귀 테스트를 추가하고 수정해줘.
```

## 실제 매핑

Codex는 `/hive:*` slash command를 직접 실행할 수 없다. 대신 스킬 마크다운 파일을 읽고 절차로 따른다.

- `.claude/plugins/hive/skills/discover.md`
- `.claude/plugins/hive/skills/plan.md`
- `.claude/plugins/hive/skills/execute.md`
- `.claude/plugins/hive/skills/security.md`
- `.claude/plugins/hive/skills/worklog.md`

기대 산출물은 기존 HIVE 흐름과 같다.

- `ARCHITECTURE.md`
- `PLAN.md`
- `WORKLOG.md`
- `CONTEXT.md`
- `docs/adr/*.md`

## 권장 Codex 프롬프트

```text
이 저장소의 HIVE 하네스를 사용해줘.

목표: <기능 또는 버그 수정 설명>

다음 순서로 진행해줘.
1. 필요하면 discover/map-codebase를 수행한다.
2. Wave 스타일 계획을 만든다.
3. 다음 Wave 하나만 구현한다.
4. 범위에 맞는 테스트를 실행한다.
5. 보안 위험을 검토한다.
6. 여러 단계 작업이면 WORKLOG.md를 갱신한다.
```

## 사용량을 아래에서 보기

Codex CLI에는 Claude Code의 `statusLine`과 같은 하단 상태바 설정이 없다. 대신 Codex TUI 로그의 마지막 token usage를 읽는 스크립트를 사용한다.

한 번 출력:

```bash
python3 scripts/codex-usage-status.py
```

예상 형태:

```text
Codex gpt-5.5 | in 13.1k cached 11.6k | out 14 r 0 | total 13.1k
```

tmux 하단바에 붙이려면 `~/.tmux.conf`에 추가한다.

```tmux
set -g status-right "#(python3 /Users/jaybee/lab/HIVE/scripts/codex-usage-status.py)"
set -g status-interval 5
```

적용:

```bash
tmux source-file ~/.tmux.conf
```

tmux를 쓰지 않는 경우에는 별도 터미널에서 watch로 볼 수 있다.

```bash
watch -n 5 python3 /Users/jaybee/lab/HIVE/scripts/codex-usage-status.py
```
