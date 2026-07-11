from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.ui.helpers import load_markdown, load_output_csv, load_output_json

STATUS_ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
from src.ui.pillar_display import render_pillar_tabs


def _render_checklist(
    data_dir: Path,
    output_dir: Path,
    gpt_ctx: dict,
    candidates: pd.DataFrame | None,
    holdings: pd.DataFrame | None,
) -> None:
    from src.alpha.approval_checklist import build_approval_checklist, checklist_blocking, checklist_summary
    from src.alpha.target_bridge import kr_alpha_target_sum, load_kr_alpha_budget
    from src.data_loader import load_target_portfolio

    current = load_target_portfolio(data_dir / "target_portfolio.csv")
    kr_sum = kr_alpha_target_sum(current)
    budget = load_kr_alpha_budget(output_dir)
    cand_n = len(candidates) if candidates is not None else 0
    replace_n = trim_n = 0
    if holdings is not None and not holdings.empty:
        replace_n = int((holdings["review_action"] == "REPLACE_CANDIDATE").sum())
        trim_n = int((holdings["review_action"] == "TRIM").sum())

    items = build_approval_checklist(
        gpt_ctx,
        candidate_count=cand_n,
        kr_alpha_target_sum=kr_sum,
        kr_alpha_budget=budget,
        replace_count=replace_n,
        trim_count=trim_n,
    )
    summary = checklist_summary(items)
    c1, c2, c3 = st.columns(3)
    c1.metric("통과", summary["pass"])
    c2.metric("주의", summary["warn"])
    c3.metric("차단", summary["fail"])

    for item in items:
        icon = STATUS_ICON[item.status]
        if item.status == "fail":
            st.error(f"{icon} **{item.label}** — {item.detail}")
        elif item.status == "warn":
            st.warning(f"{icon} **{item.label}** — {item.detail}")
        else:
            st.success(f"{icon} **{item.label}** — {item.detail}")

    if checklist_blocking(items):
        st.error("차단 항목이 있습니다. Target 반영 전에 데이터·후보 상태를 확인하세요.")


