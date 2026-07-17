"""Rescore trigger hooks — values stay [TODO] in config; no silent schedule."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from alpha_system.schema import AlphaSystemConfig


@dataclass(frozen=True)
class RescoreDecision:
    should_rescore: bool
    matched_triggers: tuple[str, ...]
    reason: str


def evaluate_rescore_triggers(
    cfg: AlphaSystemConfig,
    *,
    as_of: date,
    fired_events: Iterable[str] = (),
) -> RescoreDecision:
    """
    Hook only: if config.rescore_triggers is empty ([TODO]), never auto-rescore.
    When filled, rescore iff any fired event id is listed.
    """
    triggers = list(cfg.scoring.rescore_triggers or [])
    if not triggers:
        return RescoreDecision(
            should_rescore=False,
            matched_triggers=(),
            reason=(
                f"as_of={as_of.isoformat()}: rescore_triggers [TODO] empty — "
                "hook idle (no default calendar)"
            ),
        )
    fired = set(fired_events)
    matched = tuple(sorted(t for t in triggers if t in fired))
    if matched:
        return RescoreDecision(
            should_rescore=True,
            matched_triggers=matched,
            reason=f"matched rescore triggers: {list(matched)}",
        )
    return RescoreDecision(
        should_rescore=False,
        matched_triggers=(),
        reason="configured triggers present but none fired in this snapshot",
    )
