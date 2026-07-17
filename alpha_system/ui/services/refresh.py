"""Run price + fundamentals refresh on the host PC."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Any


@dataclass
class RefreshResult:
    ok: bool
    message: str
    detail: dict[str, Any]


def run_data_refresh(data_dir: Path, *, scope: str = "holdings") -> RefreshResult:
    """
    Invoke existing PyKRX bulk collect (prices + fundamentals).
    Runs locally on the machine hosting Streamlit — not a remote API.
    """
    try:
        from src.settings.user_secrets import apply_secrets_to_env
        from src.data_refresh.pykrx_bulk import run_pykrx_bulk_collect
    except ImportError as exc:
        return RefreshResult(
            ok=False,
            message="수집 모듈을 불러올 수 없습니다.",
            detail={"error": str(exc)},
        )

    apply_secrets_to_env(data_dir)
    try:
        result = run_pykrx_bulk_collect(
            data_dir,
            scope=scope,
            merge_existing_universe=True,
            write_history=True,
            enrich_dart=True,
        )
        return RefreshResult(
            ok=True,
            message="현재가·펀더멘털 갱신 완료",
            detail={
                "as_of": getattr(result, "as_of", None),
                "tickers": getattr(result, "tickers_processed", None),
                "errors": getattr(result, "errors", None),
            },
        )
    except Exception as exc:
        return RefreshResult(ok=False, message=str(exc), detail={"error": str(exc)})


def run_quant_snapshot_refresh(
    root: Path,
    *,
    collect_scope: str = "liquid",
) -> RefreshResult:
    """One-click collection: operational data, then alpha quant snapshot.

    The subprocess isolates alpha_portfolio's local ``src`` package from the
    dashboard's top-level ``src`` package. No target portfolio writer is called.
    """
    operational = run_data_refresh(root / "data", scope="holdings")
    if not operational.ok:
        return RefreshResult(
            ok=False,
            message=f"운용 데이터 갱신 실패: {operational.message}",
            detail={"operational": operational.detail},
        )

    script = root / "scripts" / "run_alpha_quant_snapshot.py"
    command = [
        sys.executable,
        str(script),
        "--root",
        str(root),
        "--collect",
        "--collect-scope",
        collect_scope,
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1200,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RefreshResult(
            ok=False,
            message=f"정량 스냅샷 실행 실패: {exc}",
            detail={"operational": operational.detail, "error": str(exc)},
        )

    detail: dict[str, Any] = {
        "operational": operational.detail,
        "command": "run_alpha_quant_snapshot.py --collect --collect-scope "
        + collect_scope,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "target_portfolio_written": False,
    }
    if completed.returncode != 0:
        return RefreshResult(
            ok=False,
            message="정량 스냅샷 생성 실패",
            detail=detail,
        )

    provenance = root / "data" / "alpha_quant_snapshot_provenance.json"
    if provenance.exists():
        try:
            import json

            detail["provenance"] = json.loads(provenance.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            detail["provenance_path"] = str(provenance)
    return RefreshResult(
        ok=True,
        message="정량 데이터·alpha_scores 갱신 완료",
        detail=detail,
    )
