"""
tests/test_run_repository.py

RunRepository の run 初期化・命名規則検証・ステータス取得を検証する。
"""

import pytest
from pathlib import Path

from apsf.storage.run_repository import RunRepository, STANDARD_FILES


@pytest.fixture
def template_dir(tmp_path: Path) -> Path:
    """最小限のテンプレートディレクトリを作成して返す"""
    template = tmp_path / "_template"
    template.mkdir()
    for f in ["goal.md", "plan.md", "model-assignment.md"]:
        (template / f).write_text(f"# {f}\n", encoding="utf-8")
    return template


@pytest.fixture
def runs_dir(tmp_path: Path) -> Path:
    return tmp_path / "runs"


@pytest.fixture
def repo(runs_dir: Path, template_dir: Path) -> RunRepository:
    return RunRepository(runs_dir=runs_dir, template_dir=template_dir)


# --- 命名規則のテスト ---

@pytest.mark.parametrize("name,expected", [
    ("2026-03-15_sochi-blocks_sns-post-template", True),
    ("2026-03-15_dx_invoice-flow", True),
    ("2026-01-01_a_b", True),
    ("sochi-blocks_sns-post-template", False),   # 日付なし
    ("2026-03-15_sochi-blocks", False),           # topic なし
    ("2026-03-15_SoChi-Blocks_Test", False),      # 大文字含む
    ("", False),
])
def test_validate_run_name(repo: RunRepository, name: str, expected: bool) -> None:
    assert repo.validate_run_name(name) == expected


# --- run 初期化のテスト ---

def test_init_run_creates_directory(repo: RunRepository) -> None:
    """init_run でディレクトリが作成されること"""
    run_dir = repo.init_run("2026-03-15_sochi-blocks_test-run")
    assert run_dir.exists()
    assert run_dir.is_dir()


def test_init_run_copies_template_files(repo: RunRepository) -> None:
    """_template のファイルがコピーされること"""
    repo.init_run("2026-03-15_sochi-blocks_test-run")
    assert (repo.get_run_dir("2026-03-15_sochi-blocks_test-run") / "goal.md").exists()


def test_init_run_invalid_name_raises(repo: RunRepository) -> None:
    """不正な run 名は ValueError を送出すること"""
    with pytest.raises(ValueError, match="Invalid run name"):
        repo.init_run("invalid_name")


def test_init_run_duplicate_raises(repo: RunRepository) -> None:
    """重複する run 名は FileExistsError を送出すること"""
    repo.init_run("2026-03-15_sochi-blocks_test-run")
    with pytest.raises(FileExistsError):
        repo.init_run("2026-03-15_sochi-blocks_test-run")


def test_init_run_force_overwrites(repo: RunRepository) -> None:
    """force=True の場合は上書きできること"""
    repo.init_run("2026-03-15_sochi-blocks_test-run")
    run_dir = repo.init_run("2026-03-15_sochi-blocks_test-run", force=True)
    assert run_dir.exists()


# --- ステータス取得のテスト ---

def test_run_exists(repo: RunRepository) -> None:
    repo.init_run("2026-03-15_sochi-blocks_test-run")
    assert repo.run_exists("2026-03-15_sochi-blocks_test-run") is True
    assert repo.run_exists("nonexistent") is False


def test_is_completed_false_without_result(repo: RunRepository) -> None:
    """result.md がなければ未完了とみなすこと"""
    repo.init_run("2026-03-15_sochi-blocks_test-run")
    assert repo.is_completed("2026-03-15_sochi-blocks_test-run") is False


def test_list_runs_excludes_template(repo: RunRepository, template_dir: Path) -> None:
    """_template は list_runs に含まれないこと"""
    repo.init_run("2026-03-15_sochi-blocks_first")
    repo.init_run("2026-03-15_sochi-blocks_second")
    runs = repo.list_runs()
    assert "_template" not in runs
    assert "2026-03-15_sochi-blocks_first" in runs
    assert "2026-03-15_sochi-blocks_second" in runs


def test_format_run_name(repo: RunRepository) -> None:
    name = repo.format_run_name("2026-03-15", "sochi-blocks", "sns-post-template")
    assert name == "2026-03-15_sochi-blocks_sns-post-template"
