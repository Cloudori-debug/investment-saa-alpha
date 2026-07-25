# 채팅 승계 핸드오프 (레거시 multi_asset → investment-saa-alpha)

> **목적:** `C:\Cursor` 워크스페이스의 구 채팅(레거시 `multi_asset_trigger_portfolio` 개발·하케다카·FASTJUSIK 논의)에서 확정된 결정을 **SAA 알파 투자 채팅**이 그대로 이어받게 한다.  
> **코드 루트:** `C:\Cursor\investment-saa-alpha` (구 경로 `multi_asset_trigger_portfolio`는 이 저장소로 통합됨)  
> **원본 채팅 transcript:** `93ceb171-5386-4466-a75e-f5010b0da3b4`  
> **작성일:** 2026-07-11 · **단일 채팅 정리:** 2026-07-14

### v1 / v2 분리 (2026-07-19)

| | 경로 | 역할 |
|--|------|------|
| **v1 (이 저장소)** | `C:\Cursor\investment-saa-alpha` | **유지·운영** — 만족하는 선정·UI 기준판. 대규모 기능 추가 지양 |
| **v2** | `C:\Cursor\investment-saa-alpha-v2` | **등급업 개발** — 재채점 신호 레이어·운영 보완. 차터 `investment-saa-alpha-v2/docs/V2_CHARTER.md` |

- 차트·수급으로 순위 변경 / CECS 자동 조정은 **어느 쪽에서도 하지 않음**
- 신규 기능·실험은 **v2만**. v1에는 버그·운영 핫픽스만

**다른 채팅에서 시작할 때:** 이 파일을 먼저 읽고, 아래 「불변 규칙」을 어기지 말 것. v2 작업이면 v2 폴더 + `V2_CHARTER.md`.

---

## 0b. 단일 채팅방 운영 (2026-07-14)

| 항목 | 내용 |
|------|------|
| **공식 채팅 제목** | `SAA 알파 투자` |
| **원칙** | 이 프로젝트 작업은 **이 채팅 하나**에서 이어간다. 주제가 갈라져도 새 채팅을 남발하지 말 것. |
| **새 채팅이 필요한 경우** | 컨텍스트가 너무 커져 응답이 불안정할 때만. 새 채팅 첫 메시지에 이 핸드오프를 읽게 하고, 아래 「최근 완료」만 한 줄로 넘긴다. |
| **다른 채팅** | 같은 주제의 옛 채팅(구 multi_asset / 단발 조사)은 핸드오프·RESULT 문서에 결정이 있으면 **삭제해도 됨**. Cursor는 채팅을 자동 병합하지 않음 — 사이드바에서 수동 삭제. |

### 최근 완료 (이 채팅에서 이어받음)