def _render_target_approval_tab(
    data_dir: Path,
    output_dir: Path,
    candidates: pd.DataFrame | None,
    holdings: pd.DataFrame | None,
    port_proposal_df: pd.DataFrame | None,
) -> None:
    from src.alpha.target_bridge import (
        default_add_candidates,
        default_remove_candidates,
        default_trim_candidates,
        load_kr_alpha_budget,
        propose_target_changes,
        resolve_add_candidate,
        write_proposal_outputs,
    )
    from src.alpha.target_draft_bridge import (
        default_target_draft_path,
        enrich_target_changes_for_display,
        load_replace_pairs,
        load_target_changes,
        load_target_draft,
        merge_target_draft,
    )
    from src.data_loader import _normalize_ticker, load_target_portfolio
    from src.ui.table_display import (
        alpha_list_table_height,
        replace_pairs_column_config,
        show_dataframe_readable,
        target_approval_table_height,
        target_changes_column_config,
        target_proposal_diff_column_config,
    )

    st.subheader("Target 승인 · 반영")
    st.info(
        "operational target 변경은 **대시보드 Step ⑥** 또는 **이 Target 승인 탭**에서 "
        "동일하게 승인 반영할 수 있습니다. "
        "승인 시 target_write_audit 및 target_portfolio_guard를 통과해야 합니다. "
        "Actual Buy Allowed=0 또는 NO_TRADE 상태에서는 승인 후에도 신규매수가 허용되지 않을 수 있습니다."
    )

    draft_default = default_target_draft_path()
    with st.expander("alpha_portfolio target_draft 가져오기", expanded=draft_default.exists()):
        st.caption("alpha_portfolio `target_draft.csv` → kr_alpha 행만 merge (자동 덮어쓰기 없음)")
        draft_path = Path(st.text_input("target_draft 경로", value=str(draft_default), key="alpha_draft_path"))
        if draft_path.exists():
            try:
                draft_df = load_target_draft(draft_path)
                changes_df = load_target_changes(draft_path.parent / "target_changes.csv")
                pairs_df = load_replace_pairs(draft_path.parent / "replace_pairs.csv")
                st.markdown("**draft 목표**")
                show_dataframe_readable(draft_df, height=target_approval_table_height(len(draft_df)), key="alpha_draft_table")
                if not changes_df.empty:
                    st.markdown("**변경 로그**")
                    changes_view = enrich_target_changes_for_display(
                        changes_df,
                        draft_df=draft_df,
                        pairs_df=pairs_df,
                        data_dir=data_dir,
                    )
                    show_dataframe_readable(
                        changes_view,
                        column_config=target_changes_column_config(),
                        height=target_approval_table_height(len(changes_view)),
                        key="alpha_draft_changes",
                    )
                if not pairs_df.empty:
                    st.markdown("**Replace 매핑**")
                    st.caption(
                        "퇴출(exit) 종목 → 편입(candidate) 후보 1:1 교체 제안 · "
                        "rank = alpha 후보 순위 · reason = 편입 사유 (`replace_in for {퇴출티커}`)"
                    )
                    show_dataframe_readable(
                        pairs_df,
                        column_config=replace_pairs_column_config(),
                        height=target_approval_table_height(len(pairs_df)),
                        key="alpha_draft_pairs",
                    )
                budget_draft = load_kr_alpha_budget(output_dir)
                if st.button("📥 draft → 변경안 미리보기", key="alpha_draft_preview"):
                    proposal = merge_target_draft(
                        load_target_portfolio(data_dir / "target_portfolio.csv"),
                        draft_df,
                        kr_alpha_budget=budget_draft,
                        changes_df=changes_df if not changes_df.empty else None,
                    )
                    st.session_state["target_proposal"] = proposal
                    write_proposal_outputs(proposal, output_dir)
                    st.success("target_portfolio_proposed.csv 생성")
            except Exception as exc:
                st.error(str(exc))
        else:
            st.info(f"draft 없음: {draft_path}")

    st.divider()
    if candidates is None:
        candidates = pd.DataFrame()
    if holdings is None:
        holdings = pd.DataFrame()

    cand_rows = candidates.to_dict(orient="records") if not candidates.empty else []
    hold_rows = holdings.to_dict(orient="records") if not holdings.empty else []

    default_trims = default_trim_candidates(hold_rows)
    default_rems = default_remove_candidates(hold_rows)
    default_adds = default_add_candidates(
        cand_rows, limit=8, output_dir=output_dir, data_dir=data_dir,
    )
    default_add_tickers = {str(c["ticker"]) for c in default_adds}
    weight_by_ticker = {
        _normalize_ticker(str(c["ticker"])): float(c.get("target_weight", 2.5)) for c in default_adds
    }

    if port_proposal_df is not None and not port_proposal_df.empty:
        st.markdown("**시스템 포트 제안 (기본 선택)**")
        show_dataframe_readable(
            port_proposal_df,
            height=target_approval_table_height(len(port_proposal_df)),
            key="alpha_port_proposal",
        )

    priority_df = load_output_csv(output_dir, "hakedaka_priority_review.csv")
    diag_df = load_output_csv(output_dir, "hakedaka_overlap_diagnostics.csv")
    if priority_df is not None and not priority_df.empty:
        st.markdown("**⭐ 하케다카 우선 검토 (QVM 통과 + DART verified)**")
        st.caption("강제 편입 아님 — 승인 탭에서 우선 확인. 유동성 미통과는 제안 포트 불가.")
        show_dataframe_readable(
            priority_df,
            height=target_approval_table_height(len(priority_df)),
            key="alpha_hakedaka_priority",
        )
    elif diag_df is not None and not diag_df.empty:
        overlap = int(diag_df["in_shortlist"].astype(str).str.lower().eq("true").sum())
        st.caption(f"하케다카∩숏리스트 {overlap}종 — `hakedaka_overlap_diagnostics.csv`에서 원인 확인")

    st.markdown("**1. 보유 조정 (TRIM / REPLACE)**")
    trim_sel = st.multiselect(
        "TRIM (목표→min_weight)",
        options=sorted(default_trims | {str(h["ticker"]) for h in hold_rows}),
        default=sorted(default_trims),
        key="alpha_trim",
    )
    remove_sel = st.multiselect(
        "REMOVE / REPLACE (target에서 제거)",
        options=sorted(default_rems | {str(h["ticker"]) for h in hold_rows}),
        default=sorted(default_rems),
        key="alpha_remove",
    )

    st.markdown("**2. 신규 후보 추가**")
    buy_options = sorted(
        set(weight_by_ticker.keys())
        | {str(r["ticker"]) for r in cand_rows if r.get("eligible_action") in {"BUY_CANDIDATE", "WATCH"}}
    )
    add_sel = st.multiselect(
        "추가할 종목",
        options=buy_options,
        default=sorted(default_add_tickers & set(buy_options)),
        key="alpha_add",
    )
    new_weight = st.number_input("신규 기본 weight (%)", 0.5, 10.0, 2.5, 0.5, key="alpha_weight")

    add_payload = []
    name_pools = list(default_adds) + cand_rows + hold_rows
    if port_proposal_df is not None and not port_proposal_df.empty:
        name_pools.extend(port_proposal_df.to_dict(orient="records"))
    for ticker in add_sel:
        add_payload.append(
            resolve_add_candidate(
                ticker,
                data_dir=data_dir,
                pools=name_pools,
                default_new_weight=weight_by_ticker.get(_normalize_ticker(ticker), new_weight),
            )
        )
    budget = load_kr_alpha_budget(output_dir)
    if budget is not None:
        st.caption(f"Compass kr_alpha 예산: **{budget:.1f}%**")

    if st.button("📋 변경안 미리보기", type="primary", key="alpha_preview"):
        proposal = propose_target_changes(
            load_target_portfolio(data_dir / "target_portfolio.csv"),
            add_candidates=add_payload,
            trim_tickers=set(trim_sel),
            remove_tickers=set(remove_sel),
            kr_alpha_budget=budget,
            default_new_weight=new_weight,
            data_dir=data_dir,
        )
        st.session_state["target_proposal"] = proposal
        write_proposal_outputs(proposal, output_dir)

    proposal = st.session_state.get("target_proposal")
    if proposal:
        from src.ui.target_approval_actions import render_proposal_preview, render_target_approval_actions

        st.markdown("**3. 변경 diff**")
        render_proposal_preview(proposal, key_prefix="alpha")
        render_target_approval_actions(
            proposal,
            data_dir,
            output_dir,
            key_prefix="alpha",
            session_proposal_key="target_proposal",
        )


