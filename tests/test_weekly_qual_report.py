"""Weekly integrated qualitative report + domain gates."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest
import yaml

from alpha_system.journal import clear_entries, list_entries
from alpha_system.ui.services.cecs_workbench import import_ai_suggestions, reopen_final_for_rescoring
from alpha_system.ui.services.weekly_domain_gates import approve_domain, mark_sources_reviewed
from alpha_system.ui.services.weekly_qual_report import (
    WeeklySubject,
    parse_weekly_qual_markdown,
    persist_targets_supplement,
    persist_weekly_suggestions,
    waiting_target_subjects,
    write_targets_supplement_report,
    write_weekly_qual_report,
)


def test_weekly_request_has_sections_a_to_e(tmp_path: Path) -> None:
    clear_entries()
    report = write_weekly_qual_report(
        summary_subjects=[
            WeeklySubject("005830", "DB손해보험", "insurance"),
            WeeklySubject("021240", "코웨이", "consumer"),
        ],
        deep_subjects=[WeeklySubject("005830", "DB손해보험", "insurance")],
        t2_event_ids=["commercial_code_enforcement_decrees"],
        docs_dir=tmp_path / "docs",
        as_of=date(2026, 7, 17),
        generated_at=datetime(2026, 7, 17, 16, 0, 0),
        journal_path=tmp_path / "journal.jsonl",
    )
    md = report.markdown
    for section in (
        "A_CECS_SUMMARY",
        "B_FINAL6_DEEP",
        "C_T2_EVENTS",
        "D_THESIS",
        "E_TARGET_VALUATION",
    ):
        assert f"## {section}" in md
    assert "## [005830] DB손해보험" in md
    assert "### DEEP [005830]" in md
    assert "### EVENT [commercial_code_enforcement_decrees]" in md
    assert "### THESIS" in md
    assert "### TARGET [005830]" in md
    assert "숫자 칸 형식" in md
    assert "65 (AI 초안)" in md  # as forbidden example in the rules
    assert "숫자만" in md
    assert "48000" in md  # target_price example
    assert "0.75" in md  # pbr_max example
    assert list_entries(action_kind="WEEKLY_QUAL_REPORT_GENERATED")
    clear_entries()


def test_weekly_be_requires_deep_subjects(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="proposal_book|B/E"):
        write_weekly_qual_report(
            summary_subjects=[WeeklySubject("005830", "DB손해보험", "insurance")],
            deep_subjects=[],
            t2_event_ids=["commercial_code_enforcement_decrees"],
            docs_dir=tmp_path / "docs",
            as_of=date(2026, 7, 18),
        )


def test_apply_targets_fails_closed_when_deep_tickers_empty(tmp_path: Path) -> None:
    clear_entries()
    root = tmp_path
    (root / "data").mkdir()
    (root / "data" / "target_portfolio.csv").write_text(
        "ticker,asset_group,target_weight\n005830,kr_alpha,10\n", encoding="utf-8"
    )
    suggestions = {
        "report_id": "WQR-empty-deep",
        "deep_tickers": [],
        "targets": [
            {
                "ticker": "005830",
                "pbr_max": 1.0,
                "fundamental_reason": "x",
                "rationale": "y",
                "sources": ["https://example.com"],
            }
        ],
        "source_reviewed": {"targets": ["005830"]},
        "approved": {k: False for k in ("cecs", "t2", "thesis", "targets")},
        "domain_status": {"targets": "ai_suggested"},
    }
    import json

    (root / "data" / "weekly_qual_suggestions.json").write_text(
        json.dumps(suggestions, ensure_ascii=False), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="deep_tickers"):
        approve_domain(
            root=root,
            domain="targets",
            approved_by="operator",
            as_of=date(2026, 7, 18),
            reviewed_keys=["005830"],
            journal_path=tmp_path / "j.jsonl",
            exit_targets_path=root / "data" / "kr_alpha_exit_targets.yaml",
            confirm_steps=2,
        )
    clear_entries()


def test_persist_deep_tickers_ignores_targets_union(tmp_path: Path) -> None:
    from alpha_system.ui.services.weekly_qual_report import (
        parse_weekly_qual_markdown,
        persist_weekly_suggestions,
    )

    root = tmp_path
    (root / "data").mkdir()
    parsed = parse_weekly_qual_markdown(_filled_weekly_md())
    out = persist_weekly_suggestions(
        root=root,
        parsed=parsed,
        report_name="x.md",
        as_of=date(2026, 7, 18),
        locked_deep_tickers=["005830"],
    )
    import json

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["deep_tickers"] == ["005830"]
    assert "999999" not in data["deep_tickers"]


def test_apply_targets_rejects_ticker_not_in_final_snapshot(tmp_path: Path) -> None:
    clear_entries()
    root = tmp_path
    (root / "data").mkdir()
    target_csv = root / "data" / "target_portfolio.csv"
    target_csv.write_text("ticker,asset_group,target_weight\n005830,kr_alpha,10\n", encoding="utf-8")
    suggestions = {
        "report_id": "WQR-test",
        "deep_tickers": ["005830"],
        "targets": [
            {
                "ticker": "999999",
                "pbr_max": 1.0,
                "fundamental_reason": "stale",
                "rationale": "not in final",
                "sources": ["https://example.com"],
            }
        ],
        "source_reviewed": {"targets": ["999999"]},
        "approved": {k: False for k in ("cecs", "t2", "thesis", "targets")},
        "domain_status": {"targets": "ai_suggested"},
    }
    import json

    (root / "data" / "weekly_qual_suggestions.json").write_text(
        json.dumps(suggestions, ensure_ascii=False), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="최종 선정"):
        approve_domain(
            root=root,
            domain="targets",
            approved_by="operator",
            as_of=date(2026, 7, 18),
            reviewed_keys=["999999"],
            journal_path=tmp_path / "j.jsonl",
            exit_targets_path=root / "data" / "kr_alpha_exit_targets.yaml",
            confirm_steps=2,
        )
    clear_entries()


def test_apply_targets_skips_stale_outside_proposal(tmp_path: Path) -> None:
    """Stale prior-final names are skipped; current proposal targets still apply."""
    clear_entries()
    root = tmp_path
    (root / "data").mkdir()
    target_csv = root / "data" / "target_portfolio.csv"
    target_csv.write_text("ticker,asset_group,target_weight\n005830,kr_alpha,10\n", encoding="utf-8")
    suggestions = {
        "report_id": "WQR-mix",
        "deep_tickers": ["005830"],
        "targets": [
            {
                "ticker": "036530",
                "pbr_max": 0.7,
                "fundamental_reason": "stale prior final",
                "rationale": "left proposal book",
                "sources": ["https://example.com/snt"],
            },
            {
                "ticker": "005830",
                "pbr_max": 1.2,
                "fundamental_reason": "current",
                "rationale": "in book",
                "sources": ["https://example.com/db"],
            },
        ],
        "source_reviewed": {"targets": ["036530", "005830"]},
        "approved": {k: False for k in ("cecs", "t2", "thesis", "targets")},
        "domain_status": {"targets": "ai_suggested"},
    }
    import json

    (root / "data" / "weekly_qual_suggestions.json").write_text(
        json.dumps(suggestions, ensure_ascii=False), encoding="utf-8"
    )
    result = approve_domain(
        root=root,
        domain="targets",
        approved_by="operator",
        as_of=date(2026, 7, 19),
        reviewed_keys=["036530", "005830"],
        journal_path=tmp_path / "j.jsonl",
        exit_targets_path=root / "data" / "kr_alpha_exit_targets.yaml",
        confirm_steps=0,
    )
    applied = result["applied"]
    assert applied["tickers"] == ["005830"]
    assert applied["skipped_not_in_proposal"] == ["036530"]
    saved = json.loads(
        (root / "data" / "weekly_qual_suggestions.json").read_text(encoding="utf-8")
    )
    assert [t["ticker"] for t in saved["targets"]] == ["005830"]
    yaml_text = (root / "data" / "kr_alpha_exit_targets.yaml").read_text(encoding="utf-8")
    assert "005830" in yaml_text
    assert "036530" not in yaml_text
    clear_entries()


def test_domain_approve_is_isolated_and_target_portfolio_unchanged(tmp_path: Path) -> None:
    clear_entries()
    root = tmp_path
    (root / "data").mkdir()
    target_csv = root / "data" / "target_portfolio.csv"
    target_csv.write_text("ticker,asset_group,target_weight\n005830,kr_alpha,10\n", encoding="utf-8")
    before = hashlib.sha256(target_csv.read_bytes()).hexdigest()

    cecs = root / "data" / "cecs_manual_scoring_template.csv"
    pd.DataFrame(
        [
            {
                "ticker": "005830",
                "name": "DB손해보험",
                "as_of": "2026-07-17",
                "sector": "insurance",
                "execution_continuity": "",
                "execution_rationale": "",
                "pension_flow_score": "",
                "pension_rationale": "",
                "investment_purpose_flag": "",
                "investment_purpose_rationale": "",
                "policy_dependency_flag": "0.50",
                "cecs_computed": "",
                "status": "final",
            }
        ]
    ).to_csv(cecs, index=False)

    filled = _filled_weekly_md()
    parsed = parse_weekly_qual_markdown(filled)
    assert parsed.domain_status["cecs"] == "ai_suggested"
    assert parsed.domain_status["t2"] == "ai_suggested"
    assert parsed.domain_status["thesis"] == "ai_suggested"
    assert parsed.domain_status["targets"] == "ai_suggested"

    persist_weekly_suggestions(
        root=root,
        parsed=parsed,
        report_name="weekly_filled.md",
        as_of=date(2026, 7, 17),
        journal_path=root / "journal.jsonl",
    )

    with pytest.raises(ValueError, match="출처 미확인"):
        approve_domain(
            root=root,
            domain="t2",
            approved_by="op",
            as_of=date(2026, 7, 17),
            reviewed_keys=[],
            confirm_steps=2,
            journal_path=root / "journal.jsonl",
            runtime_path=root / "data" / "alpha_dashboard_runtime.json",
        )

    mark_sources_reviewed(root=root, domain="t2", keys=["commercial_code_enforcement_decrees"])
    approve_domain(
        root=root,
        domain="t2",
        approved_by="op",
        as_of=date(2026, 7, 17),
        reviewed_keys=["commercial_code_enforcement_decrees"],
        confirm_steps=2,
        journal_path=root / "journal.jsonl",
        runtime_path=root / "data" / "alpha_dashboard_runtime.json",
    )

    payload = __import__("json").loads(
        (root / "data" / "weekly_qual_suggestions.json").read_text(encoding="utf-8")
    )
    assert payload["approved"]["t2"] is True
    assert payload["approved"]["cecs"] is False
    assert payload["approved"]["thesis"] is False
    assert payload["approved"]["targets"] is False

    # Upload alone did not demote final. Explicit domain approval performs an
    # audited re-open + immediate re-finalization in one operator action.
    assert pd.read_csv(cecs, dtype=str).iloc[0]["status"] == "final"
    mark_sources_reviewed(root=root, domain="cecs", keys=["005830"])
    approve_domain(
        root=root,
        domain="cecs",
        approved_by="op",
        as_of=date(2026, 7, 17),
        reviewed_keys=["005830"],
        journal_path=root / "journal.jsonl",
        cecs_path=cecs,
    )
    assert pd.read_csv(cecs, dtype=str).iloc[0]["status"] == "final"

    mark_sources_reviewed(root=root, domain="targets", keys=["005830"])
    approve_domain(
        root=root,
        domain="targets",
        approved_by="op",
        as_of=date(2026, 7, 17),
        reviewed_keys=["005830"],
        journal_path=root / "journal.jsonl",
        exit_targets_path=root / "data" / "kr_alpha_exit_targets.yaml",
    )
    yaml_data = yaml.safe_load(
        (root / "data" / "kr_alpha_exit_targets.yaml").read_text(encoding="utf-8")
    )
    assert yaml_data["tickers"]["005830"]["valuation"]["pbr_max"] == 1.2
    assert hashlib.sha256(target_csv.read_bytes()).hexdigest() == before

    kinds = {e.action_kind for e in list_entries()}
    assert "T2_EVENT_RECORD" in kinds
    assert "TARGET_VALUATION_MODIFY" in kinds
    assert "WEEKLY_DOMAIN_APPROVED" in kinds
    clear_entries()


def test_reupload_preserves_only_identical_approved_domains(tmp_path: Path) -> None:
    root = tmp_path
    (root / "data").mkdir()
    filled = _filled_weekly_md()
    parsed = parse_weekly_qual_markdown(filled)
    path = persist_weekly_suggestions(
        root=root,
        parsed=parsed,
        report_name="weekly_filled.md",
        as_of=date(2026, 7, 17),
        journal_path=root / "journal.jsonl",
    )
    json_mod = __import__("json")
    payload = json_mod.loads(path.read_text(encoding="utf-8"))
    payload["approved"]["cecs"] = True
    payload["approved"]["t2"] = True
    payload["domain_status"]["cecs"] = "approved"
    payload["domain_status"]["t2"] = "approved"
    payload["source_reviewed"]["cecs"] = ["005830"]
    payload["source_reviewed"]["t2"] = ["commercial_code_enforcement_decrees"]
    payload["approved_meta"] = {
        "cecs": {"approved_by": "op"},
        "t2": {"approved_by": "op"},
    }
    path.write_text(
        json_mod.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Identical re-upload keeps both approvals.
    persist_weekly_suggestions(
        root=root,
        parsed=parsed,
        report_name="weekly_filled_v2.md",
        as_of=date(2026, 7, 17),
        journal_path=root / "journal.jsonl",
    )
    same = json_mod.loads(path.read_text(encoding="utf-8"))
    assert same["approved"]["cecs"] is True
    assert same["approved"]["t2"] is True

    # Changing CECS invalidates CECS approval, while unchanged T2 stays approved.
    changed = parse_weekly_qual_markdown(
        filled.replace(
            "- 점수 제안(0-100): 80",
            "- 점수 제안(0-100): 81",
            1,
        )
    )
    persist_weekly_suggestions(
        root=root,
        parsed=changed,
        report_name="weekly_filled_v3.md",
        as_of=date(2026, 7, 17),
        journal_path=root / "journal.jsonl",
    )
    updated = json_mod.loads(path.read_text(encoding="utf-8"))
    assert updated["approved"]["cecs"] is False
    assert updated["approved"]["t2"] is True


def test_cecs_final_guard_blocks_import_without_reopen(tmp_path: Path) -> None:
    clear_entries()
    path = tmp_path / "cecs.csv"
    pd.DataFrame(
        [
            {
                "ticker": "005830",
                "name": "DB손해보험",
                "execution_continuity": "0.80",
                "pension_flow_score": "0.50",
                "investment_purpose_flag": "1.00",
                "policy_dependency_flag": "0.50",
                "cecs_computed": "70",
                "status": "final",
                "execution_rationale": "old",
                "pension_rationale": "old",
                "investment_purpose_rationale": "old",
            }
        ]
    ).to_csv(path, index=False)

    from alpha_system.ui.services.cecs_ai_research import parse_cecs_ai_research_markdown

    parsed = parse_cecs_ai_research_markdown(
        """## [005830] DB손해보험