| 영역 | RESULT / 요지 |
|------|----------------|
| **Ops A CECS (v2)** | v2만: `total_score` 정량 100%(cecs 가중 0). 정성 필수=T2·논지·목표가. 상세는 v2 핸드오프 (2026-07-25) |
| kr_alpha min/max 밴드 | `TARGET_MINMAX_BAND_FIX_RESULT` — 예산 스케일 시 min/max 동반 |
| 위성 캡 | `SATELLITE_CAP_ALIGNMENT_RESULT` — sleeve×budget 동적 캡, 071050 정렬 |
| 레짐 격차 경고 | `REGIME_OVERRIDE_DIVERGENCE_ALERT_RESULT` — AC-05b |
| 격차 지속 에스컬레이션 | `REGIME_DIVERGENCE_ESCALATION_RESULT` — 로그 3일째 재촉 (소급 없음) |
| Alpha BT 표본 라벨 | `ALPHA_BACKTEST_SAMPLE_QUALITY_FIX_RESULT` — scored_days_used 기준 품질 |
| 실행.bat 「멈춤」 | 실제 hang 아님(5~10분). CLI 진행 메시지 추가 |
| 레짐 만료·재검토 | `REGIME_OVERRIDE_EXPIRY_REVIEW_FIX_RESULT` — 만료 시 policy_cap↔computed 정합, AC-05c/AC-05 승격 |
| 레짐 재분류 CAUTION | `REGIME_CAUTION_RECLASSIFICATION_RESULT` — YELLOW→CAUTION(수동) 원장 검증 완료(2026-07-14). fsr perms 정합, gap 3→2·escalation 리셋. scope 불변·ops target 자동 미반영. 다음 판단: AC-05b/05c 또는 ≤8/14 |
| 익절·테제·비중 갭 점검 | `EXIT_WEIGHT_GAP_AUDIT_RESULT` — P0 확정 |
| CECS AI 배치 승인 | 고정 Markdown 요청서·업로드 파서·`ai_suggested` 저장·종목별 출처 확인 게이트·개별/배치 승인·감사 저널 구현 |
| 익절·테제 1차(가시성) | `EXIT_TAKEPROFIT_THESIS_RESULT` — assess_*+보드+빈 YAML. target 자동변경 없음. 목표가 기입·2차는 별도 승인 |
| 목표가 워크시트 | `KR_ALPHA_EXIT_TARGET_WORKSHEET_RESULT` — 원장 검증 완료. yaml 목표치는 아래 「exit targets 기입」 |
| exit targets 기입 | `kr_alpha_exit_targets.yaml` 7종(KT·코웨이·DB손보·동원·오리온·SNT·현대GF) 기계적 초안 반영(2026-07-15). 000660 의도적 미설정. assess_take_profit: 7종 targets_missing=False·전부 Hold/NONE. 보드 CSV는 **전체 분석 재실행** 후 UI 반영 |
| target write 03:53 조사 | `TARGET_WRITE_AUDIT_20260715_INVESTIGATION_RESULT` — 원장 본인 승인 확인·종결 |
| 익절 보드 대시보드 | `ALPHA_SIGNAL_BOARD_DASHBOARD_EXPOSURE_RESULT` — 알파→보유 리뷰만 (⑥·Target 승인 노출 되돌림) |
| Gap 표 익절 참고 | `GAP_TABLE_EXIT_SIGNAL_REFERENCE_RESULT` — Gap에 익절상태(+근접도 접미사) |
| 익절 목표 근접도 | `EXIT_TARGET_PROXIMITY_RESULT` — 미도달 시 VAL/FUND % 근접 표시(확률 아님). 보드 재생성 완료 |
| 익절 표 범례 | `EXIT_SIGNAL_TABLE_LEGEND_RESULT` — 보유 리뷰 범례+Gap 한 줄 안내(표시만) |
| 익절 목표 제안규칙 | `EXIT_TARGET_SUGGESTION_RULE_RESULT` — 워크시트 suggested_* (role+ROE). target_*/yaml 자동기입 없음 |
| cleanup phase 0 | `CODEBASE_CLEANUP_PHASE_0_RESULT` — `alpha_v0_2` archive 완료·원장 검증 종결 (2026-07-15) |
| cleanup phase 1 | `CODEBASE_CLEANUP_PHASE_1_RESULT` — value_list archive · 원장 라이브 검증 종결(2026-07-15 20:34 log / daily_report disabled 문구). **종결** |
| cleanup phase 2 | `CODEBASE_CLEANUP_PHASE_2_RESULT` — alpha_v2·alpha_flow archive 원장 검증 종결(2026-07-15). 커밋 `548effa`. **종결** |
| 경제 나침반 0·1 | `ECONOMIC_COMPASS_PHASE_0_1_RESULT` — 원장 검증 종결(2026-07-16). tilt×0.4 실증·히스테리시스는 override 없는 날 관찰 지속. **종결** |
| target write 추적성 | `TARGET_WRITE_AUDIT_TRACEABILITY_FIX_RESULT` — 원장 검증 완료(2026-07-15). material=21·승인자 필수·writer_module·toast. 건 종결 |
| 익절 목표상태 마커 | `EXIT_TARGET_STATUS_MARKER_RESULT` — 원장 검증 완료(2026-07-15). name 다음 ⚠️/✅·배너·target_* 공란. 건 종결 |
| 정량+주간정성 재설계 | scoreboard=`alpha_scores`·proposal/ops 북 분리·CECS final 보호·`run_alpha_quant_snapshot`·주간 A~E 요청서/영역별 게이트·`WEEKLY_QUAL_REPORT_SPEC` (2026-07-17) |
| 홈·수집·승인 단순화 | 홈=`자동 준비 2칸 + 지금 할 일 1건 + 제안 결과 + 접힌 운용`; 정량 전체 갱신 1클릭; 정성 1파일·승인판 1화면 (2026-07-17) |
| 결재함 전용 UI | 메뉴=`홈·결재함·포트폴리오·저널`. CECS/T2/논지/저널 직접기입 제거. 수집→출처확인→영역별승인만 (`approval.py`, 2026-07-17) |
| 편입 수·컷오프 연동 | 철학 정합 복원: **절대 cutoff 먼저 → 편입 수 5~8(기본 6)**. 6~30 상대순위 슬라이더는 설계 충돌로 철회. target 자동 변경 없음 (2026-07-18) |
| 최종선정 갭보완 | 절대 cutoff → 섹터당≤2(`sector_group`) → 5~8. 목표가 없으면 대기후보·편입 차단(다음 주 E). B/E는 proposal만(CECS fallback 제거) (2026-07-18) |
| 안정판 저장 | 커밋 `614a87c` + 태그 `stable-20260718-final-selection`. 검증 문서 `ALPHA_FINAL_SELECTION_HARDENING_RESULT`(Claude 재검증용). focused 37 passed (2026-07-18) |
| cleanup A+C | 상대순위 슬라이더 제거(포트폴리오 절대컷만). 죽은 페이지·디버그 스크립트 → `archive/20260718_*`. `CODEBASE_CLEANUP_AC_20260718_RESULT` (2026-07-18) |
| cleanup B+D | 대체 API(AI검증·CECS writer·save_cecs_score) + 일회성 스크립트 8개 archive. `CODEBASE_CLEANUP_BD_20260718_RESULT` (2026-07-18) |
| Claude 검수 브리프 | `docs/CLAUDE_REVIEW_BRIEF_20260718.md` — P0 하드닝·P1 cleanup 잔재·불변규칙. 외부 Claude 붙여넣기용 (2026-07-18) |
| 검수 채택 3건 반영 | provisional 배지(빈점수→50) · deep_tickers fail-closed · entry 목표가 게이트 SoT 일원화 (`missing_entry_target_tickers`) (2026-07-18) |
| 목표가 대기 보충 | E-only 요청서·업로드 병합·결재함 탭3. 섹터 캡(≤2)·스타일 인원캡 없음 — **변경 없음** (2026-07-18) |
| E 업로드 계약 고정 | 요청서에 `_reference`/`_____`/값줄 주석 금지·완성 예 명시. 파서 실패 메시지 구체화 (2026-07-19) |
| 홈 주기·신선도 경고 | 판단용 데이터 노후 시 홈 경고+해당 메뉴 이동. 주기 갱신 안내 expander (2026-07-19) |
| UI 타이포·계층 | 전 메뉴 제목/카드/탭/expander 가독성 강화 (`styles.py`). IA·큰틀 유지 (2026-07-19) |
| **v2 분리·분할매수 승인** | 등급업은 `C:\Cursor\investment-saa-alpha-v2`. 분할매수 규칙 **승인(2026-07-19)** — v1은 유지판 |

