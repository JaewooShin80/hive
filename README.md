# HIVE Harness

Claude Code용 개발 워크플로우 하네스. Andrej Karpathy의 4원칙을 기반으로 Opus·Sonnet·Haiku 멀티에이전트를 오케스트레이션하여 일관성 있는 고품질 코드를 생성한다.

> **스킬 목록·의존성·모델 매트릭스는 [`SKILLS.md`](.claude/plugins/hive/SKILLS.md) 가 단일 소스.** 이 README는 설치·운영에만 집중한다.

---

## 핵심 개념

| 개념 | 요약 |
|---|---|
| **Karpathy 4원칙** | 코딩 전 사고 / 단순성 / 외과적 변경 / 목표 기반 실행 — [`CLAUDE.md`](CLAUDE.md) |
| **Multi-Agent 역할** | Opus(Advisor) → Sonnet(Worker) → Haiku(Generator). `settings.json`의 env로 모델 교체 가능 |
| **계층 진척 모델** | Milestone(semver) → Phase(목적 그룹) → Wave(0.5~3일 작업 단위) |
| **계획 트리플** | `ROADMAP.md`(Phase 인덱스) + `PLAN.md`(Wave 상세) + `WORKLOG.md`(작업일지) |
| **컨텍스트 80% 규칙** | 사용률 80% 이상이면 새 태스크 시작 전 반드시 `/compact`, 70%부터 경고 (CLAUDE.md RULE 5) |
| **결정론 가드** | hooks가 시크릿/위험 bash/컨텍스트 임계치를 자동 차단·경고 |

---

## 설치

macOS · Linux · Windows 모두 동일한 설치기(`scripts/hive-install.js`)를 사용한다.
`install.sh`(bash)와 `install.ps1`(PowerShell)은 이를 호출하는 얇은 래퍼일 뿐이다.

```bash
# 1) 하네스 받기 (업그레이드 시 git pull 후 설치 명령만 재실행)
git clone https://github.com/JaewooShin80/hive.git ~/hive
```

### A. 전역 설치 (권장 — 모든 프로젝트에서 `/hive:*`)

```bash
~/hive/install.sh --global                 # macOS / Linux / Git Bash
```
```powershell
~\hive\install.ps1 --global                 # Windows PowerShell
# 실행 정책 차단 시: powershell -ExecutionPolicy Bypass -File ~\hive\install.ps1 --global
```

### B. 프로젝트 설치 (새 프로젝트 · 기존 프로젝트 공통)

```bash
~/hive/install.sh --target ~/my-project    # macOS / Linux / Git Bash
```
```powershell
~\hive\install.ps1 --target C:\dev\my-project   # Windows PowerShell
```

### 설치 결과

| 대상 | 위치 (`<base>` = `~/.claude` 또는 `<project>/.claude`) |
|---|---|
| 스킬 → `/hive:*` 명령 | `<base>/commands/hive/*.md` |
| 공통 표준 (`_shared`, `SKILLS.md`) | `<base>/hive/` — 명령 목록에 섞이지 않도록 commands 밖에 둠 |
| hooks 6종 | `<base>/hooks/hive-*.js` + `settings.json`에 `node "<절대경로>"`로 자동 등록 |
| 저장된 Workflow | `<base>/workflows/hive-wave.js` — `/hive:execute` 4단계 병렬 디스패치 (Claude Code 전용, 없으면 Agent 도구로 대체) |
| 상태바 | `node "<scripts>/hive-status.js"` — Python(`python3`→`python`→`py -3`) 자동 탐색 |
| 스크립트 | 프로젝트: `<project>/scripts/` · 전역: `~/.claude/scripts/hive/` |

- `settings.json`은 **덮어쓰지 않고 병합**한다 (기존 값 우선, 재실행해도 중복 없음). `CLAUDE.md`는 이미 있으면 보존.
- hook·상태바 명령이 `node "<경로>"` 형태라 Windows에서 Claude Code가 Git Bash/PowerShell 어느 쪽으로 실행해도 동작한다.
- CI가 ubuntu·macOS·Windows에서 단위 테스트와 `install.sh`/`install.ps1` 글로벌 설치를 매 push마다 검증한다.
- `--dry-run`으로 변경 내용을 미리 확인할 수 있다. 설치 후 Claude Code를 재시작하고 `/hive:discover`로 진입.

---

## 사전 요구사항

| 도구 | 용도 | 필수/선택 |
|------|------|----------|
| Claude Code CLI | 모든 명령 실행 | 필수 |
| `git` | 버전 관리 / worktree | 필수 |
| `node` | 설치기 + hooks(`hive-*.js`) + 상태바 런처 + Playwright | 필수 |
| Python 3 (`python3`/`python`/`py -3`) | 상태바·진척 파싱, gen_skills_index | 필수 (없으면 상태바/진척 대시보드 미표시) |
| `@openai/codex` | 교차 AI 검증 | 선택 (`/hive:codex-review`) |

