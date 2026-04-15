from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class SimulationConfig:
    initial_equity: float = 10_000.0
    entry_slippage_bps: float = 10.0
    exit_slippage_bps: float = 10.0
    baseline_slippage_bps: float = 10.0
    stress_slippage_bps: float = 25.0
    fee_per_trade: float = 0.0
    per_trade_risk_cap: float = 200.0
    daily_loss_stop: float = 500.0
    weekly_loss_stop: float = 500.0
    drawdown_floor_ratio: float = 0.90
    consecutive_loss_limit: int = 3
    cooldown_trading_days: int = 3
    minimum_overlap_years: float = 3.0
    minimum_trade_count: int = 30
    warm_up_trading_days: int = 60
    # v0.2 strategy rule switches (defaults preserve v0.1 behaviour)
    use_v02_rules: bool = False


@dataclass(frozen=True)
class Position:
    symbol: str
    entry_date: str
    entry_signal_date: str
    entry_price: float
    stop_price: float
    bars_held: int = 0


@dataclass(frozen=True)
class Trade:
    symbol: str
    entry_signal_date: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    exit_reason: str
    pnl: float
    bars_held: int
    stop_gap_fill: bool = False


@dataclass(frozen=True)
class BacktestMetrics:
    total_return: float
    annualized_return: float
    max_drawdown: float
    profit_factor: float
    win_rate: float
    average_trade_pnl: float
    median_trade_pnl: float
    trade_count: int
    consecutive_loss_max: int
    exposure_ratio: float
    skipped_gap_up_entries: int
    stop_gap_fills: int
    control_violations: tuple[str, ...] = ()


@dataclass(frozen=True)
class BacktestDecision:
    outcome: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SimulationResult:
    trades: tuple[Trade, ...]
    metrics: BacktestMetrics
    equity_curve: tuple[tuple[str, float], ...]
    queued_entry_symbol: str | None
    warm_up_complete: bool


