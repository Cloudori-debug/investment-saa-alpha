from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from src.data_loader import _normalize_ticker, load_target_portfolio, normalize_target_weights_to_100, write_target_portfolio
from src.models import TargetRow

ChangeType = Literal["add", "trim", "remove", "adjust", "unchanged"]


@dataclass
class TargetChange:
    ticker: str
    name: str
    change_type: ChangeType
    old_weight: float | None
    new_weight: float
    asset_group: str
    reason: str


@dataclass
class TargetProposal:
    rows: list[TargetRow]
    changes: list[TargetChange] = field(default_factory=list)
    kr_alpha_sum: float = 0.0
    kr_alpha_budget: float | None = None
    warnings: list[str] = field(default_factory=list)


def load_kr_alpha_budget(output_dir: Path) -> float | None:
    path = output_dir / "target_asset_allocation.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    matched = df[df["asset_group"] == "kr_alpha"]
    if matched.empty:
        return None
    return float(matched.iloc[0]["final_target"])


def kr_alpha_target_sum(targets: list[TargetRow]) -> float:
    return round(sum(t.target_weight for t in targets if t.asset_group == "kr_alpha"), 2)


def _pick_name(ticker: str, raw_name: str | None) -> str | None:
    name = str(raw_name or "").strip()
    code = _normalize_ticker(ticker)
    if name and _normalize_ticker(name) != code and name != ticker:
        return name
    return None


def resolve_add_candidate(
    ticker: str,
    *,
    data_dir: Path | None = None,
    pools: list[dict[str, Any]] | None = None,
    default_new_weight: float = 2.0,
    default_min_weight: float = 1.0,
    default_max_weight: float = 4.0,
) -> dict[str, Any]:
    """추가 후보 dict — name을 universe·후보 풀에서 보강."""
    code = _normalize_ticker(ticker)
    merged: dict[str, Any] = {"ticker": code}

    for row in pools or []:
        if _normalize_ticker(str(row.get("ticker", ""))) != code:
            continue
        for key, val in row.items():
            if key == "ticker":
                continue
            if val is not None and str(val).strip() != "":
                merged[key] = val
        picked = _pick_name(code, merged.get("name"))
        if picked:
            merged["name"] = picked

    merged["ticker"] = code

    if not _pick_name(code, merged.get("name")) and data_dir is not None:
        from src.position_lookup import lookup_ticker_metadata

        meta = lookup_ticker_metadata(data_dir, code)
        merged["name"] = str(meta.get("name") or code)
        if not merged.get("sector"):
            merged["sector"] = str(meta.get("sector") or "")
    elif not merged.get("name"):
        merged["name"] = code

    merged.setdefault("target_weight", default_new_weight)
    merged.setdefault("min_weight", default_min_weight)
    merged.setdefault("max_weight", default_max_weight)
    merged.setdefault("role", "alpha_screener")
    return merged