### Alpha BT 라벨 — 검증 완료 (2026-07-14, 옵션 a 종료)

- 독립 검증: 코드/csv/report/테스트 일치. `scored_days_used=10`, `price_history_days=270`, `sample_quality=insufficient`.
- 수익률·quintile 수치(excess -8.26% / net -8.79% 등)는 **재계산 없음·재생성만** — 계산 로직 불변 확인.
- `insufficient` = 시스템 스스로 「예측력 판단 불가」. 넷초과·quintile 역전은 **스코어링 버그 증거가 아니라 표본 부족으로 무의미**.
- **옵션 (b)** (과거 분기별 발표시점 재무 히스토리 구축)는 **후순위** — dry-run 완료 · policy_cap · 레짐 divergence 해소가 먼저.

### 열린 항목 (짧게 · 우선순위)

1. dry-run / policy_cap(~2026-09-24) / Actual Buy — 의도된 대기·운영자 판단
2. CAUTION 재검토 — AC-05b/AC-05c 또는 **≤2026-08-14**; kr_alpha TAA vs ops는 사람 승인 시에만
3. **경제 나침반** — (a) Turbulence 게이트 WAIT **25/60행**. (b) 방법 B 백테스트 완료(`METHOD_B_RESULT`) — excess DSR 비유의·MDD 개선만. 임계값 미변경
4. **익절·테제 P0** — yaml 7종 초안·로직 검증 완료. 2차(실행 연동) 미승인
5. **스크린→객관 6종 (정책 B)** — UI proposal_book = dry CLI 동일 경로(`select_eligible`+섹터 캡). 주간 정성 승인 후 운영. target 자동쓰기 금지
6. **주간 정성 운영** — 금 요청서 → 주말 작성 → 월 영역별 승인. B/E=현재 proposal만. 목표가 대기는 E 보충(탭3)으로 채운 뒤 승인·편입
7. ~~객관 고점수·섹터분산~~ — `max_names_per_sector=2` + shortfall 반영 완료 (2026-07-18). 스타일(Q/V) 인원캡 없음 — 추가 변경 불필요
8. (후순위) Alpha BT 옵션 b — PIT 재무 히스토리 · QVM-SR 유효성 검증
9. ~~목표가 대기 보충~~ — E-only 생성·병합·UI 탭3 완료 (2026-07-18)
---

