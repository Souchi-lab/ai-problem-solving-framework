from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .storage.artifact_repository import ArtifactRepository


@dataclass(frozen=True)
class WriteResult:
    path: Path
    manifest_synced: bool


class ArtifactWriter:
    """
    Canonical phase-artifact writer for S1+S2.

    This wrapper is intentionally narrow: it writes the artifact and performs
    manifest sync through ArtifactRepository. Phase transitions remain the
    caller's responsibility.
    """

    def write(
        self,
        *,
        path: Path,
        content: str,
        writing_role: str,
        run_dir: Path,
    ) -> WriteResult:
        ArtifactRepository(writing_role=writing_role, run_dir=run_dir).write(path, content)
        return WriteResult(path=path, manifest_synced=True)
