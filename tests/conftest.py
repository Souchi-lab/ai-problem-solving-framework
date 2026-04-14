from __future__ import annotations

import shutil
from pathlib import Path

import pytest


_TMP_COUNTER = 0


@pytest.fixture
def tmp_path() -> Path:
    """Provide a writable temp dir without relying on pytest's basetemp factory.

    The sandboxed Windows environment used in APSF build verification can reject
    pytest's default tmp_path/basetemp creation flow with PermissionError even
    when normal file I/O works. A direct tempfile-backed fixture keeps the test
    contract intact for tmp_path-based tests while avoiding that environment bug.
    """

    global _TMP_COUNTER

    root = Path.cwd() / ".codex-verification" / "pytest-fixtures"
    root.mkdir(parents=True, exist_ok=True)
    _TMP_COUNTER += 1
    path = root / f"apsf-{_TMP_COUNTER:04d}"
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
