"""
SnapshotCaptureService のテスト

カバー範囲:
  - success path: metadata / payload が正しいレイアウトで保存される
  - payload path: canonical POSIX form で保存される
  - path validation: `.`/`..` エスケープ、絶対パス、run_dir 外を拒否
  - directory 指定を拒否
  - file not found を拒否
  - non-UTF-8 / binary content を拒否
  - preflight: 最初のファイルが valid でも後続が invalid ならすべて保存しない
  - round-trip: capture → restore で元の content が返ること
  - RestoreService の encoding フィールド check（run-065 deferred 実装）
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsf.core.restore.snapshot_capture_service import (
    CaptureResult,
    SnapshotCaptureError,
    SnapshotCaptureService,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _metadata(run_dir: Path, snapshot_id: str) -> dict:
    return json.loads(
        (run_dir / "recovery" / "snapshots" / snapshot_id / "metadata.json")
        .read_text(encoding="utf-8")
    )


def _payload(run_dir: Path, snapshot_id: str, rel_path: str) -> str:
    return (
        run_dir / "recovery" / "snapshots" / snapshot_id / "payload" / rel_path
    ).read_text(encoding="utf-8")


# ── success path ──────────────────────────────────────────────────────────────

def test_capture_single_file_creates_metadata_and_payload(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write(run_dir / "plan.md", "# Plan\n")

    result = SnapshotCaptureService().capture(run_dir, "snap-001", ["plan.md"])

    assert result.snapshot_id == "snap-001"
    assert result.captured_paths == ["plan.md"]
    assert result.encoding == "utf-8"

    meta = _metadata(run_dir, "snap-001")
    assert meta["snapshot_id"] == "snap-001"
    assert meta["file_count"] == 1
    assert meta["target_paths"] == ["plan.md"]
    assert meta["encoding"] == "utf-8"
    assert len(meta["content_hashes"]) == 1

    assert _payload(run_dir, "snap-001", "plan.md") == "# Plan\n"


def test_capture_multiple_files(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write(run_dir / "plan.md", "# Plan\n")
    _write(run_dir / "build.md", "# Build\n")

    result = SnapshotCaptureService().capture(
        run_dir, "snap-002", ["plan.md", "build.md"]
    )

    assert sorted(result.captured_paths) == ["build.md", "plan.md"]
    meta = _metadata(run_dir, "snap-002")
    assert meta["file_count"] == 2


def test_capture_nested_file_canonical_posix_path(tmp_path: Path) -> None:
    """ネストされたファイルが POSIX separator で保存されること。"""
    run_dir = tmp_path / "my-run"
    _write(run_dir / "src" / "app.py", "# app\n")

    result = SnapshotCaptureService().capture(run_dir, "snap-003", ["src/app.py"])

    assert result.captured_paths == ["src/app.py"]
    assert _payload(run_dir, "snap-003", "src/app.py") == "# app\n"


def test_capture_source_phase_recorded_in_metadata(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write(run_dir / "plan.md", "# Plan\n")

    SnapshotCaptureService().capture(
        run_dir, "snap-004", ["plan.md"], source_phase="BUILD_NEEDED"
    )

    meta = _metadata(run_dir, "snap-004")
    assert meta["source_phase"] == "BUILD_NEEDED"


def test_capture_content_hash_matches_sha256(tmp_path: Path) -> None:
    import hashlib

    run_dir = tmp_path / "my-run"
    content = "# Plan\n"
    _write(run_dir / "plan.md", content)

    SnapshotCaptureService().capture(run_dir, "snap-005", ["plan.md"])

    meta = _metadata(run_dir, "snap-005")
    expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert meta["content_hashes"][0] == expected


# ── path normalization ────────────────────────────────────────────────────────

def test_capture_normalizes_dotslash_prefix(tmp_path: Path) -> None:
    """./plan.md → canonical: plan.md"""
    run_dir = tmp_path / "my-run"
    _write(run_dir / "plan.md", "# Plan\n")

    result = SnapshotCaptureService().capture(run_dir, "snap-norm", ["./plan.md"])

    assert result.captured_paths == ["plan.md"]


# ── path validation errors ────────────────────────────────────────────────────

def test_capture_rejects_absolute_path(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    run_dir.mkdir()

    with pytest.raises(SnapshotCaptureError, match="absolute path is not allowed"):
        SnapshotCaptureService().capture(
            run_dir, "snap-x", [str(run_dir / "plan.md")]
        )


def test_capture_rejects_dotdot_escape(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    run_dir.mkdir()
    _write(tmp_path / "outside.txt", "secret")

    with pytest.raises(SnapshotCaptureError, match="path escapes run directory"):
        SnapshotCaptureService().capture(run_dir, "snap-x", ["../outside.txt"])


def test_capture_rejects_directory(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    (run_dir / "src").mkdir(parents=True)

    with pytest.raises(SnapshotCaptureError, match="directory is not supported"):
        SnapshotCaptureService().capture(run_dir, "snap-x", ["src"])


def test_capture_rejects_nonexistent_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    run_dir.mkdir()

    with pytest.raises(SnapshotCaptureError, match="file not found"):
        SnapshotCaptureService().capture(run_dir, "snap-x", ["missing.md"])


def test_capture_rejects_non_utf8_content(tmp_path: Path) -> None:
    """non-UTF-8 バイト列を含むファイルは capture を拒否する。"""
    run_dir = tmp_path / "my-run"
    run_dir.mkdir()
    binary_file = run_dir / "data.bin"
    binary_file.write_bytes(b"\xff\xfe binary content")

    with pytest.raises(SnapshotCaptureError, match="non-UTF-8 or binary"):
        SnapshotCaptureService().capture(run_dir, "snap-x", ["data.bin"])


# ── preflight atomicity ───────────────────────────────────────────────────────

def test_capture_preflight_rejects_all_when_second_file_invalid(tmp_path: Path) -> None:
    """2 ファイル目が invalid の場合、1 ファイル目も保存されないこと。"""
    run_dir = tmp_path / "my-run"
    _write(run_dir / "plan.md", "# Plan\n")
    # build.md は存在しない

    with pytest.raises(SnapshotCaptureError, match="file not found"):
        SnapshotCaptureService().capture(
            run_dir, "snap-partial", ["plan.md", "build.md"]
        )

    # payload が保存されていないこと
    snap_dir = run_dir / "recovery" / "snapshots" / "snap-partial"
    assert not (snap_dir / "payload" / "plan.md").exists()


# ── round-trip: capture → restore ────────────────────────────────────────────

def test_capture_then_restore_round_trip(tmp_path: Path) -> None:
    """capture で保存した snapshot を restore で復元すると元の content が得られること。"""
    from apsf.core.restore.restore_service import RestoreService

    run_dir = tmp_path / "my-run"
    original = "# Plan\n\nOriginal content.\n"
    _write(run_dir / "plan.md", original)

    SnapshotCaptureService().capture(run_dir, "snap-rt", ["plan.md"])

    # plan.md を上書き
    (run_dir / "plan.md").write_text("# Plan\n\nModified.\n", encoding="utf-8")

    # restore
    RestoreService().apply_snapshot(run_dir, "snap-rt", "round-trip test")

    assert (run_dir / "plan.md").read_text(encoding="utf-8") == original


# ── RestoreService encoding check（run-065 deferred 実装）────────────────────

def test_restore_rejects_unsupported_encoding_in_metadata(tmp_path: Path) -> None:
    """metadata の encoding が utf-8 以外の場合は RestoreError になること。"""
    from apsf.core.restore.restore_service import RestoreError, RestoreService

    run_dir = tmp_path / "my-run"
    snap_dir = run_dir / "recovery" / "snapshots" / "snap-enc"
    (snap_dir / "payload").mkdir(parents=True)

    metadata = {
        "snapshot_id": "snap-enc",
        "source_phase": "",
        "captured_at": "2026-04-02T00:00:00+00:00",
        "file_count": 1,
        "target_paths": ["plan.md"],
        "content_hashes": ["abc"],
        "encoding": "latin-1",  # unsupported
    }
    (snap_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(RestoreError, match="unsupported snapshot encoding"):
        RestoreService().apply_snapshot(run_dir, "snap-enc", "test reason")


def test_restore_treats_absent_encoding_as_utf8(tmp_path: Path) -> None:
    """metadata に encoding フィールドがない場合は utf-8 fallback で動作すること。"""
    from apsf.core.restore.restore_service import RestoreService

    run_dir = tmp_path / "my-run"
    snap_dir = run_dir / "recovery" / "snapshots" / "snap-noenc"
    (snap_dir / "payload").mkdir(parents=True)

    metadata = {
        "snapshot_id": "snap-noenc",
        "source_phase": "",
        "captured_at": "2026-04-02T00:00:00+00:00",
        "file_count": 1,
        "target_paths": ["plan.md"],
        "content_hashes": ["abc"],
        # encoding フィールドなし → utf-8 fallback
    }
    (snap_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (snap_dir / "payload" / "plan.md").write_text("# Plan\n", encoding="utf-8")

    result = RestoreService().apply_snapshot(run_dir, "snap-noenc", "test reason")
    assert result.snapshot_id == "snap-noenc"
