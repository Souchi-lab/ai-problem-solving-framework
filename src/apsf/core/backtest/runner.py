from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from apsf.core.artifact_writer import ArtifactWriter

from .delivery_adapter import load_price_history_from_delivery_layout
from .reporting import (
    BacktestSuiteResult,
    load_price_history_from_records,
    render_adoption_verdict_markdown,
    render_metrics_report_markdown,
    render_paper_trade_checklist_markdown,
    run_backtest_suite,
)
from .strategy_simulator import SimulationConfig


DEFAULT_INPUT_FILE = "backtest_input.json"
DEFAULT_METRICS_REPORT_FILE = "metrics_report.md"
DEFAULT_ADOPTION_VERDICT_FILE = "adoption_verdict.md"
DEFAULT_CHECKLIST_FILE = "paper_trade_checklist.md"
DEFAULT_DELIVERY_DATA_DIR = "data"


@dataclass(frozen=True)
class BacktestArtifactPaths:
    metrics_report: Path
    adoption_verdict: Path
    paper_trade_checklist: Path


@dataclass(frozen=True)
class BacktestArtifactResult:
    suite: BacktestSuiteResult
    paths: BacktestArtifactPaths


def load_backtest_input_artifact(path: Path) -> dict[str, tuple]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("backtest input artifact must be a JSON object keyed by symbol.")
    return load_price_history_from_records(payload)


def write_backtest_artifacts(
    *,
    run_dir: Path,
    price_history_by_symbol: dict[str, tuple],
    config: SimulationConfig | None = None,
    artifact_writer: ArtifactWriter | None = None,
    provenance_label: str = "unspecified",
    provenance_note: str | None = None,
) -> BacktestArtifactResult:
    suite = run_backtest_suite(
        price_history_by_symbol,
        config=config,
        provenance_label=provenance_label,
        provenance_note=provenance_note,
    )
    writer = artifact_writer or ArtifactWriter()

    metrics_report_path = run_dir / DEFAULT_METRICS_REPORT_FILE
    adoption_verdict_path = run_dir / DEFAULT_ADOPTION_VERDICT_FILE
    checklist_path = run_dir / DEFAULT_CHECKLIST_FILE

    writer.write(
        path=metrics_report_path,
        content=render_metrics_report_markdown(suite),
        writing_role="Builder",
        run_dir=run_dir,
    )
    writer.write(
        path=adoption_verdict_path,
        content=render_adoption_verdict_markdown(suite),
        writing_role="Builder",
        run_dir=run_dir,
    )
    writer.write(
        path=checklist_path,
        content=render_paper_trade_checklist_markdown(suite.paper_trade_checklist),
        writing_role="Builder",
        run_dir=run_dir,
    )

    return BacktestArtifactResult(
        suite=suite,
        paths=BacktestArtifactPaths(
            metrics_report=metrics_report_path,
            adoption_verdict=adoption_verdict_path,
            paper_trade_checklist=checklist_path,
        ),
    )


def build_backtest_artifacts_from_input(
    *,
    run_dir: Path,
    input_path: Path | None = None,
    config: SimulationConfig | None = None,
    artifact_writer: ArtifactWriter | None = None,
) -> BacktestArtifactResult:
    resolved_input = input_path or (run_dir / DEFAULT_INPUT_FILE)
    price_history = load_backtest_input_artifact(resolved_input)
    return write_backtest_artifacts(
        run_dir=run_dir,
        price_history_by_symbol=price_history,
        config=config,
        artifact_writer=artifact_writer,
        provenance_label="json_input_artifact",
        provenance_note=f"Loaded from {resolved_input.name}.",
    )


def build_backtest_artifacts_from_delivery_layout(
    *,
    run_dir: Path,
    data_root: Path | None = None,
    config: SimulationConfig | None = None,
    artifact_writer: ArtifactWriter | None = None,
) -> BacktestArtifactResult:
    resolved_data_root = data_root or (run_dir / DEFAULT_DELIVERY_DATA_DIR)
    load_result = load_price_history_from_delivery_layout(resolved_data_root)
    if load_result.adapter_mode == "json_mirror_adapter":
        provenance_label = "delivery_layout_parquet_json_mirror"
        provenance_note = (
            "Loaded from .parquet.json mirror files under data/prices/{ticker}/. "
            "This is the accepted adapter boundary for Parquet-shaped delivery until a native Parquet reader is installed."
        )
    else:
        provenance_label = "delivery_layout_json_mirror"
        provenance_note = (
            "Loaded from JSON mirror files under data/prices/{ticker}/{year}.json. "
            "This is a contract-layout adapter path, not native Parquet ingestion."
        )
    return write_backtest_artifacts(
        run_dir=run_dir,
        price_history_by_symbol=load_result.price_history_by_symbol,
        config=config,
        artifact_writer=artifact_writer,
        provenance_label=provenance_label,
        provenance_note=provenance_note,
    )
