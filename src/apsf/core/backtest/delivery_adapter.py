from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .reporting import load_price_history_from_records

JSON_MIRROR_SUFFIX = ".parquet.json"


@dataclass(frozen=True)
class DeliveryLayoutLoadResult:
    price_history_by_symbol: dict[str, tuple]
    json_sources: tuple[Path, ...]
    json_mirror_sources: tuple[Path, ...]
    parquet_sources: tuple[Path, ...]
    adapter_mode: str


def load_price_history_from_delivery_layout(data_root: Path) -> DeliveryLayoutLoadResult:
    prices_root = data_root / "prices"
    if not prices_root.exists():
        raise ValueError(f"delivery layout missing prices directory: {prices_root}")

    json_sources: list[Path] = []
    json_mirror_sources: list[Path] = []
    parquet_sources: list[Path] = []
    records_by_symbol: dict[str, list[dict[str, object]]] = {}

    for ticker_dir in sorted(path for path in prices_root.iterdir() if path.is_dir()):
        symbol = ticker_dir.name
        for source in sorted(ticker_dir.iterdir()):
            name_lower = source.name.lower()
            suffix = source.suffix.lower()
            if name_lower.endswith(JSON_MIRROR_SUFFIX):
                payload = json.loads(source.read_text(encoding="utf-8"))
                if not isinstance(payload, list):
                    raise ValueError(f"delivery JSON mirror source must be a list of records: {source}")
                records_by_symbol.setdefault(symbol, []).extend(payload)
                json_mirror_sources.append(source)
            elif suffix == ".json":
                payload = json.loads(source.read_text(encoding="utf-8"))
                if not isinstance(payload, list):
                    raise ValueError(f"delivery JSON source must be a list of records: {source}")
                records_by_symbol.setdefault(symbol, []).extend(payload)
                json_sources.append(source)
            elif suffix == ".parquet":
                parquet_sources.append(source)

    if parquet_sources and not json_sources and not json_mirror_sources:
        raise ValueError(
            "delivery layout contains only Parquet sources. "
            "A native Parquet reader is not installed in this repository yet; "
            f"provide {JSON_MIRROR_SUFFIX} files under the same data/prices/{{ticker}}/ layout."
        )
    if not records_by_symbol:
        raise ValueError(f"delivery layout contains no supported JSON sources: {prices_root}")

    history = load_price_history_from_records(records_by_symbol)
    adapter_mode = "json_mirror_adapter" if json_mirror_sources else "json_direct"
    return DeliveryLayoutLoadResult(
        price_history_by_symbol=history,
        json_sources=tuple(json_sources),
        json_mirror_sources=tuple(json_mirror_sources),
        parquet_sources=tuple(parquet_sources),
        adapter_mode=adapter_mode,
    )