## 0. 한 줄 운영 원칙

| 구분 | 의미 | 현재 기본 |
|------|------|-----------|
| **Executable** | 계좌에서 실제로 해도 시스템과 맞는 액션 | ETF·현금·채권 (scope 허용 시) |
| **Research / Review-only** | 참고·사람 승인만 | kr_alpha, 하케다카, 수급(FASTJUSIK류) |
| **제안 포트** | `alpha_portfolio_proposal` 순위 | `proposal_mode: pure_qvm` |
| **승인 포트** | `data/target_portfolio.csv` | **사람만** 변경 (자동 금지) |

실투자: **ETF executable**, **개별주/하케다카/수급은 Review-only** 유지.

---

## 1. 불변 규칙 (AC-HK + 실행 분리)

상세: [`HAKEDAKA_ACCEPTANCE.md`](HAKEDAKA_ACCEPTANCE.md), [`HAKEDAKA_KR_ALPHA_POLICY.md`](HAKEDAKA_KR_ALPHA_POLICY.md)

| ID | 규칙 |
|----|------|
| AC-HK-01 | `liquidity_pass=false` → 제안 포트 편입 불가 |
| AC-HK-02 | `hard_slot_enabled=false` — 하케다카만으로 편입 불가 |
| AC-HK-05 | `shadow_slot_candidate`는 표시용 — target 자동 변경 없음 |
| AC-HK-06 | sector / single-name / kr_alpha cap 항상 우선 |
| 실행 | `ETF_ONLY` 등일 때 kr_alpha는 **Review-only** (`execution_scope.py`) |
| 유동성 | `liquidity_bypass_for_proposal: false` — 우회 금지 |
| tie-breaker | 기본 OFF. shadow 2~4주 관찰 후에만 `qvm_with_tiebreaker` 검토 |

`data/hakedaka_integration.yaml` 핵심 기본값:

```yaml
proposal_mode: pure_qvm
hakedaka_tiebreaker_enabled: false
liquidity_bypass_for_proposal: false
hard_slot_enabled: false
shadow_slot_candidate_enabled: true
```

---

## 2. 프로젝트·경로 맵

| 이름 | 경로 | 역할 |
|------|------|------|
| **현재 본체** | `C:\Cursor\investment-saa-alpha` | 나침반 + SAA/TAA + 알파 + UI |
| CECS 스크리너 | `investment-saa-alpha/alpha_portfolio` | QVM 하위 패키지 |
| 구 폴더 | `C:\Cursor\multi_asset_trigger_portfolio` | 레거시(있으면 참고만, 작업은 saa-alpha에서) |
| UI 진입 | `투자나침반.bat` / `streamlit run app.py` | |

파이프라인 대략 순서: **나침반 → 하케다카 DART → 알파 → 리서치/오버레이 → acceptance**

---

## 3. 하케다카 연동 (이미 구현된 것)

| 영역 | 파일 / 산출물 |
|------|----------------|
| DART 공시 | `src/value_list/dart_disclosure.py` |
| DART 검증 | `outputs/hakedaka_dart_verification.csv` |
| overlap 진단 | `outputs/hakedaka_overlap_diagnostics.csv` |
| 우선 검토 | `outputs/hakedaka_priority_review.csv` |
| 알파 브릿지 | `src/value_list/alpha_bridge.py` |
| SAA/TAA 오버레이 | `src/value_list/compass_overlay.py` |
| 수용 테스트 | `tests/test_hakedaka_acceptance.py` |

**정책 합의:** 최종 제안 포트에 하케다카 **강제 편입 비추**. soft preference / shadow만.  
overlap이 적을 수 있음 → 버그 아님 (유동성·시총·pillar 탈락이 대부분).

