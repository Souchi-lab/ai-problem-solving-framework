from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from apsf.core.artifact_writer import ArtifactWriter


DEFAULT_FALLBACK_MARKDOWN_FILE = "fallback_manual_order.md"
DEFAULT_FALLBACK_CSV_FILE = "fallback_manual_order.csv"


@dataclass(frozen=True)
class ManualOrderFallback:
    generated_at: datetime
    symbol: str
    quantity: str
    order_type: str
    order_deadline: str
    stop_price: float
    strategy_summary: str
    remaining_loss_budget_jpy: float
    signal_id: str
    fallback_reason: str


def render_manual_order_fallback_markdown(fallback: ManualOrderFallback) -> str:
    timestamp = fallback.generated_at.strftime("%Y-%m-%d %H:%M JST")
    return (
        "# Manual Order Fallback\n\n"
        f"- Generated at: {timestamp}\n"
        f"- Signal ID: {fallback.signal_id}\n"
        f"- Fallback reason: {fallback.fallback_reason}\n\n"
        "## Order Instruction\n\n"
        f"- Symbol: {fallback.symbol}\n"
        f"- Quantity: {fallback.quantity}\n"
        f"- Order type: {fallback.order_type}\n"
        f"- Order deadline: {fallback.order_deadline}\n"
        f"- Reverse-stop price: {fallback.stop_price:.2f} JPY\n"
        f"- Strategy summary: {fallback.strategy_summary}\n"
        f"- Remaining daily loss budget: {fallback.remaining_loss_budget_jpy:.2f} JPY / 500.00 JPY\n\n"
        "## Manual Completion Steps\n\n"
        "1. Place the broker order manually using the parameters above.\n"
        "2. Update `data/order_state.json` with the broker order id and final fill price.\n"
        "3. Mark `fallback_used` as `true` and append a `MANUAL_ORDER_COMPLETED` log entry.\n"
        "4. Enter the reverse-stop order manually after fill confirmation.\n"
    )


def render_manual_order_fallback_csv(fallback: ManualOrderFallback) -> str:
    return (
        "generated_at,signal_id,fallback_reason,symbol,quantity,order_type,order_deadline,stop_price_jpy,"
        "remaining_loss_budget_jpy,strategy_summary\n"
        f"{fallback.generated_at.isoformat()},{fallback.signal_id},{_csv_escape(fallback.fallback_reason)},"
        f"{fallback.symbol},{fallback.quantity},{fallback.order_type},{fallback.order_deadline},"
        f"{fallback.stop_price:.2f},{fallback.remaining_loss_budget_jpy:.2f},{_csv_escape(fallback.strategy_summary)}\n"
    )


def write_manual_order_fallback_artifacts(
    *,
    run_dir: Path,
    fallback: ManualOrderFallback,
    artifact_writer: ArtifactWriter | None = None,
    markdown_name: str = DEFAULT_FALLBACK_MARKDOWN_FILE,
    csv_name: str = DEFAULT_FALLBACK_CSV_FILE,
) -> tuple[Path, Path]:
    writer = artifact_writer or ArtifactWriter()
    markdown_path = run_dir / markdown_name
    csv_path = run_dir / csv_name
    writer.write(
        path=markdown_path,
        content=render_manual_order_fallback_markdown(fallback),
        writing_role="Builder",
        run_dir=run_dir,
    )
    writer.write(
        path=csv_path,
        content=render_manual_order_fallback_csv(fallback),
        writing_role="Builder",
        run_dir=run_dir,
    )
    return markdown_path, csv_path


def _csv_escape(value: str) -> str:
    escaped = value.replace('"', '""')
    return f'"{escaped}"'
