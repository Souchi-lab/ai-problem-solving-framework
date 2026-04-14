from __future__ import annotations

from datetime import date, timedelta

from apsf.core.backtest import (
    SimulationConfig,
    load_price_history_from_records,
    render_adoption_verdict_markdown,
    render_metrics_report_markdown,
    render_paper_trade_checklist_markdown,
    run_backtest_suite,
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


def test_load_price_history_from_records_sorts_and_casts() -> None:
    history = load_price_history_from_records(
        {
            "1306": [
                {"date": "2026-01-02", "open": "101", "high": "102", "low": "100", "close": "101", "volume": "1000"},
                {"date": "2026-01-01", "open": "100", "high": "101", "low": "99", "close": "100", "volume": "900"},
            ]
        }
    )

    assert [bar.date for bar in history["1306"]] == ["2026-01-01", "2026-01-02"]
    assert history["1306"][0].open == 100.0


def test_run_backtest_suite_and_renderers_produce_artifact_text() -> None:
    start = date(2025, 1, 1)
    records = {
        "1306": _records(count=380, start=start, close=100.0, drift=0.3, volume=10_000.0),
        "1348": _records(count=380, start=start, close=101.0, drift=0.25, volume=11_000.0),
        "2558": _records(count=380, start=start, close=102.0, drift=0.2, volume=12_000.0),
    }
    history = load_price_history_from_records(records)

    suite = run_backtest_suite(
        history,
        config=SimulationConfig(
            entry_slippage_bps=0.0,
            exit_slippage_bps=0.0,
            baseline_slippage_bps=0.0,
            stress_slippage_bps=5.0,
            warm_up_trading_days=60,
            minimum_overlap_years=1.0,
        ),
        provenance_label="synthetic_test_data",
        provenance_note="Deterministic synthetic records for regression coverage.",
    )

    report_md = render_metrics_report_markdown(suite)
    verdict_md = render_adoption_verdict_markdown(suite)
    checklist_md = render_paper_trade_checklist_markdown(suite.paper_trade_checklist)

    assert "# Backtest Metrics Report" in report_md
    assert "Data provenance: `synthetic_test_data`" in report_md
    assert "## Stress Case" in report_md
    assert "# Adoption Verdict" in verdict_md
    assert "Deterministic synthetic records for regression coverage." in verdict_md
    assert "Outcome:" in verdict_md
    assert "# Paper-Trade Checklist" in checklist_md
    assert "- [ ] Verify data fetch covers 1306, 1348, and 2558 with no silent gaps." in checklist_md
    assert suite.yearly_returns
