"""
test_cli_write_phase.py — `apsf write-phase` コマンドのテスト

テスト方針:
- phase に応じて正しい output file が選ばれる
- --print-prompt で保存されない
- --stdin で本文が保存される
- empty / whitespace-only / template-only 入力は保存されない
- 既存 meaningful content がある場合、デフォルトで上書きされない
- --force で上書きできる
- --dry-run で保存されない
- 保存後に次アクション案内が出る

CliRunner を使って Typer コマンドを直接呼び出す。
ファイルシステム操作は tmp_path で分離する。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from apsf.core.storage.force_audit_repository import ForceAuditRepository
from apsf.legacy.cli.main import app
from apsf.legacy.orchestration.transcript_generator import TranscriptGenerator
import apsf.legacy.config.settings as settings_module

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


def _meaningful_content(lines: int = 5) -> str:
    """テスト用の meaningful content を返す。"""
    return "\n".join([f"Meaningful content line {i}" for i in range(lines)]) + "\n"


def _invoke_write_phase(
    tmp_path: Path,
    run_name: str,
    args: list[str],
    input_text: str | None = None,
) -> "typer.testing.Result":
    """APSF_ROOT を tmp_path に向けて write-phase を実行する。"""
    env = {**os.environ, "APSF_ROOT": str(tmp_path)}
    return runner.invoke(
        app, ["write-phase", run_name] + args,
        input=input_text,
        env=env,
    )


def _write_run_state(
    run_dir: Path,
    *,
    phase: str,
    owner: str,
    phase_status: str = "pending",
) -> None:
    (run_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "current_phase": phase,
                "phase_status": phase_status,
                "current_owner": owner,
                "retry_count": 0,
                "last_error": "",
                "active_handoff_id": "",
                "gate_failures": [],
            }
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# TestWritePhaseBasic: 基本的な保存動作
# ---------------------------------------------------------------------------

class TestWritePhaseBasic:
    RUN = "2099-01-01_test-case_write-basic"
    CONTENT = _meaningful_content(5)

    def _setup_plan_needed(self, tmp_path: Path) -> Path:
        """execution-assignment.md と goal.md を充填 → PLAN_NEEDED 状態の run を作る。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        return run_dir

    def test_correct_file_chosen_for_phase(self, tmp_path: Path) -> None:
        """PLAN_NEEDED フェーズでは plan.md が作成される。"""
        run_dir = self._setup_plan_needed(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0, result.output
        assert (run_dir / "plan.md").exists()

    def test_stdin_saves_content(self, tmp_path: Path) -> None:
        """--stdin でコンテンツが保存される。"""
        run_dir = self._setup_plan_needed(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0
        assert (run_dir / "plan.md").exists()

    def test_saved_content_matches_input(self, tmp_path: Path) -> None:
        """保存された内容が入力と一致する。"""
        run_dir = self._setup_plan_needed(tmp_path)
        _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        saved = (run_dir / "plan.md").read_text(encoding="utf-8")
        assert saved == self.CONTENT

    def test_shows_saved_confirmation(self, tmp_path: Path) -> None:
        """保存後に [Saved] が出力に含まれる。"""
        self._setup_plan_needed(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0
        assert "[Saved]" in result.output

    def test_shows_next_action_after_save(self, tmp_path: Path) -> None:
        """保存後に [Next] + apsf next が出力に含まれる。"""
        self._setup_plan_needed(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0
        assert "[Next]" in result.output
        assert "apsf next" in result.output


def test_write_phase_advances_run_state_after_review_save(tmp_path: Path) -> None:
    _setup_env(tmp_path)
    run_name = "2099-01-01_test-case_write-review-state"
    run_dir = _create_run(tmp_path, run_name)
    _fill_file(run_dir, "execution-assignment.md")
    _fill_file(run_dir, "goal.md")
    _fill_file(run_dir, "build.md")
    _write_run_state(run_dir, phase="REVIEW_NEEDED", owner="Critic")
    stale_state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    stale_state["retry_count"] = 3
    stale_state["last_error"] = "stale failure"
    stale_state["active_handoff_id"] = "handoff-789"
    stale_state["gate_failures"] = ["old blocker"]
    (run_dir / "run_state.json").write_text(json.dumps(stale_state), encoding="utf-8")

    review_content = (
        "# Review\n\n"
        "## Summary of review\n\n"
        "Builder must revise the implementation.\n\n"
        "## Critical Issues\n\n"
        "- Missing canonical write path verification.\n\n"
        "## Suggested Improvements\n\n"
        "- [Critical] Fix the write path.\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Build","human_owned_blocker":false}\n'
        "```\n"
    )

    result = _invoke_write_phase(tmp_path, run_name, ["--stdin"], review_content)

    assert result.exit_code == 0, result.output
    state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    assert state["current_phase"] == "IMPROVE_NEEDED"
    assert state["current_owner"] == "Human"
    assert state["phase_status"] == "pending"
    assert state["retry_count"] == 0
    assert state["last_error"] == ""
    assert state["gate_failures"] == []


def test_write_phase_review_save_writes_canonical_judge_advisory(tmp_path: Path) -> None:
    _setup_env(tmp_path)
    run_name = "2099-01-01_test-case_write-review-advisory"
    run_dir = _create_run(tmp_path, run_name)
    _fill_file(run_dir, "execution-assignment.md")
    _fill_file(run_dir, "goal.md")
    _fill_file(run_dir, "build.md")
    _write_run_state(run_dir, phase="REVIEW_NEEDED", owner="Critic")

    review_content = (
        "# Review\n\n"
        "## Summary of review\n\n"
        "Return to Builder.\n\n"
        "## Critical Issues\n\n"
        "- Builder-facing blocking defect.\n\n"
        "## Suggested Improvements\n\n"
        "- [Critical] Fix the blocking defect.\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Build","human_owned_blocker":false}\n'
        "```\n"
    )

    result = _invoke_write_phase(tmp_path, run_name, ["--stdin"], review_content)

    assert result.exit_code == 0, result.output
    advisory = json.loads((run_dir / "judge_advisory.json").read_text(encoding="utf-8"))
    assert advisory["recommendation"] == "Return to Build"
    assert advisory["human_owned_blocker"] is False
    assert advisory["advisory_source"] == "judge_structured"
    assert advisory["source"] == "write-phase review completion"
    assert advisory["phase"] == "IMPROVE_NEEDED"
    assert advisory["freshness_token"]


def test_write_phase_review_save_writes_plan_reroute_advisory(tmp_path: Path) -> None:
    _setup_env(tmp_path)
    run_name = "2099-01-01_test-case_write-review-advisory-plan"
    run_dir = _create_run(tmp_path, run_name)
    _fill_file(run_dir, "execution-assignment.md")
    _fill_file(run_dir, "goal.md")
    _fill_file(run_dir, "build.md")
    _write_run_state(run_dir, phase="REVIEW_NEEDED", owner="Critic")

    review_content = (
        "# Review\n\n"
        "## Summary of review\n\n"
        "Return to Planner.\n\n"
        "## Critical Issues\n\n"
        "- Planning boundary is wrong.\n\n"
        "## Suggested Improvements\n\n"
        "- [Critical] Rework the plan.\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Plan","human_owned_blocker":false}\n'
        "```\n"
    )

    result = _invoke_write_phase(tmp_path, run_name, ["--stdin"], review_content)

    assert result.exit_code == 0, result.output
    advisory = json.loads((run_dir / "judge_advisory.json").read_text(encoding="utf-8"))
    assert advisory["recommendation"] == "Return to Plan"
    assert advisory["human_owned_blocker"] is False


def test_write_phase_review_save_requires_structured_advisory_block(tmp_path: Path) -> None:
    _setup_env(tmp_path)
    run_name = "2099-01-01_test-case_write-review-advisory-missing"
    run_dir = _create_run(tmp_path, run_name)
    _fill_file(run_dir, "execution-assignment.md")
    _fill_file(run_dir, "goal.md")
    _fill_file(run_dir, "build.md")
    _write_run_state(run_dir, phase="REVIEW_NEEDED", owner="Critic")

    review_content = (
        "# Review\n\n"
        "## Summary of review\n\n"
        "Missing structured advisory.\n\n"
        "## Critical Issues\n\n"
        "- Still meaningful review content.\n\n"
        "## Major Issues\n\n"
        "- Another concrete issue.\n\n"
        "## Notes\n\n"
        "Judge still needs a structured recommendation block.\n"
    )

    result = _invoke_write_phase(tmp_path, run_name, ["--stdin"], review_content)

    assert result.exit_code == 1, result.output
    assert "apsf-judge-advisory" in result.output
    assert not (run_dir / "judge_advisory.json").exists()


def test_write_phase_review_save_fails_when_duplicate_identical_advisory_blocks_exist(tmp_path: Path) -> None:
    _setup_env(tmp_path)
    run_name = "2099-01-01_test-case_write-review-advisory-duplicate-identical"
    run_dir = _create_run(tmp_path, run_name)
    _fill_file(run_dir, "execution-assignment.md")
    _fill_file(run_dir, "goal.md")
    _fill_file(run_dir, "build.md")
    _write_run_state(run_dir, phase="REVIEW_NEEDED", owner="Critic")

    review_content = (
        "# Review\n\n"
        "## Summary of review\n\n"
        "Duplicate advisory blocks.\n\n"
        "## Critical Issues\n\n"
        "- One clear issue.\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Build","human_owned_blocker":false}\n'
        "```\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Build","human_owned_blocker":false}\n'
        "```\n"
    )

    result = _invoke_write_phase(tmp_path, run_name, ["--stdin"], review_content)

    assert result.exit_code == 1, result.output
    assert "multiple blocks are not allowed" in result.output
    assert not (run_dir / "judge_advisory.json").exists()