def propose_target_changes(
    current: list[TargetRow],
    *,
    add_candidates: list[dict[str, Any]],
    trim_tickers: set[str],
    remove_tickers: set[str],
    kr_alpha_budget: float | None = None,
    default_new_weight: float = 2.0,
    default_min_weight: float = 1.0,
    default_max_weight: float = 4.0,
    data_dir: Path | None = None,
) -> TargetProposal:
    """Alpha 승인안 기반 target_portfolio 제안 (자동 반영 아님)."""
    from src.alpha.loaders import load_prices

    price_have: set[str] = set()
    if data_dir is not None:
        price_have = {p.ticker for p in load_prices(data_dir / "prices.csv")}

    row_map = {t.ticker: t.model_copy(deep=True) for t in current}
    changes: list[TargetChange] = []
    warnings: list[str] = []

    if data_dir is not None:
        from src.alpha.target_portfolio_guard import get_blocked_reintroductions, _normalize_ticker

        blocked = get_blocked_reintroductions(data_dir)
        for ticker in list(row_map):
            norm = _normalize_ticker(ticker)
            if norm in blocked:
                row = row_map.pop(ticker)
                warnings.append(
                    f"{ticker}: unintended removal block — proposal baseline에서 제외 "
                    f"(override_previous_removal 필요)"
                )
                changes.append(
                    TargetChange(
                        ticker,
                        row.name,
                        "remove",
                        row.target_weight,
                        0.0,
                        row.asset_group,
                        "blocked unintended reintroduction",
                    )
                )

    for ticker in trim_tickers:
        if ticker not in row_map:
            continue
        row = row_map[ticker]
        if row.asset_group != "kr_alpha":
            warnings.append(f"{ticker}: kr_alpha 외 종목 TRIM 스킵")
            continue
        old = row.target_weight
        new = row.min_weight
        row.target_weight = new
        changes.append(
            TargetChange(ticker, row.name, "trim", old, new, row.asset_group, "Alpha TRIM 승인")
        )

    for ticker in remove_tickers:
        if ticker not in row_map:
            continue
        row = row_map[ticker]
        if row.asset_group != "kr_alpha":
            warnings.append(f"{ticker}: kr_alpha 외 종목 REMOVE 스킵")
            continue
        old = row.target_weight
        row.target_weight = 0.0
        changes.append(
            TargetChange(ticker, row.name, "remove", old, 0.0, row.asset_group, "Alpha REPLACE/REMOVE 승인")
        )

    for cand in add_candidates:
        enriched = resolve_add_candidate(
            str(cand.get("ticker", "")),
            data_dir=data_dir,
            pools=[cand],
            default_new_weight=default_new_weight,
            default_min_weight=default_min_weight,
            default_max_weight=default_max_weight,
        )
        ticker = str(enriched["ticker"])
        if data_dir is not None:
            from src.alpha.target_portfolio_guard import get_blocked_reintroductions

            blocked = get_blocked_reintroductions(data_dir)
            norm = ticker.zfill(6) if ticker.isdigit() and len(ticker) < 6 else ticker
            if norm in blocked:
                warnings.append(
                    f"{ticker}: unintended removal block — approval_bridge 재편입 불가 "
                    f"(override_previous_removal 필요)"
                )
                continue
        if price_have and ticker not in price_have:
            warnings.append(f"{ticker}: 시세 미확보 — target 추가 스킵 (research-only)")
            continue
        if ticker in row_map and row_map[ticker].target_weight > 0:
            warnings.append(f"{ticker}: 이미 target에 존재")
            continue
        weight = float(enriched.get("target_weight", default_new_weight))
        display_name = str(enriched.get("name") or ticker)
        row = TargetRow(
            ticker=ticker,
            name=display_name,
            asset_group="kr_alpha",
            sector=str(enriched.get("sector", "")),
            role=str(enriched.get("role", "alpha_screener")),
            target_weight=weight,
            min_weight=float(enriched.get("min_weight", default_min_weight)),
            max_weight=float(enriched.get("max_weight", default_max_weight)),
        )
        row_map[ticker] = row
        changes.append(
            TargetChange(ticker, display_name, "add", None, weight, "kr_alpha", "Alpha BUY 후보 승인")
        )

    rows = [r for r in row_map.values() if not (r.asset_group == "kr_alpha" and r.target_weight <= 0)]
    kr_sum = kr_alpha_target_sum(rows)

    if kr_alpha_budget is not None and kr_sum > kr_alpha_budget + 0.01:
        factor = kr_alpha_budget / kr_sum if kr_sum else 1.0
        for row in rows:
            if row.asset_group != "kr_alpha":
                continue
            old = row.target_weight
            row.target_weight = round(old * factor, 2)
            if abs(old - row.target_weight) > 0.01:
                changes.append(
                    TargetChange(
                        row.ticker,
                        row.name,
                        "adjust",
                        old,
                        row.target_weight,
                        row.asset_group,
                        f"kr_alpha 예산 {kr_alpha_budget:.1f}% 맞춤 스케일",
                    )
                )
        kr_sum = kr_alpha_target_sum(rows)
        warnings.append(f"kr_alpha 합계를 Compass 예산에 맞게 {factor:.2%} 스케일 조정")

    return TargetProposal(
        rows=rows,
        changes=changes,
        kr_alpha_sum=kr_sum,
        kr_alpha_budget=kr_alpha_budget,
        warnings=warnings,
    )


def compute_full_diff(before: list[TargetRow], after: list[TargetRow]) -> list[TargetChange]:
    before_map = {t.ticker: t for t in before}
    after_map = {t.ticker: t for t in after}
    all_tickers = sorted(set(before_map) | set(after_map))
    diffs: list[TargetChange] = []

    for ticker in all_tickers:
        b = before_map.get(ticker)
        a = after_map.get(ticker)
        if b and a:
            if abs(b.target_weight - a.target_weight) < 0.01:
                continue
            ctype: ChangeType = "adjust"
            if a.target_weight < b.target_weight and a.target_weight <= a.min_weight:
                ctype = "trim"
            if a.target_weight == 0:
                ctype = "remove"
            diffs.append(
                TargetChange(
                    ticker,
                    a.name,
                    ctype,
                    b.target_weight,
                    a.target_weight,
                    a.asset_group,
                    "weight 변경",
                )
            )
        elif a and not b:
            diffs.append(
                TargetChange(ticker, a.name, "add", None, a.target_weight, a.asset_group, "신규 추가")
            )
        elif b and not a:
            diffs.append(
                TargetChange(ticker, b.name, "remove", b.target_weight, 0.0, b.asset_group, "제거")
            )
    return diffs


