"""이벤트/갱신 렌더 헬퍼 — 화면 진입점은 approval.render_approval."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from alpha_system.journal import append_record
from alpha_system.ui.services.auto_journal import journal_data_refresh, journal_go_live_blocked
from alpha_system.ui.services.context import DashboardContext
from alpha_system.ui.services.go_live_gate import block_go_live_reasons
from alpha_system.ui.services.refresh import run_quant_snapshot_refresh
from alpha_system.ui.services.runtime_state import RuntimeState
from alpha_system.ui.services.ui_copy import copy_get


def render_events(ctx: DashboardContext) -> None:
    """Legacy entry — redirects to the approval hub."""
    from alpha_system.ui.pages.approval import render_approval

    render_approval(ctx)


def _render_weekly_qual(
    ctx: DashboardContext,
    *,
    focused: bool = False,
) -> None:
    """One collection surface and one compact domain approval board."""
    from datetime import date as _date

    import pandas as pd

    from alpha_system.ui.services.weekly_domain_gates import (
        approve_domain,
        mark_sources_reviewed,
    )
    from alpha_system.ui.services.weekly_qual_report import (
        DOMAIN_KEYS,
        load_weekly_suggestions,
        parse_weekly_qual_markdown,
        persist_weekly_suggestions,
        subjects_from_cecs_df,
        subjects_from_portfolio_rows,
        write_weekly_qual_report,
    )

    st.subheader("주간 정성 수집·승인")
    st.caption(
        "금 요청서 1개 → 주말 작성 → 월 업로드 1회 → 이 화면에서 영역별 승인"
    )
    if focused:
        st.info("홈의 「지금 할 일」에서 연결되었습니다.")

    cecs_path = ctx.root / "data" / "cecs_manual_scoring_template.csv"
    cecs_df = pd.read_csv(cecs_path, dtype=str) if cecs_path.exists() else pd.DataFrame()
    summary = subjects_from_cecs_df(cecs_df, limit=30)
    # B/E = current proposal_book only (no CECS summary[:N] fallback).
    n_deep = int(getattr(ctx.cfg.sizing, "target_names", 6) or 6)
    deep = subjects_from_portfolio_rows(ctx.portfolio_rows[:n_deep])

    collect_tab, upload_tab = st.tabs(["1. 요청서 생성·다운로드", "2. 완성본 업로드"])
    with collect_tab:
        st.caption("A CECS 30요약 · B 최종선정 심층 · C T2 · D 논지 · E 목표가")
        can_gen = bool(deep)
        if not can_gen:
            st.error(
                "proposal_book(최종 선정)이 비어 B/E를 만들 수 없습니다. "
                "정량·컷오프·eligibility·섹터 캡을 먼저 확인하세요."
            )
        if st.button(
            "이번 주 요청서 생성",
            type="primary",
            key="btn_weekly_qual_gen",
            use_container_width=True,
            disabled=not can_gen,
        ):
            report = write_weekly_qual_report(
                summary_subjects=summary,
                deep_subjects=deep,
                t2_event_ids=list(ctx.cfg.tranches["T2"].event_ids),
                docs_dir=ctx.root / "docs",
                as_of=ctx.as_of,
                input_paths=[
                    ctx.root
                    / "alpha_portfolio"
                    / "data"
                    / "output"
                    / "alpha_scores.csv",
                    cecs_path,
                    ctx.root / "data" / "fundamentals.csv",
                ],
            )
            st.session_state["weekly_qual_md"] = report.markdown
            st.session_state["weekly_qual_path"] = str(report.path)
            st.session_state["weekly_qual_deep_tickers"] = [
                str(s.get("ticker") or "").zfill(6) for s in deep if s.get("ticker")
            ]
            st.success(f"생성됨: {report.path.name}")

        md = st.session_state.get("weekly_qual_md")
        path = st.session_state.get("weekly_qual_path")
        if md:
            st.download_button(
                "요청서 다운로드",
                data=md,
                file_name=Path(path).name if path else "weekly_qual_report.md",
                mime="text/markdown",
                key="weekly_qual_dl",
                use_container_width=True,
            )

    with upload_tab:
        uploaded = st.file_uploader(
            "AI 작성 완료 Markdown",
            type=["md", "markdown", "txt"],
            key="weekly_qual_upload",
        )
        if uploaded is not None and st.button(
            "업로드·영역 분리",
            type="primary",
            key="weekly_qual_parse",
            use_container_width=True,
        ):
            text = uploaded.getvalue().decode("utf-8-sig")
            parsed = parse_weekly_qual_markdown(text)
            out = persist_weekly_suggestions(
                root=ctx.root,
                parsed=parsed,
                report_name=uploaded.name,
                as_of=ctx.as_of or _date.today(),
            )
            st.success(
                "업로드 완료: "
                + ", ".join(
                    f"{k}={parsed.domain_status.get(k)}" for k in DOMAIN_KEYS
                )
                + f" → `{out.name}`"
            )
            for domain, failures in parsed.domain_failures.items():
                if failures:
                    st.warning(f"{domain}: " + "; ".join(failures[:5]))
            st.rerun()

    payload = load_weekly_suggestions(ctx.root)
    if not payload:
        return

    approved_map = dict(payload.get("approved") or {})
    domain_statuses = dict(payload.get("domain_status") or {})
    pending_n = sum(
        1
        for key in DOMAIN_KEYS
        if domain_statuses.get(key) == "ai_suggested"
        and not approved_map.get(key, False)
    )
    st.markdown("#### 최종 확인·승인판")
    st.caption(
        f"승인 남음 {pending_n}영역 · 출처 확인 후 해당 영역만 적용 · "
        "다른 영역 자동 승인 없음 · 승인된 영역도 펼치면 보고서 재확인 가능"
    )
    if pending_n == 0 and any(approved_map.values()):
        st.info("이번 주 영역 승인 완료. 아래 카드를 펼치면 승인 당시 보고서를 다시 볼 수 있습니다.")
    approver = st.text_input(
        "공통 승인자",
        value="operator",
        key="weekly_approver",
    )
    for domain in DOMAIN_KEYS:
        status = (payload.get("domain_status") or {}).get(domain, "—")
        approved = bool(approved_map.get(domain))
        domain_label = {
            "cecs": "CECS",
            "t2": "T2 이벤트",
            "thesis": "논지",
            "targets": "목표가",
        }.get(domain, domain)
        suffix = " — 승인 완료 · 펼치면 보고서 재확인" if approved else f" — {status}"
        with st.expander(
            f"{domain_label}{suffix}",
            expanded=(not approved and pending_n <= 2),
        ):
            if approved:
                meta = (payload.get("approved_meta") or {}).get(domain) or {}
                by = meta.get("approved_by") or "—"
                as_of_meta = meta.get("as_of") or payload.get("as_of") or "—"
                st.success(f"승인·적용 완료 · 승인자 `{by}` · as_of {as_of_meta}")
                st.caption("아래는 승인 당시 보고서입니다. 조회만 가능하며 재승인 버튼은 없습니다.")
                _render_domain_report(payload, domain)
                continue
            if status != "ai_suggested":
                st.warning(
                    "이 영역은 승인 가능한 제안이 없습니다. "
                    "파싱 실패 내용을 보완해 완성본을 다시 업로드하세요."
                )
                failures = (payload.get("domain_failures") or {}).get(domain) or []
                if failures:
                    with st.expander(f"파싱 실패 {len(failures)}건", expanded=False):
                        for failure in failures:
                            st.caption(f"• {failure}")
                continue
            keys = _domain_review_keys(payload, domain)
            _render_domain_report(payload, domain)
            source_confirmed = st.checkbox(
                f"위 {domain_label} 보고서 내용과 출처 원문을 모두 확인했습니다",
                key=f"weekly_source_confirm_{domain}",
            )
            confirm = 0
            if domain == "t2":
                st.warning("승인하면 T2 이벤트 기록이 생성됩니다.")
                c1 = st.checkbox("이벤트 기록 영향을 이해했습니다", key="weekly_t2_c1")
                c2 = st.checkbox("T2 적용을 최종 확인합니다", key="weekly_t2_c2")
                confirm = int(c1) + int(c2)
            elif domain == "thesis":
                st.error("damage=true 승인 시 미집행 트랜치 동결 판단에 반영됩니다.")
                c1 = st.checkbox("동결 가능성을 이해했습니다", key="weekly_th_c1")
                c2 = st.checkbox("논지 근거를 재확인했습니다", key="weekly_th_c2")
                c3 = st.checkbox("논지 적용을 최종 확인합니다", key="weekly_th_c3")
                confirm = int(c1) + int(c2) + int(c3)
            elif domain == "targets":
                st.info("승인해도 target_portfolio.csv는 변경하지 않습니다.")

            if st.button(
                f"{domain_label}만 승인",
                key=f"weekly_approve_{domain}",
                disabled=not source_confirmed,
                use_container_width=True,
            ):
                try:
                    # One click stores source review and applies this domain.
                    mark_sources_reviewed(root=ctx.root, domain=domain, keys=keys)
                    approve_domain(
                        root=ctx.root,
                        domain=domain,
                        approved_by=approver,
                        as_of=ctx.as_of or _date.today(),
                        reviewed_keys=keys,
                        confirm_steps=confirm,
                    )
                    st.success(f"{domain_label} 승인 완료")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def _render_domain_report(payload: dict, domain: str) -> None:
    """Render parsed judgments and sources as a continuous approval report."""
    st.markdown("#### 결재 검토 보고서")
    st.caption(
        f"보고서 `{payload.get('report_name') or '—'}` · "
        f"기준일 {payload.get('as_of') or '—'} · "
        f"report_id `{payload.get('report_id') or '—'}`"
    )

    if domain == "cecs":
        items = payload.get("cecs") or []
        st.info(
            f"CECS {len(items)}종 · execution / pension / purpose 순서입니다. "
            "점수 50은 AI가 점수를 비워 잠정 중립값으로 변환된 경우가 포함됩니다."
        )
        for index, item in enumerate(items, 1):
            ticker = str(item.get("ticker") or "")
            name = str(item.get("name") or ticker)
            with st.container(border=True):
                st.markdown(f"##### {index}. {name} (`{ticker}`)")
                score_cols = st.columns(3)
                for col, axis, label in zip(
                    score_cols,
                    ("execution", "pension", "purpose"),
                    ("실행·환원", "연기금", "투자목적"),
                ):
                    score = (item.get(axis) or {}).get("score_100")
                    col.metric(label, f"{score:g}" if isinstance(score, (int, float)) else "—")

                for axis, label in (
                    ("execution", "실행·환원"),
                    ("pension", "연기금"),
                    ("purpose", "투자목적"),
                ):
                    detail = item.get(axis) or {}
                    st.markdown(f"**{label} 판단**")
                    st.write(detail.get("rationale") or "내용 없음")
                    _render_sources(detail.get("sources") or [])

        deep = [
            item
            for item in (payload.get("deep_dives") or [])
            if any(
                str(item.get(key) or "").strip() not in {"", "_____", "확인 불가"}
                for key in (
                    "disclosure",
                    "buyback_dividend",
                    "pension",
                    "investment_purpose",
                    "risks",
                )
            )
        ]
        if deep:
            st.markdown("#### 최종 후보 심층 검토")
            for item in deep:
                with st.container(border=True):
                    st.markdown(
                        f"##### {item.get('name') or item.get('ticker')} "
                        f"(`{item.get('ticker') or '—'}`)"
                    )
                    for key, label in (
                        ("disclosure", "공시·지배구조"),
                        ("buyback_dividend", "자사주·배당·환원"),
                        ("pension", "연기금·수급"),
                        ("investment_purpose", "투자목적"),
                        ("risks", "리스크"),
                    ):
                        st.markdown(f"**{label}**")
                        st.write(item.get(key) or "내용 없음")
                    _render_sources(item.get("sources") or [])

    elif domain == "t2":
        items = payload.get("t2") or []
        for index, item in enumerate(items, 1):
            with st.container(border=True):
                st.markdown(
                    f"##### {index}. T2 이벤트 `{item.get('event_id') or '—'}`"
                )
                st.markdown(
                    f"- 발생 판단: **{'발생' if item.get('fired') else '미발생'}**"
                )
                st.markdown("**판단 근거**")
                st.write(item.get("rationale") or "내용 없음")
                _render_sources(item.get("sources") or [])

    elif domain == "thesis":
        item = payload.get("thesis") or {}
        with st.container(border=True):
            st.markdown(
                "##### 논지 훼손 판단: "
                + ("**훼손**" if item.get("damage") else "**훼손 없음**")
            )
            st.markdown("**판단 근거**")
            st.write(item.get("rationale") or "내용 없음")
            _render_sources(item.get("sources") or [])

    elif domain == "targets":
        items = payload.get("targets") or []
        st.info("이 보고서를 승인해도 `target_portfolio.csv`는 변경되지 않습니다.")
        for index, item in enumerate(items, 1):
            with st.container(border=True):
                st.markdown(
                    f"##### {index}. {item.get('name') or item.get('ticker')} "
                    f"(`{item.get('ticker') or '—'}`)"
                )
                cols = st.columns(2)
                cols[0].metric("PBR 상한", item.get("pbr_max") or "—")
                cols[1].metric("목표가", item.get("target_price") or "—")
                st.markdown("**펀더멘털 사유**")
                st.write(item.get("fundamental_reason") or "내용 없음")
                st.markdown("**판단 근거**")
                st.write(item.get("rationale") or "내용 없음")
                _render_sources(item.get("sources") or [])


def _render_sources(sources: list[str] | tuple[str, ...]) -> None:
    st.markdown("**출처**")
    if not sources:
        st.caption("• 출처 없음")
        return
    for index, source in enumerate(sources, 1):
        value = str(source).strip()
        if value.startswith(("http://", "https://")):
            st.markdown(f"- [출처 {index}]({value}) — `{value}`")
        elif value.startswith("[") and "](" in value:
            st.markdown(f"- {value}")
        else:
            st.caption(f"• {value or '출처 없음'}")


def _domain_review_keys(payload: dict, domain: str) -> list[str]:
    if domain == "cecs":
        return [str(x.get("ticker")) for x in payload.get("cecs") or [] if x.get("ticker")]
    if domain == "t2":
        fired = [
            str(x.get("event_id"))
            for x in payload.get("t2") or []
            if x.get("fired") and x.get("event_id")
        ]
        return fired or ["t2_none"]
    if domain == "thesis":
        return ["thesis"]
    if domain == "targets":
        return [str(x.get("ticker")) for x in payload.get("targets") or [] if x.get("ticker")]
    return []


def _render_t3_detail(ctx: DashboardContext) -> None:
    st.markdown("#### T3 PBR 이력·판정")
    pbr = ctx.t3_pbr
    if not pbr.available:
        st.markdown(
            '<div class="alpha-muted-note">'
            "이력 데이터 필요 — KOSPI 시장 PBR 10년 이력이 없어 저가 매수 조건을 "
            "판단할 수 없습니다. 아래 데이터 갱신·이력 적재를 확인하세요."
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption(pbr.source_note)
        return
    pct = pbr.percentile_10y
    history_detail = ""
    hist_path = ctx.root / "data" / "kospi_market_pbr_history.csv"
    if hist_path.exists():
        try:
            import pandas as pd

            history = pd.read_csv(hist_path)
            dates = pd.to_datetime(history.get("month_end"), errors="coerce").dropna()
            if not dates.empty:
                history_detail = (
                    f"- 이력: **{len(history)}개월** "
                    f"({dates.min().date().isoformat()} ~ {dates.max().date().isoformat()})\n"
                    f"- 파일: `{hist_path}`\n"
                )
        except Exception:
            history_detail = f"- 파일: `{hist_path}`\n"
    st.markdown(
        history_detail
        + f"- 최근 완료월 PBR: **{pbr.current_pbr if pbr.current_pbr is not None else '—'}**\n"
        f"- 10년 백분위: **{pct if pct is not None else '—'}%** "
        f"(하위 {pbr.bottom_pct}% 밴드)\n"
        f"- 밴드 진입: **{'예' if pbr.in_bottom_band else '아니오' if pbr.in_bottom_band is not None else '판정 불가'}**\n"
        f"- as_of: {pbr.as_of.isoformat() if pbr.as_of else '—'}\n"
        f"- 다음 판정: **매월 말**\n"
        f"- 소스: {pbr.source_note}"
    )


def _render_go_live(ctx: DashboardContext, *, expand: bool = False) -> None:
    st.markdown("#### Go-live 선언")
    if not ctx.pre_launch and ctx.effective_go_live is not None:
        st.info(
            copy_get(
                "go_live",
                "already_live",
                date=ctx.effective_go_live.isoformat(),
            )
        )
        return

    if ctx.checklist is not None:
        st.caption(f"체크리스트 {ctx.checklist.done}/{ctx.checklist.total}")
        for item in ctx.checklist.items:
            mark = "OK" if item.ok else "미충족"
            st.markdown(f"- **{mark}** {item.title}: {item.why} → {item.todo}")

    st.warning(copy_get("go_live", "warn"))
    c1 = st.checkbox(copy_get("go_live", "confirm_1"), key="gl_c1")
    c2 = st.checkbox(copy_get("go_live", "confirm_2"), key="gl_c2")
    live_date = st.date_input("가동 기준일", value=date.today(), key="gl_date")
    if st.button("go-live 선언", disabled=not (c1 and c2), key="gl_submit"):
        blocking = block_go_live_reasons(ctx.checklist) if ctx.checklist else []
        if blocking:
            msg = copy_get(
                "checklist",
                "go_live_blocked",
                items="; ".join(blocking),
            )
            journal_go_live_blocked(as_of=date.today(), items=blocking)
            st.error(msg)
            return
        iso = live_date.isoformat()
        append_record(
            action_kind="GO_LIVE_DECLARE",
            as_of=live_date,
            subject="*",
            rationale="operator go-live declaration",
            trigger_snapshot={"go_live_date": iso},
            payload={"go_live_date": iso},
        )
        runtime = RuntimeState.load(ctx.root / "data" / "alpha_dashboard_runtime.json")
        runtime.go_live_date = iso
        runtime.save(ctx.root / "data" / "alpha_dashboard_runtime.json")
        st.success(copy_get("go_live", "success", date=iso))
        st.rerun()


def _render_data_refresh(ctx: DashboardContext) -> None:
    st.caption(
        "정량 전체 갱신 한 번으로 운용 데이터와 alpha_scores를 함께 갱신합니다. "
        "이 PC에서 실행되며 수 분 걸릴 수 있습니다."
    )
    for src in ctx.source_status:
        rec = f"권장 {src.recommended_days}일" if src.recommended_days else "수동"
        st.text(f"• {src.label} — {src.path} ({rec})")
    hist = ctx.root / "data" / "kospi_market_pbr_history.csv"
    st.caption(f"T3 이력 CSV: {'있음' if hist.exists() else '없음'} — {hist}")
    if st.button(
        "정량 전체 갱신",
        type="primary",
        key="btn_quant_snapshot_refresh",
        use_container_width=True,
    ):
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
            provenance = result.detail.get("provenance") or {}
            if provenance:
                st.caption(
                    f"run_id {provenance.get('run_id', '—')} · "
                    f"scored {provenance.get('scored_rows', '—')} · "
                    f"as_of {provenance.get('as_of', '—')}"
                )
            st.rerun()
        else:
            st.error(result.message)
            with st.expander("실패 상세"):
                st.json(result.detail)