def test_write_phase_review_save_fails_when_duplicate_conflicting_advisory_blocks_exist(tmp_path: Path) -> None:
    _setup_env(tmp_path)
    run_name = "2099-01-01_test-case_write-review-advisory-duplicate-conflict"
    run_dir = _create_run(tmp_path, run_name)
    _fill_file(run_dir, "execution-assignment.md")
    _fill_file(run_dir, "goal.md")
    _fill_file(run_dir, "build.md")
    _write_run_state(run_dir, phase="REVIEW_NEEDED", owner="Critic")

    review_content = (
        "# Review\n\n"
        "## Summary of review\n\n"
        "Conflicting advisory blocks.\n\n"
        "## Critical Issues\n\n"
        "- One clear issue.\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Build","human_owned_blocker":false}\n'
        "```\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Plan","human_owned_blocker":true}\n'
        "```\n"
    )

    result = _invoke_write_phase(tmp_path, run_name, ["--stdin"], review_content)

    assert result.exit_code == 1, result.output
    assert "multiple blocks are not allowed" in result.output
    assert not (run_dir / "judge_advisory.json").exists()


def test_write_phase_fails_closed_when_state_sync_fails(tmp_path: Path) -> None:
    _setup_env(tmp_path)
    run_name = "2099-01-01_test-case_write-sync-failure"
    run_dir = _create_run(tmp_path, run_name)
    _fill_file(run_dir, "execution-assignment.md")
    _fill_file(run_dir, "goal.md")

    with patch(
        "apsf.core.state.transition_service.TransitionService.transition",
        side_effect=RuntimeError("state sync failed"),
    ):
        result = _invoke_write_phase(tmp_path, run_name, ["--stdin"], _meaningful_content(5))

    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, RuntimeError)
    assert "state sync failed" in str(result.exception)
    assert (run_dir / "plan.md").exists()