---

## 4. FASTJUSIK (`fastjusik.com/pension`) — 레퍼런스만

| 할 것 | 하지 말 것 |
|-------|------------|
| KRX / PyKRX로 동일 지표 직접 계산 | 사이트 스크래핑 |
| 수급은 **shadow / Signal Board / 승인 탭** | 수급만으로 proposal 편입 |
| `institution_*` = 기관 proxy (연기금 100% 아님 명시) | HTS「기관계」=「연기금」동일시 |

### FASTJUSIK → 프로그램 매핑

| FASTJUSIK | 프로그램 | 상태 |
|-----------|----------|------|
| 당일 순매수/매도 | `investor_flows` / institutional flow | 부분 구현 |
| 연속 수급 | streak | `alpha_v2`/`alpha_flow`는 `archive/20260715_*`로 격리(2026-07-15). v1 `investor_flows`·신호보드 경로는 유지 |
| 외국인 동반 | foreign+institution 부호 일치 | 확장/표시 |
| 방향 전환 | 연속 후 반전 | 확장/표시 |
| NPS 5% 보유 | DART 대량보유 | 선택 확장 |
| 경제지표 | compass / market_indicators | 이미 있음 |

**원칙:** FASTJUSIK는 「누가 사고 있나」 참고, 시스템은 「사도 되나」(QVM·유동성·Scope).

---

## 5. Executable vs Research (실투자 기준)

**해도 됨 (조건 충족 시)**  
- Executable 섹션 ETF/현금/채권  
- 데이터 최신 + 트리거 + 본인 승인  

**하면 안 됨 (시스템과 불일치)**  
- kr_alpha 신규·Replace를 Executable처럼 실행  
- 하케다카·수급 단독으로 target 자동 변경  
- dry-run 미충족인데 실운용 자동 승인으로 간주  

리포트는 **Executable** / **Review-only** 섹션을 섞지 말 것.

---

## 6. UI·운용 합의

- 사용법 탭, 상태 배너, 대시보드에 executable 요약  
- Target 승인 UI만 `target_portfolio` 변경  
- 하케다카 탭: diagnostics + shadow 후보 (강제 슬롯 아님)  
- 수급: Target 승인 / 하케다카에 「기관 수급」 우선 노출 (표시만)

---

## 7. 미완료 / 다음 작업 (레거시 채팅 기준)

당시 합의된 다음 스텝 (saa-alpha에서 이미 일부 구현됐을 수 있음 — **코드 대조 후** 진행):

1. `investor_flows_history` append + streak/동반/전환  
2. diagnostics·signal board에 shadow 플래그만 병합 (`flow_role: shadow_only`)  
3. Target 승인 「수급 우선 검토」 UI  
4. (선택) DART NPS 5%  
5. shadow 2~4주 후 tie-breaker A/B — yaml만, AC-HK 유지  

구현 시 **proposal_mode=pure_qvm** 기본 유지.

---

## 8. 관련 문서 (우선 읽기 순서)

1. 이 파일 (`CHAT_HANDOFF_LEGACY_MULTI_ASSET.md`)  
2. [`HAKEDAKA_ACCEPTANCE.md`](HAKEDAKA_ACCEPTANCE.md)  
3. [`HAKEDAKA_KR_ALPHA_POLICY.md`](HAKEDAKA_KR_ALPHA_POLICY.md)  
4. [`RUN_MODE_POLICY.md`](RUN_MODE_POLICY.md)  
5. [`USER_GUIDE.md`](USER_GUIDE.md)  
6. [`ACCEPTANCE_CRITERIA.md`](ACCEPTANCE_CRITERIA.md)  

검증 스크립트(경로가 구 폴더를 가리키면 saa-alpha로 바꿔 실행):

```powershell
cd C:\Cursor\investment-saa-alpha
pytest tests/test_hakedaka_acceptance.py -q
```

---

## 9. 구 채팅 삭제 여부

- **코드·이 문서가 saa-alpha에 있으면** 구 `C:\Cursor` / multi_asset / 단발 조사 채팅은 삭제해도 됨.  
- 삭제 시 잃는 것: 대화 원문만. 결정은 이 핸드오프 + `docs/*_RESULT.md`로 승계됨.
- **남길 채팅:** 제목 `SAA 알파 투자` 하나. (위 §0b)
