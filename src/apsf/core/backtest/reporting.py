from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .strategy_simulator import (
    BacktestDecision,
    Bar,
    SimulationConfig,
    SimulationResult,
    evaluate_adoption,
    run_backtest,
)


@dataclass(frozen=True)
class YearlyReturn:
    year: int
    start_equity: float
    end_equity: float
    return_pct: float


@dataclass(frozen=True)
class RollingWindowStat:
    start_date: str
    end_date: str
    value: float


@dataclass(frozen=True)
class BacktestSuiteResult:
    base_result: SimulationResult
    stress_result: SimulationResult
    decision: BacktestDecision
    yearly_returns: tuple[YearlyReturn, ...]
    rolling_six_month_returns: tuple[RollingWindowStat, ...]
    rolling_six_month_drawdowns: tuple[RollingWindowStat, ...]
    paper_trade_checklist: tuple[str, ...]
    provenance_label: str = "unspecified"
    provenance_note: str | None = None


REQUIRED_BAR_FIELDS = ("date", "open", "high", "low", "close", "volume")
DEFAULT_PAPER_TRADE_CHECKLIST = (
    "Verify data fetch covers 1306, 1348, and 2558 with no silent gaps.",
    "Confirm indicator calculations match the frozen v0.1 formulas.",
    "Verify gap-up skip behavior is logged and suppresses next-open entries.",
    "Verify reverse-stop gap-through exits use opening-price fills when breached through the stop.",
    "Verify daily and weekly loss-stop pauses block new entries without canceling open-position risk management.",
    "Verify one-position exclusivity across the full three-ticker universe.",
    "Verify restart behavior does not duplicate queued orders or trade state.",
    "Verify paper-trade logs reconcile with simulator trade chronology and verdict assumptions.",
)


def load_price_history_from_records(
    records_by_symbol: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, tuple[Bar, ...]]:
    history: dict[str, tuple[Bar, ...]] = {}
    for symbol, records in records_by_symbol.items():
        bars: list[Bar] = []
        for index, record in enumerate(records):
            missing = [field for field in REQUIRED_BAR_FIELDS if field not in record]
            if missing:
                raise ValueError(f"{symbol} record {index} is missing fields: {', '.join(missing)}")
            bars.append(
                Bar(
                    date=str(record["date"]),
                    open=float(record["open"]),
                    high=float(record["high"]),
                    low=float(record["low"]),
                    close=float(record["close"]),
                    volume=float(record["volume"]),
                )
            )
        history[symbol] = tuple(sorted(bars, key=lambda bar: bar.date))
    return history


def run_backtest_suite(
    price_history_by_symbol: Mapping[str, Sequence[Bar]],
    *,
    config: SimulationConfig | None = None,
    provenance_label: str = "unspecified",
    provenance_note: str | None = None,
) -> BacktestSuiteResult:
    config = config or SimulationConfig()
    base_result = run_backtest(price_history_by_symbol, config=config)
    stress_config = SimulationConfig(
        initial_equity=config.initial_equity,
        entry_slippage_bps=config.stress_slippage_bps,
        exit_slippage_bps=config.stress_slippage_bps,
        baseline_slippage_bps=config.baseline_slippage_bps,
        stress_slippage_bps=config.stress_slippage_bps,
        fee_per_trade=config.fee_per_trade,
        per_trade_risk_cap=config.per_trade_risk_cap,
        daily_loss_stop=config.daily_loss_stop,
        weekly_loss_stop=config.weekly_loss_stop,
        drawdown_floor_ratio=config.drawdown_floor_ratio,
        consecutive_loss_limit=config.consecutive_loss_limit,
        cooldown_trading_days=config.cooldown_trading_days,
        minimum_overlap_years=config.minimum_overlap_years,
        minimum_trade_count=config.minimum_trade_count,
        warm_up_trading_days=config.warm_up_trading_days,
    )
    stress_result = run_backtest(price_history_by_symbol, config=stress_config)
    decision = evaluate_adoption(
        base_result,
        minimum_overlap_years=config.minimum_overlap_years,
        harsher_case_profitable=stress_result.metrics.total_return > 0.0,
    )
    return BacktestSuiteResult(
        base_result=base_result,
        stress_result=stress_result,
        decision=decision,
        yearly_returns=tuple(_yearly_returns(base_result.equity_curve)),
        rolling_six_month_returns=tuple(_rolling_returns(base_result.equity_curve)),
        rolling_six_month_drawdowns=tuple(_rolling_drawdowns(base_result.equity_curve)),
        paper_trade_checklist=DEFAULT_PAPER_TRADE_CHECKLIST,
        provenance_label=provenance_label,
        provenance_note=provenance_note,
    )