# ---------------------------------------------------------------------------
# TestWritePrompt: --print-prompt オプション
# ---------------------------------------------------------------------------

class TestWritePrompt:
    RUN = "2099-01-01_test-case_write-prompt"

    def _setup(self, tmp_path: Path) -> Path:
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        return run_dir

    def test_print_prompt_does_not_save(self, tmp_path: Path) -> None:
        """--print-prompt ではファイルが作成されない。"""
        run_dir = self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--print-prompt"])
        assert result.exit_code == 0
        assert not (run_dir / "plan.md").exists()

    def test_print_prompt_shows_instruction(self, tmp_path: Path) -> None:
        """--print-prompt では instruction が表示される。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--print-prompt"])
        assert result.exit_code == 0
        # instruction セクションが含まれる
        assert "--- Instruction ---" in result.output


# ---------------------------------------------------------------------------
# TestWritePhaseValidation: 空・テンプレートのみの入力チェック
# ---------------------------------------------------------------------------

class TestWritePhaseValidation:
    RUN = "2099-01-01_test-case_write-validation"

    def _setup(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")

    def test_empty_input_rejected(self, tmp_path: Path) -> None:
        """空入力は保存されない（exit_code != 0）。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], "")
        assert result.exit_code != 0
        run_dir = tmp_path / "runs" / self.RUN
        assert not (run_dir / "plan.md").exists()

    def test_whitespace_only_rejected(self, tmp_path: Path) -> None:
        """空白のみの入力は保存されない。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], "   \n\n  \t\n")
        assert result.exit_code != 0

    def test_template_scaffolding_rejected(self, tmp_path: Path) -> None:
        """テンプレート骨格のみの入力（見出し・コメント・空チェックボックス）は保存されない。"""
        self._setup(tmp_path)
        template_only = (
            "# Plan\n"
            "\n"
            "<!-- template comment -->\n"
            "\n"
            "---\n"
            "\n"
            "## Section\n"
            "\n"
            "-\n"
            "- [ ] Unchecked item\n"
            "\n"
            "**Label**:\n"
        )
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], template_only)
        assert result.exit_code != 0

    def test_transport_preamble_is_sanitized_before_save(self, tmp_path: Path) -> None:
        """wrapper/log の前置きがあっても Markdown 本文だけ保存する。"""
        self._setup(tmp_path)
        input_text = (
            "[APSF] run: test\n"
            "[Step 2/3] invoke claude -p...\n"
            "[Note] wrapper note\n"
            "\n"
            "# Plan\n"
            "\n"
            "Actual line 1\n"
            "Actual line 2\n"
            "Actual line 3\n"
            "Actual line 4\n"
        )
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], input_text)
        assert result.exit_code == 0, result.output
        saved = (tmp_path / "runs" / self.RUN / "plan.md").read_text(encoding="utf-8")
        assert saved.startswith("# Plan\n")
        assert "[APSF]" not in saved
        assert "[Step 2/3]" not in saved

    def test_transport_only_input_is_rejected(self, tmp_path: Path) -> None:
        """transport/status text だけなら phase file として保存しない。"""
        self._setup(tmp_path)
        input_text = (
            "[APSF] run: test\n"
            "[Step 2/3] invoke claude -p...\n"
            "[Done] build.md saved\n"
            "Permission required\n"
        )
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], input_text)
        assert result.exit_code != 0
        assert not (tmp_path / "runs" / self.RUN / "plan.md").exists()


# ---------------------------------------------------------------------------
# TestWritePhaseOverwrite: 上書き保護 / --force
# ---------------------------------------------------------------------------

class TestWritePhaseOverwrite:
    RUN = "2099-01-01_test-case_write-overwrite"
    CONTENT = _meaningful_content(5)

    def _setup(self, tmp_path: Path) -> Path:
        """
        PLAN_NEEDED フェーズの run を作る（target = plan.md）。
        plan.md に部分的な内容（1行、filled 閾値未満）を事前書き込みして
        上書き保護を発動させる。

        _has_any_content (>0 行) で保護されるため、
        _is_filled (>3 行) を満たさなくても保護が有効になる。
        """
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        # Phase = PLAN_NEEDED; plan.md に部分的な記入（1 行 = filled 未満）
        (run_dir / "plan.md").write_text(
            "# Plan\n\nPartial draft — do not overwrite without --force.\n",
            encoding="utf-8",
        )
        return run_dir

    def test_filled_file_blocked_by_default(self, tmp_path: Path) -> None:
        """既存のコンテンツがある場合、デフォルトでは上書きされない。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code != 0

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        """--force で既存コンテンツを上書きできる。"""
        run_dir = self._setup(tmp_path)
        new_content = _meaningful_content(5).replace("Meaningful", "Updated")
        result = _invoke_write_phase(
            tmp_path,
            self.RUN,
            ["--stdin", "--force", "--force-reason", "intentional overwrite"],
            new_content,
        )
        assert result.exit_code == 0
        saved = (run_dir / "plan.md").read_text(encoding="utf-8")
        assert "Updated" in saved

    def test_force_without_reason_blocked(self, tmp_path: Path) -> None:
        """--force に reason がない場合は block される。"""
        run_dir = self._setup(tmp_path)
        original = (run_dir / "plan.md").read_text(encoding="utf-8")

        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin", "--force"], self.CONTENT)

        assert result.exit_code == 2
        assert "--force-reason is required" in result.stderr
        assert (run_dir / "plan.md").read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# TestWritePhaseForceWarning: --force --stdin 上書き警告
