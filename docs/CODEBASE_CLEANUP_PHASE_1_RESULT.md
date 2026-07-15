# Cleanup Phase 1 — `value_list` (하케다카) archive

> SPEC: [`CODEBASE_CLEANUP_PHASE_0_1_2_SPEC.md`](CODEBASE_CLEANUP_PHASE_0_1_2_SPEC.md)  
> 원칙: **삭제 아님 · git mv · `ENABLE_HAKEDAKA=False` 기본**. kr_alpha 코어·익절엔진 미변경.

## 1. 이동 목록

| 원본 | archive | 개수 |
|------|---------|------|
| `src/value_list/` | `archive/20260715_value_list/` | 35 `.py` |
| `scripts/run_hakedaka_*.py` | `archive/20260715_hakedaka_scripts/` | 7 |
| 관련 테스트 (`test_hakedaka_*`, `test_research_automation`, `test_dart_accounts_fetch`) | `archive/20260715_tests/` | +15 (기존 v0.2 테스트와 공존) |

## 2. 잔여 참조 처리

신규 [`src/hakedaka_gate.py`](../src/hakedaka_gate.py):
- `ENABLE_HAKEDAKA=False` (환경변수 `ENABLE_HAKEDAKA=1`로 복구 가능 — 패키지를 `src/value_list`로 되돌린 뒤)
- 스텁: `proposal_sort_score` / `eligible_for_proposal_row`(AC-HK 유동성) / merge·bonus·registry no-op
- 호출부: `alpha_pipeline`, `portfolio_selector`, `full_pipeline`, `post_decision_artifacts`, `tier_h`, `report_writer`, `export_daily_brief`

## 3. 검증

| 항목 | 결과 |
|------|------|
| `import src.main` | ok |
| `hakedaka_enabled()` | False · registry=[] |
| portfolio_selector / price_coverage / export_daily_brief / shadow_config | 핵심 스위트 통과 (1건 `test_saa_taa_ticker_tables` 사전 비중 합 불일치 — 하케다카와 무관) |
| `tests/test_hakedaka_gate.py` | 추가 |

**다음:** 원장 검증 후 2단계(`alpha_v2` + `alpha_flow`) 진행 여부 결정.
