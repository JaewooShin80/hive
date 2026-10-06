# Shared: 요구사항·참고 문서 읽기

사용자가 문서 경로를 주면(spec 1단계, discover C) 형식별로 다음과 같이 읽는다. `Read` 도구는 텍스트·PDF·이미지만 읽고 docx/xlsx/pptx/hwp 같은 바이너리 문서는 읽지 못한다.

| 형식 | 방법 |
|---|---|
| `.md` `.txt` `.csv` | `Read` |
| `.pdf` | `Read` (10쪽 초과면 `pages` 지정) 또는 `pdf` 스킬 |
| `.docx` | `docx` 스킬 → 없으면 `pandoc input.docx -t gfm` → 없으면 `python3 -c "import docx; …"` (표는 `document.tables`도 읽는다) |
| `.xlsx` | `xlsx` 스킬 → 없으면 openpyxl 로 시트별 셀 덤프 |
| `.pptx` | `pptx` 스킬 → 없으면 python-pptx 로 슬라이드별 텍스트 |
| `.hwp` `.hwpx` | 사용자에게 PDF/DOCX 변환을 요청 (`hwp5txt`가 있으면 사용) |
| 이미지(스캔본) | `Read`로 보고 내용을 받아 적는다 |

규칙:
- 변환 결과는 프로젝트 `docs/input/<원본이름>.md`에 저장하고, 원본 경로와 변환 방법을 첫 줄에 적는다. 이후 단계는 변환본을 읽는다.
- 원문의 요구사항 ID(예: `REQ-01`)는 버리지 않는다. REQUIREMENTS.md 기능 목록의 `원본` 열에 매핑한다.
- 표·번호 목록이 깨졌으면 원본과 대조해 바로잡은 뒤 진행한다.