def write_proposal_outputs(proposal: TargetProposal, output_dir: Path) -> None:
    from src.alpha.target_write_audit import proposal_output_dir

    out_dir = proposal_output_dir(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_target_portfolio(proposal.rows, out_dir / "target_portfolio_proposed.csv")
    if proposal.changes:
        pd.DataFrame([c.__dict__ for c in proposal.changes]).to_csv(
            out_dir / "target_proposal_diff.csv",
            index=False,
            encoding="utf-8-sig",
        )


def apply_proposed_target(
    proposal: TargetProposal,
    target_path: Path,
    *,
    backup_dir: Path | None = None,
    approved_by: str = "human",
    data_dir: Path | None = None,
    output_dir: Path | None = None,
    approved_by_user: bool = True,
    override_previous_removal: frozenset[str] | None = None,
) -> Path:
    """사람 승인 후 data/target_portfolio.csv 반영. 백업 필수."""
    from src.alpha.target_write_audit import write_operational_target
    from src.validation.bundle_consistency import resolve_pipeline_run_id

    target_path.parent.mkdir(parents=True, exist_ok=True)
    data_dir = data_dir or target_path.parent
    out_dir = output_dir or (data_dir.parent / "outputs")
    pipeline_run_id = resolve_pipeline_run_id(out_dir)

    rows, normalized = normalize_target_weights_to_100(proposal.rows)
    if normalized:
        proposal.warnings.append(
            "target_weight 합계를 100%로 정규화 (이전 kr_alpha/전체 합 초과 방지)"
        )

    from src.alpha.target_portfolio_guard import (
        TargetPortfolioWriteBlockedError,
        filter_blocked_reintroduction_rows,
    )

    rows, stripped = filter_blocked_reintroduction_rows(data_dir, rows)
    proposal.warnings.extend(stripped)

    result = write_operational_target(
        data_dir,
        rows,
        source="approval_bridge",
        reason=f"alpha_proposal_approved_by={approved_by}",
        approved_by_user=approved_by_user,
        writer_module="target_bridge.apply_proposed_target",
        output_dir=out_dir,
        run_id=pipeline_run_id,
        proposal_source_id=str(out_dir / "proposals" / "target_portfolio_proposed.csv"),
        backup=bool(backup_dir is not False),
        override_previous_removal=override_previous_removal,
    )
    if result.blocked or not result.path:
        reason = result.audit.get("target_write_reason", "target write blocked")
        raise TargetPortfolioWriteBlockedError(reason)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = out_dir / "approval_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": stamp,
        "approved_by": approved_by,
        "target_path": str(result.path),
        "change_count": len(proposal.changes),
        "kr_alpha_sum": proposal.kr_alpha_sum,
        "warnings": proposal.warnings,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return result.path


def default_trim_candidates(holdings_review: list[dict]) -> set[str]:
    return {str(h["ticker"]) for h in holdings_review if h.get("review_action") == "TRIM"}


def default_remove_candidates(holdings_review: list[dict]) -> set[str]:
    return {str(h["ticker"]) for h in holdings_review if h.get("review_action") == "REPLACE_CANDIDATE"}


def default_add_candidates(
    candidates: list[dict],
    limit: int = 8,
    *,
    output_dir: Path | None = None,
    data_dir: Path | None = None,
) -> list[dict]:
    from src.alpha.portfolio_selector import load_portfolio_proposal
    from src.alpha.loaders import load_prices

    price_have: set[str] = set()
    if data_dir is not None:
        price_have = {p.ticker for p in load_prices(data_dir / "prices.csv")}

    if output_dir is not None:
        proposal = load_portfolio_proposal(output_dir)
        if proposal:
            out: list[dict] = []
            for row in proposal[:limit]:
                if row.get("eligible_action") == "NO_NEW":
                    continue
                if str(row.get("grade", "")) == "Reject":
                    continue
                ticker = str(row["ticker"])
                if price_have and ticker not in price_have:
                    continue
                out.append(
                    {
                        "ticker": row["ticker"],
                        "name": row.get("name", row["ticker"]),
                        "sector": row.get("sector", ""),
                        "grade": row.get("grade", "B"),
                        "eligible_action": row.get("eligible_action", "BUY_CANDIDATE"),
                        "target_weight": float(row.get("proposed_weight_pct", 2.5)),
                        "role": row.get("role", ""),
                    }
                )
            if out:
                return out

    out = []
    for row in candidates:
        if row.get("eligible_action") != "BUY_CANDIDATE":
            continue
        if row.get("grade") != "A":
            continue
        ticker = str(row.get("ticker", ""))
        if price_have and ticker not in price_have:
            continue
        out.append(row)
        if len(out) >= limit:
            break
    return out
