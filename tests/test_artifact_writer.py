from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from apsf.core.artifact_writer import ArtifactWriter


def test_artifact_writer_writes_artifact_and_updates_manifest(tmp_path: Path) -> None:
    run_dir = tmp_path / "test-run"
    run_dir.mkdir()
    target_path = run_dir / "build.md"

    result = ArtifactWriter().write(
        path=target_path,
        content="# Build\n\nContent.\n",
        writing_role="Builder",
        run_dir=run_dir,
    )

    assert result.path == target_path
    assert result.manifest_synced is True
    assert target_path.read_text(encoding="utf-8") == "# Build\n\nContent.\n"

    manifest = json.loads((run_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert manifest["entries"]["build.md"]["written_by"] == "Builder"
    assert manifest["entries"]["build.md"]["revision"] == 1


def test_artifact_writer_propagates_manifest_update_failure(tmp_path: Path) -> None:
    run_dir = tmp_path / "test-run"
    run_dir.mkdir()
    target_path = run_dir / "build.md"

    with patch(
        "apsf.core.manifest.manifest_repository.ManifestRepository.update_entry",
        side_effect=RuntimeError("manifest update failed"),
    ):
        with pytest.raises(RuntimeError, match="manifest update failed"):
            ArtifactWriter().write(
                path=target_path,
                content="# Build\n\nContent.\n",
                writing_role="Builder",
                run_dir=run_dir,
            )
