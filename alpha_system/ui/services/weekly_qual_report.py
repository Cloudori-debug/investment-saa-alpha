"""Weekly integrated qualitative AI report — request schema A–E + parser.

Sections:
  A_CECS_SUMMARY — shortlist 30 CECS axis summaries
  B_FINAL6_DEEP — deep dive for proposed six
  C_T2_EVENTS — commercial code / MSCI / IFRS18
  D_THESIS — thesis damage signs
  E_TARGET_VALUATION — target PBR/price proposals for six

AI suggestions stay domain-isolated until separate approval gates apply them.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from alpha_system.journal import append_record
from alpha_system.ui.services.cecs_ai_research import (
    USAGE_WARNING,
    CecsResearchSubject,
    ParsedResearchAxis,
    ParsedResearchSuggestion,
    parse_cecs_ai_research_markdown,
)

SECTION_IDS = (
    "A_CECS_SUMMARY",
    "B_FINAL6_DEEP",
    "C_T2_EVENTS",
    "D_THESIS",
    "E_TARGET_VALUATION",
)

DOMAIN_KEYS = ("cecs", "t2", "thesis", "targets")


@dataclass(frozen=True)
class WeeklySubject:
    ticker: str
    name: str
    sector: str = ""


@dataclass(frozen=True)
class WeeklyQualReport:
    markdown: str
    path: Path
    report_id: str
    as_of: date
    generated_at: datetime
    input_snapshot_hash: str
    summary_tickers: tuple[str, ...]
    deep_tickers: tuple[str, ...]


@dataclass(frozen=True)
class ParsedT2Event:
    event_id: str
    fired: bool
    rationale: str
    sources: tuple[str, ...]


@dataclass(frozen=True)
class ParsedThesis:
    damage: bool
    rationale: str
    sources: tuple[str, ...]


@dataclass(frozen=True)
class ParsedTargetValuation:
    ticker: str
    name: str
    pbr_max: float | None
    target_price: float | None
    rationale: str
    sources: tuple[str, ...]
    fundamental_reason: str


@dataclass(frozen=True)
class ParsedDeepDive:
    ticker: str
    name: str
    disclosure: str
    buyback_dividend: str
    pension: str
    investment_purpose: str
    risks: str
    sources: tuple[str, ...]


@dataclass
class WeeklyParseResult:
    report_id: str
    as_of: str
    input_snapshot_hash: str
    cecs_suggestions: tuple[ParsedResearchSuggestion, ...] = ()
    deep_dives: tuple[ParsedDeepDive, ...] = ()
    t2_events: tuple[ParsedT2Event, ...] = ()
    thesis: ParsedThesis | None = None
    targets: tuple[ParsedTargetValuation, ...] = ()
    domain_failures: dict[str, tuple[str, ...]] = field(default_factory=dict)
    domain_status: dict[str, str] = field(default_factory=dict)


def build_weekly_qual_markdown(
    *,
    summary_subjects: Sequence[WeeklySubject],
    deep_subjects: Sequence[WeeklySubject],
    t2_event_ids: Sequence[str],
    as_of: date,
    generated_at: datetime,
    report_id: str,
    input_snapshot_hash: str,
) -> str:
    lines = [
        "# 주간 통합 정성 AI 요청서",
        "",
        f"- report_id: `{report_id}`",
        f"- as_of: `{as_of.isoformat()}`",
        f"- generated_at: `{generated_at.isoformat(timespec='seconds')}`",
        f"- input_snapshot_hash: `{input_snapshot_hash}`",
        "",
        f"> {USAGE_WARNING}",
        "",
        "## 작성 규칙",
        "",
        "1. 섹션 헤더(`## A_CECS_SUMMARY` 등)와 필드 라벨을 변경하지 마세요.",
        "2. 확인 불가한 항목은 추정하지 말고 근거에 `확인 불가; 검색 키워드: ...`를 적으세요.",
        "3. 각 영역은 별도 승인됩니다. 한 섹션 실패가 다른 섹션을 자동 승인하지 않습니다.",
        "4. `target_portfolio.csv` 변경 제안은 금지입니다. 목표가 YAML 제안만 허용합니다.",
        "5. **숫자 칸 형식(파서 계약 — 반드시 준수)**",
        "   - CECS `점수 제안(0-100):` → **숫자만**. 예: `65`",
        "     금지: `65 (AI 초안)`, `65점`, `약 65`, 점수 칸에 `확인 불가`",
        "     못 정하면 `_____`만 (업로드 시 잠정 50). `확인 불가`는 근거·출처에만.",
        "   - 목표가 `pbr_max:` → **숫자만**. 예: `0.75`",
        "     금지: `0.75배`, `0.7배 (2028년 목표)`, `1.4배 (대신증권…)`",
        "   - 목표가 `target_price:` → **원 단위 숫자만** (쉼표·원·범위·주석 금지). 예: `48000`",
        "     금지: `48,000원`, `200,000~250,000원`, `150000원 (한화…)`",
        "   - `pbr_max`와 `target_price` 중 **최소 1개**는 숫자로 채우세요. 둘 다 `_____`면 업로드 실패.",
        "   - 증권사명·범위·근거 설명은 `펀더멘털 사유`/`근거` 칸에만 쓰세요.",
        "   - 출처 URL은 줄마다 단독으로 적어도 됩니다.",
        "",
        "---",
        "",
        "## A_CECS_SUMMARY",
        "",
        "shortlist 30종 CECS 3축 요약. 종목 블록은 `## [TICKER] 이름` 형식을 유지하세요.",
        "각 축의 `점수 제안(0-100):`은 숫자만(또는 `_____`). 괄호·주석·한글을 붙이지 마세요.",
        "",
    ]
    for subject in summary_subjects:
        lines.extend(_cecs_block(subject))
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## B_FINAL6_DEEP",
            "",
            "최종 제안 6종 심층(공시·환원·연기금·투자목적·리스크).",
            "",
        ]
    )
    for subject in deep_subjects:
        lines.extend(
            [
                f"### DEEP [{subject.ticker}] {subject.name}",
                f"- 섹터: {subject.sector or '—'}",
                "- 공시/지배구조: _____",
                "- 자사주·배당·환원: _____",
                "- 연기금·수급: _____",
                "- 투자목적: _____",
                "- 리스크: _____",
                "- 출처:",
                "  - ",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "## C_T2_EVENTS",
            "",
            "제도 이벤트 발생 여부. fired는 true/false만.",
            "",
        ]
    )
    for eid in t2_event_ids:
        lines.extend(
            [
                f"### EVENT [{eid}]",
                "- fired: false",
                "- 근거: _____",
                "- 출처:",
                "  - ",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "## D_THESIS",
            "",
            "### THESIS",
            "- damage: false",
            "- 근거: _____",
            "- 출처:",
            "  - ",
            "",
            "---",
            "",
            "## E_TARGET_VALUATION",
            "",
            "제안 6종 목표가/PBR. target_portfolio 자동 변경 금지.",
            "`pbr_max`는 배수 숫자만(예: `0.75`), `target_price`는 원 단위 숫자만(예: `48000`).",
            "둘 중 최소 1개는 숫자. `배`/`원`/쉼표/범위(~)/증권사 주석은 근거 칸에만.",
            "",
        ]
    )
    for subject in deep_subjects:
        lines.extend(
            [
                f"### TARGET [{subject.ticker}] {subject.name}",
                "- pbr_max: _____",
                "- target_price: _____",
                "- 펀더멘털 사유: _____",
                "- 근거: _____",
                "- 출처:",
                "  - ",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_weekly_qual_report(
    *,
    summary_subjects: Sequence[WeeklySubject],
    deep_subjects: Sequence[WeeklySubject],
    t2_event_ids: Sequence[str],
    docs_dir: Path,
    as_of: date | None = None,
    generated_at: datetime | None = None,
    input_paths: Sequence[Path] | None = None,
    journal_path: Path | None = None,
) -> WeeklyQualReport:
    if not summary_subjects:
        raise ValueError("A_CECS_SUMMARY 대상이 없습니다.")
    if not deep_subjects:
        raise ValueError(
            "B/E(심층·목표가) 대상이 없습니다. proposal_book 최종 선정이 필요합니다."
        )
    generated_at = generated_at or datetime.now()
    as_of = as_of or generated_at.date()
    report_id = f"WQR-{generated_at.strftime('%Y%m%d-%H%M%S')}"
    input_snapshot_hash = _hash_inputs(input_paths or [])
    summary = tuple(_norm_subject(s) for s in summary_subjects)
    deep = tuple(_norm_subject(s) for s in deep_subjects)
    markdown = build_weekly_qual_markdown(
        summary_subjects=summary,
        deep_subjects=deep,
        t2_event_ids=t2_event_ids,
        as_of=as_of,
        generated_at=generated_at,
        report_id=report_id,
        input_snapshot_hash=input_snapshot_hash,
    )
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / f"weekly_qual_report_{generated_at.strftime('%Y%m%d')}.md"
    _atomic_write_text(path, markdown)
    append_record(
        action_kind="WEEKLY_QUAL_REPORT_GENERATED",
        as_of=as_of,
        subject=report_id,
        rationale=f"weekly qual request: {path.name}",
        payload={
            "path": str(path),
            "report_id": report_id,
            "input_snapshot_hash": input_snapshot_hash,
            "summary_tickers": [s.ticker for s in summary],
            "deep_tickers": [s.ticker for s in deep],
            "domains": list(DOMAIN_KEYS),
        },
        journal_path=journal_path,
    )
    return WeeklyQualReport(
        markdown=markdown,
        path=path,
        report_id=report_id,
        as_of=as_of,
        generated_at=generated_at,
        input_snapshot_hash=input_snapshot_hash,
        summary_tickers=tuple(s.ticker for s in summary),
        deep_tickers=tuple(s.ticker for s in deep),
    )


def parse_weekly_qual_markdown(text: str) -> WeeklyParseResult:
    meta = _parse_meta(text)
    sections = _split_sections(text)
    domain_failures: dict[str, list[str]] = {k: [] for k in DOMAIN_KEYS}
    domain_status: dict[str, str] = {k: "missing" for k in DOMAIN_KEYS}

    cecs_suggestions: tuple[ParsedResearchSuggestion, ...] = ()
    if "A_CECS_SUMMARY" in sections:
        parsed = parse_cecs_ai_research_markdown(sections["A_CECS_SUMMARY"])
        cecs_suggestions = parsed.suggestions
        if parsed.failures:
            domain_failures["cecs"].extend(parsed.failures)
        domain_status["cecs"] = (
            "ai_suggested" if cecs_suggestions else ("failed" if parsed.failures else "empty")
        )
    else:
        domain_failures["cecs"].append("A_CECS_SUMMARY 섹션 없음")

    deep_dives: list[ParsedDeepDive] = []
    if "B_FINAL6_DEEP" in sections:
        deep_dives, deep_fail = _parse_deep(sections["B_FINAL6_DEEP"])
        domain_failures["cecs"].extend(deep_fail)  # deep is CECS-adjacent qualitative
        # Deep alone must not mark CECS approvable — approve_domain reads `cecs` only.
    else:
        domain_failures["cecs"].append("B_FINAL6_DEEP 섹션 없음")

    t2_events: list[ParsedT2Event] = []
    if "C_T2_EVENTS" in sections:
        t2_events, t2_fail = _parse_t2(sections["C_T2_EVENTS"])
        domain_failures["t2"].extend(t2_fail)
        domain_status["t2"] = (
            "ai_suggested" if t2_events else ("failed" if t2_fail else "empty")
        )
    else:
        domain_failures["t2"].append("C_T2_EVENTS 섹션 없음")

    thesis: ParsedThesis | None = None
    if "D_THESIS" in sections:
        thesis, th_fail = _parse_thesis(sections["D_THESIS"])
        domain_failures["thesis"].extend(th_fail)
        domain_status["thesis"] = (
            "ai_suggested" if thesis is not None else ("failed" if th_fail else "empty")
        )
    else:
        domain_failures["thesis"].append("D_THESIS 섹션 없음")

    targets: list[ParsedTargetValuation] = []
    if "E_TARGET_VALUATION" in sections:
        targets, tg_fail = _parse_targets(sections["E_TARGET_VALUATION"])
        domain_failures["targets"].extend(tg_fail)
        domain_status["targets"] = (
            "ai_suggested" if targets else ("failed" if tg_fail else "empty")
        )
    else:
        domain_failures["targets"].append("E_TARGET_VALUATION 섹션 없음")

    return WeeklyParseResult(
        report_id=meta.get("report_id", ""),
        as_of=meta.get("as_of", ""),
        input_snapshot_hash=meta.get("input_snapshot_hash", ""),
        cecs_suggestions=cecs_suggestions,
        deep_dives=tuple(deep_dives),
        t2_events=tuple(t2_events),
        thesis=thesis,
        targets=tuple(targets),
        domain_failures={k: tuple(v) for k, v in domain_failures.items()},
        domain_status=domain_status,
    )


def persist_weekly_suggestions(
    *,
    root: Path,
    parsed: WeeklyParseResult,
    report_name: str,
    as_of: date,
    journal_path: Path | None = None,
    locked_deep_tickers: Sequence[str] | None = None,
) -> Path:
    """Store domain-isolated AI suggestions without applying to engine inputs."""
    out = root / "data" / "weekly_qual_suggestions.json"
    previous: dict[str, Any] = {}
    if out.exists():
        try:
            previous = json.loads(out.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = {}
    payload = {
        "report_id": parsed.report_id,
        "report_name": report_name,
        "as_of": as_of.isoformat(),
        "input_snapshot_hash": parsed.input_snapshot_hash,
        "imported_at": datetime.now().isoformat(timespec="seconds"),
        "domain_status": {
            k: ("ai_suggested" if parsed.domain_status.get(k) == "ai_suggested" else "empty")
            for k in DOMAIN_KEYS
        },
        "domain_failures": parsed.domain_failures,
        "cecs": [_suggestion_dict(s) for s in parsed.cecs_suggestions],
        "deep_dives": [asdict(d) for d in parsed.deep_dives],
        "t2": [asdict(e) for e in parsed.t2_events],
        "thesis": asdict(parsed.thesis) if parsed.thesis else None,
        "targets": [asdict(t) for t in parsed.targets],
        # Proposal-only allowlist: deep_dives (B) only — never union targets (E),
        # or a rogue target ticker could admit itself. Prefer caller lock, else
        # previous snapshot from report generation, else deep_dives tickers.
        "deep_tickers": _resolve_locked_deep_tickers(
            locked_deep_tickers=locked_deep_tickers,
            previous=previous,
            deep_dives=parsed.deep_dives,
        ),
        "source_reviewed": {k: [] for k in DOMAIN_KEYS},
        "approved": {k: False for k in DOMAIN_KEYS},
    }
    _preserve_unchanged_approvals(payload, previous)
    out.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(out, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    append_record(
        action_kind="WEEKLY_QUAL_IMPORT",
        as_of=as_of,
        subject=parsed.report_id or report_name,
        rationale="weekly qual import → domain ai_suggested (not applied)",
        payload={
            "path": str(out),
            "domain_status": payload["domain_status"],
            "failures": parsed.domain_failures,
        },
        journal_path=journal_path,
    )
    return out


def _preserve_unchanged_approvals(
    payload: dict[str, Any],
    previous: dict[str, Any],
) -> None:
    """Keep an approved domain only when the same report carries identical data."""
    if not previous:
        return
    same_report = (
        str(previous.get("report_id") or "") == str(payload.get("report_id") or "")
        and str(previous.get("input_snapshot_hash") or "")
        == str(payload.get("input_snapshot_hash") or "")
    )
    if not same_report:
        return

    domain_data_keys = {
        "cecs": ("cecs",),
        "t2": ("t2",),
        "thesis": ("thesis",),
        "targets": ("targets",),
    }
    for domain, keys in domain_data_keys.items():
        was_approved = bool((previous.get("approved") or {}).get(domain))
        unchanged = all(
            _json_equivalent(previous.get(key), payload.get(key))
            for key in keys
        )
        if not (was_approved and unchanged):
            continue
        payload["approved"][domain] = True
        payload["domain_status"][domain] = "approved"
        payload["source_reviewed"][domain] = list(
            (previous.get("source_reviewed") or {}).get(domain) or []
        )
        old_meta = (previous.get("approved_meta") or {}).get(domain)
        if old_meta is not None:
            payload.setdefault("approved_meta", {})[domain] = old_meta


def _json_equivalent(left: Any, right: Any) -> bool:
    """Compare persisted JSON data with dataclass/asdict tuples normalized."""
    return json.dumps(left, ensure_ascii=False, sort_keys=True) == json.dumps(
        right,
        ensure_ascii=False,
        sort_keys=True,
    )


def load_weekly_suggestions(root: Path) -> dict[str, Any]:
    path = root / "data" / "weekly_qual_suggestions.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def subjects_from_cecs_df(cecs_df: Any, *, limit: int | None = 30) -> list[WeeklySubject]:
    import pandas as pd

    if cecs_df is None or getattr(cecs_df, "empty", True):
        return []
    rows: list[WeeklySubject] = []
    for _, row in cecs_df.iterrows():
        rows.append(
            WeeklySubject(
                ticker=str(row.get("ticker", "")).zfill(6),
                name=str(row.get("name", "") or ""),
                sector=str(row.get("sector", "") or ""),
            )
        )
        if limit is not None and len(rows) >= limit:
            break
    return rows


def subjects_from_portfolio_rows(rows: Sequence[Any]) -> list[WeeklySubject]:
    out: list[WeeklySubject] = []
    for row in rows:
        out.append(
            WeeklySubject(
                ticker=str(getattr(row, "ticker", "")).zfill(6),
                name=str(getattr(row, "name", "") or ""),
                sector=str(getattr(row, "sector", "") or ""),
            )
        )
    return out


def _cecs_block(subject: WeeklySubject) -> list[str]:
    lines = [
        f"## [{subject.ticker}] {subject.name}",
        f"- 섹터: {subject.sector or '—'}",
        "",
    ]
    for axis in ("execution", "pension", "purpose"):
        lines.extend(
            [
                f"### {axis}",
                "- 점수 제안(0-100): _____",
                "- 근거: _____",
                "- 출처:",
                "  - ",
                "",
            ]
        )
    return lines


def _norm_subject(subject: WeeklySubject) -> WeeklySubject:
    return WeeklySubject(
        ticker=str(subject.ticker).zfill(6),
        name=(subject.name or "").strip(),
        sector=(subject.sector or "").strip(),
    )


def _hash_inputs(paths: Sequence[Path]) -> str:
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p).lower()):
        if not path.exists():
            h.update(f"{path}=missing\n".encode("utf-8"))
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        h.update(f"{path.as_posix()}={digest}\n".encode("utf-8"))
    return h.hexdigest()[:16]


def _parse_meta(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for key in ("report_id", "as_of", "input_snapshot_hash"):
        m = re.search(rf"-\s*{key}:\s*`([^`]+)`", text)
        if m:
            out[key] = m.group(1).strip()
    return out


def _split_sections(text: str) -> dict[str, str]:
    pattern = re.compile(
        r"^##\s+(A_CECS_SUMMARY|B_FINAL6_DEEP|C_T2_EVENTS|D_THESIS|E_TARGET_VALUATION)\s*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    out: dict[str, str] = {}
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[match.group(1)] = text[start:end].strip()
    return out


def _parse_sources(block: str) -> tuple[str, ...]:
    sources: list[str] = []
    in_sources = False
    for raw in block.splitlines():
        line = raw.rstrip()
        if re.match(r"^\s*-\s*출처\s*:", line):
            inline = line.split(":", 1)[1].strip()
            if inline and inline not in {"_____", ""}:
                sources.append(inline)
            in_sources = True
            continue
        if in_sources:
            m = re.match(r"^\s*-\s+(.+)$", line)
            if m:
                val = m.group(1).strip()
                if val and val != "_____":
                    sources.append(val)
            elif line.strip() and not line.strip().startswith("-"):
                in_sources = False
    if not sources:
        return ("확인 불가",)
    return tuple(sources)


def _field(block: str, label: str) -> str:
    m = re.search(rf"-\s*{re.escape(label)}\s*:\s*(.+)$", block, re.MULTILINE)
    if not m:
        return ""
    return m.group(1).strip()


def _parse_deep(text: str) -> tuple[list[ParsedDeepDive], list[str]]:
    chunks = re.split(r"(?m)^###\s+DEEP\s+\[", text)
    out: list[ParsedDeepDive] = []
    failures: list[str] = []
    for chunk in chunks[1:]:
        header, _, body = chunk.partition("\n")
        hm = re.match(r"(\d{6})\]\s*(.*)$", header.strip())
        if not hm:
            failures.append(f"DEEP 헤더 파싱 실패: {header[:40]}")
            continue
        ticker, name = hm.group(1), hm.group(2).strip()
        sources = _parse_sources(body)
        out.append(
            ParsedDeepDive(
                ticker=ticker,
                name=name,
                disclosure=_field(body, "공시/지배구조") or "확인 불가",
                buyback_dividend=_field(body, "자사주·배당·환원") or "확인 불가",
                pension=_field(body, "연기금·수급") or "확인 불가",
                investment_purpose=_field(body, "투자목적") or "확인 불가",
                risks=_field(body, "리스크") or "확인 불가",
                sources=sources,
            )
        )
    return out, failures


def _parse_t2(text: str) -> tuple[list[ParsedT2Event], list[str]]:
    chunks = re.split(r"(?m)^###\s+EVENT\s+\[", text)
    out: list[ParsedT2Event] = []
    failures: list[str] = []
    for chunk in chunks[1:]:
        header, _, body = chunk.partition("\n")
        eid = header.strip().rstrip("]")
        if not eid:
            failures.append("EVENT id 없음")
            continue
        fired_raw = _field(body, "fired").lower()
        if fired_raw not in {"true", "false"}:
            failures.append(f"{eid}: fired는 true/false 필요")
            continue
        rationale = _field(body, "근거")
        if not rationale or rationale == "_____":
            failures.append(f"{eid}: 근거 필요")
            continue
        out.append(
            ParsedT2Event(
                event_id=eid,
                fired=fired_raw == "true",
                rationale=rationale,
                sources=_parse_sources(body),
            )
        )
    return out, failures


def _parse_thesis(text: str) -> tuple[ParsedThesis | None, list[str]]:
    m = re.search(r"(?ms)^###\s+THESIS\s*$(.*)", text)
    if not m:
        return None, ["THESIS 블록 없음"]
    body = m.group(1)
    damage_raw = _field(body, "damage").lower()
    if damage_raw not in {"true", "false"}:
        return None, ["damage는 true/false 필요"]
    rationale = _field(body, "근거")
    if not rationale or rationale == "_____":
        return None, ["논지 근거 필요"]
    return (
        ParsedThesis(
            damage=damage_raw == "true",
            rationale=rationale,
            sources=_parse_sources(body),
        ),
        [],
    )


def _parse_targets(text: str) -> tuple[list[ParsedTargetValuation], list[str]]:
    chunks = re.split(r"(?m)^###\s+TARGET\s+\[", text)
    out: list[ParsedTargetValuation] = []
    failures: list[str] = []
    for chunk in chunks[1:]:
        header, _, body = chunk.partition("\n")
        hm = re.match(r"(\d{6})\]\s*(.*)$", header.strip())
        if not hm:
            failures.append(f"TARGET 헤더 파싱 실패: {header[:40]}")
            continue
        ticker, name = hm.group(1), hm.group(2).strip()
        fund_reason = _field(body, "펀더멘털 사유")
        rationale = _field(body, "근거")
        if not fund_reason or fund_reason == "_____":
            failures.append(f"{ticker}: 펀더멘털 사유 필요")
            continue
        if not rationale or rationale == "_____":
            failures.append(f"{ticker}: 근거 필요")
            continue
        pbr_raw = _field(body, "pbr_max")
        price_raw = _field(body, "target_price")
        pbr = _float_blank(pbr_raw)
        price = _float_blank(price_raw)
        if pbr is None and price is None:
            failures.append(f"{ticker}: pbr_max 또는 target_price 필요")
            continue
        sources = _parse_sources(body)
        if sources == ("확인 불가",):
            failures.append(f"{ticker}: 출처 필요")
            continue
        out.append(
            ParsedTargetValuation(
                ticker=ticker,
                name=name,
                pbr_max=pbr,
                target_price=price,
                rationale=rationale,
                sources=sources,
                fundamental_reason=fund_reason,
            )
        )
    return out, failures


def _float_blank(raw: str) -> float | None:
    text = (raw or "").strip()
    if not text or text in {"_____", "확인 불가", "-"}:
        return None
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def _resolve_locked_deep_tickers(
    *,
    locked_deep_tickers: Sequence[str] | None,
    previous: Mapping[str, Any],
    deep_dives: Sequence[Any],
) -> list[str]:
    """Proposal-book allowlist only — never expand from targets section."""
    if locked_deep_tickers:
        return sorted(
            {
                str(t).zfill(6)
                for t in locked_deep_tickers
                if str(t).strip()
            }
        )
    prev = previous.get("deep_tickers") or []
    if prev:
        return sorted({str(t).zfill(6) for t in prev if str(t).strip()})
    return sorted(
        {
            str(getattr(d, "ticker", "") or "").zfill(6)
            for d in deep_dives
            if getattr(d, "ticker", None)
        }
    )


def _suggestion_dict(suggestion: ParsedResearchSuggestion) -> dict[str, Any]:
    def axis(a: ParsedResearchAxis) -> dict[str, Any]:
        return {
            "score_100": a.score_100,
            "rationale": a.rationale,
            "sources": list(a.sources),
            "provisional": bool(getattr(a, "provisional", False)),
        }

    return {
        "ticker": suggestion.ticker,
        "name": suggestion.name,
        "execution": axis(suggestion.execution),
        "pension": axis(suggestion.pension),
        "purpose": axis(suggestion.purpose),
    }


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def load_exit_target_tickers(root: Path) -> set[str]:
    """Approved target-valuation tickers from kr_alpha_exit_targets.yaml."""
    import yaml

    path = root / "data" / "kr_alpha_exit_targets.yaml"
    if not path.exists():
        return set()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return set()
    tickers = data.get("tickers") or {}
    return {str(t).zfill(6) for t in tickers if str(t).strip()}


def waiting_target_subjects(
    proposal_rows: Sequence[Any],
    *,
    root: Path,
) -> list[WeeklySubject]:
    """Proposal-book names that still lack approved exit target valuation."""
    have = load_exit_target_tickers(root)
    waiting: list[WeeklySubject] = []
    for row in subjects_from_portfolio_rows(proposal_rows):
        if row.ticker not in have:
            waiting.append(row)
    return waiting


def build_targets_supplement_markdown(
    *,
    waiting_subjects: Sequence[WeeklySubject],
    proposal_tickers: Sequence[str],
    as_of: date,
    generated_at: datetime,
    report_id: str,
) -> str:
    """E-only request for waiting candidates (no A–D redo)."""
    subjects = tuple(_norm_subject(s) for s in waiting_subjects)
    prop = sorted({str(t).zfill(6) for t in proposal_tickers if str(t).strip()})
    lines = [
        "# 목표가 대기 후보 보충 요청서 (E only)",
        "",
        f"- report_id: `{report_id}`",
        f"- as_of: `{as_of.isoformat()}`",
        f"- generated_at: `{generated_at.isoformat(timespec='seconds')}`",
        "- mode: `targets_supplement`",
        f"- proposal_tickers: `{', '.join(prop)}`",
        f"- waiting_tickers: `{', '.join(s.ticker for s in subjects)}`",
        "",
        f"> {USAGE_WARNING}",
        "",
        "이 파일은 **목표가(E)만** 채웁니다. CECS/T2/논지는 건드리지 마세요.",
        "대상은 현재 제안 북 중 목표가 미승인(대기) 종목뿐입니다.",
        "`pbr_max`는 배수 숫자만, `target_price`는 원 단위 숫자만.",
        "",
        "---",
        "",
        "## E_TARGET_VALUATION",
        "",
    ]
    for subject in subjects:
        lines.extend(
            [
                f"### TARGET [{subject.ticker}] {subject.name}",
                "- pbr_max: _____",
                "- target_price: _____",
                "- 펀더멘털 사유: _____",
                "- 근거: _____",
                "- 출처:",
                "  - ",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_targets_supplement_report(
    *,
    waiting_subjects: Sequence[WeeklySubject],
    proposal_tickers: Sequence[str],
    docs_dir: Path,
    as_of: date | None = None,
    generated_at: datetime | None = None,
    journal_path: Path | None = None,
) -> WeeklyQualReport:
    if not waiting_subjects:
        raise ValueError("대기 후보(목표가 미승인)가 없습니다.")
    generated_at = generated_at or datetime.now()
    as_of = as_of or generated_at.date()
    report_id = f"WQR-E-{generated_at.strftime('%Y%m%d-%H%M%S')}"
    waiting = tuple(_norm_subject(s) for s in waiting_subjects)
    prop = sorted({str(t).zfill(6) for t in proposal_tickers if str(t).strip()})
    markdown = build_targets_supplement_markdown(
        waiting_subjects=waiting,
        proposal_tickers=prop,
        as_of=as_of,
        generated_at=generated_at,
        report_id=report_id,
    )
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / f"weekly_qual_targets_supplement_{generated_at.strftime('%Y%m%d')}.md"
    _atomic_write_text(path, markdown)
    append_record(
        action_kind="WEEKLY_TARGETS_SUPPLEMENT_GENERATED",
        as_of=as_of,
        subject=report_id,
        rationale=f"targets supplement request: {path.name}",
        payload={
            "path": str(path),
            "report_id": report_id,
            "waiting_tickers": [s.ticker for s in waiting],
            "proposal_tickers": prop,
            "domains": ["targets"],
        },
        journal_path=journal_path,
    )
    return WeeklyQualReport(
        markdown=markdown,
        path=path,
        report_id=report_id,
        as_of=as_of,
        generated_at=generated_at,
        input_snapshot_hash="",
        summary_tickers=(),
        deep_tickers=tuple(s.ticker for s in waiting),
    )


def persist_targets_supplement(
    *,
    root: Path,
    parsed: WeeklyParseResult,
    report_name: str,
    as_of: date,
    proposal_tickers: Sequence[str],
    waiting_tickers: Sequence[str],
    journal_path: Path | None = None,
) -> Path:
    """Merge E-only upload into suggestions without wiping other domains."""
    if not parsed.targets:
        raise ValueError("목표가 제안이 없습니다. E_TARGET_VALUATION을 채우세요.")
    prop = sorted({str(t).zfill(6) for t in proposal_tickers if str(t).strip()})
    waiting = {str(t).zfill(6) for t in waiting_tickers if str(t).strip()}
    if not prop:
        raise ValueError("proposal_tickers(최종 선정)가 필요합니다.")
    for t in parsed.targets:
        tk = str(t.ticker).zfill(6)
        if tk not in prop:
            raise ValueError(
                f"목표가 보충 거부: 최종 선정 밖 종목 {tk}. "
                "현재 proposal_book 기준으로 다시 생성하세요."
            )
        if waiting and tk not in waiting:
            raise ValueError(
                f"목표가 보충 거부: 대기 목록에 없는 종목 {tk}."
            )

    out = root / "data" / "weekly_qual_suggestions.json"
    previous = load_weekly_suggestions(root)
    payload = dict(previous) if previous else {}
    payload.setdefault("domain_status", {k: "empty" for k in DOMAIN_KEYS})
    payload.setdefault("domain_failures", {k: [] for k in DOMAIN_KEYS})
    payload.setdefault("source_reviewed", {k: [] for k in DOMAIN_KEYS})
    payload.setdefault("approved", {k: False for k in DOMAIN_KEYS})
    payload["report_id"] = parsed.report_id or payload.get("report_id") or "WQR-E"
    payload["report_name"] = report_name
    payload["as_of"] = as_of.isoformat()
    payload["imported_at"] = datetime.now().isoformat(timespec="seconds")
    payload["mode"] = "targets_supplement"
    payload["deep_tickers"] = prop
    # Merge targets: keep prior non-waiting rows, replace waiting tickers.
    prior_targets = [
        t
        for t in (payload.get("targets") or [])
        if str(t.get("ticker") or "").zfill(6) not in waiting
    ]
    new_targets = [asdict(t) for t in parsed.targets]
    payload["targets"] = prior_targets + new_targets
    payload["domain_status"]["targets"] = "ai_suggested"
    payload["domain_failures"]["targets"] = list(
        (parsed.domain_failures or {}).get("targets") or []
    )
    payload["source_reviewed"]["targets"] = []
    payload["approved"]["targets"] = False

    out.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(out, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    append_record(
        action_kind="WEEKLY_TARGETS_SUPPLEMENT_IMPORT",
        as_of=as_of,
        subject=str(payload.get("report_id") or report_name),
        rationale="targets supplement import → targets ai_suggested only",
        payload={
            "path": str(out),
            "waiting_tickers": sorted(waiting),
            "proposal_tickers": prop,
            "target_tickers": [str(t.ticker).zfill(6) for t in parsed.targets],
        },
        journal_path=journal_path,
    )
    return out


# Keep CecsResearchSubject import available for callers that adapt lists.
__all__ = [
    "DOMAIN_KEYS",
    "SECTION_IDS",
    "WeeklySubject",
    "WeeklyQualReport",
    "WeeklyParseResult",
    "build_weekly_qual_markdown",
    "write_weekly_qual_report",
    "parse_weekly_qual_markdown",
    "persist_weekly_suggestions",
    "persist_targets_supplement",
    "load_weekly_suggestions",
    "load_exit_target_tickers",
    "waiting_target_subjects",
    "build_targets_supplement_markdown",
    "write_targets_supplement_report",
    "subjects_from_cecs_df",
    "subjects_from_portfolio_rows",
    "CecsResearchSubject",
]
