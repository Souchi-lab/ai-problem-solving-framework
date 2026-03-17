"""
tests/test_markdown_repository.py

MarkdownRepository の read/write/exists/list_files を検証する。
"""

import pytest
from pathlib import Path

from apsf.storage.markdown_repository import MarkdownRepository


@pytest.fixture
def repo(tmp_path: Path) -> MarkdownRepository:
    """一時ディレクトリをベースにした MarkdownRepository を返す"""
    return MarkdownRepository(base_dir=tmp_path)


def test_write_and_read(repo: MarkdownRepository) -> None:
    """書き込んだ内容が読み込めること"""
    repo.write("goal.md", "# Goal\n\nTest goal content")
    content = repo.read("goal.md")
    assert "Test goal content" in content


def test_read_missing_returns_empty(repo: MarkdownRepository) -> None:
    """存在しないファイルを読むと空文字を返すこと"""
    content = repo.read("nonexistent.md")
    assert content == ""


def test_exists_returns_false_for_missing(repo: MarkdownRepository) -> None:
    """存在しないファイルで False を返すこと"""
    assert repo.exists("goal.md") is False


def test_exists_returns_true_after_write(repo: MarkdownRepository) -> None:
    """書き込み後に exists が True を返すこと"""
    repo.write("plan.md", "# Plan")
    assert repo.exists("plan.md") is True


def test_is_empty_for_missing_file(repo: MarkdownRepository) -> None:
    """存在しないファイルは empty とみなすこと"""
    assert repo.is_empty("goal.md") is True


def test_is_empty_for_whitespace_only(repo: MarkdownRepository) -> None:
    """空白のみのファイルは empty とみなすこと"""
    repo.write("goal.md", "   \n  ")
    assert repo.is_empty("goal.md") is True


def test_is_empty_false_for_content(repo: MarkdownRepository) -> None:
    """内容があれば empty でないこと"""
    repo.write("goal.md", "# Goal\n\nContent here")
    assert repo.is_empty("goal.md") is False


def test_list_files(repo: MarkdownRepository) -> None:
    """書き込んだファイルが list_files に含まれること"""
    repo.write("goal.md", "# Goal")
    repo.write("plan.md", "# Plan")
    files = repo.list_files()
    assert "goal.md" in files
    assert "plan.md" in files


def test_write_creates_parent_dirs(tmp_path: Path) -> None:
    """サブディレクトリが存在しない場合でも write できること"""
    repo = MarkdownRepository(base_dir=tmp_path / "deep" / "nested")
    repo.write("test.md", "content")
    assert (tmp_path / "deep" / "nested" / "test.md").exists()
