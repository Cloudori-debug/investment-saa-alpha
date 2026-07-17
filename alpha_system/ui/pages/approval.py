"""결재함 — 자동 수집 결과 검토·영역별 승인만 (직접 점수/이벤트 기입 없음)."""

from __future__ import annotations

import streamlit as st

from alpha_system.ui.pages import events, rules, scores
from alpha_system.ui.services.context import DashboardContext
from alpha_system.ui.services.nav import (
    FOCUS_CECS_SCORE,
    FOCUS_DATA_REFRESH,
    FOCUS_GO_LIVE,
    FOCUS_RULES_PREFIX,
    FOCUS_SCORES,
    FOCUS_T2,
    FOCUS_T3_DETAIL,
    FOCUS_WEEKLY_QUAL,
    consume_focus,
)


def render_approval(ctx: DashboardContext) -> None:
    focus = consume_focus()

    st.subheader("결재함")
    st.caption(
        "정량·정성 수집 결과를 검토하고, 출처 확인 후 영역별로만 승인합니다. "
        "점수·이벤트·논지를 직접 기입하는 화면은 없습니다."
    )

    weekly_focus = focus in {
        FOCUS_WEEKLY_QUAL,
        FOCUS_T2,
        FOCUS_CECS_SCORE,
    }
    quant_focus = focus in {FOCUS_DATA_REFRESH, FOCUS_SCORES, FOCUS_T3_DETAIL}
    live_focus = focus == FOCUS_GO_LIVE or (
        bool(focus) and str(focus).startswith(FOCUS_RULES_PREFIX)
    )

    tab_weekly, tab_quant, tab_live = st.tabs(
        ["주간 정성 승인", "정량·스코어", "가동·체크리스트"]
    )

    with tab_weekly:
        if weekly_focus:
            st.info("홈/체크리스트에서 연결됨 — 출처 확인 후 해당 영역만 승인하세요.")
        events._render_weekly_qual(ctx, focused=weekly_focus)

    with tab_quant:
        if focus == FOCUS_DATA_REFRESH:
            st.info("정량 스냅샷 갱신 섹션입니다.")
        st.markdown("#### 정량 전체 갱신")
        events._render_data_refresh(ctx)
        st.divider()
        if focus == FOCUS_T3_DETAIL:
            st.info("T3 판정 상세입니다.")
        events._render_t3_detail(ctx)
        st.divider()
        st.markdown("#### 스코어보드 (조회)")
        if focus == FOCUS_SCORES:
            st.info("스코어 검토용 조회 화면입니다.")
        scores.render_scores(ctx)

    with tab_live:
        if live_focus:
            st.info("가동 선언·체크리스트 구간입니다.")
        events._render_go_live(ctx, expand=(focus == FOCUS_GO_LIVE))
        st.divider()
        with st.expander("규칙·체크리스트 (읽기 전용)", expanded=live_focus):
            # rules.render_rules consumes nav_focus; restore tranche deep-link.
            if focus and str(focus).startswith(FOCUS_RULES_PREFIX):
                st.session_state["nav_focus"] = focus
            rules.render_rules(ctx)
