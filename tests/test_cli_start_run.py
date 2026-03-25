"""
test_cli_start_run.py — `apsf start-run` コマンドのテスト

テスト方針:
- start-run で run が正しく生成される
- template が正しくコピーされる
- --dry-run でファイル生成が行われない
- 出力に run path / file list / next action が含まれる

CliRunner を使って Typer コマンドを直接呼び出す。
ファイルシステム操作は tmp_path で分離する。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from apsf.cli.main import app
from apsf.storage.run_repository import RunRepository
import apsf.config.settings as settings_module

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixture: settings シングルトンを各テスト前後にリセット
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_settings_singleton():
    """get_settings() のシングルトンをリセットして各テストを独立させる。"""
    settings_module._settings_instance = None
    yield
    settings_module._settings_instance = None


# ---------------------------------------------------------------------------
# Helper: テスト用の runs/ と _template/ を tmp_path に作る
# ---------------------------------------------------------------------------

def _setup_env(tmp_path: Path) -> tuple[Path, Path]:
    """
    tmp_path に runs/ と runs/_template/ を作り、
    テンプレートファイルを 3 本置く。
    APSF_ROOT を tmp_path に向けるため、get_settings のベースを一時置換。
    """
    runs_dir = tmp_path / "runs"
    template_dir = runs_dir / "_template"
    template_dir.mkdir(parents=True)

    for fname in ["goal.md", "plan.md", "build.md"]:
        (template_dir / fname).write_text(f"# {fname}\n", encoding="utf-8")

    return runs_dir, template_dir


def _invoke_start_run(tmp_path: Path, args: list[str]) -> "typer.testing.Result":
    """APSF_ROOT を tmp_path に向けて start-run を実行する。"""
    import os
    env = {**os.environ, "APSF_ROOT": str(tmp_path)}
    return runner.invoke(app, ["start-run"] + args, env=env)


# ---------------------------------------------------------------------------
# 正常系: run が生成される
# ---------------------------------------------------------------------------

class TestStartRunCreation:
    def test_creates_run_directory(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(tmp_path, ["2099-01-01_test-case_my-topic"])
        assert result.exit_code == 0, result.output
        run_dir = tmp_path / "runs" / "2099-01-01_test-case_my-topic"
        assert run_dir.exists()

    def test_copies_template_files(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(tmp_path, ["2099-01-01_test-case_my-topic"])
        assert result.exit_code == 0
        run_dir = tmp_path / "runs" / "2099-01-01_test-case_my-topic"
        assert (run_dir / "goal.md").exists()
        assert (run_dir / "plan.md").exists()
        assert (run_dir / "build.md").exists()

    def test_output_contains_run_path(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(tmp_path, ["2099-01-01_test-case_my-topic"])
        assert result.exit_code == 0
        assert "2099-01-01_test-case_my-topic" in result.output

    def test_output_contains_file_list(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(tmp_path, ["2099-01-01_test-case_file-list"])
        assert result.exit_code == 0
        assert "goal.md" in result.output
        assert "plan.md" in result.output

    def test_output_contains_next_action(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(tmp_path, ["2099-01-01_test-case_next-action"])
        assert result.exit_code == 0
        # "next step" か "goal.md" が次アクションとして出力される
        output_lower = result.output.lower()
        assert "goal" in output_lower or "next" in output_lower

    def test_output_mentions_apsf_next(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(tmp_path, ["2099-01-01_test-case_mentions-next"])
        assert result.exit_code == 0
        assert "apsf next" in result.output

    def test_creates_run_directory_in_taxonomy(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(
            tmp_path,
            [
                "2099-01-01_test-case_taxonomy-create",
                "--taxonomy",
                "fw-improvement",
            ],
        )
        assert result.exit_code == 0, result.output
        run_dir = (
            tmp_path
            / "runs"
            / "fw-improvement"
            / "2099-01-01_test-case_taxonomy-create"
        )
        assert run_dir.exists()

    def test_taxonomy_run_copies_template_files(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(
            tmp_path,
            [
                "2099-01-01_test-case_taxonomy-files",
                "--taxonomy",
                "work",
            ],
        )
        assert result.exit_code == 0, result.output
        run_dir = tmp_path / "runs" / "work" / "2099-01-01_test-case_taxonomy-files"
        assert (run_dir / "goal.md").exists()
        assert (run_dir / "plan.md").exists()
        assert (run_dir / "build.md").exists()


# ---------------------------------------------------------------------------
# 日付自動付与
# ---------------------------------------------------------------------------

class TestDateAutoPrepend:
    def test_date_prepended_when_absent(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        # 日付なし → 今日の日付 + slug で作成される
        result = _invoke_start_run(tmp_path, ["test-case_my-feature"])
        assert result.exit_code == 0
        assert "Date auto-prepended" in result.output
        # 作成された run ディレクトリが YYYY-MM-DD-NNN_ で始まる
        runs_dir = tmp_path / "runs"
        created = [d for d in runs_dir.iterdir() if d.is_dir() and d.name != "_template"]
        assert len(created) == 1
        assert re.match(r"^\d{4}-\d{2}-\d{2}-\d{3}_", created[0].name)

    def test_seq_increments_when_same_day_runs_repeat(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result1 = _invoke_start_run(tmp_path, ["test-case_first"])
        result2 = _invoke_start_run(tmp_path, ["test-case_second"])
        assert result1.exit_code == 0, result1.output
        assert result2.exit_code == 0, result2.output

        runs_dir = tmp_path / "runs"
        created = sorted(d.name for d in runs_dir.iterdir() if d.is_dir() and d.name != "_template")
        assert len(created) == 2
        assert re.match(r"^\d{4}-\d{2}-\d{2}-001_test-case_first$", created[0])
        assert re.match(r"^\d{4}-\d{2}-\d{2}-002_test-case_second$", created[1])

    def test_date_not_doubled_when_already_present(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(tmp_path, ["2099-12-31_test-case_already-dated"])
        assert result.exit_code == 0
        assert "Date auto-prepended" not in result.output
        # 2099-12-31 が 1 つだけ存在する
        assert result.output.count("2099-12-31") >= 1


# ---------------------------------------------------------------------------
# --dry-run: 実際には作成しない
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_dry_run_does_not_create_directory(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(
            tmp_path, ["2099-01-01_test-case_dry-test", "--dry-run"]
        )
        assert result.exit_code == 0
        run_dir = tmp_path / "runs" / "2099-01-01_test-case_dry-test"
        assert not run_dir.exists()

    def test_dry_run_output_contains_would_create(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(
            tmp_path, ["2099-01-01_test-case_dry-preview", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "DRY-RUN" in result.output or "dry" in result.output.lower()

    def test_dry_run_lists_template_files(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(
            tmp_path, ["2099-01-01_test-case_dry-files", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "goal.md" in result.output

    def test_dry_run_shows_run_name_preview(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(
            tmp_path, ["2099-01-01_test-case_name-preview", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "2099-01-01_test-case_name-preview" in result.output

    def test_dry_run_shows_taxonomy_path(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(
            tmp_path,
            [
                "2099-01-01_test-case_taxonomy-preview",
                "--dry-run",
                "--taxonomy",
                "fw-improvement",
            ],
        )
        assert result.exit_code == 0
        assert "runs" in result.output
        assert "fw-improvement" in result.output
        assert "2099-01-01_test-case_taxonomy-preview" in result.output


# ---------------------------------------------------------------------------
# エラーケース
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# テンプレート構造: オプションファイルが含まれていないことを確認
# ---------------------------------------------------------------------------

class TestTemplateStructure:
    def test_template_does_not_include_improve_plan(self) -> None:
        """improve-plan.md は runs/_template/ に含まれてはならない（v0.2 手動作成ファイル）。"""
        project_root = Path(__file__).parent.parent
        template_dir = project_root / "runs" / "_template"
        assert not (template_dir / "improve-plan.md").exists(), (
            "improve-plan.md should not be in _template/. "
            "It is a v0.2 optional file created manually by the user."
        )

    def test_template_does_not_include_verify(self) -> None:
        """verify.md は runs/_template/ に含まれてはならない（v0.2 手動作成ファイル）。"""
        project_root = Path(__file__).parent.parent
        template_dir = project_root / "runs" / "_template"
        assert not (template_dir / "verify.md").exists(), (
            "verify.md should not be in _template/. "
            "It is a v0.2 optional file created manually by the user."
        )

    def test_template_includes_standard_files(self) -> None:
        """標準ファイルは runs/_template/ に含まれていること。"""
        project_root = Path(__file__).parent.parent
        template_dir = project_root / "runs" / "_template"
        for fname in ["goal.md", "plan.md", "build.md", "review.md", "improve.md", "result.md"]:
            assert (template_dir / fname).exists(), f"{fname} should be in _template/"


class TestInitRunOptionalFiles:
    def test_init_run_does_not_create_optional_phase_files(self, tmp_path: Path) -> None:
        """init_run で作成された run に improve-plan.md / verify.md が含まれないことを確認。"""
        # 実際の _template/ を使用して RunRepository を初期化
        project_root = Path(__file__).parent.parent
        real_template = project_root / "runs" / "_template"
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()

        repo = RunRepository(runs_dir=runs_dir, template_dir=real_template)
        run_dir = repo.init_run("2099-01-01_test-case_optional-check")

        assert not (run_dir / "improve-plan.md").exists(), \
            "improve-plan.md should not be created by init_run (optional phase file)"
        assert not (run_dir / "verify.md").exists(), \
            "verify.md should not be created by init_run (optional phase file)"

    def test_init_run_standard_files_still_created(self, tmp_path: Path) -> None:
        """init_run で標準ファイルは引き続き作成されること。"""
        project_root = Path(__file__).parent.parent
        real_template = project_root / "runs" / "_template"
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()

        repo = RunRepository(runs_dir=runs_dir, template_dir=real_template)
        run_dir = repo.init_run("2099-01-01_test-case_standard-check")

        for fname in ["goal.md", "plan.md", "build.md", "review.md", "improve.md", "result.md"]:
            assert (run_dir / fname).exists(), f"{fname} should be created by init_run"

    def test_start_run_cli_does_not_create_optional_phase_files(self, tmp_path: Path) -> None:
        """apsf start-run で improve-plan.md / verify.md が作成されないことを確認（CLI 経由）。"""
        import os
        # 実際の _template/ を参照するため、APSF_ROOT をプロジェクトルートに向ける
        project_root = Path(__file__).parent.parent
        env = {**os.environ, "APSF_ROOT": str(project_root)}
        run_name = "2099-01-01_test-case_no-optional-files"
        result = runner.invoke(app, ["start-run", run_name], env=env)
        assert result.exit_code == 0, result.output
        run_dir = project_root / "runs" / run_name
        try:
            assert not (run_dir / "improve-plan.md").exists()
            assert not (run_dir / "verify.md").exists()
        finally:
            # テスト後にクリーンアップ
            if run_dir.exists():
                import shutil
                shutil.rmtree(run_dir)


# ---------------------------------------------------------------------------
# エラーケース
# ---------------------------------------------------------------------------

class TestStartRunErrors:
    def test_invalid_name_exits_with_error(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        result = _invoke_start_run(tmp_path, ["INVALID NAME WITH SPACES"])
        assert result.exit_code != 0

    def test_duplicate_run_exits_with_error(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        run_name = "2099-01-01_test-case_dup-test"
        _invoke_start_run(tmp_path, [run_name])  # 1回目: 作成
        result = _invoke_start_run(tmp_path, [run_name])  # 2回目: 重複
        assert result.exit_code != 0

    def test_force_flag_overwrites_existing(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        run_name = "2099-01-01_test-case_force-test"
        _invoke_start_run(tmp_path, [run_name])  # 1回目作成
        result = _invoke_start_run(tmp_path, [run_name, "--force"])  # 上書き
        assert result.exit_code == 0
        assert "2099-01-01_test-case_force-test" in result.output
