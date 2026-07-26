# investment-saa-alpha — Agent 안내 (v1 유지판)

## v1 / v2

- **이 저장소 = v1 유지·운영.** 대규모 기능·재채점 레이어는 **`C:\Cursor\investment-saa-alpha-v2`** 에서만.
- v2 차터: v2 쪽 `docs/V2_CHARTER.md`

## 단일 채팅방

- **공식 채팅 제목:** `SAA 알파 투자`
- 이 저장소 작업은 **그 채팅 하나**에서 이어간다. 주제별 새 채팅을 기본으로 만들지 말 것.
- 컨텍스트가 한계에 닿아 새 채팅이 불가피할 때만: 첫 응답 전에 [`docs/CHAT_HANDOFF_LEGACY_MULTI_ASSET.md`](docs/CHAT_HANDOFF_LEGACY_MULTI_ASSET.md)를 읽고, 「최근 완료 / 열린 항목」을 따른다.

## 새 채팅 / SAA 알파 투자 채팅 시작 시

1. **필수:** [`docs/CHAT_HANDOFF_LEGACY_MULTI_ASSET.md`](docs/CHAT_HANDOFF_LEGACY_MULTI_ASSET.md) 를 읽고 불변 규칙을 따른다.
2. 하케다카: [`docs/HAKEDAKA_ACCEPTANCE.md`](docs/HAKEDAKA_ACCEPTANCE.md), [`docs/HAKEDAKA_KR_ALPHA_POLICY.md`](docs/HAKEDAKA_KR_ALPHA_POLICY.md)
3. **v1 작업** 루트: `C:\Cursor\investment-saa-alpha` · **v2 작업** 루트: `C:\Cursor\investment-saa-alpha-v2`
4. **알파 대시보드 UI:** [`docs/ALPHA_SYSTEM_UIUX_MASTER_SPEC.md`](docs/ALPHA_SYSTEM_UIUX_MASTER_SPEC.md) 가 단일 기준. 문안은 `docs/UI_COPY.md`.

## 불변 요약

- `proposal_mode: pure_qvm` — 하케다카·수급으로 제안 순위 바꾸지 않음 (기본)
- `target_portfolio.csv` 자동 변경 금지 — 사람 승인만
- ETF Executable / kr_alpha·하케다카·수급 Review-only
- FASTJUSIK 스크래핑 금지 — KRX/PyKRX·DART 직접
