from __future__ import annotations

from datetime import date, timedelta

from apsf.core.backtest import (
    Bar,
    SimulationConfig,
    evaluate_adoption,
    run_backtest,
)


def _flat_bars(
    symbol_prefix: str,
    *,
    start_day: int,
    count: int,
    close: float,
    volume: float,
) -> list[Bar]:
    bars: list[Bar] = []
    start = date(2026, 1, 1) + timedelta(days=start_day - 1)
    for offset in range(count):
        current = start + timedelta(days=offset)
        bars.append(
            Bar(
                date=current.isoformat(),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=volume,
            )
        )
    return bars


def test_gap_up_entry_is_skipped() -> None:
    bars = _flat_bars("A", start_day=1, count=60, close=100.0, volume=100.0)
    bars.append(Bar(date="2026-03-02", open=100.0, high=101.0, low=100.0, close=101.0, volume=140.0))
    bars.append(Bar(date="2026-03-03", open=103.0, high=103.0, low=102.0, close=102.5, volume=100.0))

    result = run_backtest({"1306": bars}, config=SimulationConfig(entry_slippage_bps=0.0, exit_slippage_bps=0.0))

    assert result.metrics.skipped_gap_up_entries == 1
    assert result.metrics.trade_count == 0


def test_reverse_stop_uses_open_price_on_gap_through() -> None:
    bars = _flat_bars("A", start_day=1, count=60, close=1_000.0, volume=100.0)
    bars.append(Bar(date="2026-03-02", open=1_000.0, high=1_010.0, low=1_000.0, close=1_005.0, volume=140.0))
    bars.append(Bar(date="2026-03-03", open=1_005.0, high=1_006.0, low=1_000.0, close=1_004.0, volume=100.0))
    bars.append(Bar(date="2026-03-04", open=900.0, high=920.0, low=880.0, close=905.0, volume=100.0))

    result = run_backtest({"1306": bars}, config=SimulationConfig(entry_slippage_bps=0.0, exit_slippage_bps=0.0))

    assert result.metrics.trade_count == 1
    trade = result.trades[0]
    assert trade.exit_reason == "reverse_stop"
    assert trade.stop_gap_fill is True
    assert trade.exit_price == 900.0


def test_daily_loss_stop_blocks_new_signal_after_large_loss() -> None:
    losing = _flat_bars("A", start_day=1, count=60, close=1_000.0, volume=100.0)
    losing.append(Bar(date="2026-03-02", open=1_000.0, high=1_010.0, low=1_000.0, close=1_005.0, volume=140.0))
    losing.append(Bar(date="2026-03-03", open=1_005.0, high=1_006.0, low=1_000.0, close=1_004.0, volume=100.0))
    losing.append(Bar(date="2026-03-04", open=940.0, high=950.0, low=930.0, close=945.0, volume=100.0))

    candidate = _flat_bars("B", start_day=1, count=60, close=100.0, volume=100.0)
    candidate.append(Bar(date="2026-03-02", open=100.0, high=100.0, low=100.0, close=100.0, volume=100.0))
    candidate.append(Bar(date="2026-03-03", open=100.0, high=100.0, low=100.0, close=100.0, volume=100.0))
    candidate.append(Bar(date="2026-03-04", open=100.0, high=101.0, low=100.0, close=101.0, volume=140.0))
    candidate.append(Bar(date="2026-03-05", open=101.0, high=102.0, low=101.0, close=102.0, volume=100.0))

    result = run_backtest(
        {"1306": losing, "1348": candidate},
        config=SimulationConfig(
            entry_slippage_bps=0.0,
            exit_slippage_bps=0.0,
            daily_loss_stop=50.0,
            weekly_loss_stop=1_000.0,
        ),
    )

    assert result.metrics.trade_count == 1
    assert result.queued_entry_symbol is None


def test_evaluate_adoption_returns_hold_when_trade_count_is_too_small() -> None:
    bars = _flat_bars("A", start_day=1, count=60, close=100.0, volume=100.0)
    bars.append(Bar(date="2026-03-02", open=100.0, high=101.0, low=100.0, close=101.0, volume=140.0))
    bars.append(Bar(date="2026-03-03", open=101.0, high=102.0, low=101.0, close=102.0, volume=100.0))
    bars.append(Bar(date="2026-03-04", open=102.0, high=103.0, low=102.0, close=103.0, volume=100.0))

    result = run_backtest({"1306": bars}, config=SimulationConfig(entry_slippage_bps=0.0, exit_slippage_bps=0.0))
    decision = evaluate_adoption(result, minimum_overlap_years=3.0, harsher_case_profitable=True)

    assert decision.outcome == "hold"
    assert "insufficient_trade_count" in decision.reasons


def test_warm_up_is_explicit_and_blocks_early_signal() -> None:
    bars = _flat_bars("A", start_day=1, count=59, close=100.0, volume=100.0)
    bars.append(Bar(date="2026-03-01", open=100.0, high=101.0, low=100.0, close=101.0, volume=140.0))
    bars.append(Bar(date="2026-03-02", open=101.0, high=102.0, low=101.0, close=102.0, volume=100.0))
    bars.append(Bar(date="2026-03-03", open=102.0, high=103.0, low=102.0, close=103.0, volume=100.0))

    result = run_backtest(
        {"1306": bars},
        config=SimulationConfig(entry_slippage_bps=0.0, exit_slippage_bps=0.0, warm_up_trading_days=60),
    )

    assert result.warm_up_complete is True
    assert result.metrics.trade_count == 0