def render_metrics_report_markdown(suite: BacktestSuiteResult) -> str:
    base = suite.base_result.metrics
    stress = suite.stress_result.metrics
    provenance_block = _render_provenance_block(suite)
    yearly_lines = (
        "\n".join(
            f"| {item.year} | {item.start_equity:.2f} | {item.end_equity:.2f} | {item.return_pct * 100:.2f}% |"
            for item in suite.yearly_returns
        )
        if suite.yearly_returns
        else "| n/a | n/a | n/a | n/a |"
    )
    return (
        "# Backtest Metrics Report\n\n"
        f"{provenance_block}"
        "## Base Case\n\n"
        f"- Total return: {base.total_return * 100:.2f}%\n"
        f"- Annualized return: {base.annualized_return * 100:.2f}%\n"
        f"- Max drawdown: {base.max_drawdown * 100:.2f}%\n"
        f"- Profit factor: {base.profit_factor:.2f}\n"
        f"- Trade count: {base.trade_count}\n"
        f"- Exposure ratio: {base.exposure_ratio * 100:.2f}%\n"
        f"- Gap-up skips: {base.skipped_gap_up_entries}\n"
        f"- Stop gap fills: {base.stop_gap_fills}\n\n"
        "## Stress Case\n\n"
        f"- Total return: {stress.total_return * 100:.2f}%\n"
        f"- Annualized return: {stress.annualized_return * 100:.2f}%\n"
        f"- Max drawdown: {stress.max_drawdown * 100:.2f}%\n"
        f"- Profit factor: {stress.profit_factor:.2f}\n"
        f"- Trade count: {stress.trade_count}\n\n"
        "## Yearly Returns\n\n"
        "| Year | Start Equity | End Equity | Return |\n"
        "|---|---:|---:|---:|\n"
        f"{yearly_lines}\n"
    )


def render_adoption_verdict_markdown(suite: BacktestSuiteResult) -> str:
    reasons = ", ".join(suite.decision.reasons) if suite.decision.reasons else "none"
    provenance_block = _render_provenance_block(suite)
    return (
        "# Adoption Verdict\n\n"
        f"{provenance_block}"
        f"- Outcome: `{suite.decision.outcome}`\n"
        f"- Reasons: {reasons}\n"
        f"- Base-case total return: {suite.base_result.metrics.total_return * 100:.2f}%\n"
        f"- Stress-case total return: {suite.stress_result.metrics.total_return * 100:.2f}%\n"
        f"- Max drawdown: {suite.base_result.metrics.max_drawdown * 100:.2f}%\n"
        f"- Trade count: {suite.base_result.metrics.trade_count}\n"
    )


def render_paper_trade_checklist_markdown(checklist: Sequence[str]) -> str:
    lines = "\n".join(f"- [ ] {item}" for item in checklist)
    return f"# Paper-Trade Checklist\n\n{lines}\n"


def _render_provenance_block(suite: BacktestSuiteResult) -> str:
    lines = [
        f"- Data provenance: `{suite.provenance_label}`",
    ]
    if suite.provenance_note:
        lines.append(f"- Provenance note: {suite.provenance_note}")
    return "## Provenance\n\n" + "\n".join(lines) + "\n\n"


def _yearly_returns(equity_curve: Sequence[tuple[str, float]]) -> list[YearlyReturn]:
    grouped: dict[int, list[tuple[str, float]]] = {}
    for date_text, equity in equity_curve:
        year = int(date_text[:4])
        grouped.setdefault(year, []).append((date_text, equity))
    items: list[YearlyReturn] = []
    for year in sorted(grouped):
        rows = grouped[year]
        start_equity = rows[0][1]
        end_equity = rows[-1][1]
        items.append(
            YearlyReturn(
                year=year,
                start_equity=start_equity,
                end_equity=end_equity,
                return_pct=(end_equity / start_equity) - 1.0 if start_equity else 0.0,
            )
        )
    return items


def _rolling_returns(
    equity_curve: Sequence[tuple[str, float]],
    *,
    window_days: int = 126,
) -> list[RollingWindowStat]:
    if len(equity_curve) < window_days:
        return []
    stats: list[RollingWindowStat] = []
    for start_index in range(0, len(equity_curve) - window_days + 1):
        window = equity_curve[start_index : start_index + window_days]
        start_date, start_equity = window[0]
        end_date, end_equity = window[-1]
        stats.append(
            RollingWindowStat(
                start_date=start_date,
                end_date=end_date,
                value=(end_equity / start_equity) - 1.0 if start_equity else 0.0,
            )
        )
    return stats


def _rolling_drawdowns(
    equity_curve: Sequence[tuple[str, float]],
    *,
    window_days: int = 126,
) -> list[RollingWindowStat]:
    if len(equity_curve) < window_days:
        return []
    stats: list[RollingWindowStat] = []
    for start_index in range(0, len(equity_curve) - window_days + 1):
        window = equity_curve[start_index : start_index + window_days]
        peak = window[0][1]
        drawdown = 0.0
        for _, equity in window:
            peak = max(peak, equity)
            drawdown = min(drawdown, (equity / peak) - 1.0)
        stats.append(
            RollingWindowStat(
                start_date=window[0][0],
                end_date=window[-1][0],
                value=drawdown,
            )
        )
    return stats
