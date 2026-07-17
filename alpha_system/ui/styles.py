"""Mobile-first Streamlit styles — semantic status colors only."""

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
[data-testid="stAppViewContainer"] .main .block-container {{
  padding-top: 0.75rem;
  padding-bottom: 2rem;
  max-width: 720px;
}}
.alpha-action-queue {{
  border-left: 4px solid #f59e0b;
  background: transparent;
  padding: 0.6rem 0.75rem;
  margin-bottom: 0.75rem;
  border-radius: 0;
}}
.alpha-banner-muted {{
  border-left: 4px solid #9ca3af;
  background: #f9fafb;
  padding: 0.6rem 0.75rem;
  margin-bottom: 0.75rem;
  color: #4b5563;
}}
.alpha-banner-danger {{
  border-left: 4px solid #ef4444;
  background: #fef2f2;
  padding: 0.6rem 0.75rem;
  margin-bottom: 0.75rem;
  color: #991b1b;
}}
.alpha-action-item {{
  padding: 0.45rem 0;
  font-size: 0.95rem;
  line-height: 1.35;
  border-bottom: 1px solid #e5e7eb;
}}
.alpha-empty-queue {{
  border-left: 4px solid #22c55e;
  background: transparent;
  padding: 0.6rem 0.75rem;
  margin-bottom: 0.75rem;
  border-radius: 0;
  color: #166534;
}}
.alpha-card {{
  border: none;
  border-radius: 0;
  padding: 0.65rem 0.75rem;
  margin-bottom: 0.5rem;
  background: transparent;
  border-bottom: 1px solid #e5e7eb;
}}
.alpha-card-ok {{ border-left: 4px solid #22c55e; padding-left: 0.65rem; }}
.alpha-card-warn {{ border-left: 4px solid #f59e0b; padding-left: 0.65rem; }}
.alpha-card-danger {{ border-left: 4px solid #ef4444; padding-left: 0.65rem; }}
.alpha-card-muted {{ border-left: 4px solid #9ca3af; padding-left: 0.65rem; }}
.alpha-muted-note {{
  color: #6b7280;
  font-size: 0.9rem;
  border-left: 2px solid #9ca3af;
  padding: 0.45rem 0.65rem;
  margin: 0.35rem 0;
  background: #f9fafb;
}}
.alpha-badge-warn {{
  display: inline-block;
  background: #fef3c7;
  color: #92400e;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}}
.alpha-badge-danger {{
  display: inline-block;
  background: #fee2e2;
  color: #991b1b;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}}
.alpha-badge-ok {{
  display: inline-block;
  background: #dcfce7;
  color: #166534;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}}

/* Portfolio list — 3-tier hierarchy (container / row / extend) */
.pf-list {{
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
  padding: 0.15rem 0.65rem 0.25rem;
  margin-bottom: 0.75rem;
}}
.pf-row-main {{
  padding: 0.45rem 0 0.35rem;
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
  font-size: 0.92rem;
  margin-bottom: 0.3rem;
}}
.pf-weight-ok {{ color: #166534; font-weight: 600; }}
.pf-weight-warn {{ color: #92400e; font-weight: 700; }}
.pf-weight-danger {{ color: #991b1b; font-weight: 700; }}
.pf-upside {{ margin-left: auto; font-size: 0.85rem; }}
.pf-tone-accent {{ color: #2563eb; font-weight: 600; }}
.pf-tone-danger {{ color: #991b1b; font-weight: 600; }}
.pf-tone-muted {{ color: #6b7280; }}
.muted {{ color: #6b7280; }}

.pf-bar-block {{ margin: 0.2rem 0 0.15rem; }}
.pf-bar-caption {{
  font-size: 0.72rem;
  color: #6b7280;
  margin-bottom: 0.12rem;
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
  padding: 0.25rem 0;
}}
.pf-missing-legacy {{
  color: #92400e;
}}

/* Expand = parent-row extension (no nested card border) */
.pf-extend {{
  margin: 0 0 0.15rem;
  padding: 0.55rem 0 0.55rem 0.65rem;
  background: #f3f4f6;
  border-left: 2px solid #2563eb;
  border-radius: 0;
}}
.pf-sec {{ margin: 0.45rem 0 0.55rem; }}
.pf-sec-title {{
  font-size: 11px;
  color: #6b7280;
  font-weight: 600;
  letter-spacing: 0.02em;
  margin-bottom: 0.2rem;
  text-transform: none;
}}
.pf-sec-body {{
  font-size: 0.88rem;
  line-height: 1.4;
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
