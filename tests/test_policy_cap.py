from __future__ import annotations

from src.models import MarketIndicators
from src.policy_cap import apply_policy_cap_to_approval, resolve_policy_cap


def test_policy_cap_limits_full_with_alpha():
    market = MarketIndicators(
        date="2026-06-24",
        kospi=8471.0,
        kospi_recent_high=9114.0,
        vix=18.6,
        usdkrw=1540.0,
        regime="YELLOW_STABLE",
        regime_override_reason="BOK FSR Jun-2026: FSI 17.2 warning stage",
        regime_expires_date="2026-09-24",
    )
    cap = resolve_policy_cap(
        market,
        technical_scope="FULL_WITH_ALPHA",
        data_gate="GREEN",
        health_gate="GREEN",
    )
    assert cap.active is True
    assert cap.technical_execution_scope == "FULL_WITH_ALPHA"
    assert cap.capped_execution_scope == "ETF_ONLY"
    assert cap.max_operational_approval == "YELLOW"
    assert apply_policy_cap_to_approval("GREEN", cap) == "YELLOW"


def test_policy_cap_inactive_without_manual_regime():
    market = MarketIndicators(
        date="2026-06-24",
        regime="AUTO",
    )
    cap = resolve_policy_cap(
        market,
        technical_scope="FULL_WITH_ALPHA",
        data_gate="GREEN",
        health_gate="GREEN",
    )
    assert cap.active is False
    assert cap.capped_execution_scope == "FULL_WITH_ALPHA"
    assert apply_policy_cap_to_approval("GREEN", cap) == "GREEN"


def test_policy_cap_expired_manual_regime():
    market = MarketIndicators(
        date="2026-06-25",
        regime="YELLOW_STABLE",
        regime_expires_date="2026-06-01",
    )
    cap = resolve_policy_cap(
        market,
        technical_scope="FULL_WITH_ALPHA",
        data_gate="GREEN",
        health_gate="GREEN",
    )
    assert cap.active is True
    assert cap.expiry_status == "EXPIRED_REVIEW_REQUIRED"
    assert cap.capped_execution_scope == "ETF_ONLY"
