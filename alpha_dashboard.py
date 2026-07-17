"""
알파 시스템 대시보드 — Streamlit 단일 앱 (모바일 우선).

실행:
  streamlit run alpha_dashboard.py --server.address 0.0.0.0

같은 Wi-Fi의 폰에서 http://<PC-IP>:8501 로 접속.
외부 인터넷에 포트를 열지 마세요 (보안).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from alpha_system.ui.pages import approval, home, journal, portfolio
from alpha_system.ui.services.context import load_context
from alpha_system.ui.services.nav import (
    PAGE_APPROVAL,
    PAGE_HOME,
    PAGE_JOURNAL,
    PAGE_PORTFOLIO,
    PRIMARY_PAGES,
    apply_pending_page,
    normalize_page_label,
)
from alpha_system.ui.styles import inject_dashboard_styles

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="알파 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "compact_mode" not in st.session_state:
    st.session_state["compact_mode"] = False
if "alpha_page" not in st.session_state:
    st.session_state["alpha_page"] = PAGE_HOME
else:
    st.session_state["alpha_page"] = normalize_page_label(
        st.session_state.get("alpha_page")
    )

apply_pending_page()

with st.sidebar:
    st.markdown("**레이아웃**")
    st.toggle(
        "컴팩트 모드 (모바일 1열)",
        key="compact_mode",
        help="켜면 본문 폭을 좁혀 모바일 1열 레이아웃을 강제합니다.",
    )

inject_dashboard_styles(compact=bool(st.session_state.get("compact_mode")))

PAGES = {
    PAGE_HOME: home.render_home,
    PAGE_APPROVAL: approval.render_approval,
    PAGE_PORTFOLIO: portfolio.render_portfolio,
    PAGE_JOURNAL: journal.render_journal,
}

st.markdown("### 알파 시스템")

page = st.radio(
    "화면",
    list(PRIMARY_PAGES),
    horizontal=True,
    label_visibility="collapsed",
    key="alpha_page",
)

try:
    ctx = load_context(ROOT)
except Exception as exc:
    st.error(f"컨텍스트 로드 실패: {exc}")
    st.stop()

PAGES[page](ctx)

st.caption(
    f"as_of {ctx.as_of.isoformat()} · 결재·조회 우선 · "
    "target_portfolio 자동 변경 없음"
)