def run_backtest(
    price_history_by_symbol: Mapping[str, Sequence[Bar]],
    *,
    config: SimulationConfig | None = None,
) -> SimulationResult:
    config = config or SimulationConfig()
    common_dates = _common_dates(price_history_by_symbol)
    if not common_dates:
        metrics = BacktestMetrics(
            total_return=0.0,
            annualized_return=0.0,
            max_drawdown=0.0,
            profit_factor=0.0,
            win_rate=0.0,
            average_trade_pnl=0.0,
            median_trade_pnl=0.0,
            trade_count=0,
            consecutive_loss_max=0,
            exposure_ratio=0.0,
            skipped_gap_up_entries=0,
            stop_gap_fills=0,
            control_violations=("missing_overlap_history",),
        )
        return SimulationResult(
            trades=(),
            metrics=metrics,
            equity_curve=(),
            queued_entry_symbol=None,
            warm_up_complete=False,
        )

    history = {
        symbol: {bar.date: bar for bar in bars if bar.date in common_dates}
        for symbol, bars in price_history_by_symbol.items()
    }
    ordered_history = {
        symbol: [history[symbol][date] for date in common_dates]
        for symbol in sorted(history)
    }
    indicators = {
        symbol: _compute_indicators(bars)
        for symbol, bars in ordered_history.items()
    }

    equity = config.initial_equity
    peak_equity = equity
    equity_curve: list[tuple[str, float]] = []
    trades: list[Trade] = []
    control_violations: list[str] = []
    position: Position | None = None
    queued_entry: dict[str, object] | None = None
    queued_exit_reason: str | None = None
    skipped_gap_up_entries = 0
    stop_gap_fills = 0
    exposure_days = 0
    halted = False
    cooldown_remaining = 0
    consecutive_losses = 0
    current_week_key: tuple[int, int] | None = None
    week_start_equity = equity

    for index, date in enumerate(common_dates):
        warm_up_complete = (index + 1) > config.warm_up_trading_days
        day_start_equity = equity if position is None else equity - position.entry_price + ordered_history[position.symbol][index - 1].close if index > 0 else equity
        current_week = _week_key(date)
        if current_week != current_week_key:
            current_week_key = current_week
            week_start_equity = day_start_equity

        realized_today = 0.0

        if queued_exit_reason and position is not None:
            bar = ordered_history[position.symbol][index]
            exit_price = _apply_sell_slippage(bar.open, config.exit_slippage_bps) - config.fee_per_trade
            pnl = exit_price - position.entry_price
            realized_today += pnl
            equity += pnl
            trades.append(
                Trade(
                    symbol=position.symbol,
                    entry_signal_date=position.entry_signal_date,
                    entry_date=position.entry_date,
                    exit_date=date,
                    entry_price=position.entry_price,
                    exit_price=exit_price,
                    exit_reason=queued_exit_reason,
                    pnl=pnl,
                    bars_held=position.bars_held,
                )
            )
            consecutive_losses, cooldown_remaining = _update_loss_state(
                pnl,
                consecutive_losses=consecutive_losses,
                cooldown_remaining=cooldown_remaining,
                config=config,
            )
            position = None
            queued_exit_reason = None

        if queued_entry is not None and position is None and not halted:
            symbol = str(queued_entry["symbol"])
            signal_close = float(queued_entry["signal_close"])
            stop_price = float(queued_entry["stop_price"])
            signal_date = str(queued_entry["signal_date"])
            bar = ordered_history[symbol][index]
            if bar.open > signal_close * 1.01:
                skipped_gap_up_entries += 1
            else:
                entry_price = _apply_buy_slippage(bar.open, config.entry_slippage_bps) + config.fee_per_trade
                position = Position(
                    symbol=symbol,
                    entry_date=date,
                    entry_signal_date=signal_date,
                    entry_price=entry_price,
                    stop_price=stop_price,
                )
            queued_entry = None

        if position is not None:
            bar = ordered_history[position.symbol][index]
            if bar.low <= position.stop_price:
                stop_gap = bar.open <= position.stop_price
                raw_exit = bar.open if stop_gap else position.stop_price
                exit_price = _apply_sell_slippage(raw_exit, config.exit_slippage_bps) - config.fee_per_trade
                pnl = exit_price - position.entry_price
                realized_today += pnl
                equity += pnl
                trades.append(
                    Trade(
                        symbol=position.symbol,
                        entry_signal_date=position.entry_signal_date,
                        entry_date=position.entry_date,
                        exit_date=date,
                        entry_price=position.entry_price,
                        exit_price=exit_price,
                        exit_reason="reverse_stop",
                        pnl=pnl,
                        bars_held=position.bars_held + 1,
                        stop_gap_fill=stop_gap,
                    )
                )
                if stop_gap:
                    stop_gap_fills += 1
                consecutive_losses, cooldown_remaining = _update_loss_state(
                    pnl,
                    consecutive_losses=consecutive_losses,
                    cooldown_remaining=cooldown_remaining,
                    config=config,
                )
                position = None
                queued_exit_reason = None

        unrealized_today = 0.0
        if position is not None:
            bar = ordered_history[position.symbol][index]
            unrealized_today = bar.close - position.entry_price
            exposure_days += 1
            if index > 0:
                indicator = indicators[position.symbol][index]
                ll_prev = indicator.ll15_prev if config.use_v02_rules else indicator.ll10_prev
                ll_breach_reason = "ll15_breach" if config.use_v02_rules else "ll10_breach"
                if ll_prev is not None and indicator.atr14 is not None:
                    raised_stop = max(
                        position.stop_price,
                        _floor_to_tick(bar.close - (2.0 * indicator.atr14), _tick_size(bar.close)),
                        ll_prev,
                    )
                    position = Position(
                        symbol=position.symbol,
                        entry_date=position.entry_date,
                        entry_signal_date=position.entry_signal_date,
                        entry_price=position.entry_price,
                        stop_price=raised_stop,
                        bars_held=position.bars_held + 1,
                    )
                    if bar.close < ll_prev:
                        queued_exit_reason = ll_breach_reason
                    elif indicator.sma20 is not None and bar.close < indicator.sma20:
                        queued_exit_reason = "sma20_breach"

        marked_equity = equity + unrealized_today
        peak_equity = max(peak_equity, marked_equity)
        if marked_equity < peak_equity * config.drawdown_floor_ratio:
            halted = True

        day_pnl = marked_equity - day_start_equity
        week_pnl = marked_equity - week_start_equity
        entry_blocked = (
            halted
            or cooldown_remaining > 0
            or day_pnl <= -config.daily_loss_stop
            or week_pnl <= -config.weekly_loss_stop
        )

        if warm_up_complete and position is None and queued_entry is None and not entry_blocked:
            for symbol, bars in ordered_history.items():
                indicator = indicators[symbol][index]
                bar = bars[index]
                if not _entry_signal(bar, indicator, config):
                    continue
                if position is not None:
                    control_violations.append("one_position_violation")
                    break
                queued_entry = {
                    "symbol": symbol,
                    "signal_close": bar.close,
                    "stop_price": _initial_stop(bar.close, indicator.atr14),
                    "signal_date": date,
                }
                break

        if cooldown_remaining > 0 and position is None:
            cooldown_remaining -= 1

        equity_curve.append((date, marked_equity))

    metrics = _calculate_metrics(
        config=config,
        common_dates=common_dates,
        trades=trades,
        equity_curve=equity_curve,
        exposure_days=exposure_days,
        skipped_gap_up_entries=skipped_gap_up_entries,
        stop_gap_fills=stop_gap_fills,
        control_violations=control_violations,
    )
    queued_symbol = None if queued_entry is None else str(queued_entry["symbol"])
    return SimulationResult(
        trades=tuple(trades),
        metrics=metrics,
        equity_curve=tuple(equity_curve),
        queued_entry_symbol=queued_symbol,
        warm_up_complete=len(common_dates) > config.warm_up_trading_days,
    )


