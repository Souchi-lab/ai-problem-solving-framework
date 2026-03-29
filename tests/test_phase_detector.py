"""
test_phase_detector.py — PhaseDetector のユニットテスト

テスト方針:
- 各フェーズへの遷移を単独でテストする
- _is_filled のヒューリスティックをテストする
- tmp_path を使って実際のファイルを書き込む
"""

from __future__ import annotations

from pathlib import Path

import pytest

from apsf.legacy.orchestration.phase_detector import Phase, PhaseDetector


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _fill(run_dir: Path, filename: str, lines: int = 5) -> None:
    """意味のある行を lines 本書いて「充填済み」にする。
    transcript.md は 'Generated:' を含む内容を書く（_is_filled の特別判定に対応）。
    """
    if filename == "transcript.md":
        content = "# Transcript\n\nGenerated: 2099-01-01T00:00:00\n\n" + "\n".join(
            [f"Content line {i}" for i in range(lines)]
        )
    else:
        content = "\n".join([f"Content line {i}" for i in range(lines)])
    _write(run_dir / filename, content)


def _fill_comments_only(run_dir: Path, filename: str) -> None:
    """コメント行・区切り行だけのファイルを作る（_is_filled → False）。"""
    content = (
        "<!-- comment 1 -->\n"
        "<!-- comment 2 -->\n"
        "---\n"
        "\n"
        "# Heading only\n"
    )
    _write(run_dir / filename, content)


# ---------------------------------------------------------------------------
# _is_filled
# ---------------------------------------------------------------------------

