from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Mapping

from .jquants_delivery import (
    DEFAULT_JQUANTS_BASE_URL,
    JQuantsFetchResult,
    UniverseConstituent,
    UniverseSnapshot,
    fetch_jquants_daily_bars,
    write_delivery_layout,
)


DEFAULT_JQUANTS_TOKEN_ENV_VARS = (
    "JQUANTS_API_KEY",
    "JQUANTS_API_TOKEN",
    "JQUANTS_ID_TOKEN",
    "JQUANTS_BEARER_TOKEN",
)
DEFAULT_DATA_ROOT_DIRNAME = "data"
DEFAULT_UNIVERSE_CONSTITUENTS = (
    UniverseConstituent(
        ticker="1306",
        name="NEXT FUNDS TOPIX ETF",
        underlying_index="TOPIX",
        currency_exposure="JPY",
    ),
    UniverseConstituent(
        ticker="1348",
        name="MAXIS TOPIX ETF",
        underlying_index="TOPIX",
        currency_exposure="JPY",
    ),
    UniverseConstituent(
        ticker="2558",
        name="MAXIS US Stock (S&P 500) ETF",
        underlying_index="S&P 500",
        currency_exposure="USD_hedged",
    ),
)


@dataclass(frozen=True)
class MaterializedDeliveryResult:
    data_root: Path
    written_paths: tuple[Path, ...]
    fetch_result: JQuantsFetchResult


def resolve_jquants_api_token(
    *,
    env: Mapping[str, str] | None = None,
    candidate_env_vars: tuple[str, ...] = DEFAULT_JQUANTS_TOKEN_ENV_VARS,
) -> str:
    source = env or os.environ
    for key in candidate_env_vars:
        value = source.get(key)
        if value and value.strip():
            return value.strip()
    raise ValueError(
        "J-Quants API token is not configured. "
        f"Set one of: {', '.join(candidate_env_vars)}"
    )


def materialize_jquants_delivery_layout(
    *,
    run_dir: Path,
    from_date: date,
    to_date: date,
    api_token: str | None = None,
    base_url: str = DEFAULT_JQUANTS_BASE_URL,
    fetch_json: Callable[[str, Mapping[str, str]], Mapping[str, object]] | None = None,
) -> MaterializedDeliveryResult:
    token = api_token or resolve_jquants_api_token()
    tickers = tuple(item.ticker for item in DEFAULT_UNIVERSE_CONSTITUENTS)
    fetch_result = fetch_jquants_daily_bars(
        api_token=token,
        tickers=tickers,
        from_date=from_date,
        to_date=to_date,
        base_url=base_url,
        fetch_json=fetch_json,
    )
    data_root = run_dir / DEFAULT_DATA_ROOT_DIRNAME
    written_paths = write_delivery_layout(
        data_root=data_root,
        bars_by_ticker=fetch_result.bars_by_ticker,
        universe_snapshot=UniverseSnapshot(
            evaluated_at=to_date.isoformat(),
            adtv_threshold_jpy=50_000_000.0,
            tickers=DEFAULT_UNIVERSE_CONSTITUENTS,
        ),
    )
    return MaterializedDeliveryResult(
        data_root=data_root,
        written_paths=written_paths,
        fetch_result=fetch_result,
    )
