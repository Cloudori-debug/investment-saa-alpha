"""Startup cadence guide + judgment-critical freshness alerts with deep links."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional, Sequence

from alpha_system.ui.services.context import DashboardContext, PortfolioRow
from alpha_system.ui.services.data_freshness import SourceStatus
from alpha_system.ui.services.nav import (
    FOCUS_DATA_REFRESH,
    FOCUS_WEEKLY_QUAL,
    PAGE_APPROVAL,
    PAGE_PORTFOLIO,
)
from alpha_system.ui.services.weekly_qual_report import load_weekly_suggestions


@dataclass(frozen=True)
class CadenceGuideItem:
    cadence: str
    title: str
    detail: str
    page: str
    focus: Optional[str] = None


@dataclass(frozen=True)
class FreshnessAlert:
    key: str
    severity: str  # warn | danger
    title: str
    detail: str
    cta_label: str
    page: str
    focus: Optional[str] = None
    # When True, home shows an in-place quant snapshot refresh button.
    inline_quant_refresh: bool = False


# Operator-facing schedule — keep in sync with dashboard.yaml recommended_days.
CADENCE_GUIDE: tuple[CadenceGuideItem, ...] = (
    CadenceGuideItem(
        cadence="사용 전 / 매 거래일",
        title="현재가 · 정량 스냅샷",
        detail="prices·alpha_scores를 갱신해야 제안 북·갭 판단이 최신입니다.",
        page=PAGE_APPROVAL,
        focus=FOCUS_DATA_REFRESH,
    ),
    CadenceGuideItem(
        cadence="주 1회 (금~월)",
        title="주간 정성 A~E",
        detail="요청서 생성 → 작성 → 업로드 → 영역별 승인. 목표가 대기는 E 보충.",
        page=PAGE_APPROVAL,
        focus=FOCUS_WEEKLY_QUAL,
    ),
    CadenceGuideItem(
        cadence="월 1회",
        title="T3 시장 PBR",
        detail="KOSPI 시장 PBR 이력이 한 달 이상 멈추면 월간 판정이 흔들립니다.",
        page=PAGE_APPROVAL,
        focus=FOCUS_DATA_REFRESH,
    ),
    CadenceGuideItem(
        cadence="분기·수시",
        title="펀더멘털 · 목표가",
        detail="정량 갱신에 펀더멘털이 포함됩니다. 제안 북 목표가는 결재함에서 승인.",
        page=PAGE_APPROVAL,
        focus=FOCUS_WEEKLY_QUAL,
    ),
    CadenceGuideItem(
        cadence="판단 전",
        title="제안 북 · 운용 북",
        detail="스크린 결과와 실보유를 포트폴리오에서 대조한 뒤 승인합니다.",
        page=PAGE_PORTFOLIO,
        focus=None,
    ),
)


def _parse_iso_date(raw: Any) -> Optional[date]:
    if raw is None:
        return None
    text = str(raw).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _weekly_as_of(root: Path, weekly: dict[str, Any]) -> Optional[date]:
    parsed = _parse_iso_date(weekly.get("as_of"))
    if parsed:
        return parsed
    path = root / "data" / "weekly_qual_suggestions.json"
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).date()


def _source_map(sources: Sequence[SourceStatus]) -> dict[str, SourceStatus]:
    return {s.key: s for s in sources}


def _missing_target_tickers(rows: Sequence[PortfolioRow]) -> list[str]:
    out: list[str] = []
    for row in rows:
        if not getattr(row, "has_target", True):
            out.append(str(row.ticker).zfill(6))
    return out


def build_freshness_alerts(
    ctx: DashboardContext,
    *,
    today: date | None = None,
) -> list[FreshnessAlert]:
    """Judgment-critical staleness only — not every inventory row."""
    today = today or getattr(ctx, "as_of", None) or date.today()
    sources = _source_map(ctx.source_status or [])
    alerts: list[FreshnessAlert] = []

    prices = sources.get("prices")
    if prices is not None and (not prices.exists or prices.stale):
        as_of = prices.as_of.isoformat() if prices.as_of else "—"
        alerts.append(
            FreshnessAlert(
                key="prices",
                severity="danger" if not prices.exists else "warn",
                title="현재가가 오래되었습니다",
                detail=(
                    f"prices as_of {as_of} "
                    f"(권장 {prices.recommended_days or 1}일). "
                    "갭·목표가 근접도 판단이 부정확할 수 있습니다."
                ),
                cta_label="정량 전체 갱신",
                page=PAGE_APPROVAL,
                focus=FOCUS_DATA_REFRESH,
                inline_quant_refresh=True,
            )
        )

    scores = sources.get("alpha_scores")
    if scores is None or not scores.exists:
        alerts.append(
            FreshnessAlert(
                key="alpha_scores_missing",
                severity="danger",
                title="정량 스냅샷이 없습니다",
                detail="alpha_scores가 없어 제안 북·적격을 판단할 수 없습니다.",
                cta_label="정량 전체 갱신",
                page=PAGE_APPROVAL,
                focus=FOCUS_DATA_REFRESH,
                inline_quant_refresh=True,
            )
        )
    elif scores.stale:
        as_of = scores.as_of.isoformat() if scores.as_of else "—"
        alerts.append(
            FreshnessAlert(
                key="alpha_scores_stale",
                severity="warn",
                title="정량 스냅샷 갱신이 필요합니다",
                detail=(
                    f"alpha_scores as_of {as_of} "
                    f"(권장 {scores.recommended_days or 7}일). "
                    "제안 순위가 옛 점수일 수 있습니다."
                ),
                cta_label="정량 전체 갱신",
                page=PAGE_APPROVAL,
                focus=FOCUS_DATA_REFRESH,
                inline_quant_refresh=True,
            )
        )

    weekly = load_weekly_suggestions(ctx.root)
    if not weekly:
        alerts.append(
            FreshnessAlert(
                key="weekly_missing",
                severity="warn",
                title="주간 정성 리포트가 없습니다",
                detail="CECS·T2·논지·목표가를 이번 주 요청서로 수집·승인하세요.",
                cta_label="주간 정성으로",
                page=PAGE_APPROVAL,
                focus=FOCUS_WEEKLY_QUAL,
            )
        )
    else:
        w_as_of = _weekly_as_of(ctx.root, weekly)
        rec_days = 14
        weekly_src = sources.get("weekly_qual_suggestions")
        if weekly_src and weekly_src.recommended_days is not None:
            rec_days = int(weekly_src.recommended_days)
        if w_as_of is not None and (today - w_as_of).days > rec_days:
            alerts.append(
                FreshnessAlert(
                    key="weekly_stale",
                    severity="warn",
                    title="주간 정성이 오래되었습니다",
                    detail=(
                        f"주간 정성 as_of {w_as_of.isoformat()} "
                        f"(권장 {rec_days}일). 새 요청서·승인을 검토하세요."
                    ),
                    cta_label="주간 정성으로",
                    page=PAGE_APPROVAL,
                    focus=FOCUS_WEEKLY_QUAL,
                )
            )
        pending = [
            k
            for k, ok in (weekly.get("approved") or {}).items()
            if not ok
            and (weekly.get("domain_status") or {}).get(k) == "ai_suggested"
        ]
        if pending:
            alerts.append(
                FreshnessAlert(
                    key="weekly_pending",
                    severity="warn",
                    title="주간 정성 승인이 남아 있습니다",
                    detail=f"미승인 영역: {', '.join(pending)}",
                    cta_label="승인판 열기",
                    page=PAGE_APPROVAL,
                    focus=FOCUS_WEEKLY_QUAL,
                )
            )

    missing_targets = _missing_target_tickers(ctx.portfolio_rows or [])
    if missing_targets:
        shown = ", ".join(missing_targets[:6])
        more = f" 외 {len(missing_targets) - 6}종" if len(missing_targets) > 6 else ""
        alerts.append(
            FreshnessAlert(
                key="targets_missing",
                severity="warn",
                title="제안 북에 목표가 없는 종목이 있습니다",
                detail=(
                    f"{shown}{more}. 편입 판단 전 E 보충·승인으로 exit YAML을 채우세요."
                ),
                cta_label="목표가 보충으로",
                page=PAGE_APPROVAL,
                focus=FOCUS_WEEKLY_QUAL,
            )
        )

    kospi = sources.get("kospi_pbr_history")
    if kospi is not None and kospi.exists and kospi.stale:
        as_of = kospi.as_of.isoformat() if kospi.as_of else "—"
        alerts.append(
            FreshnessAlert(
                key="kospi_pbr",
                severity="warn",
                title="T3용 시장 PBR 이력이 오래되었습니다",
                detail=f"KOSPI PBR as_of {as_of}. 월간 판정 전에 갱신하세요.",
                cta_label="정량 전체 갱신",
                page=PAGE_APPROVAL,
                focus=FOCUS_DATA_REFRESH,
                inline_quant_refresh=True,
            )
        )

    fundamentals = sources.get("fundamentals")
    if fundamentals is not None and fundamentals.exists and fundamentals.stale:
        as_of = fundamentals.as_of.isoformat() if fundamentals.as_of else "—"
        alerts.append(
            FreshnessAlert(
                key="fundamentals",
                severity="warn",
                title="펀더멘털이 오래되었습니다",
                detail=(
                    f"fundamentals as_of {as_of} "
                    f"(권장 {fundamentals.recommended_days or 90}일)."
                ),
                cta_label="정량 전체 갱신",
                page=PAGE_APPROVAL,
                focus=FOCUS_DATA_REFRESH,
                inline_quant_refresh=True,
            )
        )

    return alerts


def cadence_guide() -> tuple[CadenceGuideItem, ...]:
    return CADENCE_GUIDE