# ---------------------------------------------------------------------------

class TestWritePhaseForceWarning:
    """
    --force --stdin で既存コンテンツを上書きするとき、
    stderr に "[Warn] Overwriting <file> (current phase target)" が出ることを検証する。
    stdout は汚染されないこと。
    """
    RUN = "2099-01-01_test-case_force-warning"
    CONTENT = _meaningful_content(5)

    def _setup(self, tmp_path: Path) -> Path:
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        # plan.md に部分的な記入（上書き保護対象）
        (run_dir / "plan.md").write_text(
            "# Plan\n\nExisting content.\n", encoding="utf-8"
        )
        return run_dir

    def test_force_stdin_warns_on_stderr(self, tmp_path: Path) -> None:
        """--force --stdin で上書きするとき stderr に警告が出る。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(
            tmp_path,
            self.RUN,
            ["--stdin", "--force", "--force-reason", "intentional overwrite"],
            self.CONTENT,
        )
        assert result.exit_code == 0, result.output
        assert "Overwriting" in result.stderr
        assert "plan.md" in result.stderr

    def test_force_stdin_warning_mentions_phase_target(self, tmp_path: Path) -> None:
        """警告メッセージに 'current phase target' が含まれる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(
            tmp_path,
            self.RUN,
            ["--stdin", "--force", "--force-reason", "intentional overwrite"],
            self.CONTENT,
        )
        assert result.exit_code == 0
        assert "current phase target" in result.stderr

    def test_force_stdin_warning_not_in_stdout(self, tmp_path: Path) -> None:
        """上書き警告は stdout に出ない（pipe 透過性を保つ）。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(
            tmp_path,
            self.RUN,
            ["--stdin", "--force", "--force-reason", "intentional overwrite"],
            self.CONTENT,
        )
        assert result.exit_code == 0
        assert "Overwriting" not in result.stdout

    def test_force_stdin_no_warning_when_no_existing_content(self, tmp_path: Path) -> None:
        """既存コンテンツがない場合は警告が出ない。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        # plan.md は空（テンプレートのまま）
        result = _invoke_write_phase(
            tmp_path,
            self.RUN,
            ["--stdin", "--force", "--force-reason", "intentional overwrite"],
            self.CONTENT,
        )
        assert result.exit_code == 0
        assert "Overwriting" not in result.stderr