def evaluate_adoption(
    result: SimulationResult,
    *,
    minimum_overlap_years: float,
    harsher_case_profitable: bool,
) -> BacktestDecision:
    reasons: list[str] = []
    overlap_years = len(result.equity_curve) / 252.0
    if overlap_years < minimum_overlap_years:
        reasons.append("insufficient_history")
    if result.metrics.max_drawdown <= -0.30:
        reasons.append("drawdown_breach")
    if result.metrics.trade_count < 30:
        reasons.append("insufficient_trade_count")
    if not harsher_case_profitable:
        reasons.append("stress_case_unprofitable")
    if result.metrics.control_violations:
        reasons.append("control_violation")

    if "drawdown_breach" in reasons or result.metrics.total_return <= 0.0:
        return BacktestDecision(outcome="no_go", reasons=tuple(reasons or ["base_case_unprofitable"]))
    if reasons:
        return BacktestDecision(outcome="hold", reasons=tuple(reasons))
    return BacktestDecision(outcome="go_to_paper_trade", reasons=())


@dataclass(frozen=True)
class _IndicatorRow:
    sma20: float | None = None
    sma60: float | None = None
    hh20_prev: float | None = None
    ll10_prev: float | None = None
    avg_volume20: float | None = None
    atr14: float | None = None
    hh15_prev: float | None = None
    ll15_prev: float | None = None


def _compute_indicators(bars: Sequence[Bar]) -> list[_IndicatorRow]:
    rows: list[_IndicatorRow] = []
    true_ranges: list[float] = []
    for index, bar in enumerate(bars):
        prev_close = bars[index - 1].close if index > 0 else bar.close
        tr = max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close))
        true_ranges.append(tr)
        rows.append(
            _IndicatorRow(
                sma20=_mean([b.close for b in bars[index - 19 : index + 1]]) if index >= 19 else None,
                sma60=_mean([b.close for b in bars[index - 59 : index + 1]]) if index >= 59 else None,
                hh20_prev=max(b.high for b in bars[index - 20 : index]) if index >= 20 else None,
                ll10_prev=min(b.low for b in bars[index - 10 : index]) if index >= 10 else None,
                avg_volume20=_mean([b.volume for b in bars[index - 19 : index + 1]]) if index >= 19 else None,
                atr14=_mean(true_ranges[index - 13 : index + 1]) if index >= 13 else None,
                hh15_prev=max(b.high for b in bars[index - 15 : index]) if index >= 15 else None,
                ll15_prev=min(b.low for b in bars[index - 15 : index]) if index >= 15 else None,
            )
        )
    return rows


def _entry_signal(bar: Bar, indicator: _IndicatorRow, config: SimulationConfig) -> bool:
    if config.use_v02_rules:
        # v0.2: HH15, Volume >= AvgVolume20 (no 1.2x multiplier)
        if (
            indicator.hh15_prev is None
            or indicator.sma20 is None
            or indicator.sma60 is None
            or indicator.avg_volume20 is None
            or indicator.atr14 is None
        ):
            return False
        if bar.close <= indicator.hh15_prev:
            return False
        if bar.close <= indicator.sma20:
            return False
        if indicator.sma20 <= indicator.sma60:
            return False
        if bar.volume < indicator.avg_volume20:
            return False
    else:
        # v0.1: HH20, Volume >= 1.2 * AvgVolume20
        if (
            indicator.hh20_prev is None
            or indicator.sma20 is None
            or indicator.sma60 is None
            or indicator.avg_volume20 is None
            or indicator.atr14 is None
        ):
            return False
        if bar.close <= indicator.hh20_prev:
            return False
        if bar.close <= indicator.sma20:
            return False
        if indicator.sma20 <= indicator.sma60:
            return False
        if bar.volume < 1.2 * indicator.avg_volume20:
            return False
    return (bar.close - _initial_stop(bar.close, indicator.atr14)) <= config.per_trade_risk_cap


