"""
test_cli_act.py — `apsf act` コマンドのテスト

テスト方針:
- Human 担当 phase では生成せず停止する
- Auto 担当 phase（plan / build / review）では LLM を呼び出して保存する
- 既存コンテンツがある場合はデフォルトで上書きしない
- --dry-run では保存しない
- LLM 呼び出しは unittest.mock.patch でモックする

CliRunner を使って Typer コマンドを直接呼び出す。
ファイルシステム操作は tmp_path で分離する。
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from apsf.cli.main import app
from apsf.core.providers.base import GenerateResponse
import apsf.config.settings as settings_module

runner = CliRunner()

# ---------------------------------------------------------------------------
# LLM モック: 5行の meaningful content を返す
# ---------------------------------------------------------------------------

_MOCK_CONTENT = "\n".join([f"Generated line {i}" for i in range(5)])
_MOCK_RESPONSE = GenerateResponse(
    content=_MOCK_CONTENT,
    model="claude-sonnet-4-6",
    provider="anthropic",
)

# ---------------------------------------------------------------------------
# Fixture: settings シングルトンをリセット
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    """get_settings() のシングルトンをリセットして各テストを独立させる。"""
    settings_module._settings_instance = None
    yield
    settings_module._settings_instance = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_env(tmp_path: Path) -> None:
    """runs/_template/ を最小構成で作成する。"""
    template_dir = tmp_path / "runs" / "_template"
    template_dir.mkdir(parents=True)
    for fname in [
        "execution-assignment.md", "goal.md", "plan.md", "build.md",
        "review.md", "improve.md", "result.md", "transcript.md",
    ]:
        (template_dir / fname).write_text(f"# {fname}\n", encoding="utf-8")


def _create_run(tmp_path: Path, run_name: str) -> Path:
    """run ディレクトリを作成して返す。"""
    run_dir = tmp_path / "runs" / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _fill_file(run_dir: Path, filename: str, lines: int = 5) -> None:
    """意味のある内容（5行）でファイルを埋める。"""
    content = "\n".join([f"Real content line {i}" for i in range(lines)]) + "\n"
    (run_dir / filename).write_text(content, encoding="utf-8")


def _invoke_act(
    tmp_path: Path,
    run_name: str,
    args: list[str] | None = None,
) -> "typer.testing.Result":
    """APSF_ROOT を tmp_path に向けて act を実行する。"""
    env = {**os.environ, "APSF_ROOT": str(tmp_path)}
    return runner.invoke(app, ["act", run_name] + (args or []), env=env)


# ---------------------------------------------------------------------------
# TestActHumanStop: Human 担当 phase では停止する
# ---------------------------------------------------------------------------


class TestActHumanStop:
    RUN = "2099-01-01_test-case_act-human"

    def test_goal_needed_stops_with_human_message(self, tmp_path: Path) -> None:
        """goal.md 未充填 → Human メッセージで停止し、ファイルを生成しない。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        # goal.md は未充填

        result = _invoke_act(tmp_path, self.RUN)

        assert result.exit_code == 0
        assert "human" in result.output.lower()
        assert not (run_dir / "goal.md").exists()

    def test_improve_needed_stops_with_human_message(self, tmp_path: Path) -> None:
        """IMPROVE_NEEDED（Judge phase）では Human メッセージで停止し、improve.md を生成しない。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        for fname in [
            "execution-assignment.md", "goal.md", "plan.md", "build.md", "review.md",
        ]:
            _fill_file(run_dir, fname)
        # improve.md は未充填 → IMPROVE_NEEDED

        result = _invoke_act(tmp_path, self.RUN)

        assert result.exit_code == 0
        assert "human" in result.output.lower()
        assert not (run_dir / "improve.md").exists()


# ---------------------------------------------------------------------------
# TestActAutoGeneration: Auto 担当 phase では LLM を呼び出して保存する
# ---------------------------------------------------------------------------


class TestActAutoGeneration:
    RUN = "2099-01-01_test-case_act-auto"

    def test_plan_auto_generated(self, tmp_path: Path) -> None:
        """goal.md 充填済み、plan.md 未充填 → plan.md を自動生成する。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")

        with patch(
            "apsf.orchestration.act_service.ActService._get_provider",
            return_value=_MockProvider(),
        ):
            result = _invoke_act(tmp_path, self.RUN)

        assert result.exit_code == 0, result.output
        assert (run_dir / "plan.md").exists()
        saved = (run_dir / "plan.md").read_text(encoding="utf-8")
        assert _MOCK_CONTENT in saved

    def test_plan_prompt_includes_specialist_guidance_when_assignment_has_ptype(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        planners_dir = tmp_path / "framework" / "agents" / "planners"
        planners_dir.mkdir(parents=True)
        (planners_dir / "bugfix-planner.md").write_text(
            "# Specialist: P-02 Bug Fix Planner\n\nBug-fix emphasis.\n",
            encoding="utf-8",
        )

        run_dir = _create_run(tmp_path, self.RUN)
        (run_dir / "execution-assignment.md").write_text(
            "# Execution Assignment\n\n"
            "## Run Name\n\n`test-run`\n\n"
            "## Role Execution Assignments\n\n"
            "Planner: cli  Builder: cli  Critic: human  Judge: human\n\n"
            "## Planner Specialist\n\n"
            "- Primary P-TYPE: P-02 Bug Fix\n"
            "- Specialist Path: framework/agents/planners/bugfix-planner.md\n",
            encoding="utf-8",
        )
        _fill_file(run_dir, "goal.md")

        captured = {}

        class _CapturingProvider:
            @property
            def provider_name(self) -> str:
                return "mock"

            def generate(self, request):
                captured["prompt"] = request.prompt
                return _MOCK_RESPONSE

        with patch(
            "apsf.orchestration.act_service.ActService._get_provider",
            return_value=_CapturingProvider(),
        ):
            result = _invoke_act(tmp_path, self.RUN)

        assert result.exit_code == 0, result.output
        assert "Planner Specialist Guidance" in captured["prompt"]
        assert "Bug-fix emphasis." in captured["prompt"]

    def test_build_auto_generated(self, tmp_path: Path) -> None:
        """plan.md 充填済み、build.md 未充填 → build.md を自動生成する。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        _fill_file(run_dir, "plan.md")

        with patch(
            "apsf.orchestration.act_service.ActService._get_provider",
            return_value=_MockProvider(),
        ):
            result = _invoke_act(tmp_path, self.RUN)

        assert result.exit_code == 0, result.output
        assert (run_dir / "build.md").exists()

    def test_review_auto_generated(self, tmp_path: Path) -> None:
        """build.md 充填済み、review.md 未充填 → review.md を自動生成する。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        _fill_file(run_dir, "plan.md")
        _fill_file(run_dir, "build.md")

        with patch(
            "apsf.orchestration.act_service.ActService._get_provider",
            return_value=_MockProvider(),
        ):
            result = _invoke_act(tmp_path, self.RUN)

        assert result.exit_code == 0, result.output
        assert (run_dir / "review.md").exists()


# ---------------------------------------------------------------------------
# TestActProtection: 既存コンテンツは上書きしない
# ---------------------------------------------------------------------------


class TestActProtection:
    RUN = "2099-01-01_test-case_act-protection"

    def test_already_filled_not_overwritten(self, tmp_path: Path) -> None:
        """次 phase ファイルがすでに充填済みなら、上書きせず安全停止する。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        _fill_file(run_dir, "plan.md")
        # build.md に既存コンテンツ（_has_any_content = True）
        original = "Existing build content line\n"
        (run_dir / "build.md").write_text(original, encoding="utf-8")

        with patch(
            "apsf.orchestration.act_service.ActService._get_provider",
            return_value=_MockProvider(),
        ):
            result = _invoke_act(tmp_path, self.RUN)

        assert result.exit_code == 0, result.output
        # build.md の内容が書き換えられていないこと
        saved = (run_dir / "build.md").read_text(encoding="utf-8")
        assert saved == original
        # already_filled メッセージが含まれること
        assert "already" in result.output.lower() or "force" in result.output.lower()


# ---------------------------------------------------------------------------
# TestActDryRun: --dry-run では保存しない
# ---------------------------------------------------------------------------


class TestActDryRun:
    RUN = "2099-01-01_test-case_act-dryrun"

    def test_dry_run_does_not_save(self, tmp_path: Path) -> None:
        """--dry-run では plan.md が作成されず、DRY-RUN メッセージが出力される。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")

        with patch(
            "apsf.orchestration.act_service.ActService._get_provider",
            return_value=_MockProvider(),
        ):
            result = _invoke_act(tmp_path, self.RUN, ["--dry-run"])

        assert result.exit_code == 0, result.output
        assert not (run_dir / "plan.md").exists()
        assert "DRY-RUN" in result.output

    def test_dry_run_shows_full_prompt(self, tmp_path: Path) -> None:
        """--dry-run ではプロンプト全文が出力に含まれる（--- Prompt --- セクション）。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")

        with patch(
            "apsf.orchestration.act_service.ActService._get_provider",
            return_value=_MockProvider(),
        ):
            result = _invoke_act(tmp_path, self.RUN, ["--dry-run"])

        assert result.exit_code == 0, result.output
        assert "--- Prompt ---" in result.output
        # prompt には goal.md の内容が含まれるはず（render_plan_prompt が goal_content を使う）
        assert len(result.output) > 200  # 実質的なプロンプト内容が出力されている


# ---------------------------------------------------------------------------
# TestActPrintPrompt: --print-prompt では stdout にプロンプトのみ出力
# ---------------------------------------------------------------------------


class TestActPrintPrompt:
    RUN = "2099-01-01_test-case_act-printprompt"

    def test_print_prompt_outputs_prompt_only(self, tmp_path: Path) -> None:
        """--print-prompt では plan.md を保存せず、プロンプト内容を stdout に出力する。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")

        with patch(
            "apsf.orchestration.act_service.ActService._get_provider",
            return_value=_MockProvider(),
        ):
            result = _invoke_act(tmp_path, self.RUN, ["--print-prompt"])

        assert result.exit_code == 0, result.output
        # ファイルは保存されない
        assert not (run_dir / "plan.md").exists()
        # ヘッダー（====）は出力されない（純粋プロンプト出力）
        assert "====" not in result.output
        # プロンプト内容が含まれる
        assert len(result.output.strip()) > 0

    def test_print_prompt_on_human_phase_exits_cleanly(self, tmp_path: Path) -> None:
        """--print-prompt で Human phase の場合は exit_code == 0 で終了する。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        # goal.md は未充填 → GOAL_NEEDED (Human phase)

        result = _invoke_act(tmp_path, self.RUN, ["--print-prompt"])

        assert result.exit_code == 0, result.output


class TestActClaudeCliExecutor:
    RUN = "2099-01-01_test-case_act-claude-cli"

    def test_claude_cli_timeout_exits_without_writing(self, tmp_path: Path, monkeypatch) -> None:
        """--executor claude-cli で claude -p が timeout したら明示的に止まる。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")

        monkeypatch.setenv("APSF_ROOT", str(tmp_path))
        monkeypatch.setenv("APSF_CLAUDE_TIMEOUT_SEC", "30")

        class _Completed:
            def __init__(self, returncode=0, stdout="", stderr=""):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        def _fake_run(cmd, *args, **kwargs):
            if cmd[:3] == ["apsf", "act", self.RUN]:
                return _Completed(returncode=0, stdout="# Plan\n\nPrompt body\n")
            if cmd[:2] == ["claude", "-p"]:
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=30)
            raise AssertionError(f"unexpected command: {cmd}")

        monkeypatch.setattr("shutil.which", lambda name: "claude" if name == "claude" else None)
        monkeypatch.setattr("subprocess.run", _fake_run)

        result = runner.invoke(app, ["act", self.RUN, "--executor", "claude-cli"])

        assert result.exit_code == 124, result.output
        assert "timed out" in result.output.lower()
        assert not (run_dir / "plan.md").exists()


# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------


class _MockProvider:
    """テスト用の最小モックプロバイダ。"""

    @property
    def provider_name(self) -> str:
        return "mock"

    def generate(self, request):
        return _MOCK_RESPONSE
