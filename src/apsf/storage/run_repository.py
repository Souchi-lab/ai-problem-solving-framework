"""
RunRepository — run ディレクトリの初期化・管理

runs/ 以下のディレクトリ構造を扱う。
_template/ からのコピー、標準ファイルパスの取得、run 一覧の取得などを担当する。
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Optional


# run 命名規則のパターン: YYYY-MM-DD_case-key_topic
_RUN_NAME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_[a-z0-9-]+_[a-z0-9-]+$")

# run 内の標準ファイル一覧（順序が workflow の順番に対応）
STANDARD_FILES = [
    "execution-assignment.md",
    "model-assignment.md",
    "goal.md",
    "plan.md",
    "handoff.md",
    "build.md",
    "review.md",
    "improve.md",
    "result.md",
]

# オプションファイル一覧（参照用: init_run では生成しない）
#
# 生成タイミング:
#   - improve-plan.md : ユーザーが v0.2 フローを使う場合に手動作成
#   - verify.md       : ユーザーが v0.2 フローを使う場合に手動作成
#   - transcript.md   : `apsf transcript` コマンドが result.md 完了後に自動生成
#
# IMPROVE_PLAN_OPTIONAL / VERIFY_OPTIONAL フェーズは、
# これらのファイルが run ディレクトリに存在する場合にのみ発火する。
OPTIONAL_FILES: list[str] = [
    "improve-plan.md",  # v0.2: Improve Plan フェーズ（手動作成）
    "verify.md",        # v0.2: Verify フェーズ（手動作成）
    "transcript.md",    # result.md 完了後に `apsf transcript` が生成
]


class RunRepository:
    """
    runs/ ディレクトリの管理クラス。

    使用例:
        repo = RunRepository(runs_dir=Path("runs"), template_dir=Path("runs/_template"))
        repo.init_run("2026-03-15_sochi-blocks_sns-post-template")
        path = repo.get_file_path("2026-03-15_sochi-blocks_sns-post-template", "goal.md")
    """

    def __init__(self, runs_dir: Path, template_dir: Path):
        self._runs_dir = runs_dir
        self._template_dir = template_dir

    @property
    def runs_dir(self) -> Path:
        return self._runs_dir

    def validate_run_name(self, run_name: str) -> bool:
        """命名規則 YYYY-MM-DD_case-key_topic に従っているかを確認する。"""
        return bool(_RUN_NAME_PATTERN.match(run_name))

    def init_run(self, run_name: str, force: bool = False) -> Path:
        """
        _template/ をコピーして新しい run ディレクトリを作成する。

        Args:
            run_name: runs/ 以下に作成するフォルダ名
            force: True の場合、既存ディレクトリを上書きする

        Returns:
            作成した run ディレクトリの Path

        Raises:
            ValueError: 命名規則違反
            FileExistsError: すでに存在する（force=False の場合）
        """
        if not self.validate_run_name(run_name):
            raise ValueError(
                f"Invalid run name: '{run_name}'\n"
                "Expected format: YYYY-MM-DD_case-key_topic\n"
                "Example: 2026-03-15_sochi-blocks_sns-post-template"
            )

        run_dir = self._runs_dir / run_name

        if run_dir.exists() and not force:
            raise FileExistsError(
                f"Run directory already exists: {run_dir}\n"
                "Use force=True to overwrite."
            )

        if not self._template_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found: {self._template_dir}"
            )

        if run_dir.exists():
            shutil.rmtree(run_dir)

        shutil.copytree(self._template_dir, run_dir)
        return run_dir

    def get_run_dir(self, run_name: str) -> Path:
        """run ディレクトリの Path を返す（存在確認なし）。"""
        return self._runs_dir / run_name

    def get_file_path(self, run_name: str, filename: str) -> Path:
        """runs/<run_name>/<filename> の Path を返す（存在確認なし）。"""
        return self._runs_dir / run_name / filename

    def run_exists(self, run_name: str) -> bool:
        """run ディレクトリが存在するかどうかを返す。"""
        return (self._runs_dir / run_name).is_dir()

    def list_runs(self) -> list[str]:
        """runs/ 以下の全 run 名を返す（_template を除く）。"""
        if not self._runs_dir.exists():
            return []
        return [
            d.name
            for d in sorted(self._runs_dir.iterdir())
            if d.is_dir() and d.name != "_template"
        ]

    def get_run_status(self, run_name: str) -> dict[str, bool]:
        """
        run 内の標準ファイルの存在状況を返す。
        result.md があれば完了とみなせる。
        """
        run_dir = self._runs_dir / run_name
        return {filename: (run_dir / filename).exists() for filename in STANDARD_FILES}

    def is_completed(self, run_name: str) -> bool:
        """result.md が存在する場合に完了とみなす。"""
        return (self._runs_dir / run_name / "result.md").exists()

    def format_run_name(self, date: str, case_key: str, topic: str) -> str:
        """
        命名規則に従った run 名を生成する。

        Args:
            date: YYYY-MM-DD 形式
            case_key: ケース名（kebab-case）
            topic: テーマ（kebab-case）

        Example:
            format_run_name("2026-03-15", "sochi-blocks", "sns-post-template")
            → "2026-03-15_sochi-blocks_sns-post-template"
        """
        return f"{date}_{case_key}_{topic}"