def render_alpha_page(data_dir: Path, output_dir: Path, *, focus: str | None = None) -> None:
    from src.ui.nav_shortcuts import (
        ALPHA_SUB_TAB_KEYS,
        ALPHA_SUB_TAB_LABELS,
        FOCUS_ALPHA_REVIEW,
        FOCUS_ALPHA_TARGET,
        FOCUS_TO_ALPHA_SUB_TAB,
        render_nav_hint,
    )
    from src.ui.table_display import alpha_list_table_height, show_dataframe_readable

    st.header("🔬 알파 — QVM-SR 스크리너")
    st.caption(
        "Q(30%) · V(25%) · M(20%) · SR(15%) · 6~8종 집중 · target 자동 덮어쓰기 없음"
    )

    if focus in FOCUS_TO_ALPHA_SUB_TAB:
        st.session_state["alpha_sub_tab_key"] = FOCUS_TO_ALPHA_SUB_TAB[focus]

    render_nav_hint(focus)

    with st.expander("QVM-SR 축 설명"):
        st.markdown(
            """
| 축 | 의미 |
|----|------|
| **Q** | Quality — ROE, 마진, FCF 등 |
| **V** | Valuation — PER, PBR, EV/EBITDA 등 |
| **M** | Momentum — 3/6/12M 수익률 |
| **SR** | Shareholder Return — 배당·FCF yield (Sharpe 아님) |
"""
        )

    gpt_ctx = load_output_json(output_dir, "gpt_context.json")
    candidates = load_output_csv(output_dir, "alpha_candidates.csv")
    holdings = load_output_csv(output_dir, "holdings_review.csv", dtype=str)
    shortlist = load_output_csv(output_dir, "alpha_shortlist.csv")
    port_proposal_df = load_output_csv(output_dir, "alpha_portfolio_proposal.csv")
    pillar_lb = load_output_csv(output_dir, "alpha_pillar_leaderboard.csv")
    excluded = load_output_csv(output_dir, "excluded.csv", dtype=str)

    if gpt_ctx is None:
        st.info("Alpha 출력 없음. 사이드바 **전체 분석 실행**을 먼저 실행하세요.")
        return

    meta = gpt_ctx.get("shortlist_meta") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("숏리스트 풀", meta.get("pool_size", len(candidates) if candidates is not None else 0))
    c2.metric("포트 제안", meta.get("proposal_size", len(port_proposal_df) if port_proposal_df is not None else 0))
    c3.metric("목표 보유", "6~8종")
    c4.metric("하케다카∩숏리스트", meta.get("hakedaka_in_shortlist", 0))

    active_key = str(st.session_state.get("alpha_sub_tab_key") or "shortlist")
    if active_key not in ALPHA_SUB_TAB_KEYS:
        active_key = "shortlist"
    active_idx = ALPHA_SUB_TAB_KEYS.index(active_key)

    selected_label = st.radio(
        "알파 섹션",
        list(ALPHA_SUB_TAB_LABELS),
        index=active_idx,
        horizontal=True,
        key="alpha_sub_tab_radio",
        label_visibility="collapsed",
    )
    active_key = ALPHA_SUB_TAB_KEYS[ALPHA_SUB_TAB_LABELS.index(selected_label)]
    st.session_state["alpha_sub_tab_key"] = active_key

    if active_key == "shortlist":
        st.subheader("축별 Top 10 · 투자 유효성")
        scored_n = meta.get("scored_count")
        if pillar_lb is not None and not pillar_lb.empty:
            render_pillar_tabs(pillar_lb, scored_count=scored_n)
        else:
            st.info("전체 분석 실행 후 `alpha_pillar_leaderboard.csv` 생성")

        if meta.get("pool_size", 0) <= 1:
            st.caption("숏리스트가 적으면 PyKRX liquid scope로 유니버스를 확장하세요 (alpha_portfolio).")

        st.subheader("QVM-SR 숏리스트 (종합 유효 후보)")
        if shortlist is not None and not shortlist.empty:
            cols = [
                c for c in (
                    "pool_rank", "ticker", "name", "sector",
                    "q_rank", "v_rank", "m_rank", "sr_rank", "pillars_pass",
                    "quality_score", "valuation_score", "momentum_score", "shareholder_return_score",
                    "total_score", "grade", "eligible_action",
                    "in_hakedaka", "hakedaka_grade", "dart_verified", "dart_signal",
                    "hakedaka_bonus", "hakedaka_priority",
                )
                if c in shortlist.columns
            ]
            show_dataframe_readable(
                shortlist[cols],
                height=alpha_list_table_height(len(shortlist)),
                key="alpha_shortlist",
            )
        elif candidates is not None and not candidates.empty:
            show_dataframe_readable(
                candidates,
                height=alpha_list_table_height(len(candidates)),
                key="alpha_candidates_fallback",
            )
        else:
            st.caption("숏리스트 없음")

        with st.expander("제외 종목", expanded=excluded is not None and not excluded.empty):
            if excluded is not None and not excluded.empty:
                show_dataframe_readable(
                    excluded,
                    height=alpha_list_table_height(len(excluded)),
                    key="alpha_excluded",
                )
            else:
                st.caption("제외 없음")

    elif active_key == "proposal":
        st.subheader("최종 포트 제안 (6~8종)")
        st.caption("섹터 cap · role(core/satellite/value) · Compass kr_alpha 예산 균등 배분")
        if port_proposal_df is not None and not port_proposal_df.empty:
            st.dataframe(port_proposal_df, use_container_width=True, height=320)
        else:
            st.info("전체 분석 실행 후 `alpha_portfolio_proposal.csv` 생성")

    elif active_key == "review":
        st.subheader("보유·목표 종목 리뷰")
        if holdings is not None and not holdings.empty:
            st.dataframe(holdings, use_container_width=True, height=320)
        else:
            st.caption("kr_alpha 보유 리뷰 없음")
        _render_checklist(data_dir, output_dir, gpt_ctx, candidates, holdings)

    elif active_key == "target":
        _render_target_approval_tab(
            data_dir, output_dir, candidates, holdings, port_proposal_df
        )

    elif active_key == "hakedaka":
        from src.ui.hakedaka_panel import render_hakedaka_panel

        render_hakedaka_panel(data_dir, output_dir)

    elif active_key == "report":
        report = load_markdown(output_dir, "alpha_report.md")
        if report:
            st.markdown(report)
        else:
            st.caption("alpha_report.md 없음")

    elif active_key == "flow":
        from src.ui.flow_status_panel import render_flow_status_tab

        render_flow_status_tab(data_dir, output_dir)