# ---------------------------------------------------------------------------
# TestWritePhaseForceAudit: --force audit trail
# ---------------------------------------------------------------------------

class TestWritePhaseForceAudit:
    RUN = "2099-01-01_test-case_force-audit"
    CONTENT = _meaningful_content(5)

    def _setup(self, tmp_path: Path) -> Path:
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        (run_dir / "plan.md").write_text(
            "# Plan\n\nExisting content.\n", encoding="utf-8"
        )
        return run_dir

    def test_force_write_phase_creates_audit_entry(self, tmp_path: Path) -> None:
        """write-phase --force 実行で force_audit.json に overwrite entry が保存される。"""
        run_dir = self._setup(tmp_path)

        result = _invoke_write_phase(
            tmp_path,
            self.RUN,
            ["--stdin", "--force", "--force-reason", "intentional overwrite"],
            self.CONTENT,
        )

        assert result.exit_code == 0, result.output
        entries = ForceAuditRepository(run_dir).load()
        assert len(entries) == 1
        assert entries[0].command == "write-phase"
        assert entries[0].target_file == "plan.md"
        assert entries[0].override_kind == "overwrite"
        assert entries[0].had_reason is True
        assert entries[0].reason == "intentional overwrite"

    def test_force_write_phase_without_reason_is_blocked(self, tmp_path: Path) -> None:
        """write-phase --force で reason なしなら block され、audit も残らない。"""
        run_dir = self._setup(tmp_path)

        result = _invoke_write_phase(
            tmp_path,
            self.RUN,
            ["--stdin", "--force"],
            self.CONTENT,
        )

        assert result.exit_code == 2, result.output
        assert "--force-reason is required" in result.stderr
        entries = ForceAuditRepository(run_dir).load()
        assert entries == []


# ---------------------------------------------------------------------------
# TestWritePhaseDryRun: --dry-run オプション
# ---------------------------------------------------------------------------

