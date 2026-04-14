from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .order_state import ACTIVE_ORDER_STATUSES, BLOCKING_ORDER_STATUSES, OrderState


@dataclass(frozen=True)
class EntryPreflightSnapshot:
    realized_pnl_jpy: float = 0.0
    unrealized_pnl_jpy: float | None = None
    position_count: int = 0

    @property
    def daily_pnl_jpy(self) -> float:
        return self.realized_pnl_jpy


@dataclass(frozen=True)
class EntryPreflightDecision:
    status: str
    allowed: bool
    reason: str
    daily_pnl_jpy: float
    idempotency_key: str


def evaluate_entry_preflight(
    *,
    trading_date: date,
    signal_id: str,
    snapshot: EntryPreflightSnapshot,
    existing_state: OrderState | None = None,
    daily_loss_limit_jpy: float = 500.0,
    position_limit: int = 1,
) -> EntryPreflightDecision:
    idempotency_key = f"{trading_date.isoformat()}_{signal_id}"
    if (
        existing_state is not None
        and existing_state.date == trading_date.isoformat()
        and existing_state.signal_id == signal_id
        and existing_state.status in BLOCKING_ORDER_STATUSES
    ):
        return EntryPreflightDecision(
            status="IDEMPOTENCY_SKIP",
            allowed=False,
            reason=f"Blocking order state already exists for {idempotency_key}.",
            daily_pnl_jpy=snapshot.daily_pnl_jpy,
            idempotency_key=idempotency_key,
        )

    if existing_state is not None and existing_state.status in ACTIVE_ORDER_STATUSES:
        return EntryPreflightDecision(
            status="POSITION_LIMIT",
            allowed=False,
            reason=(
                "Local order state already indicates an active position/order "
                f"with status {existing_state.status!r}."
            ),
            daily_pnl_jpy=snapshot.daily_pnl_jpy,
            idempotency_key=idempotency_key,
        )

    if snapshot.daily_pnl_jpy <= -abs(daily_loss_limit_jpy):
        return EntryPreflightDecision(
            status="DAILY_LOSS_STOP",
            allowed=False,
            reason=f"Daily PnL {snapshot.daily_pnl_jpy:.2f} JPY breached limit {-abs(daily_loss_limit_jpy):.2f} JPY.",
            daily_pnl_jpy=snapshot.daily_pnl_jpy,
            idempotency_key=idempotency_key,
        )

    if snapshot.position_count >= position_limit:
        return EntryPreflightDecision(
            status="POSITION_LIMIT",
            allowed=False,
            reason=f"Open position count {snapshot.position_count} reached limit {position_limit}.",
            daily_pnl_jpy=snapshot.daily_pnl_jpy,
            idempotency_key=idempotency_key,
        )

    return EntryPreflightDecision(
        status="PASS",
        allowed=True,
        reason="Entry preflight checks passed.",
        daily_pnl_jpy=snapshot.daily_pnl_jpy,
        idempotency_key=idempotency_key,
    )
