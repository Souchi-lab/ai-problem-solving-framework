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
    ("2026-03-15_sochi-blocks_sns-post-template", True),   # 連番なし形式（後方互換）
    ("2026-03-15_dx_invoice-flow", True),
    ("2026-01-01_a_b", True),
    ("2026-03-19-006_apsf_run-repository-child-run-design", True),  # 連番付き形式
    ("2026-03-19-1_apsf_topic", True),                              # 連番1桁も有効
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


# --- child run 命名規則のテスト ---

class TestValidateChildRunName:
    @pytest.mark.parametrize("name,expected", [
        ("016c1_sochi-blocks_x-thread-content", True),
        ("001c1_apsf_topic", True),
        ("999c99_dx_invoice-flow", True),
        ("016c1_sochi-blocks", False),       # topic なし
        ("16c1_sochi-blocks_topic", False),  # 親番号 2 桁
        ("016C1_sochi-blocks_topic", False), # 大文字
        ("016c1_SoChi_topic", False),        # case-key に大文字
        ("2026-03-15_sochi-blocks_topic", False),  # top-level 形式
        ("", False),
    ])
    def test_validate_child_run_name(
        self, repo: RunRepository, name: str, expected: bool
    ) -> None:
        assert repo.validate_child_run_name(name) == expected


# --- format_child_run_name のテスト ---

class TestFormatChildRunName:
    def test_normal(self, repo: RunRepository) -> None:
        name = repo.format_child_run_name("016", 1, "sochi-blocks", "x-thread-content")
        assert name == "016c1_sochi-blocks_x-thread-content"

    def test_caller_controls_padding(self, repo: RunRepository) -> None:
        """桁数ゼロ埋めは呼び出し側の責務: "16" をそのまま使う"""
        name = repo.format_child_run_name("16", 1, "sochi-blocks", "topic")
        assert name == "16c1_sochi-blocks_topic"


# --- child run path 解決のテスト ---

class TestChildRunPathResolution:
    def test_get_child_run_dir(self, repo: RunRepository, runs_dir: Path) -> None:
        path = repo.get_child_run_dir(_PARENT, _CHILD)
        assert path == runs_dir / _PARENT / _CHILD

    def test_get_child_file_path(self, repo: RunRepository, runs_dir: Path) -> None:
        path = repo.get_child_file_path(_PARENT, _CHILD, "goal.md")
        assert path == runs_dir / _PARENT / _CHILD / "goal.md"


# --- init_child_run のテスト ---

_PARENT = "2026-03-19_sochi-blocks_parent"
_CHILD = "016c1_sochi-blocks_child"


class TestInitChildRun:
    def _make_parent(self, repo: RunRepository) -> None:
        repo.init_run(_PARENT)

    def test_creates_directory(self, repo: RunRepository) -> None:
        self._make_parent(repo)
        child_dir = repo.init_child_run(_PARENT, _CHILD)
        assert child_dir.is_dir()

    def test_copies_template_files(self, repo: RunRepository) -> None:
        self._make_parent(repo)
        repo.init_child_run(_PARENT, _CHILD)
        assert (repo.get_child_run_dir(_PARENT, _CHILD) / "goal.md").exists()

    def test_v1_invalid_parent_name(self, repo: RunRepository) -> None:
        with pytest.raises(ValueError, match="Invalid parent run name"):
            repo.init_child_run("bad-parent", _CHILD)

    def test_v2_parent_not_found(self, repo: RunRepository) -> None:
        with pytest.raises(FileNotFoundError, match="Parent run directory not found"):
            repo.init_child_run(_PARENT, _CHILD)

    def test_v3_invalid_child_name(self, repo: RunRepository) -> None:
        self._make_parent(repo)
        with pytest.raises(ValueError, match="Invalid child run name"):
            repo.init_child_run(_PARENT, "bad_child_name")

    def test_v4_duplicate_raises(self, repo: RunRepository) -> None:
        self._make_parent(repo)
        repo.init_child_run(_PARENT, _CHILD)
        with pytest.raises(FileExistsError):
            repo.init_child_run(_PARENT, _CHILD)

    def test_v4_force_overwrites(self, repo: RunRepository) -> None:
        self._make_parent(repo)
        repo.init_child_run(_PARENT, _CHILD)
        child_dir = repo.init_child_run(_PARENT, _CHILD, force=True)
        assert child_dir.is_dir()


# --- list_child_runs のテスト ---