class TestWritePhaseDryRun:
    RUN = "2099-01-01_test-case_write-dryrun"
    CONTENT = _meaningful_content(5)

    def _setup(self, tmp_path: Path) -> None:
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")

    def test_dry_run_does_not_save(self, tmp_path: Path) -> None:
        """--dry-run ではファイルが作成されない。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--dry-run"])
        assert result.exit_code == 0
        run_dir = tmp_path / "runs" / self.RUN
        assert not (run_dir / "plan.md").exists()

    def test_dry_run_shows_would_write(self, tmp_path: Path) -> None:
        """--dry-run では DRY-RUN メッセージが出力に含まれる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--dry-run"])
        assert result.exit_code == 0
        assert "DRY-RUN" in result.output


# ---------------------------------------------------------------------------
# TestWritePhaseSpecialPhases: 特殊フェーズ処理
# ---------------------------------------------------------------------------

class TestWritePhaseSpecialPhases:
    def test_complete_phase_no_write(self, tmp_path: Path) -> None:
        """COMPLETE フェーズでは何も保存されず exit 0 になる。"""
        _setup_env(tmp_path)
        run_name = "2099-01-01_test-case_write-complete"
        run_dir = _create_run(tmp_path, run_name)
        for fname in [
            "execution-assignment.md", "goal.md", "plan.md", "build.md",
            "review.md", "improve.md", "result.md", "transcript.md",
        ]:
            _fill_file(run_dir, fname)
        result = _invoke_write_phase(tmp_path, run_name, [])
        assert result.exit_code == 0
        assert "complete" in result.output.lower()

    def test_transcript_recommended_directs_to_apsf_transcript(
        self, tmp_path: Path
    ) -> None:
        """TRANSCRIPT_RECOMMENDED フェーズでは apsf transcript を案内する。"""
        _setup_env(tmp_path)
        run_name = "2099-01-01_test-case_write-transcript"
        run_dir = _create_run(tmp_path, run_name)
        for fname in [
            "execution-assignment.md", "goal.md", "plan.md", "build.md",
            "review.md", "improve.md", "result.md",
        ]:
            _fill_file(run_dir, fname)
        # transcript.md は存在しない → TRANSCRIPT_RECOMMENDED になる
        result = _invoke_write_phase(tmp_path, run_name, [])
        assert result.exit_code == 0
        assert "transcript" in result.output.lower()


# ---------------------------------------------------------------------------
# TestWritePhaseOverwriteUX: 改善C — 上書き保護 UX
# ---------------------------------------------------------------------------

class TestWritePhaseOverwriteUX:
    """改善C: --stdin ハードブロック / 対話モードの confirm は別テストクラス。"""
    RUN = "2099-01-01_test-case_write-overwrite-ux"
    CONTENT = _meaningful_content(5)

    def _setup(self, tmp_path: Path) -> Path:
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        (run_dir / "plan.md").write_text(
            "# Plan\n\nPartial draft.\n",
            encoding="utf-8",
        )
        return run_dir

    def test_stdin_overwrite_error_contains_path(self, tmp_path: Path) -> None:
        """--stdin で上書きブロック時に対象パスが出力に含まれる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code != 0
        # Path: が出力に含まれる（stderr は output に含まれる）
        assert "Path" in result.output or "plan.md" in result.output

    def test_stdin_overwrite_error_suggests_force(self, tmp_path: Path) -> None:
        """--stdin で上書きブロック時に --force コマンド例が出力に含まれる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code != 0
        assert "--force" in result.output


# ---------------------------------------------------------------------------
# TestWritePhaseEncoding: 日本語・非 ASCII エンコーディング回帰テスト
#
# Windows では sys.stdin がシステムデフォルト (cp932) で開かれるため、
# PowerShell pipe / here-string 経由の UTF-8 入力が文字化けする問題の回帰テスト。
# CliRunner は文字列を直接渡すため buffer 経路は通らないが、
# 保存→読み込み→transcript のラウンドトリップで文字化けがないことを保証する。
# ---------------------------------------------------------------------------

_JAPANESE_PLAN = (
    "# プラン\n\n"
    "目標: 日本語コンテンツのエンコーディング検証\n\n"
    "アプローチ:\n"
    "- UTF-8 で保存されること\n"
    "- transcript 生成後も保持されること\n"
    "- Windows / PowerShell 環境でも崩れないこと\n"
)

_JAPANESE_BUILD = (
    "# ビルド成果物\n\n"
    "実装内容:\n"
    "- write-phase コマンドに stdin UTF-8 読み込みを追加\n"
    "- cli/io.py に read_stdin_utf8() ヘルパーを切り出し\n"
    "- 文字化け回帰テストを整備\n\n"
    "確認済み:\n"
    "- 日本語・記号・全角文字が正しく保存される\n"
)


