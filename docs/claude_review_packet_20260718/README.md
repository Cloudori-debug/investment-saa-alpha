# Claude 검수 패킷 — 첨부용 (2026-07-18)

이 폴더를 **통째로** 다른 Claude 세션(Desktop/Projects)에 첨부하거나, 아래 파일을 선택 업로드하세요.

## 필수
- `CLAUDE_REVIEW_BRIEF_20260718.md`
- `ALPHA_FINAL_SELECTION_HARDENING_RESULT.md`

## 핵심 코드 (`code/`)
- `allocate.py`, `sector_map.py`
- `portfolio.py`, `action_panels.py`
- `evaluate.py`, `events.py`, `weekly_domain_gates.py`
- `cecs_ai_research.py`

## 테스트 (`tests/`)
- `test_select_eligible_sector_cap.py`

## 선택
- `CODEBASE_CLEANUP_AC_20260718_RESULT.md`
- `CODEBASE_CLEANUP_BD_20260718_RESULT.md`

## 첫 메시지 (복붙)

```
첨부한 CLAUDE_REVIEW_BRIEF_20260718.md 와 RESULT·code/·tests/ 를 읽고
「검수 미션」대로 독립 검수해 주세요.
코드를 수정하거나 리팩터 제안으로 범위를 넓히지 마세요.
보고 템플릿 형식으로만 답하세요.
불변 규칙 위반이 Critical입니다.
P2(E, 전체 pytest hang, 30종 매직넘버)는 수정 지시 없이 의견만.

트리아지 참고(채택 판단은 보고 후 SAA 채팅에서):
① allocate — 기존 테스트 미커버 엣지만 Major+
② action_panels — 라이브 로직 결함 vs 낡은 테스트 가정 구분
③ Critical — 불변 규칙·하드 룰 직결만
```

## 참고
원본 경로의 스냅샷 복사본입니다. 검수 후 보고서는 SAA 알파 투자(Cursor) 채팅으로 가져오면 채택/기각/보류합니다.
Cursor가 미리 쓴 교차 검수(`docs/CLAUDE_REVIEW_REPORT_20260718_CURSOR.md`)는 **첨부하지 마세요** — 독립 시선이 흐려집니다.