class TestListChildRuns:
    def test_returns_child_names(self, repo: RunRepository) -> None:
        repo.init_run(_PARENT)
        repo.init_child_run(_PARENT, _CHILD)
        repo.init_child_run(_PARENT, "016c2_sochi-blocks_second")
        children = repo.list_child_runs(_PARENT)
        assert _CHILD in children
        assert "016c2_sochi-blocks_second" in children
        assert len(children) == 2

    def test_parent_not_found_returns_empty(self, repo: RunRepository) -> None:
        result = repo.list_child_runs("nonexistent-parent")
        assert result == []

    def test_excludes_non_child_subdirs(self, repo: RunRepository, runs_dir: Path) -> None:
        repo.init_run(_PARENT)
        # validate_child_run_name が False になるサブディレクトリ
        (runs_dir / _PARENT / "not-a-child").mkdir()
        children = repo.list_child_runs(_PARENT)
        assert "not-a-child" not in children


# --- list_all_runs のテスト ---

class TestListAllRuns:
    def test_top_level_only(self, repo: RunRepository) -> None:
        repo.init_run("2026-03-19_apsf_first")
        result = repo.list_all_runs()
        assert result == ["2026-03-19_apsf_first"]

    def test_includes_child_runs(self, repo: RunRepository) -> None:
        repo.init_run(_PARENT)
        repo.init_child_run(_PARENT, _CHILD)
        result = repo.list_all_runs()
        assert _PARENT in result
        assert f"{_PARENT}/{_CHILD}" in result

    def test_excludes_template(self, repo: RunRepository) -> None:
        repo.init_run("2026-03-19_apsf_first")
        result = repo.list_all_runs()
        assert not any("_template" in r for r in result)

    def test_excludes_non_child_subdirs(self, repo: RunRepository, runs_dir: Path) -> None:
        repo.init_run(_PARENT)
        (runs_dir / _PARENT / "not-a-child").mkdir()
        result = repo.list_all_runs()
        assert f"{_PARENT}/not-a-child" not in result


# --- child run status のテスト ---

class TestChildRunStatus:
    def test_child_run_exists_true(self, repo: RunRepository) -> None:
        repo.init_run(_PARENT)
        repo.init_child_run(_PARENT, _CHILD)
        assert repo.child_run_exists(_PARENT, _CHILD) is True

    def test_child_run_exists_false(self, repo: RunRepository) -> None:
        repo.init_run(_PARENT)
        assert repo.child_run_exists(_PARENT, _CHILD) is False

    def test_get_child_run_status_keys(self, repo: RunRepository) -> None:
        from apsf.storage.run_repository import STANDARD_FILES
        repo.init_run(_PARENT)
        repo.init_child_run(_PARENT, _CHILD)
        status = repo.get_child_run_status(_PARENT, _CHILD)
        assert set(status.keys()) == set(STANDARD_FILES)

    def test_get_child_run_status_values(self, repo: RunRepository) -> None:
        repo.init_run(_PARENT)
        repo.init_child_run(_PARENT, _CHILD)
        status = repo.get_child_run_status(_PARENT, _CHILD)
        # テンプレートには goal.md が含まれる
        assert isinstance(status["goal.md"], bool)

    def test_is_child_completed_false(self, repo: RunRepository) -> None:
        repo.init_run(_PARENT)
        repo.init_child_run(_PARENT, _CHILD)
        assert repo.is_child_completed(_PARENT, _CHILD) is False

    def test_is_child_completed_true(self, repo: RunRepository) -> None:
        repo.init_run(_PARENT)
        repo.init_child_run(_PARENT, _CHILD)
        # result.md を手動作成して完了状態にする
        (repo.get_child_run_dir(_PARENT, _CHILD) / "result.md").write_text("# Result\n")
        assert repo.is_child_completed(_PARENT, _CHILD) is True


# --- child run 名による自動解決のテスト（SC-1〜SC-4）---