# ---------------------------------------------------------------------------
# TestWritePhaseUXDisplay: UX 改善 — 保存先表示 / [Saved] 目立ち
# ---------------------------------------------------------------------------

class TestWritePhaseUXDisplay:
    """
    UX 改善テスト:
    - --stdin モードで保存先が目立つ
    - --stdin モードで instruction セクションが省略される
    - [Saved] にファイル名が含まれる
    - インタラクティブモードでも保存先リマインドが出る
    - --print-prompt は instruction を引き続き表示（回帰テスト）
    """
    RUN = "2099-01-01_test-case_write-ux"
    CONTENT = _meaningful_content(5)

    def _setup(self, tmp_path: Path) -> Path:
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        return run_dir

    def test_stdin_shows_saving_to(self, tmp_path: Path) -> None:
        """--stdin モードで 'Saving to' と保存先ファイル名が表示される。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0, result.output
        assert "Saving to" in result.output
        assert "plan.md" in result.output

    def test_stdin_shows_phase_in_target_notice(self, tmp_path: Path) -> None:
        """--stdin モードで保存先通知にフェーズ名が含まれる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0
        assert "PLAN_NEEDED" in result.output

    def test_stdin_skips_instruction_section(self, tmp_path: Path) -> None:
        """--stdin モードでは '--- Instruction ---' が出力されない。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0
        assert "--- Instruction ---" not in result.output

    def test_saved_confirmation_shows_filename(self, tmp_path: Path) -> None:
        """保存後の [Saved] 行にファイル名が含まれる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0
        assert "[Saved] plan.md" in result.output

    def test_saved_confirmation_shows_path(self, tmp_path: Path) -> None:
        """保存後の出力にフルパス (Path :) が含まれる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0
        assert "Path" in result.output

    def test_interactive_shows_write_to(self, tmp_path: Path) -> None:
        """インタラクティブモードで 'Write to' と保存先ファイル名がリマインドされる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, [], self.CONTENT)
        assert result.exit_code == 0
        assert "Write to" in result.output
        assert "plan.md" in result.output

    def test_interactive_still_shows_instruction(self, tmp_path: Path) -> None:
        """インタラクティブモードでは引き続き instruction が表示される。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, [], self.CONTENT)
        assert result.exit_code == 0
        assert "--- Instruction ---" in result.output

    def test_print_prompt_still_shows_instruction(self, tmp_path: Path) -> None:
        """--print-prompt では instruction が表示される（回帰テスト）。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--print-prompt"])
        assert result.exit_code == 0
        assert "--- Instruction ---" in result.output


# ---------------------------------------------------------------------------
# TestWritePhasePipeCompat: stdout/stderr 責務分離（パイプ連携用）
# ---------------------------------------------------------------------------

class TestWritePhasePipeCompat:
    """
    stdout/stderr 責務分離テスト。
    Click 8.2+ の result.stdout / result.stderr で個別検証する。

    設計:
      stdout: instruction テキスト（--print-prompt / 対話モード）
      stderr: ステータス・ヘッダー・[Saved] などすべての UI メッセージ

    result.output  = stdout + stderr 混合（ユーザーが端末で見るもの）
    result.stdout  = stdout のみ
    result.stderr  = stderr のみ
    """
    RUN = "2099-01-01_test-case_pipe-compat"
    CONTENT = _meaningful_content(5)

    def _setup(self, tmp_path: Path) -> Path:
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        return run_dir

    def test_stdin_stdout_is_empty(self, tmp_path: Path) -> None:
        """--stdin モードでは stdout に何も出力されない（pipe 先を汚染しない）。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0, result.output
        assert result.stdout.strip() == ""

    def test_print_prompt_stdout_has_instruction_text(self, tmp_path: Path) -> None:
        """--print-prompt では stdout に instruction テキストが出力される。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--print-prompt"])
        assert result.exit_code == 0
        # instruction テキストには plan 作成に関するキーワードが含まれる
        assert "goal.md" in result.stdout or "plan" in result.stdout.lower()

    def test_print_prompt_stdout_has_no_header(self, tmp_path: Path) -> None:
        """--print-prompt では stdout にヘッダー行が含まれない。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--print-prompt"])
        assert result.exit_code == 0
        assert "Run   :" not in result.stdout
        assert "Phase :" not in result.stdout

    def test_interactive_stdout_has_instruction_text(self, tmp_path: Path) -> None:
        """対話モードでは stdout に instruction テキストが出力される。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, [], self.CONTENT)
        assert result.exit_code == 0
        assert "goal.md" in result.stdout or "plan" in result.stdout.lower()

    def test_interactive_stdout_has_no_saved(self, tmp_path: Path) -> None:
        """対話モードでは stdout に [Saved] が含まれない（stderr へ移動済み）。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, [], self.CONTENT)
        assert result.exit_code == 0
        assert "[Saved]" not in result.stdout

    def test_stdin_stderr_has_saved(self, tmp_path: Path) -> None:
        """--stdin モードでは stderr に [Saved] が含まれる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0
        assert "[Saved]" in result.stderr

    def test_stdin_stderr_has_saving_to(self, tmp_path: Path) -> None:
        """--stdin モードでは stderr に 'Saving to' が含まれる。"""
        self._setup(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], self.CONTENT)
        assert result.exit_code == 0
        assert "Saving to" in result.stderr


