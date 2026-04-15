"""
v0.2 markdown artifact renderers.

Produces metrics_report.md, adoption_verdict.md, and paper_trade_checklist.md
that comply with the canonical 001c5 schema and include a v0.1 vs v0.2
comparison section.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .eval_policy_v02 import EvalPolicyV02Result
from .reporting import BacktestSuiteResult


@dataclass(frozen=True)
class V01Baseline:
    """Frozen v0.1 real-data result for the comparison table."""
    base_total_return_pct: float = -4.58
    base_annualized_return_pct: float = -2.39
    base_max_drawdown_pct: float = 5.69   # positive magnitude
    base_profit_factor: float = 0.09
    trade_count: int = 10
    usable_calendar_year_count: int = 3
    stress_total_return_pct: float = -5.57
    stress_max_drawdown_pct: float = 6.68  # positive magnitude
    verdict: str = "no_go"
    verdict_reasons: tuple[str, ...] = (
        "insufficient_trade_count",
        "base_case_unprofitable",
        "profit_factor_fail",
        "stress_case_unprofitable",
    )


DEFAULT_V01_BASELINE = V01Baseline()

PAPER_TRADE_CHECKLIST_V02 = (
    "Verify data fetch covers 1306, 1348, and 2558 with no silent gaps.",
    "Confirm HH15 indicator uses 15-bar lookback (not 20) for the breakout entry check.",
    "Confirm LL15 indicator uses 15-bar lookback (not 10) for trailing stop and channel-exit check.",
    "Confirm volume entry filter uses Volume >= AvgVolume20 (no 1.2x multiplier).",
    "Verify gap-up skip behavior is logged and suppresses next-open entries.",
    "Verify reverse-stop gap-through exits use opening-price fills when breached through the stop.",
    "Verify daily and weekly loss-stop pauses block new entries without canceling open-position risk management.",
    "Verify one-position exclusivity across the full three-ticker universe.",
    "Verify restart behavior does not duplicate queued orders or trade state.",
    "Verify paper-trade logs reconcile with simulator trade chronology and verdict assumptions.",
)


def render_metrics_report_v02_markdown(
    suite: BacktestSuiteResult,
    policy: EvalPolicyV02Result,
    baseline: V01Baseline = DEFAULT_V01_BASELINE,
) -> str:
    base = suite.base_result.metrics
    stress = suite.stress_result.metrics

    provenance_lines = [f"- Data provenance: `{suite.provenance_label}`"]
    if suite.provenance_note:
        provenance_lines.append(f"- Provenance note: {suite.provenance_note}")
    provenance_block = "## Provenance\n\n" + "\n".join(provenance_lines) + "\n\n"

    yearly_lines = (
        "\n".join(
            f"| {item.year} | {item.start_equity:.2f} | {item.end_equity:.2f} | {item.return_pct * 100:.2f}% |"
            for item in suite.yearly_returns
        )
        if suite.yearly_returns
        else "| n/a | n/a | n/a | n/a |"
    )

    bool_rows = "\n".join(
        f"| `{name}` | `{value}` |"
        for name, value in [
            ("evidence_sufficient", policy.evidence_sufficient),
            ("evidence_limited", policy.evidence_limited),
            ("base_positive", policy.base_positive),
            ("base_negative", policy.base_negative),
            ("profit_factor_pass", policy.profit_factor_pass),
            ("profit_factor_fail", policy.profit_factor_fail),
            ("stress_positive", policy.stress_positive),
            ("stress_drawdown_ok", policy.stress_drawdown_ok),
            ("stress_pass", policy.stress_pass),
            ("stress_fail", policy.stress_fail),
            ("base_quality_pass", policy.base_quality_pass),
        ]
    )

    reasons_text = (
        ", ".join(f"`{r}`" for r in policy.verdict_reasons)
        if policy.verdict_reasons
        else "none"
    )

    # v0.1 vs v0.2 comparison table
    def _fmt(val: float, decimals: int = 2) -> str:
        return f"{val:.{decimals}f}%"

    comparison_rows = "\n".join([
        f"| Trade count | {baseline.trade_count} | {policy.trade_count} |",
        f"| Usable calendar years | {baseline.usable_calendar_year_count} | {policy.usable_calendar_year_count} |",
        f"| Base total return | {_fmt(baseline.base_total_return_pct)} | {_fmt(policy.base_total_return_pct)} |",
        f"| Base max drawdown | {_fmt(baseline.base_max_drawdown_pct)} | {_fmt(policy.base_max_drawdown_pct)} |",
        f"| Base profit factor | {baseline.base_profit_factor:.2f} | {policy.base_profit_factor:.2f} |",
        f"| Stress total return | {_fmt(baseline.stress_total_return_pct)} | {_fmt(policy.stress_total_return_pct)} |",
        f"| Stress max drawdown | {_fmt(baseline.stress_max_drawdown_pct)} | {_fmt(policy.stress_max_drawdown_pct)} |",
        f"| Verdict | `{baseline.verdict}` | `{policy.verdict}` |",
        f"| Verdict reasons | {', '.join(f'`{r}`' for r in baseline.verdict_reasons)} | {reasons_text} |",
    ])

    return (
        "# Backtest Metrics Report — v0.2\n\n"
        f"{provenance_block}"
        "## Base Case\n\n"
        f"- `base_total_return_pct`: {policy.base_total_return_pct:.2f}%\n"
        f"- `base_annualized_return_pct`: {policy.base_annualized_return_pct:.2f}%\n"
        f"- `base_max_drawdown_pct`: {policy.base_max_drawdown_pct:.2f}%\n"
        f"- `base_profit_factor`: {policy.base_profit_factor:.2f}\n"
        f"- `trade_count`: {policy.trade_count}\n"
        f"- `usable_calendar_year_count`: {policy.usable_calendar_year_count}\n"
        f"- Exposure ratio: {base.exposure_ratio * 100:.2f}%\n"
        f"- Gap-up skips: {base.skipped_gap_up_entries}\n"
        f"- Stop gap fills: {base.stop_gap_fills}\n\n"
        "## Stress Case\n\n"
        f"- `stress_total_return_pct`: {policy.stress_total_return_pct:.2f}%\n"
        f"- `stress_max_drawdown_pct`: {policy.stress_max_drawdown_pct:.2f}%\n"
        f"- Annualized return: {stress.annualized_return * 100:.2f}%\n"
        f"- Profit factor: {stress.profit_factor:.2f}\n"
        f"- Trade count: {stress.trade_count}\n\n"
        "## Yearly Returns\n\n"
        "| Year | Start Equity | End Equity | Return |\n"
        "|---|---:|---:|---:|\n"
        f"{yearly_lines}\n\n"
        "## Section 4 Booleans (001c5)\n\n"
        "| Boolean | Value |\n"
        "|---|---|\n"
        f"{bool_rows}\n\n"
        "## Verdict\n\n"
        f"- **verdict**: `{policy.verdict}`\n"
        f"- **verdict_reasons**: {reasons_text}\n\n"
        "## v0.1 vs v0.2 Comparison\n\n"
        "| Metric | v0.1 | v0.2 |\n"
        "|---|---|---|\n"
        f"{comparison_rows}\n"
    )


def render_adoption_verdict_v02_markdown(
    suite: BacktestSuiteResult,
    policy: EvalPolicyV02Result,
) -> str:
    reasons_text = (
        ", ".join(f"`{r}`" for r in policy.verdict_reasons)
        if policy.verdict_reasons
        else "none"
    )
    provenance_lines = [f"- Data provenance: `{suite.provenance_label}`"]
    if suite.provenance_note:
        provenance_lines.append(f"- Provenance note: {suite.provenance_note}")
    provenance_block = "## Provenance\n\n" + "\n".join(provenance_lines) + "\n\n"

    return (
        "# Adoption Verdict — v0.2\n\n"
        f"{provenance_block}"
        f"- `verdict`: `{policy.verdict}`\n"
        f"- `verdict_reasons`: {reasons_text}\n"
        f"- `base_total_return_pct`: {policy.base_total_return_pct:.2f}%\n"
        f"- `base_annualized_return_pct`: {policy.base_annualized_return_pct:.2f}%\n"
        f"- `base_max_drawdown_pct`: {policy.base_max_drawdown_pct:.2f}%\n"
        f"- `base_profit_factor`: {policy.base_profit_factor:.2f}\n"
        f"- `trade_count`: {policy.trade_count}\n"
        f"- `usable_calendar_year_count`: {policy.usable_calendar_year_count}\n"
        f"- `stress_total_return_pct`: {policy.stress_total_return_pct:.2f}%\n"
        f"- `stress_max_drawdown_pct`: {policy.stress_max_drawdown_pct:.2f}%\n"
        f"- `evidence_sufficient`: {policy.evidence_sufficient}\n"
        f"- `base_quality_pass`: {policy.base_quality_pass}\n"
        f"- `stress_pass`: {policy.stress_pass}\n"
    )


def render_paper_trade_checklist_v02_markdown(checklist: Sequence[str]) -> str:
    lines = "\n".join(f"- [ ] {item}" for item in checklist)
    return f"# Paper-Trade Checklist — v0.2\n\n{lines}\n"
