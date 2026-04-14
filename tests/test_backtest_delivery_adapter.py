from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from apsf.core.backtest import (
    JSON_MIRROR_SUFFIX,
    build_backtest_artifacts_from_delivery_layout,
    load_price_history_from_delivery_layout,
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


def test_load_price_history_from_delivery_layout_reads_json_contract_layout(tmp_path: Path) -> None:
    data_root = tmp_path / "data" / "prices" / "1306"
    data_root.mkdir(parents=True)
    source = data_root / "2025.json"
    source.write_text(
        json.dumps(_records(count=3, start=date(2025, 1, 1), close=100.0, drift=1.0, volume=10_000.0)),
        encoding="utf-8",
    )

    result = load_price_history_from_delivery_layout(tmp_path / "data")

    assert "1306" in result.price_history_by_symbol
    assert result.json_sources == (source,)
    assert result.adapter_mode == "json_direct"


def test_load_price_history_from_delivery_layout_reads_parquet_json_mirror(tmp_path: Path) -> None:
    ticker_dir = tmp_path / "data" / "prices" / "1306"
    ticker_dir.mkdir(parents=True)
    source = ticker_dir / f"2025{JSON_MIRROR_SUFFIX}"
    source.write_text(
        json.dumps(_records(count=3, start=date(2025, 1, 1), close=100.0, drift=1.0, volume=10_000.0)),
        encoding="utf-8",
    )
    (ticker_dir / "2025.parquet").write_bytes(b"PAR1")

    result = load_price_history_from_delivery_layout(tmp_path / "data")

    assert result.json_mirror_sources == (source,)
    assert result.parquet_sources
    assert result.adapter_mode == "json_mirror_adapter"


def test_load_price_history_from_delivery_layout_rejects_parquet_only_layout(tmp_path: Path) -> None:
    ticker_dir = tmp_path / "data" / "prices" / "1306"
    ticker_dir.mkdir(parents=True)
    (ticker_dir / "2025.parquet").write_bytes(b"PAR1")

    with pytest.raises(ValueError, match="native Parquet reader is not installed"):
        load_price_history_from_delivery_layout(tmp_path / "data")


def test_build_backtest_artifacts_from_delivery_layout_writes_outputs(tmp_path: Path) -> None:
    run_dir = tmp_path / "001c4_case"
    ticker_dir = run_dir / "data" / "prices" / "1306"
    ticker_dir.mkdir(parents=True)
    (ticker_dir / f"2025{JSON_MIRROR_SUFFIX}").write_text(
        json.dumps(_records(count=380, start=date(2025, 1, 1), close=100.0, drift=0.3, volume=10_000.0)),
        encoding="utf-8",
    )
    (ticker_dir / "2025.parquet").write_bytes(b"PAR1")
    ticker_dir = run_dir / "data" / "prices" / "1348"
    ticker_dir.mkdir(parents=True)
    (ticker_dir / f"2025{JSON_MIRROR_SUFFIX}").write_text(
        json.dumps(_records(count=380, start=date(2025, 1, 1), close=101.0, drift=0.25, volume=11_000.0)),
        encoding="utf-8",
    )
    (ticker_dir / "2025.parquet").write_bytes(b"PAR1")
    ticker_dir = run_dir / "data" / "prices" / "2558"
    ticker_dir.mkdir(parents=True)
    (ticker_dir / f"2025{JSON_MIRROR_SUFFIX}").write_text(
        json.dumps(_records(count=380, start=date(2025, 1, 1), close=102.0, drift=0.2, volume=12_000.0)),
        encoding="utf-8",
    )
    (ticker_dir / "2025.parquet").write_bytes(b"PAR1")

    result = build_backtest_artifacts_from_delivery_layout(run_dir=run_dir)

    assert result.paths.metrics_report.exists()
    assert result.paths.adoption_verdict.exists()
    assert "delivery_layout_parquet_json_mirror" in result.paths.metrics_report.read_text(encoding="utf-8")
