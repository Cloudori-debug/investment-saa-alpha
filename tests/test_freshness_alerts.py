"""Freshness alerts + cadence guide for home startup."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

from alpha_system.ui.services.data_freshness import SourceStatus
from alpha_system.ui.services.freshness_alerts import (
    build_freshness_alerts,
    cadence_guide,
)
from alpha_system.ui.services.nav import FOCUS_DATA_REFRESH, FOCUS_WEEKLY_QUAL, PAGE_APPROVAL


def _src(**kwargs) -> SourceStatus:
    base = dict(
        key="x",
        label="x",
        path="x",
        as_of=date.today(),
        recommended_days=7,
        stale=False,
        exists=True,
    )
    base.update(kwargs)
    return SourceStatus(**base)


def test_cadence_guide_has_deep_links() -> None:
    items = cadence_guide()
    assert len(items) >= 4
    assert any(i.focus == FOCUS_DATA_REFRESH for i in items)
    assert any(i.focus == FOCUS_WEEKLY_QUAL for i in items)


def test_build_freshness_alerts_prices_and_scores(tmp_path: Path) -> None:
    today = date(2026, 7, 19)
    ctx = SimpleNamespace(
        root=tmp_path,
        as_of=today,
        portfolio_rows=[],
        source_status=[
            _src(
                key="prices",
                label="prices",
                as_of=today - timedelta(days=5),
                recommended_days=1,
                stale=True,
            ),
            _src(
                key="alpha_scores",
                label="scores",
                as_of=today - timedelta(days=20),
                recommended_days=7,
                stale=True,
            ),
        ],
    )
    (tmp_path / "data").mkdir()
    alerts = build_freshness_alerts(ctx, today=today)
    keys = {a.key for a in alerts}
    assert "prices" in keys
    assert "alpha_scores_stale" in keys
    assert "weekly_missing" in keys
    price = next(a for a in alerts if a.key == "prices")
    assert price.page == PAGE_APPROVAL
    assert price.focus == FOCUS_DATA_REFRESH
    assert price.inline_quant_refresh is True
    assert price.cta_label


def test_build_freshness_alerts_missing_targets(tmp_path: Path) -> None:
    today = date(2026, 7, 19)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "weekly_qual_suggestions.json").write_text(
        '{"as_of":"2026-07-18","approved":{"cecs":true,"t2":true,"thesis":true,"targets":true},'
        '"domain_status":{"cecs":"approved","t2":"approved","thesis":"approved","targets":"approved"}}',
        encoding="utf-8",
    )
    row = SimpleNamespace(ticker="316140", has_target=False)
    ctx = SimpleNamespace(
        root=tmp_path,
        as_of=today,
        portfolio_rows=[row],
        source_status=[
            _src(key="prices", stale=False, as_of=today, recommended_days=1),
            _src(key="alpha_scores", stale=False, as_of=today, recommended_days=7),
        ],
    )
    alerts = build_freshness_alerts(ctx, today=today)
    assert any(a.key == "targets_missing" for a in alerts)
    target = next(a for a in alerts if a.key == "targets_missing")
    assert target.focus == FOCUS_WEEKLY_QUAL
    assert "316140" in target.detail
