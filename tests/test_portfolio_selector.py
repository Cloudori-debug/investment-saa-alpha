from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.alpha.alpha_pipeline import run_alpha_pipeline
from src.alpha.loaders import load_alpha_scoring_config
from src.alpha.portfolio_selector import build_shortlist_and_proposal
from src.position_lookup import lookup_ticker_metadata

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_portfolio_selector_pillar_filter():
    cfg = load_alpha_scoring_config(DATA_DIR / "alpha_scoring.yaml")
    scored = [
        {
            "ticker": "AAA",
            "name": "A",
            "sector": "tech",
            "quality_score": 80,
            "valuation_score": 20,
            "momentum_score": 70,
            "shareholder_return_score": 30,
            "total_score": 55,
            "penalty": 0,
            "grade": "B",
            "eligible_action": "WATCH",
        },
        {
            "ticker": "BBB",
            "name": "B",
            "sector": "insurance",
            "quality_score": 70,
            "valuation_score": 75,
            "momentum_score": 60,
            "shareholder_return_score": 80,
            "total_score": 72,
            "penalty": 0,
            "grade": "A",
            "eligible_action": "BUY_CANDIDATE",
        },
    ]
    result = build_shortlist_and_proposal(scored, cfg, kr_alpha_budget=15.0)
    tickers = {s.ticker for s in result.shortlist}
    assert "BBB" in tickers
    assert "AAA" not in tickers
    assert len(result.proposal) >= 1
    assert result.proposal[0].role in {"core", "satellite", "value", "balanced"}


def test_alpha_pipeline_writes_proposal(tmp_path):
    out = run_alpha_pipeline(DATA_DIR, tmp_path)
    assert (tmp_path / "alpha_portfolio_proposal.csv").exists()
    assert (tmp_path / "alpha_shortlist.csv").exists()
    assert out.result.candidates


def test_lookup_ticker_metadata():
    meta = lookup_ticker_metadata(DATA_DIR, "005830")
    assert meta["ticker"] == "005830"
    assert meta["name"]
    assert meta["sources"]


def test_pillar_leaderboard_top10_per_axis(tmp_path):
    from src.alpha.loaders import load_alpha_scoring_config
    from src.alpha.portfolio_selector import build_pillar_leaderboard, build_shortlist_and_proposal

    cfg = load_alpha_scoring_config(DATA_DIR / "alpha_scoring.yaml")
    out = run_alpha_pipeline(DATA_DIR, tmp_path)
    lb = pd.read_csv(tmp_path / "alpha_pillar_leaderboard.csv")
    assert len(lb[lb["pillar"] == "quality"]) <= 10
    assert "validity_label" in lb.columns
    assert "005830" in lb["ticker"].astype(str).str.zfill(6).values or len(lb) > 0


def test_saa_taa_ticker_tables():
    from src.ui.allocation_tickers import build_saa_ticker_targets, build_taa_ticker_targets

    saa = build_saa_ticker_targets(DATA_DIR, "defensive_balanced")
    assert not saa.empty
    assert "ticker" in saa.columns
    assert saa["SAA목표(%)"].sum() == pytest.approx(100.0, abs=2.0)
    taa = build_taa_ticker_targets(DATA_DIR / ".." / "outputs", DATA_DIR)
    if (DATA_DIR.parent / "outputs" / "generated_target_portfolio.csv").exists():
        assert not taa.empty
