from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from apsf.core.market_data import (
    DEFAULT_UNIVERSE_CONSTITUENTS,
    materialize_jquants_delivery_layout,
    resolve_jquants_api_token,
)


def test_resolve_jquants_api_token_reads_known_env_var() -> None:
    token = resolve_jquants_api_token(env={"JQUANTS_API_KEY": "abc123"})
    assert token == "abc123"


def test_resolve_jquants_api_token_raises_when_missing() -> None:
    with pytest.raises(ValueError, match="J-Quants API token is not configured"):
        resolve_jquants_api_token(env={})


def test_materialize_jquants_delivery_layout_writes_contract_tree(tmp_path: Path) -> None:
    def fake_fetch_json(api_token: str, params: dict[str, str]) -> dict[str, object]:
        base_price = {
            "13060": 100.0,
            "13480": 200.0,
            "25580": 300.0,
        }[params["code"]]
        return {
            "data": [
                {
                    "Date": "2025-01-06",
                    "Code": params["code"],
                    "O": base_price,
                    "H": base_price + 1.0,
                    "L": base_price - 1.0,
                    "C": base_price,
                    "Vo": 1000.0,
                    "Va": base_price * 1000.0,
                    "AdjFactor": 1.0,
                    "AdjC": base_price,
                }
            ]
        }

    result = materialize_jquants_delivery_layout(
        run_dir=tmp_path / "001c2_case",
        from_date=date(2025, 1, 1),
        to_date=date(2025, 1, 31),
        api_token="token-123",
        fetch_json=fake_fetch_json,
    )

    for item in DEFAULT_UNIVERSE_CONSTITUENTS:
        mirror_path = result.data_root / "prices" / item.ticker / "2025.parquet.json"
        assert mirror_path.exists()
        payload = json.loads(mirror_path.read_text(encoding="utf-8"))
        assert payload[0]["ticker"] == item.ticker

    snapshot_path = result.data_root / "universe_snapshot.json"
    assert snapshot_path.exists()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert len(snapshot["tickers"]) == 3
    assert result.fetch_result.request_urls
