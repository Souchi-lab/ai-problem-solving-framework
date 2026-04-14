from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path


ORDER_STATE_SCHEMA_VERSION = "1.0"
ACTIVE_ORDER_STATUSES = {"pending", "open", "unknown"}
BLOCKING_ORDER_STATUSES = ACTIVE_ORDER_STATUSES | {"completed"}


@dataclass(frozen=True)
class OrderLogEntry:
    timestamp: str
    event: str
    detail: str


@dataclass(frozen=True)
class OrderState:
    schema_version: str
    date: str
    signal_id: str
    status: str
    symbol: str
    order_id: str | None = None
    order_price: float | None = None
    reference_price: float | None = None
    filled_price: float | None = None
    stop_order_id: str | None = None
    stop_price: float | None = None
    cancel_review_flag: bool = False
    exit_pending: bool = False
    fallback_used: bool = False
    log_entries: tuple[OrderLogEntry, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "date": self.date,
            "signal_id": self.signal_id,
            "status": self.status,
            "symbol": self.symbol,
            "order_id": self.order_id,
            "order_price": self.order_price,
            "reference_price": self.reference_price,
            "filled_price": self.filled_price,
            "stop_order_id": self.stop_order_id,
            "stop_price": self.stop_price,
            "cancel_review_flag": self.cancel_review_flag,
            "exit_pending": self.exit_pending,
            "fallback_used": self.fallback_used,
            "log_entries": [
                {
                    "timestamp": entry.timestamp,
                    "event": entry.event,
                    "detail": entry.detail,
                }
                for entry in self.log_entries
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "OrderState":
        log_entries = tuple(
            OrderLogEntry(
                timestamp=str(entry["timestamp"]),
                event=str(entry["event"]),
                detail=str(entry["detail"]),
            )
            for entry in _as_list(payload.get("log_entries"))
        )
        return cls(
            schema_version=str(payload.get("schema_version", ORDER_STATE_SCHEMA_VERSION)),
            date=str(payload["date"]),
            signal_id=str(payload["signal_id"]),
            status=str(payload["status"]),
            symbol=str(payload["symbol"]),
            order_id=_as_optional_str(payload.get("order_id")),
            order_price=_as_optional_float(payload.get("order_price")),
            reference_price=_as_optional_float(payload.get("reference_price")),
            filled_price=_as_optional_float(payload.get("filled_price")),
            stop_order_id=_as_optional_str(payload.get("stop_order_id")),
            stop_price=_as_optional_float(payload.get("stop_price")),
            cancel_review_flag=bool(payload.get("cancel_review_flag", False)),
            exit_pending=bool(payload.get("exit_pending", False)),
            fallback_used=bool(payload.get("fallback_used", False)),
            log_entries=log_entries,
        )


def generate_signal_id(*, ticker: str, trading_date: date, direction: str = "BUY") -> str:
    normalized_direction = direction.upper()
    return f"{ticker}_{trading_date.isoformat()}_{normalized_direction}"


def create_pending_order_state(
    *,
    trading_date: date,
    symbol: str,
    signal_id: str,
    reference_price: float | None = None,
    stop_price: float | None = None,
) -> OrderState:
    return OrderState(
        schema_version=ORDER_STATE_SCHEMA_VERSION,
        date=trading_date.isoformat(),
        signal_id=signal_id,
        status="pending",
        symbol=symbol,
        reference_price=reference_price,
        stop_price=stop_price,
        log_entries=(
            OrderLogEntry(
                timestamp=_utc_now_isoformat(),
                event="ORDER_PENDING",
                detail="Pending order state initialized before broker submission.",
            ),
        ),
    )


def append_order_log_entry(
    state: OrderState,
    *,
    event: str,
    detail: str,
    timestamp: str | None = None,
) -> OrderState:
    entry = OrderLogEntry(
        timestamp=timestamp or _utc_now_isoformat(),
        event=event,
        detail=detail,
    )
    return replace(state, log_entries=state.log_entries + (entry,))


def load_order_state(path: Path) -> OrderState | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("order_state.json must contain a JSON object.")
    return OrderState.from_dict(payload)


def save_order_state(path: Path, state: OrderState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def _as_list(value: object) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("log_entries must be a JSON array.")
    normalized: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("each log entry must be a JSON object.")
        normalized.append(item)
    return normalized


def _as_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _as_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _utc_now_isoformat() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
