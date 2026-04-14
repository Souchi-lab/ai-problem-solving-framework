from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from apsf.core.execution import (
    EntryPreflightSnapshot,
    ManualOrderFallback,
    append_order_log_entry,
    create_pending_order_state,
    evaluate_entry_preflight,
    generate_signal_id,
    load_order_state,
    save_order_state,
    write_manual_order_fallback_artifacts,
)


def test_generate_signal_id_uses_ticker_date_and_direction() -> None:
    signal_id = generate_signal_id(ticker="1306", trading_date=date(2026, 4, 13))
    assert signal_id == "1306_2026-04-13_BUY"


def test_order_state_round_trip_preserves_logs(tmp_path: Path) -> None:
    state_path = tmp_path / "data" / "order_state.json"
    state = create_pending_order_state(
        trading_date=date(2026, 4, 13),
        symbol="1306",
        signal_id="1306_2026-04-13_BUY",
        reference_price=2_501.0,
        stop_price=2_440.0,
    )
    state = append_order_log_entry(
        state,
        event="CB1_PASS",
        detail="Daily PnL = 0 JPY.",
        timestamp="2026-04-13T00:05:00Z",
    )

    save_order_state(state_path, state)
    loaded = load_order_state(state_path)

    assert loaded == state
    assert state_path.read_text(encoding="utf-8").endswith("\n")


def test_entry_preflight_blocks_daily_loss_limit_when_realized_loss_breaches_limit() -> None:
    decision = evaluate_entry_preflight(
        trading_date=date(2026, 4, 13),
        signal_id="1306_2026-04-13_BUY",
        snapshot=EntryPreflightSnapshot(
            realized_pnl_jpy=-550.0,
            unrealized_pnl_jpy=0.0,
            position_count=0,
        ),
    )

    assert decision.allowed is False
    assert decision.status == "DAILY_LOSS_STOP"
    assert decision.daily_pnl_jpy == -550.0


def test_entry_preflight_does_not_count_unrealized_only_loss_toward_cb1() -> None:
    decision = evaluate_entry_preflight(
        trading_date=date(2026, 4, 13),
        signal_id="1306_2026-04-13_BUY",
        snapshot=EntryPreflightSnapshot(
            realized_pnl_jpy=0.0,
            unrealized_pnl_jpy=-700.0,
            position_count=0,
        ),
    )

    assert decision.allowed is True
    assert decision.status == "PASS"
    assert decision.daily_pnl_jpy == 0.0


def test_entry_preflight_blocks_duplicate_signal_for_same_day() -> None:
    existing_state = create_pending_order_state(
        trading_date=date(2026, 4, 13),
        symbol="1306",
        signal_id="1306_2026-04-13_BUY",
    )

    decision = evaluate_entry_preflight(
        trading_date=date(2026, 4, 13),
        signal_id="1306_2026-04-13_BUY",
        snapshot=EntryPreflightSnapshot(),
        existing_state=existing_state,
    )

    assert decision.allowed is False
    assert decision.status == "IDEMPOTENCY_SKIP"


def test_entry_preflight_blocks_when_position_limit_is_reached() -> None:
    decision = evaluate_entry_preflight(
        trading_date=date(2026, 4, 13),
        signal_id="1306_2026-04-13_BUY",
        snapshot=EntryPreflightSnapshot(position_count=1),
    )

    assert decision.allowed is False
    assert decision.status == "POSITION_LIMIT"


def test_entry_preflight_blocks_when_existing_state_is_open_from_previous_day() -> None:
    existing_state = create_pending_order_state(
        trading_date=date(2026, 4, 12),
        symbol="1306",
        signal_id="1306_2026-04-12_BUY",
    )
    existing_state = append_order_log_entry(
        existing_state,
        event="ORDER_FILLED",
        detail="Order filled and stop order pending management.",
        timestamp="2026-04-12T00:10:00Z",
    )
    existing_state = existing_state.__class__(**{**existing_state.__dict__, "status": "open"})

    decision = evaluate_entry_preflight(
        trading_date=date(2026, 4, 13),
        signal_id="1306_2026-04-13_BUY",
        snapshot=EntryPreflightSnapshot(position_count=0),
        existing_state=existing_state,
    )

    assert decision.allowed is False
    assert decision.status == "POSITION_LIMIT"


def test_write_manual_order_fallback_artifacts_writes_markdown_and_csv(tmp_path: Path) -> None:
    run_dir = tmp_path / "001c3_case"
    run_dir.mkdir()

    markdown_path, csv_path = write_manual_order_fallback_artifacts(
        run_dir=run_dir,
        fallback=ManualOrderFallback(
            generated_at=datetime(2026, 4, 13, 9, 6),
            symbol="1306",
            quantity="1 lot",
            order_type="market_buy",
            order_deadline="same_day",
            stop_price=2_440.0,
            strategy_summary="Breakout entry after 15:35 confirmation.",
            remaining_loss_budget_jpy=180.0,
            signal_id="1306_2026-04-13_BUY",
            fallback_reason="API connection refused during batch order submission.",
        ),
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    csv = csv_path.read_text(encoding="utf-8")

    assert markdown_path.exists()
    assert csv_path.exists()
    assert "Manual Order Fallback" in markdown
    assert "1306_2026-04-13_BUY" in markdown
    assert "API connection refused" in markdown
    assert "signal_id" in csv
    assert "Breakout entry after 15:35 confirmation." in csv
