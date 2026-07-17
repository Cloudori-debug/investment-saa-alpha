"""Alpha dashboard home — preparation, one action, result, folded operations."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

import streamlit as st

from alpha_system.entry.models import TrancheState
from alpha_system.ui.services.action_panels import open_panel, render_active_panel
from alpha_system.ui.services.context import DashboardContext
from alpha_system.ui.services.home_pipeline import (
    HomeOverview,
    PipelineStage,
    build_home_overview,
)
from alpha_system.ui.services.judgment_copy import explain_tranche
from alpha_system.ui.services.nav import (
    FOCUS_DATA_REFRESH,
    FOCUS_JOURNAL_DISC,
    FOCUS_RULES_PREFIX,
    FOCUS_T3_DETAIL,
    FOCUS_WEEKLY_QUAL,
    PAGE_APPROVAL,
    PAGE_JOURNAL,
    navigate,
)
from alpha_system.ui.services.ui_copy import copy_get, format_tranche_label, tranche_display
from alpha_system.ui.styles import status_card_class


def _state_level(state: TrancheState, *, pre_launch: bool, data_unknown: bool = False) -> str:
    if pre_launch:
        return "muted"
    if data_unknown:
        return "muted"
    if state in (TrancheState.EXECUTED, TrancheState.PARTIAL_EXECUTED):
        return "ok"
    if state == TrancheState.READY:
        return "warn"
    if state in (TrancheState.FROZEN, TrancheState.EXPIRED):
        return "danger"
    return "muted"


def _state_label(state: TrancheState, *, pre_launch: bool) -> str:
    if pre_launch:
        return "잠김"
    mapping = {
        TrancheState.EXECUTED: "집행완료",
        TrancheState.PARTIAL_EXECUTED: "부분집행",
        TrancheState.READY: "대기",
        TrancheState.PENDING: "대기",
        TrancheState.FROZEN: "동결",
        TrancheState.EXPIRED: "소멸",
    }
    return mapping.get(state, state.value)


def _open_tranche(ctx: DashboardContext, tid: str) -> None:
    if tid == "T2":
        navigate(PAGE_APPROVAL, focus=FOCUS_WEEKLY_QUAL)
        return
    if tid == "T3":
        hist = ctx.root / "data" / "kospi_market_pbr_history.csv"
        if hist.exists() and ctx.t3_pbr.available:
            navigate(PAGE_APPROVAL, focus=FOCUS_T3_DETAIL)
        else:
            navigate(PAGE_APPROVAL, focus=FOCUS_DATA_REFRESH)
        return
    navigate(PAGE_APPROVAL, focus=f"{FOCUS_RULES_PREFIX}{tid}")


def _open_stage(stage: PipelineStage) -> None:
    navigate(stage.page, focus=stage.focus, prefill=stage.prefill)


def _next_judgment_hint(ctx: DashboardContext) -> str:
    as_of = ctx.as_of
    if as_of >= ctx.window_end:
        return f"논지 창 종료 ({ctx.window_end.isoformat()})"
    last = monthrange(as_of.year, as_of.month)[1]
    month_end = date(as_of.year, as_of.month, last)
    if as_of < month_end:
        return f"T3 {as_of.month}월 말"
    if as_of.month == 12:
        return "T3 1월 말"
    return f"T3 {as_of.month + 1}월 말"


def _render_preparation(overview: HomeOverview) -> None:
    st.subheader("자동 준비")
    st.caption("정량과 정성을 독립적으로 확인합니다. 정상 항목은 조작할 필요가 없습니다.")
    cols = st.columns(len(overview.preparation))
    for col, item in zip(cols, overview.preparation):
        with col:
            level = "ok" if item.status == "ok" else (
                "warn" if item.status == "warn" else "muted"
            )
            label = {
                "ok": "준비",
                "warn": "확인 필요",
                "missing": "미수집",
            }.get(item.status, item.status)
            st.markdown(
                f'<div class="{status_card_class(level)}">'
                f"<strong>{item.title}</strong> — {label}<br/>"
                f"<small>{item.summary}</small></div>",
                unsafe_allow_html=True,
            )


def _render_next_action(ctx: DashboardContext, overview: HomeOverview) -> None:
    action = overview.next_action
    st.subheader("지금 할 일")
    if action is None:
        st.markdown(
            '<div class="alpha-empty-queue"><strong>'
            "추가 판단 없음 — 제안 결과를 확인하세요."
            "</strong></div>",
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        f'<div class="alpha-action-item"><strong>{action.title}</strong><br/>'
        f"{action.reason}</div>",
        unsafe_allow_html=True,
    )
    clicked = st.button(
        action.cta_label,
        type="primary",
        key="home_next_action",
        use_container_width=True,
    )
    if not clicked:
        return
    if action.key == "quant":
        from alpha_system.ui.services.auto_journal import journal_data_refresh
        from alpha_system.ui.services.refresh import run_quant_snapshot_refresh

        with st.spinner("PyKRX·DART 수집과 alpha_scores 재계산 중…"):
            result = run_quant_snapshot_refresh(ctx.root, collect_scope="liquid")
        journal_data_refresh(
            as_of=date.today(),
            ok=result.ok,
            message=result.message,
            detail=result.detail,
        )
        if result.ok:
            ctx.runtime.touch_refresh("alpha_quant_snapshot")
            ctx.runtime.save(ctx.root / "data" / "alpha_dashboard_runtime.json")
            st.success(result.message)
            st.rerun()
        st.error(result.message)
        with st.expander("실패 상세"):
            st.json(result.detail)
    else:
        _open_stage(action)


def _render_proposal_result(ctx: DashboardContext, overview: HomeOverview) -> None:
    st.subheader("제안 결과")
    if not ctx.portfolio_rows:
        st.info(
            "proposal_book 생성 대기 — 위 「지금 할 일」을 완료하면 자동 재평가됩니다."
        )
        return
    st.caption(
        f"proposal_book {overview.proposal_count}종 · 검토용 · 매입 지시 아님 · "
        "target_portfolio 자동 변경 없음"
    )
    from alpha_system.ui.services.portfolio_widgets import render_portfolio_bullets

    render_portfolio_bullets(ctx, mode="summary", key_prefix="pf_home")


def _render_tranche_card(
    ctx: DashboardContext,
    st_status,
    *,
    blocker: PipelineStage | None,
    key_suffix: str = "",
) -> None:
    tid = (
        st_status.tranche_id.value
        if hasattr(st_status.tranche_id, "value")
        else str(st_status.tranche_id)
    )
    label = format_tranche_label(tid)
    _, short_desc = tranche_display(tid)
    judgment = explain_tranche(st_status, pre_launch=ctx.pre_launch)
    data_unknown = (not judgment.mapped) or (
        "판단할 수 없" in judgment.headline or "데이터가 없어" in judgment.headline
    )
    level = _state_level(
        st_status.state, pre_launch=ctx.pre_launch, data_unknown=data_unknown
    )

    if ctx.pre_launch and blocker is not None:
        headline = (
            f"잠긴 이유: 가동 전 — 선행 단계 「{blocker.step}. {blocker.title}」미해결. "
            f"{blocker.reason}"
        )
        next_line = f"해결: {blocker.cta_label}"
    else:
        headline = judgment.headline
        next_line = judgment.next_check

    st.markdown(
        f'<div class="{status_card_class(level)}">'
        f"<strong>{label}</strong> — {_state_label(st_status.state, pre_launch=ctx.pre_launch)}<br/>"
        f"<small>{short_desc}</small><br/>"
        f"<em>시스템은 지금 이렇게 판단 중</em><br/>"
        f"{headline}"
        + (f"<br/><small>{next_line}</small>" if next_line else "")
        + "</div>",
        unsafe_allow_html=True,
    )
    if ctx.pre_launch and blocker is not None:
        if st.button("해결하러 가기", key=f"tr_fix_{tid}{key_suffix}"):
            _open_stage(blocker)
    elif st.button("자세히", key=f"tr_open_{tid}{key_suffix}"):
        _open_tranche(ctx, tid)
    if not judgment.mapped and judgment.raw_detail:
        with st.expander("원문 상세", expanded=False):
            st.code(judgment.raw_detail)


def render_home(ctx: DashboardContext) -> None:
    frozen = ctx.runtime.effective_thesis_damage()
    past_window = ctx.as_of >= ctx.window_end
    overview = build_home_overview(ctx)
    blocker = overview.next_action

    # Critical system banners only (not checklist spam)
    if frozen:
        st.markdown(
            f'<div class="alpha-banner-danger"><strong>'
            f'{copy_get("system_states", "FROZEN", "banner")}'
            f"</strong><br/>{copy_get('system_states', 'FROZEN', 'banner_detail')}</div>",
            unsafe_allow_html=True,
        )
    elif past_window:
        st.markdown(
            f'<div class="alpha-banner-danger"><strong>'
            f'{copy_get("system_states", "WINDOW_END", "banner")}'
            f"</strong><br/>{copy_get('system_states', 'WINDOW_END', 'banner_detail')}</div>",
            unsafe_allow_html=True,
        )
    elif ctx.effective_go_live is not None:
        st.caption(
            copy_get(
                "system_states",
                "LIVE",
                "banner",
                go_live_date=ctx.effective_go_live.isoformat(),
            )
        )

    _render_preparation(overview)
    _render_next_action(ctx, overview)
    _render_proposal_result(ctx, overview)

    with st.expander("운용 상태 · 트랜치 · 데이터 상세", expanded=False):
        m1, m2, m3 = st.columns(3)
        m1.metric("집행률", f"{ctx.execution_rate_pct or 0}%")
        m2.metric(
            "제안/보유/목표",
            f"{overview.proposal_count} / {ctx.held_kr_alpha} / {ctx.target_kr_alpha}",
        )
        with m3:
            st.metric("재량 이탈 누적", ctx.discretionary_count)
            if st.button("재량 이탈 보기", key="home_disc"):
                navigate(PAGE_JOURNAL, focus=FOCUS_JOURNAL_DISC)

        if not ctx.pre_launch:
            st.markdown("#### 액션 큐")
            if ctx.action_queue:
                for item in ctx.action_queue:
                    badge = {
                        "danger": "alpha-badge-danger",
                        "warn": "alpha-badge-warn",
                        "info": "alpha-badge-ok",
                    }.get(item.severity.value, "alpha-badge-warn")
                    cols = st.columns([5, 1])
                    with cols[0]:
                        st.markdown(
                            f'<div class="alpha-action-item"><span class="{badge}">'
                            f"{item.severity.value}</span> <strong>{item.title}</strong>"
                            f"<br/>{item.detail}</div>",
                            unsafe_allow_html=True,
                        )
                    with cols[1]:
                        if st.button("열기", key=f"aq_{item.key}"):
                            open_panel(item.key)
            else:
                st.caption(f"오늘 할 일 없음 — 다음 판정: {_next_judgment_hint(ctx)}")
            render_active_panel(ctx)

        st.markdown("#### 트랜치")
        statuses = list(ctx.entry_eval.statuses)
        for row in range(0, len(statuses), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = row + j
                if idx >= len(statuses):
                    break
                with col:
                    _render_tranche_card(ctx, statuses[idx], blocker=blocker)

        days_left = (ctx.window_end - ctx.as_of).days
        st.caption(f"window_end {ctx.window_end.isoformat()} — D-{max(0, days_left)}")

        st.markdown("#### 데이터 상세")
        for src in ctx.source_status:
            stale_badge = (
                '<span class="alpha-badge-danger">갱신 필요</span>'
                if src.stale
                else '<span class="alpha-badge-ok">정상</span>'
            )
            as_of_s = src.as_of.isoformat() if src.as_of else "—"
            st.markdown(
                f"**{src.label}** {stale_badge} — as_of {as_of_s} "
                f"({src.path}) {src.detail}",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"**CECS 승인** — final {ctx.cecs_final_count} / {ctx.cecs_total}종"
        )
        st.markdown(f"**sector_peer_fallback** — {ctx.sector_peer_fallback_count}종")
        st.markdown(f"**gate_pass** — {ctx.gate_pass_count}종")