class TestResolveChildRunByName:
    """
    _resolve_run_root が child run 名だけで parent/child パスを解決できることを確認する。
    これにより get_run_dir / get_file_path / run_exists が child run に対して動作する。
    """

    @pytest.fixture
    def fw_parent_with_child(self, runs_dir: Path) -> tuple[str, str]:
        """fw-improvement 配下に parent/child 構造を作成して (parent_name, child_name) を返す"""
        parent = "2026-03-19-020_apsf_parent-run"
        child = "020c1_apsf_child-run"
        (runs_dir / "fw-improvement" / parent / child).mkdir(parents=True)
        (runs_dir / "fw-improvement" / parent / child / "goal.md").write_text(
            "# Goal\n", encoding="utf-8"
        )
        return parent, child

    def test_get_run_dir_resolves_child(
        self, repo: RunRepository, runs_dir: Path, fw_parent_with_child: tuple[str, str]
    ) -> None:
        """child run 名だけで runs/fw-improvement/<parent>/<child> に解決できること"""
        parent, child = fw_parent_with_child
        path = repo.get_run_dir(child)
        assert path == runs_dir / "fw-improvement" / parent / child

    def test_run_exists_child(
        self, repo: RunRepository, fw_parent_with_child: tuple[str, str]
    ) -> None:
        """child run 名だけで run_exists が True を返すこと"""
        _, child = fw_parent_with_child
        assert repo.run_exists(child) is True

    def test_get_file_path_child(
        self, repo: RunRepository, runs_dir: Path, fw_parent_with_child: tuple[str, str]
    ) -> None:
        """child run 名だけで get_file_path が正しいパスを返すこと"""
        parent, child = fw_parent_with_child
        path = repo.get_file_path(child, "goal.md")
        assert path == runs_dir / "fw-improvement" / parent / child / "goal.md"

    def test_child_not_found_returns_legacy_path(
        self, repo: RunRepository, runs_dir: Path
    ) -> None:
        """存在しない child run 名は legacy パス（runs/<child_name>）を返すこと"""
        child = "099c1_apsf_not-found"
        path = repo.get_run_dir(child)
        assert path == runs_dir / child

    def test_top_level_run_unaffected(
        self, repo: RunRepository, runs_dir: Path, fw_parent_with_child: tuple[str, str]
    ) -> None:
        """child 解決ロジック追加後も top-level run の fallback が壊れていないこと"""
        parent, _ = fw_parent_with_child
        path = repo.get_run_dir(parent)
        assert path == runs_dir / "fw-improvement" / parent

    def test_taxonomy_explicit_unaffected(
        self, repo: RunRepository, runs_dir: Path
    ) -> None:
        """taxonomy 明示時は child スキャンを行わず指定 taxonomy のパスを返すこと"""
        child = "020c1_apsf_child-run"
        path = repo.get_run_dir(child, taxonomy="fw-improvement")
        assert path == runs_dir / "fw-improvement" / child


# --- taxonomy-aware API のテスト ---

