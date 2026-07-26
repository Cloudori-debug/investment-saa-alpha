"""Mobile-first Streamlit styles — semantic status colors + clear type hierarchy."""

from __future__ import annotations

import streamlit as st


def inject_dashboard_styles(*, compact: bool = False) -> None:
    compact_css = ""
    if compact:
        compact_css = """
[data-testid="stAppViewContainer"] .main .block-container {
  max-width: 480px !important;
}
"""
    st.markdown(
        f"""
<style>
/* —— App chrome (top nav) —— */
.alpha-app-title {{
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #111827;
  margin: 0 0 0.55rem 0;
  padding-bottom: 0.4rem;
  border-bottom: 2px solid #111827;
}}
div[role="radiogroup"] label {{
  font-size: 0.9rem !important;
  font-weight: 650 !important;
}}
div[role="radiogroup"] label p {{
  font-size: 0.9rem !important;
  font-weight: 650 !important;
}}
[data-testid="stAppViewContainer"] .main .block-container {{
  padding-top: 0.85rem;
  padding-bottom: 2.25rem;
  max-width: 720px;
}}

/* —— Typography scale (page → section → body → muted) —— */
.main h1,
.main [data-testid="stHeadingWithActionElements"] h1,
.main [data-testid="stMarkdownContainer"] h1 {{
  font-size: 1.45rem !important;
  font-weight: 700 !important;
  line-height: 1.25 !important;
  letter-spacing: -0.015em;
  color: #111827 !important;
  margin: 0 0 0.4rem 0 !important;
}}
.main h2,
.main [data-testid="stHeadingWithActionElements"] h2,
.main [data-testid="stMarkdownContainer"] h2 {{
  font-size: 1.22rem !important;
  font-weight: 700 !important;
  line-height: 1.3 !important;
  letter-spacing: -0.01em;
  color: #111827 !important;
  margin: 1.15rem 0 0.4rem 0 !important;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid #e5e7eb;
}}
.main h3,
.main [data-testid="stHeadingWithActionElements"] h3,
.main [data-testid="stMarkdownContainer"] h3 {{
  font-size: 1.05rem !important;
  font-weight: 650 !important;
  line-height: 1.35 !important;
  color: #1f2937 !important;
  margin: 0.95rem 0 0.3rem 0 !important;
}}
.main h4,
.main [data-testid="stHeadingWithActionElements"] h4,
.main [data-testid="stMarkdownContainer"] h4 {{
  font-size: 0.92rem !important;
  font-weight: 650 !important;
  line-height: 1.35 !important;
  color: #374151 !important;
  margin: 0.85rem 0 0.25rem 0 !important;
}}
.main h5,
.main [data-testid="stMarkdownContainer"] h5 {{
  font-size: 0.86rem !important;
  font-weight: 600 !important;
  color: #4b5563 !important;
  margin: 0.65rem 0 0.2rem 0 !important;
}}
.main p,
.main [data-testid="stMarkdownContainer"] p {{
  font-size: 0.94rem;
  line-height: 1.45;
  color: #1f2937;
}}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
.stCaption {{
  font-size: 0.8rem !important;
  line-height: 1.4 !important;
  color: #6b7280 !important;
  margin-bottom: 0.55rem !important;
}}

/* First heading on a page: less top gap (Streamlit subheader ≈ h2/h3) */
.main .block-container > div:first-child h2,
.main .block-container > div:first-child h3 {{
  margin-top: 0.15rem !important;
}}

/* —— Tabs / expander / metrics (menu chrome) —— */
[data-testid="stTabs"] button[data-baseweb="tab"] {{
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em;
}}
[data-testid="stTabs"] button[aria-selected="true"] {{
  font-weight: 700 !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span {{
  font-size: 0.95rem !important;
  font-weight: 650 !important;
  color: #111827 !important;
}}
[data-testid="stExpander"] details {{
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fafafa;
  padding: 0.15rem 0.35rem;
  margin-bottom: 0.55rem;
}}
[data-testid="stMetricLabel"] {{
  font-size: 0.72rem !important;
  font-weight: 650 !important;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #6b7280 !important;
}}
[data-testid="stMetricValue"] {{
  font-size: 1.35rem !important;
  font-weight: 650 !important;
  font-variant-numeric: tabular-nums;
  color: #111827 !important;
}}
[data-testid="stMetricDelta"] {{
  font-size: 0.8rem !important;
}}
div[data-testid="stVerticalBlockBorderWrapper"] {{
  border-color: #e5e7eb !important;
}}

/* —— Status / queue blocks (tier-2 rows, left accent only) —— */
.alpha-action-queue {{
  border-left: 4px solid #f59e0b;
  background: #fffbeb;
  padding: 0.7rem 0.85rem;
  margin-bottom: 0.75rem;
  border-radius: 0;
}}
.alpha-banner-muted {{
  border-left: 4px solid #9ca3af;
  background: #f9fafb;
  padding: 0.7rem 0.85rem;
  margin-bottom: 0.75rem;
  color: #4b5563;
}}
.alpha-banner-danger {{
  border-left: 4px solid #ef4444;
  background: #fef2f2;
  padding: 0.7rem 0.85rem;
  margin-bottom: 0.75rem;
  color: #991b1b;
}}
.alpha-banner-warn {{
  border-left: 4px solid #f59e0b;
  background: #fffbeb;
  padding: 0.7rem 0.85rem;
  margin-bottom: 0.75rem;
  color: #92400e;
}}
.alpha-banner-danger strong,
.alpha-banner-warn strong,
.alpha-banner-muted strong {{
  display: block;
  font-size: 0.98rem;
  font-weight: 700;
  line-height: 1.3;
  margin-bottom: 0.25rem;
  color: inherit;
}}
.alpha-action-item {{
  padding: 0.55rem 0.15rem;
  font-size: 0.94rem;
  line-height: 1.4;
  border-bottom: 1px solid #e5e7eb;
}}
.alpha-action-item strong {{
  font-size: 0.98rem;
  font-weight: 650;
  color: #111827;
}}
.alpha-empty-queue {{
  border-left: 4px solid #22c55e;
  background: #f0fdf4;
  padding: 0.7rem 0.85rem;
  margin-bottom: 0.75rem;
  border-radius: 0;
  color: #166534;
}}
.alpha-empty-queue strong {{
  font-size: 0.98rem;
  font-weight: 700;
}}
.alpha-card {{
  border: none;
  border-radius: 0;
  padding: 0.7rem 0.75rem 0.7rem 0.85rem;
  margin-bottom: 0.55rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}}
.alpha-card strong {{
  font-size: 0.96rem;
  font-weight: 700;
  color: #111827;
}}
.alpha-card small {{
  display: inline-block;
  margin-top: 0.2rem;
  font-size: 0.8rem;
  line-height: 1.4;
  color: #6b7280;
}}
.alpha-card em {{
  display: block;
  margin-top: 0.35rem;
  font-size: 0.78rem;
  font-style: normal;
  font-weight: 650;
  letter-spacing: 0.02em;
  color: #6b7280;
  text-transform: uppercase;
}}
.alpha-card-ok {{
  border-left: 4px solid #22c55e;
  background: #f0fdf4;
  padding-left: 0.75rem;
}}
.alpha-card-warn {{
  border-left: 4px solid #f59e0b;
  background: #fffbeb;
  padding-left: 0.75rem;
}}
.alpha-card-danger {{
  border-left: 4px solid #ef4444;
  background: #fef2f2;
  padding-left: 0.75rem;
}}
.alpha-card-muted {{
  border-left: 4px solid #9ca3af;
  background: #f9fafb;
  padding-left: 0.75rem;
}}
.alpha-muted-note {{
  color: #6b7280;
  font-size: 0.82rem;
  line-height: 1.4;
  border-left: 2px solid #9ca3af;
  padding: 0.5rem 0.7rem;
  margin: 0.4rem 0;
  background: #f9fafb;
}}
.alpha-badge-warn {{
  display: inline-block;
  background: #fef3c7;
  color: #92400e;
  padding: 0.12rem 0.5rem;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}}
.alpha-badge-danger {{
  display: inline-block;
  background: #fee2e2;
  color: #991b1b;
  padding: 0.12rem 0.5rem;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}}
.alpha-badge-ok {{
  display: inline-block;
  background: #dcfce7;
  color: #166534;
  padding: 0.12rem 0.5rem;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}}

/* —— Portfolio list — 3-tier (container / row / extend) —— */
.pf-list {{
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
  padding: 0.2rem 0.75rem 0.3rem;
  margin-bottom: 0.85rem;
  box-shadow: 0 1px 0 rgba(17, 24, 39, 0.04);
}}
.pf-row-main {{
  padding: 0.5rem 0 0.4rem;
}}
.pf-hairline {{
  border-bottom: 1px solid #e5e7eb;
  margin: 0;
}}
.pf-bullet-top {{
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.35rem 0.65rem;
  font-size: 0.94rem;
  margin-bottom: 0.3rem;
}}
.pf-weight-ok {{ color: #166534; font-weight: 700; }}
.pf-weight-warn {{ color: #92400e; font-weight: 700; }}
.pf-weight-danger {{ color: #991b1b; font-weight: 700; }}
.pf-upside {{ margin-left: auto; font-size: 0.84rem; font-weight: 600; }}
.pf-tone-accent {{ color: #2563eb; font-weight: 650; }}
.pf-tone-danger {{ color: #991b1b; font-weight: 650; }}
.pf-tone-muted {{ color: #6b7280; }}
.muted {{ color: #6b7280; }}

.pf-bar-block {{ margin: 0.25rem 0 0.2rem; }}
.pf-bar-caption {{
  font-size: 0.72rem;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 0.14rem;
  letter-spacing: 0.02em;
}}
.pf-bar-track {{
  position: relative;
  height: 10px;
  background: #e5e7eb;
  border-radius: 5px;
  overflow: hidden;
}}
.pf-bar-thin {{ height: 6px; }}
.pf-bar-price {{ height: 10px; }}
.pf-bar-fill {{
  position: absolute;
  left: 0; top: 0; bottom: 0;
  border-radius: 5px;
  max-width: 100%;
}}
.pf-fill-accent {{ background: #2563eb; }}
.pf-fill-ok {{ background: #22c55e; }}
.pf-fill-warn {{ background: #f59e0b; }}
.pf-fill-danger {{ background: #ef4444; }}
.pf-bar-labels {{
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  color: #6b7280;
  margin-bottom: 0.1rem;
}}
.pf-missing {{
  color: #991b1b;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.25rem 0;
}}
.pf-missing-legacy {{
  color: #92400e;
}}

/* Expand = parent-row extension (no nested card border) */
.pf-extend {{
  margin: 0 0 0.2rem;
  padding: 0.6rem 0 0.6rem 0.7rem;
  background: #f3f4f6;
  border-left: 2px solid #2563eb;
  border-radius: 0;
}}
.pf-sec {{ margin: 0.5rem 0 0.55rem; }}
.pf-sec-title {{
  font-size: 0.72rem;
  color: #6b7280;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin-bottom: 0.22rem;
  text-transform: uppercase;
}}
.pf-sec-body {{
  font-size: 0.88rem;
  line-height: 1.45;
  color: #111827;
  padding: 0;
}}

@media (min-width: 768px) {{
  [data-testid="stAppViewContainer"] .main .block-container {{
    max-width: 1100px;
  }}
}}
{compact_css}
</style>
        """,
        unsafe_allow_html=True,
    )


def status_card_class(level: str) -> str:
    return {
        "ok": "alpha-card alpha-card-ok",
        "warn": "alpha-card alpha-card-warn",
        "danger": "alpha-card alpha-card-danger",
        "muted": "alpha-card alpha-card-muted",
    }.get(level, "alpha-card alpha-card-muted")