```bash
# Claude Code 인증
claude login                    # Pro/Team
# 또는
export ANTHROPIC_API_KEY="sk-ant-..."

# Playwright (E2E 사용 시)
npm install -D @playwright/test
npx playwright install chromium

# Codex CLI (교차 검증 사용 시)
npm install -g @openai/codex && codex login
```

---

## 설치 확인

```bash
# 1) 상태바
echo '{}' | node scripts/hive-status.js
# 2-line Powerline 출력 확인 (모델·git·ctx·5h·7d)

# 2) 스킬 인식 — Claude Code 세션에서
/hive:
# 자동완성에 23개 스킬 노출 (discover, plan, execute, ...)

# 3) 진척 대시보드
/hive:progress
# ROADMAP.md/PLAN.md 있으면 Milestone·Phase·Wave 진척률 표시
```

---

## 빠른 시작

```text
[brownfield]  /hive:map-codebase     # 기존 코드베이스 4-병렬 분석

/hive:discover  → /hive:plan  → /hive:execute (반복)
        │                                  │
        │                                  ├─ /hive:debug         (테스트 실패 시)
        │                                  ├─ /hive:worktree      (병렬 Wave)
        │                                  └─ /hive:security       (Wave 완료 후)
        │
        └─ /hive:roadmap init        # 다중 Phase 마일스톤일 때
                                      # → /hive:milestone new vX.Y.Z

/hive:playwright  → /hive:uat       # 전체 완료 후
/hive:milestone complete             # 마일스톤 tag + 회고
```

작업 중단 후 재시작: `/hive:worklog resume`.

전체 명령 목록과 의존성 그래프는 [`SKILLS.md`](.claude/plugins/hive/SKILLS.md).

---

## 결정론 가드 (Hooks)

`CLAUDE.md`의 prose 규칙을 hooks가 실시간 차단·경고로 강제한다.

| Hook | 트리거 | 동작 |
|---|---|---|
| `hive-secret-guard.js` | PreToolUse(Write/Edit) | 시크릿 패턴/시크릿 파일 경로 Write 차단 (exit 2) |
| `hive-bash-guard.js` | PreToolUse(Bash) | `rm -rf /`, `git push --force`, `curl \| sh` 등 차단 |
| `hive-ctx-guard.js` | PostToolUse | 컨텍스트 70%↑ 시 `/compact` 권고, 80%↑ 시 강한 경고 |

설치된 hooks는 `~/.claude/settings.json` 또는 프로젝트 `.claude/settings.json`의 `hooks` 블록에서 등록한다. 자세한 구성: [`.claude/plugins/hive/_shared/hooks.md`](.claude/plugins/hive/_shared/hooks.md) (v2.2.0 추가).

---

## 상태바

Claude Code 세션 하단 2-line Powerline.

```
  hive    main    ◆ Opus 4.6    $1.24    12m 
  M2·P2/4·W3/5 60%   ctx ████▌░░░░ 32%   5h ███▏│░░░░ 38% ⏳2h17m   7d █▏░░░░░░ 12% ⏳5d3h
```

- **Tier 글리프**: `◆` Opus / `◇` Sonnet / `○` Haiku / `◈` 기타. `model.display_name`을 stdin JSON에서 자동 추출하므로 신규 모델도 즉시 반영.
- **진척**: `Mn·Pa/b·Wc/d pct%` — ROADMAP/PLAN 부재 시 graceful fallback.
- **Pacing tick (`│`)**: 5h/7d 윈도우 경과 위치. tick 좌측이면 페이스 양호, 우측이면 빠른 소비.
- **컨텍스트**: 색상 임계치 ≤40% 녹/ ≤60% 황/ ≤80% 주황/ >80% 적.

### 스타일 옵션 (`HIVE_STATUS_STYLE`)

| 값 | 출력 |
|---|---|
| `powerline` (기본) | 2-line, ANSI 256-color, Unicode 바·tick |
| `color` | legacy 단일 라인 |
| `plain` | ASCII 단일 라인 (호환성 fallback) |

### Windows cp949 인코딩

`hive-status.py`는 UTF-8을 강제하므로 자동 해결. 직접 호출 시 문제가 나면:
```bash
export PYTHONIOENCODING=utf-8
```

---

## 모델 설정

| 모델 | 역할 | env 변수 |
|------|------|---------|
| `opus` | Advisor — 플랜·아키텍처·검토 | `HIVE_ADVISOR_MODEL` |
| `sonnet` | Worker — 로직·테스트 | `HIVE_WORKER_MODEL` |
| `haiku` | Generator — 보일러플레이트 | `HIVE_BOILERPLATE_MODEL` |