### execution
- 점수 제안(0-100): 90
- 근거: new
- 출처: [1차 출처: DART](https://dart.fss.or.kr/e1)

### pension
- 점수 제안(0-100): 50
- 근거: new
- 출처: [1차 출처: DART](https://dart.fss.or.kr/p1)

### purpose
- 점수 제안(0-100): 100
- 근거: new
- 출처: [1차 출처: DART](https://dart.fss.or.kr/u1)
"""
    )
    result = import_ai_suggestions(
        path=path,
        suggestions=parsed.suggestions,
        report_name="x.md",
        as_of=date(2026, 7, 17),
        journal_path=tmp_path / "j.jsonl",
    )
    assert result.imported_tickers == ()
    assert any("final" in f for f in result.failures)
    assert pd.read_csv(path, dtype=str).iloc[0]["status"] == "final"

    reopen_final_for_rescoring(
        path=path,
        tickers=["005830"],
        reopened_by="op",
        as_of=date(2026, 7, 17),
        reason="주간 리포트 재채점",
        journal_path=tmp_path / "j.jsonl",
    )
    assert pd.read_csv(path, dtype=str).iloc[0]["status"] == "draft"
    result2 = import_ai_suggestions(
        path=path,
        suggestions=parsed.suggestions,
        report_name="x.md",
        as_of=date(2026, 7, 17),
        journal_path=tmp_path / "j.jsonl",
    )
    assert result2.imported_tickers == ("005830",)
    assert pd.read_csv(path, dtype=str).iloc[0]["status"] == "ai_suggested"
    clear_entries()


def _filled_weekly_md() -> str:
    return """# 주간 통합 정성 AI 요청서

- report_id: `WQR-TEST`
- as_of: `2026-07-17`
- input_snapshot_hash: `abc`

## A_CECS_SUMMARY

## [005830] DB손해보험

### execution
- 점수 제안(0-100): 80
- 근거: ok
- 출처: [1차 출처: DART](https://dart.fss.or.kr/e1)

### pension
- 점수 제안(0-100): 50
- 근거: ok
- 출처: [1차 출처: DART](https://dart.fss.or.kr/p1)

### purpose
- 점수 제안(0-100): 100
- 근거: ok
- 출처: [1차 출처: DART](https://dart.fss.or.kr/u1)

## B_FINAL6_DEEP

### DEEP [005830] DB손해보험
- 공시/지배구조: ok
- 자사주·배당·환원: ok
- 연기금·수급: ok
- 투자목적: ok
- 리스크: ok
- 출처:
  - [1차 출처: DART](https://dart.fss.or.kr/d1)

## C_T2_EVENTS

### EVENT [commercial_code_enforcement_decrees]
- fired: true
- 근거: 시행령 확정 공고
- 출처:
  - https://www.law.go.kr/example

## D_THESIS

### THESIS
- damage: false
- 근거: 훼손 징후 없음
- 출처:
  - https://example.com/thesis

## E_TARGET_VALUATION

### TARGET [005830] DB손해보험
- pbr_max: 1.2
- target_price: _____
- 펀더멘털 사유: ROE 안정·배당 지속
- 근거: 피어 밴드 상단
- 출처:
  - https://example.com/val
"""


def test_targets_supplement_e_only_and_merge(tmp_path: Path) -> None:
    clear_entries()
    root = tmp_path
    (root / "data").mkdir()
    (root / "data" / "kr_alpha_exit_targets.yaml").write_text(
        "tickers:\n  '005830':\n    valuation:\n      pbr_max: 1.0\n",
        encoding="utf-8",
    )
    # Pre-existing CECS suggestion envelope must survive supplement merge.
    import json

    prior = {
        "report_id": "WQR-prior",
        "domain_status": {
            "cecs": "ai_suggested",
            "t2": "empty",
            "thesis": "empty",
            "targets": "empty",
        },
        "cecs": [{"ticker": "005830", "name": "DB"}],
        "targets": [],
        "approved": {k: False for k in ("cecs", "t2", "thesis", "targets")},
        "deep_tickers": ["005830", "021240"],
    }
    (root / "data" / "weekly_qual_suggestions.json").write_text(
        json.dumps(prior, ensure_ascii=False), encoding="utf-8"
    )

    from alpha_system.ui.services.weekly_qual_report import (
        persist_targets_supplement,
        waiting_target_subjects,
        write_targets_supplement_report,
    )

    rows = [
        WeeklySubject("005830", "DB손해보험", "insurance"),
        WeeklySubject("021240", "코웨이", "consumer"),
    ]
    waiting = waiting_target_subjects(rows, root=root)
    assert [s.ticker for s in waiting] == ["021240"]

    report = write_targets_supplement_report(
        waiting_subjects=waiting,
        proposal_tickers=["005830", "021240"],
        docs_dir=root / "docs",
        as_of=date(2026, 7, 18),
        generated_at=datetime(2026, 7, 18, 10, 0, 0),
        journal_path=root / "journal.jsonl",
    )
    assert "E_TARGET_VALUATION" in report.markdown
    assert "A_CECS_SUMMARY" not in report.markdown
    assert "021240" in report.markdown
    assert "005830" not in report.markdown.split("## E_TARGET_VALUATION", 1)[1]
    assert "업로드 합격 조건" in report.markdown
    assert "_reference" in report.markdown
    assert "같은 줄에" in report.markdown or "같은 줄" in report.markdown
    assert list_entries(action_kind="WEEKLY_TARGETS_SUPPLEMENT_GENERATED")

    filled = """# supplement
- report_id: `WQR-E-test`

## E_TARGET_VALUATION

### TARGET [021240] 코웨이
- pbr_max: 2.1
- target_price: 140000
- 펀더멘털 사유: 렌탈 계정 순증
- 근거: 피어 대비
- 출처:
  - https://example.com/coway
"""
    parsed = parse_weekly_qual_markdown(filled)
    assert parsed.targets and parsed.targets[0].ticker == "021240"
    out = persist_targets_supplement(
        root=root,
        parsed=parsed,
        report_name="supp.md",
        as_of=date(2026, 7, 18),
        proposal_tickers=["005830", "021240"],
        waiting_tickers=["021240"],
        journal_path=root / "journal.jsonl",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["mode"] == "targets_supplement"
    assert payload["domain_status"]["cecs"] == "ai_suggested"
    assert payload["domain_status"]["targets"] == "ai_suggested"
    assert payload["cecs"][0]["ticker"] == "005830"
    assert {t["ticker"] for t in payload["targets"]} == {"021240"}
    assert set(payload["deep_tickers"]) == {"005830", "021240"}
    assert list_entries(action_kind="WEEKLY_TARGETS_SUPPLEMENT_IMPORT")
    clear_entries()


def test_targets_supplement_rejects_outside_waiting(tmp_path: Path) -> None:
    root = tmp_path
    (root / "data").mkdir()
    filled = """## E_TARGET_VALUATION

### TARGET [000660] SK하이닉스
- pbr_max: 1.5
- target_price: 200000
- 펀더멘털 사유: x
- 근거: y
- 출처:
  - https://example.com/h
"""
    parsed = parse_weekly_qual_markdown(filled)
    with pytest.raises(ValueError, match="최종 선정 밖|대기 목록"):
        persist_targets_supplement(
            root=root,
            parsed=parsed,
            report_name="bad.md",
            as_of=date(2026, 7, 18),
            proposal_tickers=["021240"],
            waiting_tickers=["021240"],
        )


def test_targets_reference_only_upload_rejected(tmp_path: Path) -> None:
    """Blank / reference-style fills must fail with actionable message."""
    root = tmp_path
    (root / "data").mkdir()
    reference_style = """## E_TARGET_VALUATION

### TARGET [316140] 우리금융지주
- pbr_max: _____   (참고: 최근 PBR 밴드 0.34~0.58배)
- target_price: _____   (참고: 컨센서스 41,595원)
- 펀더멘털 사유: _____
- 근거: _____
- 출처:
  - https://example.com/woori
"""
    parsed = parse_weekly_qual_markdown(reference_style)
    assert not parsed.targets
    assert any("펀더멘털 사유" in f for f in parsed.domain_failures["targets"])
    with pytest.raises(ValueError, match="참고자료|_reference|_____|펀더멘털 사유"):
        persist_targets_supplement(
            root=root,
            parsed=parsed,
            report_name="weekly_qual_targets_supplement_20260718_reference.md",
            as_of=date(2026, 7, 18),
            proposal_tickers=["316140"],
            waiting_tickers=["316140"],
        )


def test_weekly_e_section_includes_upload_contract(tmp_path: Path) -> None:
    report = write_weekly_qual_report(
        summary_subjects=[WeeklySubject("005830", "DB손해보험", "insurance")],
        deep_subjects=[WeeklySubject("005830", "DB손해보험", "insurance")],
        t2_event_ids=["commercial_code_enforcement_decrees"],
        docs_dir=tmp_path / "docs",
        as_of=date(2026, 7, 19),
        generated_at=datetime(2026, 7, 19, 1, 0, 0),
        journal_path=tmp_path / "journal.jsonl",
    )
    assert "업로드 합격 조건" in report.markdown
    assert "_reference" in report.markdown
