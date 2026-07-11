from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from src.compass.regime_engine import compute_compass
from src.compass.tier2_macro import load_macro_tier2
from src.config import load_yaml
from src.data_loader import load_market_indicators


@dataclass
class RegimeAutoSyncResult:
    as_of: str
    synced: bool = False
    computed_regime: str = ""
    previous_regime: str = ""
    applied_regime: str = ""
    reason: str = ""
    warnings: list[str] = field(default_factory=list)
    suggestion_path: str = ""


def _manual_regime_active(market) -> bool:
    raw = (market.regime or "").strip().upper()
    if raw in ("", "NEUTRAL", "AUTO"):
        return False
    expires = getattr(market, "regime_expires_date", None)
    if expires and market.date[:10] > expires[:10]:
        return False
    return True


def should_auto_sync_regime(market) -> bool:
    """수동 레짐이 없거나 만료·AUTO일 때 산출 레짐으로 동기화."""
    raw = (market.regime or "").strip().upper()
    if raw in ("", "NEUTRAL", "AUTO"):
        return True
    expires = getattr(market, "regime_expires_date", None)
    if expires and market.date[:10] > expires[:10]:
        return True
    return False


def _write_suggestion(
    output_dir: Path,
    *,
    as_of: str,
    computed: str,
    applied: str,
    manual_active: bool,
    synced: bool,
    detail: dict[str, Any],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "as_of": as_of,
        "computed_regime": computed,
        "applied_regime": applied,
        "manual_override_active": manual_active,
        "auto_synced": synced,
        **detail,
    }
    path = output_dir / "regime_auto_suggestion.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def sync_regime_from_compass(
    data_dir: Path,
    output_dir: Path,
    *,
    as_of: str | None = None,
    force: bool = False,
) -> RegimeAutoSyncResult:
    """산출 레짐(computed_regime)을 market_indicators.csv에 반영 (AUTO/만료 시)."""
    mi_path = data_dir / "market_indicators.csv"
    if not mi_path.exists():
        return RegimeAutoSyncResult(as_of=as_of or "", warnings=["market_indicators.csv 없음"])

    market = load_market_indicators(mi_path)
    as_of_date = as_of or market.date or date.today().isoformat()
    rules = load_yaml(data_dir / "compass_rules.yaml")
    tier2 = load_macro_tier2(data_dir / "macro_tier2.csv", as_of=as_of_date)

    sources_path = data_dir / "tier2_sources.yaml"
    sources = load_yaml(sources_path) if sources_path.exists() else {}
    auto_enabled = bool(sources.get("auto_regime_sync", True))
    ttl_days = int(sources.get("regime_auto_ttl_days", 7))

    compass = compute_compass(market, rules, tier2=tier2, use_manual_regime=True)
    computed = compass.computed_regime.value
    previous = (market.regime or "").strip()
    manual_active = _manual_regime_active(market)

    result = RegimeAutoSyncResult(
        as_of=as_of_date,
        computed_regime=computed,
        previous_regime=previous,
        applied_regime=compass.applied_regime.value,
    )

    suggestion_path = _write_suggestion(
        output_dir,
        as_of=as_of_date,
        computed=computed,
        applied=compass.applied_regime.value,
        manual_active=manual_active,
        synced=False,
        detail={
            "market_phase": compass.market_phase.value,
            "override_active": compass.override.active,
            "override_reason": compass.override.reason,
            "tier2_used": tier2 is not None,
        },
    )
    result.suggestion_path = str(suggestion_path)

    if not auto_enabled and not force:
        result.reason = "auto_regime_sync 비활성 (tier2_sources.yaml)"
        return result

    if manual_active and not force:
        result.reason = "수동 레짐 유효 — override 유지"
        return result

    if not should_auto_sync_regime(market) and not force:
        result.reason = "자동 동기화 조건 미충족"
        return result

    expires = (date.fromisoformat(as_of_date) + timedelta(days=ttl_days)).isoformat()
    df = pd.read_csv(mi_path, dtype=str, keep_default_na=False)
    if df.empty:
        result.warnings.append("market_indicators 비어 있음")
        return result

    df.iloc[-1, df.columns.get_loc("regime")] = computed
    if "regime_override_reason" in df.columns:
        df.iloc[-1, df.columns.get_loc("regime_override_reason")] = "auto_computed_regime"
    if "regime_set_date" in df.columns:
        df.iloc[-1, df.columns.get_loc("regime_set_date")] = as_of_date
    if "regime_expires_date" in df.columns:
        df.iloc[-1, df.columns.get_loc("regime_expires_date")] = expires
    df.to_csv(mi_path, index=False)

    result.synced = True
    result.applied_regime = computed
    result.reason = f"산출 레짐 {computed} 자동 반영 (만료 {expires})"

    _write_suggestion(
        output_dir,
        as_of=as_of_date,
        computed=computed,
        applied=computed,
        manual_active=False,
        synced=True,
        detail={"reason": result.reason, "expires": expires},
    )
    return result
