from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_JQUANTS_BASE_URL = "https://api.jquants.com/v2"
DEFAULT_PARQUET_MIRROR_MODE = "json_mirror"
_PARQUET_MAGIC_BYTES = b"PAR1"


@dataclass(frozen=True)
class JQuantsDailyBar:
    date: str
    ticker: str
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int
    turnover: float
    imputed: bool = False


@dataclass(frozen=True)
class JQuantsFetchResult:
    bars_by_ticker: dict[str, tuple[JQuantsDailyBar, ...]]
    request_urls: tuple[str, ...]


@dataclass(frozen=True)
class UniverseConstituent:
    ticker: str
    name: str
    underlying_index: str
    currency_exposure: str


@dataclass(frozen=True)
class UniverseSnapshot:
    evaluated_at: str
    adtv_threshold_jpy: float
    tickers: tuple[UniverseConstituent, ...]


def fetch_jquants_daily_bars(
    *,
    api_token: str,
    tickers: Sequence[str],
    from_date: date,
    to_date: date,
    base_url: str = DEFAULT_JQUANTS_BASE_URL,
    fetch_json: Callable[[str, Mapping[str, str]], Mapping[str, object]] | None = None,
) -> JQuantsFetchResult:
    bars_by_ticker: dict[str, tuple[JQuantsDailyBar, ...]] = {}
    request_urls: list[str] = []
    fetcher = fetch_json or _default_fetch_json

    for ticker in tickers:
        records: list[Mapping[str, object]] = []
        pagination_key: str | None = None

        while True:
            params: dict[str, str] = {
                "code": _jquants_code_for_ticker(ticker),
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
            }
            if pagination_key:
                params["pagination_key"] = pagination_key

            request_urls.append(_build_request_url(base_url, params))
            payload = fetcher(api_token, params)
            page_records = _extract_data_records(payload)
            records.extend(page_records)
            pagination_key = _extract_pagination_key(payload)
            if not pagination_key:
                break

        bars_by_ticker[ticker] = normalize_jquants_daily_bars(ticker=ticker, records=records)

    return JQuantsFetchResult(
        bars_by_ticker=bars_by_ticker,
        request_urls=tuple(request_urls),
    )


def normalize_jquants_daily_bars(
    *,
    ticker: str,
    records: Sequence[Mapping[str, object]],
) -> tuple[JQuantsDailyBar, ...]:
    bars: list[JQuantsDailyBar] = []
    for index, record in enumerate(records):
        try:
            trade_date = str(record["Date"])
            close = float(record["C"])
            open_price = float(record.get("O", close))
            high = float(record.get("H", close))
            low = float(record.get("L", close))
            volume = int(float(record.get("Vo", 0.0)))
            turnover = float(record.get("Va", 0.0))
        except KeyError as exc:
            raise ValueError(f"{ticker} record {index} is missing required v2 field {exc.args[0]!r}") from exc

        adj_close_value = record.get("AdjC")
        if adj_close_value is None:
            adj_factor = record.get("AdjFactor")
            if adj_factor is None:
                raise ValueError(f"{ticker} record {index} is missing both 'AdjC' and 'AdjFactor'.")
            adj_close = close * float(adj_factor)
        else:
            adj_close = float(adj_close_value)

        bars.append(
            JQuantsDailyBar(
                date=trade_date,
                ticker=ticker,
                open=open_price,
                high=high,
                low=low,
                close=close,
                adj_close=adj_close,
                volume=volume,
                turnover=turnover,
                imputed=False,
            )
        )

    return tuple(sorted(bars, key=lambda item: item.date))


def build_delivery_records(
    bars: Sequence[JQuantsDailyBar],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    previous_adj_close: float | None = None
    for bar in bars:
        daily_return = ((bar.adj_close / previous_adj_close) - 1.0) if previous_adj_close else 0.0
        records.append(
            {
                "date": bar.date,
                "ticker": bar.ticker,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "adj_close": bar.adj_close,
                "volume": bar.volume,
                "turnover": bar.turnover,
                "daily_return": daily_return,
                "imputed": bar.imputed,
            }
        )
        previous_adj_close = bar.adj_close
    return records


def write_delivery_layout(
    *,
    data_root: Path,
    bars_by_ticker: Mapping[str, Sequence[JQuantsDailyBar]],
    universe_snapshot: UniverseSnapshot | None = None,
    parquet_mode: str = DEFAULT_PARQUET_MIRROR_MODE,
) -> tuple[Path, ...]:
    written_paths: list[Path] = []
    prices_root = data_root / "prices"
    prices_root.mkdir(parents=True, exist_ok=True)

    for ticker, bars in bars_by_ticker.items():
        by_year: dict[int, list[JQuantsDailyBar]] = {}
        for bar in bars:
            by_year.setdefault(_year_from_iso_date(bar.date), []).append(bar)

        ticker_root = prices_root / ticker
        ticker_root.mkdir(parents=True, exist_ok=True)

        for year, year_bars in sorted(by_year.items()):
            base_path = ticker_root / f"{year}.parquet"
            records = build_delivery_records(tuple(year_bars))
            if parquet_mode == DEFAULT_PARQUET_MIRROR_MODE:
                mirror_path = ticker_root / f"{year}.parquet.json"
                mirror_path.write_text(
                    json.dumps(records, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                written_paths.append(mirror_path)
                if not base_path.exists():
                    base_path.write_bytes(_PARQUET_MAGIC_BYTES)
                written_paths.append(base_path)
            else:
                raise ValueError(f"unsupported parquet_mode: {parquet_mode}")

    if universe_snapshot is not None:
        snapshot_path = data_root / "universe_snapshot.json"
        snapshot_payload = {
            "evaluated_at": universe_snapshot.evaluated_at,
            "adtv_threshold_jpy": universe_snapshot.adtv_threshold_jpy,
            "tickers": [
                {
                    "ticker": item.ticker,
                    "name": item.name,
                    "underlying_index": item.underlying_index,
                    "currency_exposure": item.currency_exposure,
                }
                for item in universe_snapshot.tickers
            ],
        }
        snapshot_path.write_text(
            json.dumps(snapshot_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written_paths.append(snapshot_path)

    return tuple(written_paths)


def _default_fetch_json(api_token: str, params: Mapping[str, str]) -> Mapping[str, object]:
    url = _build_request_url(DEFAULT_JQUANTS_BASE_URL, params)
    request = Request(url, headers={"x-api-key": api_token})
    with urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("J-Quants response must be a JSON object.")
    return payload


def _extract_data_records(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("J-Quants response is missing 'data' list.")
    records: list[Mapping[str, object]] = []
    for item in data:
        if not isinstance(item, Mapping):
            raise ValueError("J-Quants 'data' entries must be JSON objects.")
        records.append(item)
    return records


def _extract_pagination_key(payload: Mapping[str, object]) -> str | None:
    for key in ("pagination_key", "paginationKey"):
        value = payload.get(key)
        if value:
            return str(value)
    return None


def _build_request_url(base_url: str, params: Mapping[str, str]) -> str:
    return f"{base_url.rstrip('/')}/equities/bars/daily?{urlencode(params)}"


def _jquants_code_for_ticker(ticker: str) -> str:
    return f"{ticker}0"


def _year_from_iso_date(value: str) -> int:
    return datetime.strptime(value, "%Y-%m-%d").year