def _initial_stop(close: float, atr14: float | None) -> float:
    if atr14 is None:
        return close
    tick = _tick_size(close)
    stop_distance = max(2.0 * atr14, close * 0.01, 3.0 * tick)
    return _floor_to_tick(close - stop_distance, tick)


def _tick_size(price: float) -> float:
    if price <= 3_000:
        return 1.0
    if price <= 5_000:
        return 5.0
    return 10.0


def _floor_to_tick(price: float, tick: float) -> float:
    return float(int(price / tick) * tick)


def _apply_buy_slippage(price: float, bps: float) -> float:
    return price * (1.0 + (bps / 10_000.0))


def _apply_sell_slippage(price: float, bps: float) -> float:
    return price * (1.0 - (bps / 10_000.0))


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _common_dates(price_history_by_symbol: Mapping[str, Sequence[Bar]]) -> list[str]:
    date_sets = [
        {bar.date for bar in bars}
        for bars in price_history_by_symbol.values()
        if bars
    ]
    if not date_sets:
        return []
    common = set.intersection(*date_sets)
    return sorted(common)


def _week_key(date_text: str) -> tuple[int, int]:
    year, month, day = (int(part) for part in date_text.split("-"))
    import datetime as _dt

    iso = _dt.date(year, month, day).isocalendar()
    return iso.year, iso.week


def _update_loss_state(
    pnl: float,
    *,
    consecutive_losses: int,
    cooldown_remaining: int,
    config: SimulationConfig,
) -> tuple[int, int]:
    if pnl < 0:
        consecutive_losses += 1
        if consecutive_losses >= config.consecutive_loss_limit:
            cooldown_remaining = config.cooldown_trading_days
    else:
        consecutive_losses = 0
    return consecutive_losses, cooldown_remaining


def _calculate_metrics(
    *,
    config: SimulationConfig,
    common_dates: Sequence[str],
    trades: Sequence[Trade],
    equity_curve: Sequence[tuple[str, float]],
    exposure_days: int,
    skipped_gap_up_entries: int,
    stop_gap_fills: int,
    control_violations: Sequence[str],
) -> BacktestMetrics:
    if equity_curve:
        final_equity = equity_curve[-1][1]
        total_return = (final_equity / config.initial_equity) - 1.0
        years = len(equity_curve) / 252.0
        annualized_return = ((final_equity / config.initial_equity) ** (1.0 / years) - 1.0) if years > 0 else 0.0
        max_drawdown = _max_drawdown([value for _, value in equity_curve])
        exposure_ratio = exposure_days / len(common_dates)
    else:
        total_return = 0.0
        annualized_return = 0.0
        max_drawdown = 0.0
        exposure_ratio = 0.0

    pnls = [trade.pnl for trade in trades]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    profit_factor = (sum(wins) / abs(sum(losses))) if losses else (float("inf") if wins else 0.0)
    win_rate = (len(wins) / len(trades)) if trades else 0.0
    average_trade_pnl = _mean(pnls) if pnls else 0.0
    median_trade_pnl = median(pnls) if pnls else 0.0
    consecutive_loss_max = _max_consecutive_losses(pnls)

    return BacktestMetrics(
        total_return=total_return,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        profit_factor=profit_factor,
        win_rate=win_rate,
        average_trade_pnl=average_trade_pnl,
        median_trade_pnl=median_trade_pnl,
        trade_count=len(trades),
        consecutive_loss_max=consecutive_loss_max,
        exposure_ratio=exposure_ratio,
        skipped_gap_up_entries=skipped_gap_up_entries,
        stop_gap_fills=stop_gap_fills,
        control_violations=tuple(control_violations),
    )


def _max_drawdown(equity_values: Sequence[float]) -> float:
    peak = equity_values[0]
    max_drawdown = 0.0
    for equity in equity_values:
        peak = max(peak, equity)
        drawdown = (equity / peak) - 1.0
        max_drawdown = min(max_drawdown, drawdown)
    return max_drawdown


def _max_consecutive_losses(pnls: Sequence[float]) -> int:
    longest = 0
    current = 0
    for pnl in pnls:
        if pnl < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest
