from __future__ import annotations

from pathlib import Path

from apsf.core.storage.text_artifact_codec import (
    normalize_text_artifact_to_utf8,
    read_text_artifact,
)


def test_read_text_artifact_reads_cp932_legacy_file(tmp_path: Path) -> None:
    path = tmp_path / "auto_loop.log"
    path.write_bytes("自動ループ継続\n".encode("cp932"))

    assert read_text_artifact(path) == "自動ループ継続\n"


def test_normalize_text_artifact_to_utf8_rewrites_legacy_file(tmp_path: Path) -> None:
    path = tmp_path / "auto_loop.log"
    original = "自動ループ継続\n"
    path.write_bytes(original.encode("cp932"))

    changed = normalize_text_artifact_to_utf8(path)

    assert changed is True
    assert path.read_text(encoding="utf-8") == original
