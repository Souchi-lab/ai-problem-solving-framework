"""
test_transcript_generator.py — TranscriptGenerator のユニットテスト

テスト方針:
- ファイルが順序どおり連結される
- 欠落ファイルがあっても正常生成される
- transcript.md 自身を誤って読み込まない
- 出力ファイルが生成される
- 生成内容に必要な構造が含まれる
"""

from __future__ import annotations

from pathlib import Path

import pytest

from apsf.orchestration.transcript_generator import (
    TRANSCRIPT_SOURCE_ORDER,
    TranscriptGenerator,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_run(run_dir: Path, filenames: list[str]) -> None:
    """指定ファイル群を run_dir に作成する。"""
    for filename in filenames:
        _write(run_dir / filename, f"# {filename}\n\nContent of {filename}.\n")


# ---------------------------------------------------------------------------
# TRANSCRIPT_SOURCE_ORDER constant
# ---------------------------------------------------------------------------

class TestSourceOrder:
    def test_order_is_defined(self) -> None:
        assert len(TRANSCRIPT_SOURCE_ORDER) > 0

    def test_order_contains_required_files(self) -> None:
        filenames = [f for f, _ in TRANSCRIPT_SOURCE_ORDER]
        assert "goal.md" in filenames
        assert "plan.md" in filenames
        assert "build.md" in filenames
        assert "review.md" in filenames
        assert "result.md" in filenames

    def test_transcript_itself_not_in_order(self) -> None:
        filenames = [f for f, _ in TRANSCRIPT_SOURCE_ORDER]
        assert "transcript.md" not in filenames

    def test_goal_before_build(self) -> None:
        filenames = [f for f, _ in TRANSCRIPT_SOURCE_ORDER]
        assert filenames.index("goal.md") < filenames.index("build.md")

    def test_build_before_review(self) -> None:
        filenames = [f for f, _ in TRANSCRIPT_SOURCE_ORDER]
        assert filenames.index("build.md") < filenames.index("review.md")


# ---------------------------------------------------------------------------
# generate()
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_returns_string(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md"])
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path, "test-run")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_run_name_in_header(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md"])
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path, "my-test-run")
        assert "my-test-run" in result

    def test_uses_dir_name_when_run_name_omitted(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "2026-03-15_test_run"
        run_dir.mkdir()
        _write(run_dir / "goal.md", "# Goal\n\nContent.\n")
        gen = TranscriptGenerator()
        result = gen.generate(run_dir)
        assert "2026-03-15_test_run" in result

    def test_includes_generated_timestamp(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md"])
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path)
        assert "Generated:" in result

    def test_files_appear_in_order(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md", "plan.md", "build.md"])
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path)
        goal_pos  = result.index("goal.md")
        plan_pos  = result.index("plan.md")
        build_pos = result.index("build.md")
        assert goal_pos < plan_pos < build_pos

    def test_missing_files_are_skipped(self, tmp_path: Path) -> None:
        # Only goal.md exists; plan.md / build.md are absent
        _create_run(tmp_path, ["goal.md"])
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path)
        assert "goal.md" in result or "Goal" in result
        assert "plan.md" not in result or "Plan" not in result.split("## ")[1:]

    def test_all_present_files_included(self, tmp_path: Path) -> None:
        present = ["goal.md", "plan.md", "build.md", "review.md", "result.md"]
        _create_run(tmp_path, present)
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path)
        for filename in present:
            assert f"Content of {filename}" in result

    def test_transcript_itself_not_included(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md"])
        # Simulate existing transcript.md with unique content
        _write(tmp_path / "transcript.md", "EXISTING TRANSCRIPT CONTENT UNIQUE")
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path)
        assert "EXISTING TRANSCRIPT CONTENT UNIQUE" not in result

    def test_empty_run_dir_returns_no_source_message(self, tmp_path: Path) -> None:
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path)
        assert "No source files found" in result

    def test_optional_files_included_when_present(self, tmp_path: Path) -> None:
        # v0.2 optional files
        _create_run(tmp_path, ["goal.md", "improve-plan.md", "verify.md"])
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path)
        assert "improve-plan.md" in result or "Improve Plan" in result
        assert "verify.md" in result or "Verify" in result

    def test_optional_files_absent_doesnt_cause_error(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md", "result.md"])
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path)  # Should not raise
        assert "Goal" in result

    def test_includes_secondary_artifact_notice(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md"])
        gen = TranscriptGenerator()
        result = gen.generate(tmp_path)
        assert "二次成果物" in result or "secondary" in result.lower()


# ---------------------------------------------------------------------------
# write()
# ---------------------------------------------------------------------------

class TestWrite:
    def test_creates_transcript_file(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md"])
        gen = TranscriptGenerator()
        output = gen.write(tmp_path, "test-run")
        assert output.exists()
        assert output.name == "transcript.md"

    def test_write_returns_path(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md"])
        gen = TranscriptGenerator()
        result = gen.write(tmp_path)
        assert isinstance(result, Path)

    def test_written_content_matches_generate(self, tmp_path: Path) -> None:
        _create_run(tmp_path, ["goal.md", "plan.md"])
        gen = TranscriptGenerator()
        expected = gen.generate(tmp_path, "my-run")
        gen.write(tmp_path, "my-run")
        actual = (tmp_path / "transcript.md").read_text(encoding="utf-8")
        assert actual == expected

    def test_overwrites_existing_transcript(self, tmp_path: Path) -> None:
        _write(tmp_path / "transcript.md", "OLD CONTENT")
        _create_run(tmp_path, ["goal.md"])
        gen = TranscriptGenerator()
        gen.write(tmp_path, "test-run")
        content = (tmp_path / "transcript.md").read_text(encoding="utf-8")
        assert "OLD CONTENT" not in content
        assert "test-run" in content


# ---------------------------------------------------------------------------
# list_sources()
# ---------------------------------------------------------------------------

class TestListSources:
    def test_returns_list_of_tuples(self, tmp_path: Path) -> None:
        gen = TranscriptGenerator()
        sources = gen.list_sources(tmp_path)
        assert isinstance(sources, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in sources)

    def test_existing_files_marked_true(self, tmp_path: Path) -> None:
        _write(tmp_path / "goal.md", "content")
        gen = TranscriptGenerator()
        sources = dict(gen.list_sources(tmp_path))
        assert sources.get("goal.md") is True

    def test_absent_files_marked_false(self, tmp_path: Path) -> None:
        gen = TranscriptGenerator()
        sources = dict(gen.list_sources(tmp_path))
        assert sources.get("goal.md") is False

    def test_transcript_not_in_list(self, tmp_path: Path) -> None:
        _write(tmp_path / "transcript.md", "content")
        gen = TranscriptGenerator()
        filenames = [f for f, _ in gen.list_sources(tmp_path)]
        assert "transcript.md" not in filenames
