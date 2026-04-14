from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from apsf.core.market_data import (
    DEFAULT_PARQUET_MIRROR_MODE,
    UniverseConstituent,
    UniverseSnapshot,
    build_delivery_records,
    fetch_jquants_daily_bars,
    normalize_jquants_daily_bars,
    write_delivery_layout,
)


def test_normalize_jquants_daily_bars_uses_adj_close_when_present() -> None:
    bars = normalize_jquants_daily_bars(
        ticker="1306",
        records=[
            {
                "Date": "2024-01-15",
                "Code": "13060",
                "O": 2615.5,
                "H": 2645.5,
                "L": 2610.5,
                "C": 2643.0,
                "Vo": 3024650.0,
                "Va": 7971865390.0,
                "AdjFactor": 1.0,
                "AdjC": 264.3,
            }
        ],
    )

    assert len(bars) == 1
    assert bars[0].ticker == "1306"
    assert bars[0].adj_close == 264.3
    assert bars[0].volume == 3024650


def test_normalize_jquants_daily_bars_falls_back_to_adjfactor() -> None:
    bars = normalize_jquants_daily_bars(
        ticker="1348",
        records=[
            {
                "Date": "2024-01-15",
                "Code": "13480",
                "O": 2500.0,
                "H": 2550.0,
                "L": 2490.0,
                "C": 2520.0,
                "Vo": 1000.0,
                "Va": 2_520_000.0,
                "AdjFactor": 0.1,
            }
        ],
    )

    assert bars[0].adj_close == 252.0


def test_build_delivery_records_computes_daily_return_from_adj_close() -> None:
    bars = normalize_jquants_daily_bars(
        ticker="2558",
        records=[
            {
                "Date": "2024-01-15",
                "Code": "25580",
                "O": 100.0,
                "H": 101.0,
                "L": 99.0,
                "C": 100.0,
                "Vo": 100.0,
                "Va": 10_000.0,
                "AdjFactor": 1.0,
                "AdjC": 100.0,
            },
            {
                "Date": "2024-01-16",
                "Code": "25580",
                "O": 101.0,
                "H": 103.0,
                "L": 100.0,
                "C": 102.0,
                "Vo": 120.0,
                "Va": 12_240.0,
                "AdjFactor": 1.0,
                "AdjC": 102.0,
            },
        ],
    )

    records = build_delivery_records(bars)

    assert records[0]["daily_return"] == 0.0
    assert round(float(records[1]["daily_return"]), 6) == 0.02
    assert all(key in records[0] for key in ("open", "high", "low", "close", "adj_close", "volume", "turnover"))


def test_write_delivery_layout_writes_parquet_json_mirror_and_universe_snapshot(tmp_path: Path) -> None:
    bars = normalize_jquants_daily_bars(
        ticker="1306",
        records=[
            {
                "Date": "2025-01-06",
                "Code": "13060",
                "O": 100.0,
                "H": 101.0,
                "L": 99.0,
                "C": 100.0,
                "Vo": 100.0,
                "Va": 10_000.0,
                "AdjFactor": 1.0,
                "AdjC": 100.0,
            }
        ],
    )

    written = write_delivery_layout(
        data_root=tmp_path / "data",
        bars_by_ticker={"1306": bars},
        universe_snapshot=UniverseSnapshot(
            evaluated_at="2026-04-14",
            adtv_threshold_jpy=50_000_000.0,
            tickers=(
                UniverseConstituent(
                    ticker="1306",
                    name="NEXT FUNDS TOPIX ETF",
                    underlying_index="TOPIX",
                    currency_exposure="JPY",
                ),
            ),
        ),
        parquet_mode=DEFAULT_PARQUET_MIRROR_MODE,
    )

    mirror_path = tmp_path / "data" / "prices" / "1306" / "2025.parquet.json"
    parquet_path = tmp_path / "data" / "prices" / "1306" / "2025.parquet"
    snapshot_path = tmp_path / "data" / "universe_snapshot.json"

    assert mirror_path in written
    assert parquet_path in written
    assert snapshot_path in written
    assert parquet_path.read_bytes() == b"PAR1"
    payload = json.loads(mirror_path.read_text(encoding="utf-8"))
    assert payload[0]["ticker"] == "1306"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["tickers"][0]["underlying_index"] == "TOPIX"


def test_fetch_jquants_daily_bars_uses_expected_code_and_query_shape() -> None:
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_fetch_json(api_token: str, params: dict[str, str]) -> dict[str, object]:
        calls.append((api_token, dict(params)))
        return {
            "data": [
                {
                    "Date": "2024-01-15",
                    "Code": params["code"],
                    "O": 100.0,
                    "H": 101.0,
                    "L": 99.0,
                    "C": 100.0,
                    "Vo": 100.0,
                    "Va": 10_000.0,
                    "AdjFactor": 1.0,
                    "AdjC": 100.0,
                }
            ]
        }

    result = fetch_jquants_daily_bars(
        api_token="token-123",
        tickers=("1306", "1348"),
        from_date=date(2024, 1, 1),
        to_date=date(2024, 1, 31),
        fetch_json=fake_fetch_json,
    )

    assert set(result.bars_by_ticker) == {"1306", "1348"}
    assert calls[0][0] == "token-123"
    assert calls[0][1]["code"] == "13060"
    assert calls[1][1]["code"] == "13480"
    assert calls[0][1]["from"] == "2024-01-01"
    assert calls[0][1]["to"] == "2024-01-31"
    assert "equities/bars/daily" in result.request_urls[0]