class TestTaxonomy:
    """taxonomy-aware API のテスト（fallback・明示解決・同名共存）"""

    @pytest.fixture
    def fw_run(self, runs_dir: Path) -> str:
        """fw-improvement 配下に run を作成して run 名を返す"""
        name = "2026-03-19_apsf_fw-run"
        (runs_dir / "fw-improvement" / name).mkdir(parents=True)
        return name

    @pytest.fixture
    def work_run(self, runs_dir: Path) -> str:
        """work 配下に run を作成して run 名を返す"""
        name = "2026-03-19_sochi-blocks_work-run"
        (runs_dir / "work" / name).mkdir(parents=True)
        return name

    @pytest.fixture
    def legacy_run(self, repo: RunRepository) -> str:
        """runs/ 直下に run を作成して run 名を返す"""
        name = "2026-03-19_sochi-blocks_legacy-run"
        repo.init_run(name)
        return name

    # --- _resolve_run_root fallback ---

    def test_fallback_fw_improvement(
        self, repo: RunRepository, fw_run: str, runs_dir: Path
    ) -> None:
        """fw-improvement 配下にある run は fallback で解決される"""
        path = repo.get_run_dir(fw_run)
        assert path == runs_dir / "fw-improvement" / fw_run

    def test_fallback_work(
        self, repo: RunRepository, work_run: str, runs_dir: Path
    ) -> None:
        """work 配下にある run は fallback で解決される（fw-improvement にない場合）"""
        path = repo.get_run_dir(work_run)
        assert path == runs_dir / "work" / work_run

    def test_fallback_legacy(
        self, repo: RunRepository, legacy_run: str, runs_dir: Path
    ) -> None:
        """どの taxonomy にもない run は legacy パスで解決される"""
        path = repo.get_run_dir(legacy_run)
        assert path == runs_dir / legacy_run

    def test_fallback_fw_wins_over_legacy(
        self, repo: RunRepository, runs_dir: Path
    ) -> None:
        """同名 run が fw-improvement と legacy に存在する場合、fw-improvement が優先される"""
        name = "2026-03-19_apsf_same-name"
        (runs_dir / "fw-improvement" / name).mkdir(parents=True)
        (runs_dir / name).mkdir(parents=True)
        path = repo.get_run_dir(name)
        assert path == runs_dir / "fw-improvement" / name

    def test_fallback_not_found_returns_legacy_path(
        self, repo: RunRepository, runs_dir: Path
    ) -> None:
        """どこにも存在しない run は legacy パス（runs/<run_name>）を返す"""
        name = "2026-03-19_apsf_not-found"
        path = repo.get_run_dir(name)
        assert path == runs_dir / name

    # --- 明示 taxonomy 解決 ---

    def test_explicit_taxonomy_fw(
        self, repo: RunRepository, fw_run: str, runs_dir: Path
    ) -> None:
        path = repo.get_run_dir(fw_run, taxonomy="fw-improvement")
        assert path == runs_dir / "fw-improvement" / fw_run

    def test_explicit_taxonomy_ignores_legacy(
        self, repo: RunRepository, runs_dir: Path
    ) -> None:
        """taxonomy 明示時は legacy にあっても指定 taxonomy のパスを返す"""
        name = "2026-03-19_apsf_only-legacy"
        (runs_dir / name).mkdir(parents=True)
        path = repo.get_run_dir(name, taxonomy="fw-improvement")
        assert path == runs_dir / "fw-improvement" / name

    def test_run_exists_explicit_taxonomy(
        self, repo: RunRepository, fw_run: str
    ) -> None:
        assert repo.run_exists(fw_run, taxonomy="fw-improvement") is True
        assert repo.run_exists(fw_run, taxonomy="work") is False

    def test_init_run_in_taxonomy(
        self, repo: RunRepository, runs_dir: Path
    ) -> None:
        name = "2026-03-19_apsf_init-in-fw"
        run_dir = repo.init_run(name, taxonomy="fw-improvement")
        assert run_dir == runs_dir / "fw-improvement" / name
        assert (run_dir / "goal.md").exists()

    # --- list_runs ---

    def test_list_runs_taxonomy_fw(
        self, repo: RunRepository, fw_run: str, work_run: str, legacy_run: str
    ) -> None:
        runs = repo.list_runs(taxonomy="fw-improvement")
        assert fw_run in runs
        assert work_run not in runs
        assert legacy_run not in runs

    def test_list_runs_all_cross_taxonomy(
        self, repo: RunRepository, fw_run: str, work_run: str, legacy_run: str
    ) -> None:
        runs = repo.list_runs()
        assert fw_run in runs
        assert work_run in runs
        assert legacy_run in runs

    def test_list_runs_dedup_taxonomy_wins(
        self, repo: RunRepository, runs_dir: Path
    ) -> None:
        """同名 run は taxonomy 配下のもののみ返す（重複排除）"""
        name = "2026-03-19_apsf_same-name"
        (runs_dir / "fw-improvement" / name).mkdir(parents=True)
        (runs_dir / name).mkdir(parents=True)
        runs = repo.list_runs()
        assert runs.count(name) == 1

    def test_list_runs_excludes_taxonomy_dir_names(
        self, repo: RunRepository, fw_run: str
    ) -> None:
        """fw-improvement / work ディレクトリ名自体は list_runs に含まれない"""
        runs = repo.list_runs()
        assert "fw-improvement" not in runs
        assert "work" not in runs

    # --- list_all_runs ---

    def test_list_all_runs_taxonomy_fw(
        self, repo: RunRepository, fw_run: str, work_run: str
    ) -> None:
        result = repo.list_all_runs(taxonomy="fw-improvement")
        assert fw_run in result
        assert work_run not in result

    def test_list_all_runs_cross_taxonomy(
        self, repo: RunRepository, fw_run: str, work_run: str, legacy_run: str
    ) -> None:
        result = repo.list_all_runs()
        assert fw_run in result
        assert work_run in result
        assert legacy_run in result

    def test_list_all_runs_child_in_taxonomy(
        self, repo: RunRepository, runs_dir: Path
    ) -> None:
        """taxonomy 配下の parent run の child run が 'parent/child' 形式で返ること"""
        parent = "2026-03-19_apsf_parent-in-fw"
        child = "019c1_apsf_child"
        (runs_dir / "fw-improvement" / parent / child).mkdir(parents=True)
        result = repo.list_all_runs()
        assert f"{parent}/{child}" in result

    def test_list_all_runs_excludes_taxonomy_dir_names(
        self, repo: RunRepository, fw_run: str
    ) -> None:
        result = repo.list_all_runs()
        assert "fw-improvement" not in result

    # --- child run in taxonomy ---

    def test_init_child_run_in_taxonomy(
        self, repo: RunRepository, fw_run: str, runs_dir: Path
    ) -> None:
        """taxonomy に存在する parent の child run を作成できること"""
        child = "019c1_apsf_child"
        child_dir = repo.init_child_run(fw_run, child, taxonomy="fw-improvement")
        assert child_dir.is_dir()
        assert child_dir == runs_dir / "fw-improvement" / fw_run / child

    def test_child_run_exists_in_taxonomy(
        self, repo: RunRepository, fw_run: str
    ) -> None:
        child = "019c1_apsf_child"
        repo.init_child_run(fw_run, child, taxonomy="fw-improvement")
        assert repo.child_run_exists(fw_run, child, taxonomy="fw-improvement") is True
        assert repo.child_run_exists(fw_run, child, taxonomy="work") is False

    def test_is_completed_in_taxonomy(
        self, repo: RunRepository, fw_run: str, runs_dir: Path
    ) -> None:
        (runs_dir / "fw-improvement" / fw_run / "result.md").write_text("# Result\n")
        assert repo.is_completed(fw_run, taxonomy="fw-improvement") is True
        assert repo.is_completed(fw_run) is True  # fallback も fw-improvement を見つける