class TestWritePhaseEncoding:
    """日本語コンテンツの保存・読み込み・transcript 生成の回帰テスト。"""

    RUN = "2099-01-01_test-case_write-encoding"

    def _setup_goal_filled(self, tmp_path: Path) -> Path:
        """PLAN_NEEDED 状態の run を作成して run_dir を返す。"""
        _setup_env(tmp_path)
        run_dir = _create_run(tmp_path, self.RUN)
        _fill_file(run_dir, "execution-assignment.md")
        _fill_file(run_dir, "goal.md")
        return run_dir

    def test_japanese_plan_saved_without_corruption(self, tmp_path: Path) -> None:
        """日本語を含む plan.md が文字化けなく保存される。"""
        run_dir = self._setup_goal_filled(tmp_path)
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], _JAPANESE_PLAN)
        assert result.exit_code == 0, result.output
        saved = (run_dir / "plan.md").read_text(encoding="utf-8")
        assert "日本語" in saved
        assert "プラン" in saved
        assert "UTF-8" in saved

    def test_japanese_content_roundtrip_matches_input(self, tmp_path: Path) -> None:
        """保存した日本語コンテンツが入力と完全一致する。"""
        run_dir = self._setup_goal_filled(tmp_path)
        _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], _JAPANESE_PLAN)
        saved = (run_dir / "plan.md").read_text(encoding="utf-8")
        assert saved == _JAPANESE_PLAN

    def test_japanese_survives_transcript_generation(self, tmp_path: Path) -> None:
        """日本語の plan.md / build.md が transcript.md 生成後も保持される。"""
        run_dir = self._setup_goal_filled(tmp_path)

        # plan.md を日本語で保存（PLAN_NEEDED → phase advance）
        (run_dir / "plan.md").write_text(_JAPANESE_PLAN, encoding="utf-8")
        # build.md 以降も日本語で準備
        (run_dir / "build.md").write_text(_JAPANESE_BUILD, encoding="utf-8")
        for fname in ["review.md", "improve.md", "result.md"]:
            _fill_file(run_dir, fname)

        gen = TranscriptGenerator()
        gen.write(run_dir, self.RUN)

        transcript = (run_dir / "transcript.md").read_text(encoding="utf-8")
        assert "日本語" in transcript
        assert "プラン" in transcript
        assert "ビルド成果物" in transcript
        assert "read_stdin_utf8" in transcript  # build.md の内容が保持されている

    def test_multibyte_symbols_preserved(self, tmp_path: Path) -> None:
        """全角記号・括弧・矢印が文字化けなく保存される。"""
        run_dir = self._setup_goal_filled(tmp_path)
        multibyte_content = (
            "# テスト\n\n"
            "記号: →←↑↓ ・「」『』【】\n"
            "全角英数: ＡＢＣＤ　１２３４\n"
            "矢印: ⇒ ⇔ ※\n"
            "補足: このテストは Windows cp932 文字化けの回帰検証です。\n"
        )
        result = _invoke_write_phase(tmp_path, self.RUN, ["--stdin"], multibyte_content)
        assert result.exit_code == 0, result.output
        saved = (run_dir / "plan.md").read_text(encoding="utf-8")
        assert "→←↑↓" in saved
        assert "cp932" in saved
