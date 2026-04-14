from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from apsf.core.backtest import (
    SimulationConfig,
    build_backtest_artifacts_from_input,
)


def _records(*, count: int, start: date, close: float, drift: float, volume: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    price = close
    for offset in range(count):
        current = start + timedelta(days=offset)
        rows.append(
            {
                "date": current.isoformat(),
                "open": price,
                "high": price + 1.0,
                "low": price,
                "close": price + drift,
                "volume": volume,
            }
        )
        price += drift
    return rows


def test_build_backtest_artifacts_from_input_writes_run_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "001c4_case"
    run_dir.mkdir()
    payload = {
        "1306": _records(count=380, start=date(2025, 1, 1), close=100.0, drift=0.3, volume=10_000.0),
        "1348": _records(count=380, start=date(2025, 1, 1), close=101.0, drift=0.25, volume=11_000.0),
        "2558": _records(count=380, start=date(2025, 1, 1), close=102.0, drift=0.2, volume=12_000.0),
    }
    (run_dir / "backtest_input.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = build_backtest_artifacts_from_input(
        run_dir=run_dir,
        config=SimulationConfig(
            entry_slippage_bps=0.0,
            exit_slippage_bps=0.0,
            baseline_slippage_bps=0.0,
            stress_slippage_bps=5.0,
            minimum_overlap_years=1.0,
            warm_up_trading_days=60,
        ),
    )

    assert result.paths.metrics_report.exists()
    assert result.paths.adoption_verdict.exists()
    assert result.paths.paper_trade_checklist.exists()
    assert "Backtest Metrics Report" in result.paths.metrics_report.read_text(encoding="utf-8")
    assert "Adoption Verdict" in result.paths.adoption_verdict.read_text(encoding="utf-8")
    assert "Paper-Trade Checklist" in result.paths.paper_trade_checklist.read_text(encoding="utf-8")
