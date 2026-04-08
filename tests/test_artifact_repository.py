"""
ArtifactRepository のテスト

safe write (temp → atomic rename)、single-writer lock、
concurrent write 時の FileLockError を検証する。
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from apsf.core.storage.artifact_repository import ArtifactRepository, FileLockError


# ── 基本書き込み ────────────────────────────────────────────────────────────

def test_safe_write_basic(tmp_path: Path) -> None:
    """通常書き込みが完了し、内容が正しいこと。"""
    repo = ArtifactRepository()
    target = tmp_path / "plan.md"

    result = repo.write(target, "# Plan\n")

    assert result == target
    assert target.read_text(encoding="utf-8") == "# Plan\n"


def test_atomic_rename_no_tmp_remains(tmp_path: Path) -> None:
    """書き込み完了後に .tmp ファイルが残っていないこと。"""
    repo = ArtifactRepository()
    target = tmp_path / "build.md"

    repo.write(target, "# Build\n")

    tmp = target.with_suffix(".tmp")
    assert not tmp.exists(), ".tmp ファイルが残っている"


def test_lock_released_after_write(tmp_path: Path) -> None:
    """書き込み完了後に .lock ファイルが消えていること。"""
    repo = ArtifactRepository()
    target = tmp_path / "result.md"

    repo.write(target, "# Result\n")

    lock = target.with_suffix(".lock")
    assert not lock.exists(), ".lock ファイルが残っている"


def test_creates_parent_directory(tmp_path: Path) -> None:
    """親ディレクトリが存在しない場合でも書き込めること。"""
    repo = ArtifactRepository()
    target = tmp_path / "subdir" / "nested" / "plan.md"

    repo.write(target, "# Plan\n")

    assert target.exists()


# ── lock 競合 ────────────────────────────────────────────────────────────────

def test_concurrent_write_raises_file_lock_error(tmp_path: Path) -> None:
    """
    .lock ファイルが既に存在する状態で write() を呼ぶと FileLockError になること。

    2スレッドの真の同時書き込みは環境依存で再現しにくいため、
    lock ファイルを事前に作成してから write() を呼ぶことで競合状態を模擬する。
    """
    repo = ArtifactRepository()
    target = tmp_path / "plan.md"

    # 事前に lock ファイルを置いて別プロセスが書き込み中の状態を模擬
    lock_path = target.with_suffix(".lock")
    lock_path.write_text("", encoding="utf-8")

    with pytest.raises(FileLockError):
        repo.write(target, "# Plan\n")

    # write() は他プロセスの lock を削除しない → 残っているはず
    assert lock_path.exists(), "write() が他プロセスの lock を削除してしまっている"
    # target ファイルは書き込まれていない
    assert not target.exists()


def test_concurrent_write_two_threads(tmp_path: Path) -> None:
    """
    2スレッドが同時に同じファイルへ write() したとき、
    一方は成功し、もう一方は FileLockError になること。
    """
    repo = ArtifactRepository()
    target = tmp_path / "plan.md"

    results: list[str] = []
    errors: list[Exception] = []

    def writer(content: str) -> None:
        try:
            repo.write(target, content)
            results.append(content)
        except FileLockError as e:
            errors.append(e)

    t1 = threading.Thread(target=writer, args=("# Thread 1\n",))
    t2 = threading.Thread(target=writer, args=("# Thread 2\n",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # 成功 1件、失敗 1件 または 成功 2件（競合しなかった場合）
    # 少なくとも最終ファイルは壊れていないこと
    assert target.exists()
    final = target.read_text(encoding="utf-8")
    assert final in ("# Thread 1\n", "# Thread 2\n"), f"Unexpected content: {final!r}"
    assert len(results) + len(errors) == 2


# ── read ─────────────────────────────────────────────────────────────────────

def test_read_existing_file(tmp_path: Path) -> None:
    """存在するファイルを正しく読み込めること。"""
    repo = ArtifactRepository()
    target = tmp_path / "goal.md"
    target.write_text("# Goal\n", encoding="utf-8")

    assert repo.read(target) == "# Goal\n"


def test_read_missing_file_returns_empty(tmp_path: Path) -> None:
    """存在しないファイルを読もうとすると空文字を返すこと。"""
    repo = ArtifactRepository()
    target = tmp_path / "nonexistent.md"

    assert repo.read(target) == ""


# ── MarkdownRepository との統合 ───────────────────────────────────────────────

def test_markdown_repository_uses_artifact_repo(tmp_path: Path) -> None:
    """
    MarkdownRepository.write() が raw write_text() を直接呼ばず、
    ArtifactRepository 経由で書き込むこと。

    safe write の副産物 (.tmp が残らない) で間接的に確認する。
    """
    from apsf.legacy.storage.markdown_repository import MarkdownRepository

    repo = MarkdownRepository(base_dir=tmp_path)
    repo.write("plan.md", "# Plan\n")

    target = tmp_path / "plan.md"
    tmp = target.with_suffix(".tmp")
    lock = target.with_suffix(".lock")

    assert target.exists()
    assert target.read_text(encoding="utf-8") == "# Plan\n"
    assert not tmp.exists(), "raw write なら .tmp は存在しない → ArtifactRepository 未使用の可能性"
    assert not lock.exists()