교체는 `settings.json`의 env만 수정. 스킬별 모델 사용 강도는 [`SKILLS.md` "모델 사용 매트릭스"](.claude/plugins/hive/SKILLS.md#모델-사용-매트릭스) 참조.

---

## 디렉토리 구조

```
hive/
├── CLAUDE.md                     # 전역 규칙 (Karpathy 4원칙 + RULE 5 컨텍스트)
├── README.md                     # 이 파일 (설치/운영)
├── ROADMAP.md / PLAN.md /        # (런타임 생성) 계획 트리플
│   WORKLOG.md
├── scripts/
│   ├── hive-status.py           # 2-line Powerline 상태바
│   ├── hive-status.js           # 상태바 진입점 (크로스플랫폼, Python 자동 탐색)
│   ├── hive-status.sh           # 레거시 bash 진입점
│   ├── hive-install.js          # 설치기 코어 (install.sh / install.ps1 공용)
│   ├── hive_progress.py         # ROADMAP/PLAN 파서 + Phase/Wave 진척
│   ├── codex-usage-status.py     # Codex CLI 사용량
│   ├── gen_skills_index.py       # CLAUDE.md/SKILLS.md 자동 인덱스 갱신
│   └── metric_log.py / _summary.py / skill_lint.py
└── .claude/
    ├── settings.json             # env + statusLine + permissions + hooks
    ├── commands/                 # 프로젝트 슬래시 명령
    ├── hooks/                    # 결정론 가드 (hive-*.js)
    ├── workflows/                # 저장된 Claude Code workflow (hive-wave.js)
    └── plugins/hive/
        ├── SKILLS.md             # 스킬 인덱스 + 의존성 그래프
        ├── _shared/              # 공통 표준 (prereq/output/worklog/dispatch/commit/hooks)
        └── skills/*.md           # 각 스킬 정의
```

---

## 런타임 생성 파일

워크플로우 실행 중 프로젝트 루트에 생성되는 산출물.

| 파일 | 생성 시점 | 용도 |
|------|----------|------|
| `ARCHITECTURE.md` | `/hive:discover` | 선택된 아키텍처 상세 |
| `ROADMAP.md` | `/hive:roadmap init` | Phase 인덱스 + 마일스톤 메타 |
| `PLAN.md` | `/hive:plan` | Wave별 작업 플랜 |
| `WORKLOG.md` | `/hive:discover` 또는 `/hive:worklog init` | 작업일지 (재시작용) |
| `CONTEXT.md` | `/hive:grill` | 도메인 용어/제약 정렬 |
| `MILESTONE-LOG.md` | `/hive:milestone complete` | 마일스톤 회고 + git tag |
| `DEBUG-SESSION.md` | `/hive:debug` | 가설·증거·검증 기록 |
| `docs/codebase-map/*.md` | `/hive:map-codebase` | 4-매퍼 분석 보고서 |
| `docs/adr/NNNN-*.md` | `/hive:adr new` | Architecture Decision Records |
| `docs/decisions/compare-*.md` | `/hive:compare` | 옵션 비교 매트릭스 |
| `docs/UAT-REPORT.md` | `/hive:uat` | UAT 결과 |
| `REFACTOR-LOG.md` | `/hive:refactor` | 리팩토링 단계별 보존 증거 |
| `MIGRATION-PLAN.md` / `MIGRATION-REPORT.md` | `/hive:migrate` | 마이그레이션 분석·결과 |
| `ROLLBACK-LOG.md` | `/hive:rollback` | 롤백 시점·사유·영향 |
| `.worktrees/wave-*/` | `/hive:worktree create` | 병렬 Wave 작업 공간 |

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| 상태바에 `cp949` 인코딩 오류 | `PYTHONIOENCODING=utf-8` 환경변수 또는 최신 `hive-status.py` 사용 |
| 상태바 글리프 깨짐 | 터미널 폰트를 Nerd Font (JetBrains Mono NF, Sarasa Mono K 등)로 변경, 또는 `HIVE_STATUS_STYLE=plain` |
| `/hive:` 자동완성에 스킬 없음 | 글로벌 설치: `~/.claude/commands/hive/` 경로 확인. 프로젝트 설치: `.claude/commands/hive/` 확인 |
| `/hive:progress` 빈 출력 | `ROADMAP.md`/`PLAN.md` 둘 다 없으면 정상. `/hive:roadmap init`으로 생성 |
| hooks가 동작하지 않음 | `settings.json` `hooks` 블록 등록 여부, `node` 설치/PATH 확인 (hook 명령은 `node "<경로>"` 형식) |
| 컨텍스트 hook 경고 미발생 | `hive-status.py`가 `/tmp/hive-ctx-<session_id>.json` 작성 중인지 (statusLine이 `hive-status` 스크립트로 설정됐는지) 확인 |
| GitLab/GitHub push 인증 실패 | `git credential-manager configure`로 GCM 설정. Personal Access Token은 만료 전 회수 |

---

## 라이선스 / 기여

- 본 하네스는 사내·개인 워크플로우 개선 목적의 dogfooding 산출물.
- 새 스킬 추가 또는 frontmatter 변경 후 반드시 `python3 scripts/gen_skills_index.py --write CLAUDE.md SKILLS.md`로 인덱스 갱신.
- CI는 `--check`로 stale 여부를 검증한다.
