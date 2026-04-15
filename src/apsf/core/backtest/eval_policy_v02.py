"""
001c5 evaluation policy implementation for v0.2.

Field names, boolean derivations, and verdict algorithm are frozen by
eval-policy-v0.2.md (001c5 adopted).  Do not adjust thresholds here
without a corresponding change to 001c5.
"""
from __future__ import annotations

from dataclasses import dataclass

from .reporting import BacktestSuiteResult, YearlyReturn


@dataclass(frozen=True)
class EvalPolicyV02Result:
    # Canonical metric fields (Section 2)
    base_total_return_pct: float
    base_annualized_return_pct: float
    base_max_drawdown_pct: float        # positive magnitude, e.g. 5.69 not -5.69
    base_profit_factor: float
    trade_count: int
    usable_calendar_year_count: int
    yearly_returns: tuple[YearlyReturn, ...]
    stress_total_return_pct: float
    stress_max_drawdown_pct: float      # positive magnitude

    # Section 4 booleans
    evidence_sufficient: bool
    base_positive: bool
    profit_factor_pass: bool
    stress_positive: bool
    stress_drawdown_ok: bool
    stress_pass: bool
    base_quality_pass: bool
    base_negative: bool
    profit_factor_fail: bool
    stress_fail: bool
    evidence_limited: bool

    # Verdict (Section 7) and reasons (Section 8)
    verdict: str                        # "go" | "hold" | "no_go"
    verdict_reasons: tuple[str, ...]


def apply_eval_policy_v02(suite: BacktestSuiteResult) -> EvalPolicyV02Result:
    """Apply the frozen 001c5 evaluation policy to a BacktestSuiteResult."""
    base = suite.base_result.metrics
    stress = suite.stress_result.metrics

    # --- Canonical metric values ---
    base_total_return_pct = base.total_return * 100.0
    base_annualized_return_pct = base.annualized_return * 100.0
    # Drawdown stored as negative fraction in simulator; expose as positive pct
    base_max_drawdown_pct = abs(base.max_drawdown) * 100.0
    base_profit_factor = base.profit_factor
    trade_count = base.trade_count
    stress_total_return_pct = stress.total_return * 100.0
    stress_max_drawdown_pct = abs(stress.max_drawdown) * 100.0

    # usable_calendar_year_count: distinct calendar years in yearly_returns (Section 3)
    usable_calendar_year_count = len(suite.yearly_returns)

    # --- Section 4 booleans ---
    evidence_sufficient = (usable_calendar_year_count >= 3) and (trade_count >= 20)
    base_positive = base_total_return_pct > 0
    profit_factor_pass = base_profit_factor > 1.0
    stress_positive = stress_total_return_pct >= 0
    # stress_drawdown_ok: stress drawdown magnitude must not exceed base by more than 2 ppts
    stress_drawdown_ok = stress_max_drawdown_pct <= base_max_drawdown_pct + 2.0
    stress_pass = stress_positive and stress_drawdown_ok
    base_quality_pass = base_positive and profit_factor_pass
    base_negative = base_total_return_pct <= 0
    profit_factor_fail = base_profit_factor <= 1.0
    stress_fail = not stress_pass
    evidence_limited = not evidence_sufficient

    # --- Section 7: ordered verdict algorithm (first matching rule wins) ---
    if evidence_sufficient and base_quality_pass and stress_pass:
        verdict = "go"
    elif base_negative and stress_fail:
        verdict = "no_go"
    elif base_negative and profit_factor_fail:
        verdict = "no_go"
    elif evidence_limited and base_negative:
        verdict = "no_go"
    elif evidence_limited and stress_fail:
        verdict = "no_go"
    elif evidence_limited and base_quality_pass and stress_pass:
        verdict = "hold"
    elif evidence_sufficient and base_quality_pass and stress_fail:
        verdict = "hold"
    elif evidence_sufficient and base_positive and profit_factor_fail:
        verdict = "no_go"
    elif evidence_sufficient and base_negative:
        verdict = "no_go"
    else:
        verdict = "no_go"

    # --- Section 8: ordered additive verdict_reasons ---
    reasons: list[str] = []
    if usable_calendar_year_count < 3:
        reasons.append("insufficient_history")
    if trade_count < 20:
        reasons.append("insufficient_trade_count")
    if base_total_return_pct <= 0:
        reasons.append("base_case_unprofitable")
    if base_profit_factor <= 1.0:
        reasons.append("profit_factor_fail")
    if stress_total_return_pct < 0:
        reasons.append("stress_case_unprofitable")
    if stress_max_drawdown_pct > base_max_drawdown_pct + 2.0:
        reasons.append("stress_drawdown_fail")

    return EvalPolicyV02Result(
        base_total_return_pct=base_total_return_pct,
        base_annualized_return_pct=base_annualized_return_pct,
        base_max_drawdown_pct=base_max_drawdown_pct,
        base_profit_factor=base_profit_factor,
        trade_count=trade_count,
        usable_calendar_year_count=usable_calendar_year_count,
        yearly_returns=suite.yearly_returns,
        stress_total_return_pct=stress_total_return_pct,
        stress_max_drawdown_pct=stress_max_drawdown_pct,
        evidence_sufficient=evidence_sufficient,
        base_positive=base_positive,
        profit_factor_pass=profit_factor_pass,
        stress_positive=stress_positive,
        stress_drawdown_ok=stress_drawdown_ok,
        stress_pass=stress_pass,
        base_quality_pass=base_quality_pass,
        base_negative=base_negative,
        profit_factor_fail=profit_factor_fail,
        stress_fail=stress_fail,
        evidence_limited=evidence_limited,
        verdict=verdict,
        verdict_reasons=tuple(reasons),
    )
