# Shared: WORKLOG.md Update Protocol

모든 스킬이 WORKLOG.md를 갱신할 때 따르는 표준 절차.

## 갱신 시점

- **Wave 시작 시**: "현재 단계" + "현재 작업" 갱신
- **Wave 완료 시**: 체크박스 [x] + 완료 기록 추가
- **결정사항 발생 시**: "주요 결정사항" 섹션 추가
- **에러/이슈 발생 시**: "미결 이슈" 섹션 추가
- **단계 전환 시** (예: execute → security): "현재 단계" 갱신

## 갱신 절차 (atomic)

```
1. WORKLOG.md 읽기 (전체)
2. 변경할 섹션 식별
3. 한 번의 Edit으로 변경 적용 (race condition 방지)
4. git add WORKLOG.md (단, commit은 즉시 하지 않음)
5. 작업 단위 종료 시 commit에 포함
```

## 표준 섹션별 형식

### 현재 상태 갱신

```markdown
## 현재 상태
- 현재 단계: <discover | plan | execute | security | playwright | uat | refactor | migrate>
- 마지막 완료 Wave: Wave <N> (없으면 "없음")
- 현재 작업: <구체적 다음 스텝>
- 마지막 업데이트: YYYY-MM-DD HH:MM
```

### Wave 완료 기록

```markdown
## 완료된 Wave 기록
| Wave | 제목 | 완료일 | Git Commit | 비고 |
|------|------|--------|-----------|------|
| 3 | 인증 시스템 | 2026-05-02 | a1b2c3d | TDD 28 tests pass |
```

### 결정사항 추가

```markdown
## 주요 결정사항
| 날짜 | 결정 내용 | 이유 | 출처 |
|------|----------|------|------|
| 2026-05-02 | Pydantic v2 채택 | 성능 30% ↑ | /aifab:adr 0003 |
```

`출처` 컬럼: ADR 번호, /aifab:compare 결과, 또는 Wave 번호.

### 미결 이슈 추가

```markdown
## 미결 이슈
- [ ] <이슈 한 줄> (발견: YYYY-MM-DD, Wave <N>, 우선순위: high/med/low)
```

해결 시 `[x]` 처리하고 해결 commit hash 추가.

### UAT 결과 갱신

```markdown
## UAT 결과
- 날짜: YYYY-MM-DD
- 결과: 통과 / 조건부통과 / 실패
- 통과 시나리오: N/M
- 피드백:
  - <시나리오 N>: <피드백 내용>
- 후속 조치: <Wave N+1 추가 등>
```

## 자동화 vs 수동

다음은 스킬이 자동으로 갱신:
- 현재 단계 (스킬 시작/종료 시)
- 완료 Wave 기록 (execute 종료 시)
- UAT 결과 (uat 종료 시)
- 보안 검토 결과 (security 종료 시)

다음은 사용자 확인 후 갱신:
- 주요 결정사항 (애매한 결정은 명시적 확인)
- 미결 이슈 (자동 발견 + 등록 여부 확인)

## 충돌 처리

여러 스킬이 동시에 WORKLOG.md를 변경하려 할 때 (예: 워크트리 병렬):
1. 각 워크트리는 자체 WORKLOG.md 보유
2. 머지 시 메인 WORKLOG.md에 통합
3. 충돌 시 `## 미결 이슈`로 자동 추가하고 사용자에게 보고
