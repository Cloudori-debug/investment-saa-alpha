"""Entry gates — target valuation pre-fill requirement."""

from __future__ import annotations

from alpha_system.schema import AlphaSystemConfig


def check_entry_target_valuation(
    cfg: AlphaSystemConfig,
    *,
    ticker: str,
    has_target_valuation: bool,
) -> tuple[bool, str]:
    """
    Return (blocked, detail).

  Confirmed: new entry blocked when per-name target valuation is missing.
    """
    _ = ticker
    if not cfg.exit.entry_require_target_valuation:
        return False, "entry_require_target_valuation=false"
    if has_target_valuation:
        return False, "target valuation on file"
    return (
        True,
        "entry blocked: per-name target valuation missing "
        "(exit.entry_require_target_valuation=true)",
    )