class TestIsFilled:
    def test_file_not_exists_returns_false(self, tmp_path: Path) -> None:
        d = PhaseDetector(tmp_path)
        assert d._is_filled("nonexistent.md") is False

    def test_empty_file_returns_false(self, tmp_path: Path) -> None:
        _write(tmp_path / "f.md", "")
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_comments_only_returns_false(self, tmp_path: Path) -> None:
        _fill_comments_only(tmp_path, "f.md")
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_four_meaningful_lines_returns_true(self, tmp_path: Path) -> None:
        content = "line1\nline2\nline3\nline4\n"
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is True

    def test_three_meaningful_lines_returns_false(self, tmp_path: Path) -> None:
        content = "line1\nline2\nline3\n"
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_mixed_content_counts_meaningful_only(self, tmp_path: Path) -> None:
        content = (
            "# Heading\n"
            "---\n"
            "<!-- comment -->\n"
            "\n"
            "real line 1\n"
            "real line 2\n"
            "real line 3\n"
            "real line 4\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is True

    # ── 新フィルタ群 ───────────────────────────────────────────────────────

    def test_multiline_html_comment_block_excluded(self, tmp_path: Path) -> None:
        """複数行 HTML コメントブロック内の行は除外される。"""
        content = (
            "<!--\n"
            "  This is inside a multiline comment block.\n"
            "  It should not count as meaningful content.\n"
            "  Not even this line.\n"
            "  Or this one.\n"
            "-->\n"
            "real line 1\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False  # only 1 real line

    def test_bare_bullet_excluded(self, tmp_path: Path) -> None:
        """裸の箇条書き（- のみ）は除外される。"""
        content = "- \n- \n- \n- \n- \n"
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_unchecked_checkbox_excluded(self, tmp_path: Path) -> None:
        """未チェックのチェックボックス行（- [ ] ...）は除外される。"""
        content = (
            "- [ ] Step 1: do something\n"
            "- [ ] Step 2: do more\n"
            "- [ ] Step 3: finish\n"
            "- [ ] Step 4: review\n"
            "- [ ]\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_checked_checkbox_counts_as_meaningful(self, tmp_path: Path) -> None:
        """チェック済みチェックボックス（- [x]）は意味のある行として数える。"""
        content = (
            "- [x] Decision made: adopt approach A\n"
            "- [x] Confirmed with stakeholder\n"
            "- [x] Tests passing\n"
            "- [x] Documentation updated\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is True

    def test_table_separator_excluded(self, tmp_path: Path) -> None:
        """テーブル区切り行（|---|---|）は除外される。"""
        content = (
            "| Col A | Col B |\n"
            "|---|---|\n"
            "|:---|---:|\n"
            "| | |\n"
            "| | |\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        # header "| Col A | Col B |" counts (1), rest filtered
        assert d._is_filled("f.md") is False

    def test_bold_label_only_excluded(self, tmp_path: Path) -> None:
        """太字ラベル行（**Label**: のみ）は除外される。"""
        content = (
            "**採用**:\n"
            "**理由**:\n"
            "**対応する改善**:\n"
            "**対応しない改善（理由）**:\n"
            "**Selected Approach**:\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_bold_label_with_content_counts(self, tmp_path: Path) -> None:
        """太字ラベル + 内容がある行は意味のある行として数える。"""
        content = (
            "**採用**: Approach A — シンプルで保守しやすい\n"
            "**理由**: 既存の実装パターンに合致するため\n"
            "**リスク**: 処理速度は若干低下するが許容範囲内\n"
            "**次アクション**: Builder に build.md の作成を依頼\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is True

    def test_short_placeholder_bullet_excluded(self, tmp_path: Path) -> None:
        """短いプレースホルダー箇条書き（- H1: / - 概要:）は除外される。"""
        content = (
            "- H1:\n"
            "- H2:\n"
            "- 概要:\n"
            "- メリット:\n"
            "- デメリット:\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_code_fence_excluded(self, tmp_path: Path) -> None:
        """コードフェンス行（``` / ~~~）は除外される。"""
        content = (
            "```\n"
            "```python\n"
            "~~~\n"
            "~~~bash\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_fullwidth_placeholder_excluded(self, tmp_path: Path) -> None:
        """全角括弧プレースホルダー行（（...）のみ）は除外される。"""
        content = (
            "（プロンプト本文をここに貼る）\n"
            "（ここに入力してください）\n"
            "（記入例）\n"
            "（テンプレート）\n"
            "（省略可）\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_plan_template_style_is_unfilled(self, tmp_path: Path) -> None:
        """plan.md のテンプレート初期状態は unfilled と判定される。"""
        content = (
            "# Plan\n"
            "\n"
            "<!-- template comment -->\n"
            "\n"
            "---\n"
            "\n"
            "## Problem Structure\n"
            "\n"
            "-\n"
            "-\n"
            "\n"
            "---\n"
            "\n"
            "## Hypotheses\n"
            "\n"
            "- H1:\n"
            "- H2:\n"
            "\n"
            "---\n"
            "\n"
            "## Selected Approach\n"
            "\n"
            "**採用**:\n"
            "\n"
            "**理由**:\n"
            "\n"
            "---\n"
            "\n"
            "## Execution Plan\n"
            "\n"
            "- [ ] Step 1:\n"
            "- [ ] Step 2:\n"
            "- [ ] Step 3:\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    def test_improve_template_style_is_unfilled(self, tmp_path: Path) -> None:
        """improve.md のテンプレート初期状態は unfilled と判定される。"""
        content = (
            "# Improve\n"
            "\n"
            "<!-- template -->\n"
            "\n"
            "---\n"
            "\n"
            "## Decision\n"
            "\n"
            "- [ ] 続ける → 次の iteration へ\n"
            "- [ ] 終了 → result.md を書く\n"
            "\n"
            "---\n"
            "\n"
            "## Next Iteration Scope\n"
            "\n"
            "**対応する改善**:\n"
            "- [ ]\n"
            "\n"
            "**対応しない改善（理由）**:\n"
            "-\n"
        )
        _write(tmp_path / "f.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("f.md") is False

    # -- テーブルヘッダー行 / なし プレースホルダー --

    def test_table_header_before_separator_not_counted(self, tmp_path: Path) -> None:
        """テーブルヘッダー行（次行が |---|---|）はカウントしない。"""
        content = "| col1 | col2 |\n|---|---|\n| | |\n"
        assert PhaseDetector._count_meaningful_lines(content) == 0

    def test_table_header_japanese_not_counted(self, tmp_path: Path) -> None:
        """日本語列名のテーブルヘッダー行はカウントしない。"""
        content = "| ファイル | 変更内容 |\n|---|---|\n| | |\n"
        assert PhaseDetector._count_meaningful_lines(content) == 0

    def test_table_data_row_with_content_counted(self, tmp_path: Path) -> None:
        """テーブルデータ行（区切り行の直後）は meaningful としてカウントする。"""
        content = (
            "| Component | Description |\n"
            "|---|---|\n"
            "| act_service.py | Implements the act command |\n"
            "| phase_detector.py | Detects phases |\n"
        )
        # ヘッダー行はスキップ、データ行 2 行がカウントされる
        assert PhaseDetector._count_meaningful_lines(content) == 2

    def test_nashi_bullet_not_counted(self, tmp_path: Path) -> None:
        """- なし（テンプレートの「なし」表現）はカウントしない。"""
        content = "- なし\n"
        assert PhaseDetector._count_meaningful_lines(content) == 0

    def test_none_bullet_not_counted(self, tmp_path: Path) -> None:
        """- none / - N/A も同様にカウントしない。"""
        assert PhaseDetector._count_meaningful_lines("- none\n") == 0
        assert PhaseDetector._count_meaningful_lines("- N/A\n") == 0

    def test_nashi_in_real_content_overall_still_meaningful(self, tmp_path: Path) -> None:
        """実コンテンツがある review.md は なし があっても meaningful と判定される。"""
        content = (
            "## Summary\n"
            "This build is excellent and meets all criteria.\n"
            "## Risks\n"
            "### Critical\n"
            "- なし\n"
            "### Major\n"
            "- なし\n"
        )
        # "This build is excellent..." の 1 行がカウントされる
        assert PhaseDetector._count_meaningful_lines(content) >= 1

    # -- テンプレートファイル実体テスト (dogfood 再発防止) --

    def test_build_template_not_has_any_content(self, tmp_path: Path) -> None:
        """init-run 直後の build.md テンプレートは has_any_content = False。"""
        content = (
            "# Build\n"
            "\n"
            "<!-- template -->\n"
            "\n"
            "---\n"
            "\n"
            "## Files changed\n"
            "\n"
            "| ファイル | 変更内容 |\n"
            "|---|---|\n"
            "| | |\n"
            "\n"
            "---\n"
            "\n"
            "## Decisions made\n"
            "\n"
            "-\n"
            "\n"
            "## Deviations from Plan\n"
            "\n"
            "- なし\n"
            "\n"
            "## Open Issues\n"
            "\n"
            "- [ ]\n"
        )
        _write(tmp_path / "build.md", content)
        d = PhaseDetector(tmp_path)
        assert d._has_any_content("build.md") is False

    def test_review_template_not_has_any_content(self, tmp_path: Path) -> None:
        """init-run 直後の review.md テンプレートは has_any_content = False。"""
        content = (
            "# Review\n"
            "\n"
            "<!-- template -->\n"
            "\n"
            "---\n"
            "\n"
            "## Summary of review\n"
            "\n"
            "---\n"
            "\n"
            "## Risks\n"
            "\n"
            "### Critical\n"
            "- なし\n"
            "\n"
            "### Major\n"
            "- なし\n"
            "\n"
            "### Minor\n"
            "- なし\n"
            "\n"
            "---\n"
            "\n"
            "## Weak Points\n"
            "\n"
            "-\n"
            "\n"
            "## Suggested Improvements\n"
            "\n"
            "- [ ] [High]\n"
            "- [ ] [Mid]\n"
            "- [ ] [Low]\n"
        )
        _write(tmp_path / "review.md", content)
        d = PhaseDetector(tmp_path)
        assert d._has_any_content("review.md") is False

    def test_build_with_real_content_has_any_content(self, tmp_path: Path) -> None:
        """実際の内容が入った build.md は has_any_content = True。"""
        content = (
            "# Build\n"
            "\n"
            "## Files changed\n"
            "\n"
            "| ファイル | 変更内容 |\n"
            "|---|---|\n"
            "| src/apsf/orchestration/phase_detector.py | _count_meaningful_lines を修正 |\n"
            "\n"
            "## Decisions made\n"
            "\n"
            "テーブルヘッダー行を enumerate で lookahead 判定する方式を採用した。\n"
        )
        _write(tmp_path / "build.md", content)
        d = PhaseDetector(tmp_path)
        assert d._has_any_content("build.md") is True

    def test_transcript_template_without_generated_is_unfilled(self, tmp_path: Path) -> None:
        """transcript.md テンプレート（'Generated:' なし）は unfilled と判定される。"""
        # runs/_template/transcript.md はテーブル行を含むが "Generated:" は含まない
        content = (
            "# Transcript\n"
            "\n"
            "| Phase | Role | Model |\n"
            "| --- | --- | --- |\n"
            "| Planner | human | -- |\n"
            "| Builder | human | -- |\n"
            "| Judge | human | -- |\n"
        )
        _write(tmp_path / "transcript.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("transcript.md") is False

    def test_transcript_with_generated_marker_is_filled(self, tmp_path: Path) -> None:
        """transcript.md に 'Generated:' が含まれていれば filled と判定される。"""
        content = (
            "# Transcript\n"
            "\n"
            "Generated: 2026-03-17T12:00:00\n"
            "\n"
            "## Summary\n"
            "Some content here.\n"
        )
        _write(tmp_path / "transcript.md", content)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("transcript.md") is True


# ---------------------------------------------------------------------------
# Template-state scenario tests (dogfood regression)
# ---------------------------------------------------------------------------

def _write_template_stub(run_dir: Path, filename: str) -> None:
    """テンプレート初期状態に近いスタブを書く（実質コンテンツなし）。"""
    content = (
        f"# {filename}\n"
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
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / filename).write_text(content, encoding="utf-8")


class TestTemplateStateScenarios:
    """start-run 直後の状態（テンプレートのみ）に関する回帰テスト。"""

    def test_fresh_run_with_all_templates_is_not_complete(
        self, tmp_path: Path
    ) -> None:
        """start-run 直後（全ファイルがテンプレート状態）では COMPLETE にならない。"""
        for fname in [
            "execution-assignment.md",
            "goal.md",
            "plan.md",
            "build.md",
            "review.md",
            "improve.md",
            "result.md",
            "transcript.md",
        ]:
            _write_template_stub(tmp_path, fname)
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase != Phase.COMPLETE

    def test_goal_filled_plan_template_returns_plan_needed(
        self, tmp_path: Path
    ) -> None:
        """goal.md だけ記入、plan.md がテンプレート状態 → PLAN_NEEDED になる。"""
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _write_template_stub(tmp_path, "plan.md")
        # build.md / review.md / improve.md / result.md もテンプレート状態
        for fname in ["build.md", "review.md", "improve.md", "result.md"]:
            _write_template_stub(tmp_path, fname)
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.PLAN_NEEDED

    def test_template_plan_and_build_are_unfilled(self, tmp_path: Path) -> None:
        """テンプレートコメントのみの plan.md / build.md は unfilled 扱い。"""
        for fname in ["plan.md", "build.md"]:
            _write_template_stub(tmp_path, fname)
        d = PhaseDetector(tmp_path)
        assert d._is_filled("plan.md") is False
        assert d._is_filled("build.md") is False

    def test_transcript_only_does_not_cause_complete(self, tmp_path: Path) -> None:
        """transcript.md が存在しても、他の主要ファイルが未記入なら COMPLETE にならない。"""
        _fill(tmp_path, "transcript.md")
        # 他のファイルはなし（または空）
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase != Phase.COMPLETE
        assert info.phase == Phase.SETUP_NEEDED

    def test_build_template_not_already_filled_after_plan_filled(
        self, tmp_path: Path
    ) -> None:
        """dogfood 再発防止: plan.md 充填後に build.md テンプレートが already_filled 扱いにならない。

        init-run 直後の build.md テンプレート（| ファイル | 変更内容 | 行を含む）で
        _has_any_content() が False を返すことを確認する。
        これが True だと `apsf act` が --force なしで already_filled 停止する。
        """
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        # build.md はテンプレートのまま（テーブルヘッダー行あり）
        build_template = (
            "# Build\n"
            "\n"
            "<!-- template -->\n"
            "\n"
            "---\n"
            "\n"
            "## Files changed\n"
            "\n"
            "| ファイル | 変更内容 |\n"
            "|---|---|\n"
            "| | |\n"
            "\n"
            "## Deviations from Plan\n"
            "\n"
            "- なし\n"
            "\n"
            "## Open Issues\n"
            "\n"
            "- [ ]\n"
        )
        _write(tmp_path / "build.md", build_template)
        d = PhaseDetector(tmp_path)
        # _has_any_content が False → apsf act は already_filled 停止しない
        assert d._has_any_content("build.md") is False
        # フェーズは BUILD_NEEDED のまま
        info = d.detect()
        assert info.phase == Phase.BUILD_NEEDED

    def test_exact_copied_template_file_is_not_treated_as_filled(
        self, tmp_path: Path
    ) -> None:
        """runs/_template と完全一致の copied file は filled 扱いしない。"""
        runs_root = tmp_path / "runs"
        template_dir = runs_root / "_template"
        run_dir = runs_root / "2099-01-01-001_test-case_template-copy"
        template_dir.mkdir(parents=True)
        run_dir.mkdir(parents=True)

        template_content = (
            "# Plan\n"
            "\n"
            "<!-- template comment -->\n"
            "\n"
            "## Problem Structure\n"
            "-\n"
            "- [ ] Step 1:\n"
        )
        (template_dir / "plan.md").write_text(template_content, encoding="utf-8")
        (run_dir / "plan.md").write_text(template_content, encoding="utf-8")

        d = PhaseDetector(run_dir)
        assert d._is_filled("plan.md") is False
        assert d._has_any_content("plan.md") is False

    def test_review_template_not_already_filled_after_build_filled(
        self, tmp_path: Path
    ) -> None:
        """dogfood 再発防止: build.md 充填後に review.md テンプレートが already_filled 扱いにならない。"""
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        # review.md はテンプレートのまま（- なし × 3 行を含む）
        review_template = (
            "# Review\n"
            "\n"
            "<!-- template -->\n"
            "\n"
            "## Risks\n"
            "\n"
            "### Critical\n"
            "- なし\n"
            "\n"
            "### Major\n"
            "- なし\n"
            "\n"
            "### Minor\n"
            "- なし\n"
            "\n"
            "- [ ] [High]\n"
            "- [ ] [Mid]\n"
        )
        _write(tmp_path / "review.md", review_template)
        d = PhaseDetector(tmp_path)
        assert d._has_any_content("review.md") is False
        info = d.detect()
        assert info.phase == Phase.REVIEW_NEEDED


# ---------------------------------------------------------------------------
# Phase transitions
# ---------------------------------------------------------------------------

class TestPhaseDetection:
    def test_empty_run_dir_returns_setup_needed(self, tmp_path: Path) -> None:
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.SETUP_NEEDED

    def test_only_comments_in_execution_assignment_returns_setup_needed(
        self, tmp_path: Path
    ) -> None:
        _fill_comments_only(tmp_path, "execution-assignment.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.SETUP_NEEDED

    def test_execution_assignment_filled_no_goal_returns_goal_needed(
        self, tmp_path: Path
    ) -> None:
        _fill(tmp_path, "execution-assignment.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.GOAL_NEEDED

    def test_goal_filled_no_plan_returns_plan_needed(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.PLAN_NEEDED

    def test_plan_filled_no_build_returns_build_needed(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.BUILD_NEEDED

    def test_build_filled_no_review_returns_review_needed(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.REVIEW_NEEDED

    def test_review_filled_no_improve_returns_improve_needed(
        self, tmp_path: Path
    ) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.IMPROVE_NEEDED

    def test_improve_filled_no_result_returns_result_needed(
        self, tmp_path: Path
    ) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill(tmp_path, "improve.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.RESULT_NEEDED

    def test_result_filled_no_transcript_returns_transcript_recommended(
        self, tmp_path: Path
    ) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill(tmp_path, "improve.md")
        _fill(tmp_path, "result.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.TRANSCRIPT_RECOMMENDED

    def test_all_files_filled_returns_complete(self, tmp_path: Path) -> None:
        for f in [
            "execution-assignment.md",
            "goal.md",
            "plan.md",
            "build.md",
            "review.md",
            "improve.md",
            "result.md",
            "transcript.md",
        ]:
            _fill(tmp_path, f)
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.COMPLETE


# ---------------------------------------------------------------------------
# PhaseInfo content checks
# ---------------------------------------------------------------------------

class TestPhaseInfoContent:
    def test_setup_needed_has_human_as_next_role(self, tmp_path: Path) -> None:
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.next_role == "Human"
        assert info.file_to_write == "execution-assignment.md"

    def test_plan_needed_has_handoff_hint(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.PLAN_NEEDED
        assert info.handoff_hint is not None
        assert "handoff" in info.handoff_hint.lower()

    def test_build_needed_has_handoff_hint(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.BUILD_NEEDED
        assert info.handoff_hint is not None

    def test_complete_has_no_files_to_read(self, tmp_path: Path) -> None:
        for f in [
            "execution-assignment.md",
            "goal.md",
            "plan.md",
            "build.md",
            "review.md",
            "improve.md",
            "result.md",
            "transcript.md",
        ]:
            _fill(tmp_path, f)
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.COMPLETE
        assert info.files_to_read == []

    def test_evidence_is_nonempty_for_all_phases(self, tmp_path: Path) -> None:
        """全フェーズで evidence が空でないことを確認する。"""
        phases_files: list[list[str]] = [
            [],  # SETUP_NEEDED
            ["execution-assignment.md"],  # GOAL_NEEDED
            ["execution-assignment.md", "goal.md"],  # PLAN_NEEDED
            ["execution-assignment.md", "goal.md", "plan.md"],  # BUILD_NEEDED
            ["execution-assignment.md", "goal.md", "plan.md", "build.md"],  # REVIEW_NEEDED
            ["execution-assignment.md", "goal.md", "plan.md", "build.md", "review.md"],  # IMPROVE
            ["execution-assignment.md", "goal.md", "plan.md", "build.md", "review.md", "improve.md"],
            ["execution-assignment.md", "goal.md", "plan.md", "build.md", "review.md", "improve.md", "result.md"],
            ["execution-assignment.md", "goal.md", "plan.md", "build.md", "review.md", "improve.md", "result.md", "transcript.md"],
        ]
        for files in phases_files:
            run_dir = tmp_path / "_".join(files[:1] or ["empty"])
            run_dir.mkdir(exist_ok=True)
            for f in files:
                _fill(run_dir, f)
            d = PhaseDetector(run_dir)
            info = d.detect()
            assert len(info.evidence) > 0, f"evidence empty for files={files}"


# ---------------------------------------------------------------------------
# Debug fields (existing_files / filled_files / unfilled_files / decision_reason)
# ---------------------------------------------------------------------------

class TestDebugFields:
    def test_existing_files_populated(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert "execution-assignment.md" in info.existing_files
        assert "goal.md" in info.existing_files

    def test_filled_files_subset_of_existing(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill_comments_only(tmp_path, "goal.md")  # exists but unfilled
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert "execution-assignment.md" in info.filled_files
        assert "goal.md" not in info.filled_files
        assert "goal.md" in info.unfilled_files

    def test_unfilled_files_are_existing_minus_filled(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill_comments_only(tmp_path, "plan.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert set(info.unfilled_files) == set(info.existing_files) - set(info.filled_files)

    def test_decision_reason_nonempty(self, tmp_path: Path) -> None:
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.decision_reason != ""

    def test_decision_reason_mentions_deciding_file(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.PLAN_NEEDED
        assert "plan.md" in info.decision_reason

    def test_complete_has_nonempty_debug_fields(self, tmp_path: Path) -> None:
        for f in [
            "execution-assignment.md", "goal.md", "plan.md",
            "build.md", "review.md", "improve.md",
            "result.md", "transcript.md",
        ]:
            _fill(tmp_path, f)
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.COMPLETE
        assert len(info.filled_files) > 0
        assert info.decision_reason != ""


# ---------------------------------------------------------------------------
# Optional phases (IMPROVE_PLAN_OPTIONAL / VERIFY_OPTIONAL)
# ---------------------------------------------------------------------------

class TestOptionalPhases:
    def test_improve_plan_optional_triggers_after_review(
        self, tmp_path: Path
    ) -> None:
        """v0.2 フロー: review.md 充填後 + improve-plan.md 未充填 → IMPROVE_PLAN_OPTIONAL。
        IMPROVE_PLAN_OPTIONAL は Plan→Build 間ではなく Review→Improve 間に位置する。
        """
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill_comments_only(tmp_path, "improve-plan.md")  # exists but unfilled
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.IMPROVE_PLAN_OPTIONAL

    def test_improve_plan_optional_not_triggered_before_review(
        self, tmp_path: Path
    ) -> None:
        """v0.1 フロー: review.md 未充填の時点では improve-plan.md が未充填でも BUILD_NEEDED。
        init-run 直後のテンプレート improve-plan.md は IMPROVE_PLAN_OPTIONAL を発火させない。
        """
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill_comments_only(tmp_path, "improve-plan.md")  # exists but unfilled
        d = PhaseDetector(tmp_path)
        info = d.detect()
        # review.md がないため IMPROVE_PLAN_OPTIONAL にはならず BUILD_NEEDED
        assert info.phase == Phase.BUILD_NEEDED

    def test_improve_plan_optional_skipped_when_file_absent(
        self, tmp_path: Path
    ) -> None:
        # review.md filled, NO improve-plan.md → normal IMPROVE_NEEDED
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.IMPROVE_NEEDED

    def test_improve_plan_optional_skipped_when_already_filled(
        self, tmp_path: Path
    ) -> None:
        # review.md filled, improve-plan.md already filled → IMPROVE_NEEDED
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill(tmp_path, "improve-plan.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.IMPROVE_NEEDED

    def test_verify_optional_triggers_when_file_exists_unfilled(
        self, tmp_path: Path
    ) -> None:
        # improve.md filled, verify.md exists but unfilled, result.md absent
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill(tmp_path, "improve.md")
        _fill_comments_only(tmp_path, "verify.md")  # exists but unfilled
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.VERIFY_OPTIONAL

    def test_verify_optional_skipped_when_file_absent(self, tmp_path: Path) -> None:
        # improve.md filled, NO verify.md → normal RESULT_NEEDED
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill(tmp_path, "improve.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.RESULT_NEEDED

    def test_verify_optional_skipped_when_already_filled(
        self, tmp_path: Path
    ) -> None:
        # verify.md already filled → go to RESULT_NEEDED
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill(tmp_path, "improve.md")
        _fill(tmp_path, "verify.md")
        d = PhaseDetector(tmp_path)
        info = d.detect()
        assert info.phase == Phase.RESULT_NEEDED
