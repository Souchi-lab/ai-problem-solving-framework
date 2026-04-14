"""
TranscriptGenerator — run ディレクトリの md ファイルから transcript.md を生成する

run 内の一次記録ファイル群を所定順に連結し、
run 全体の流れを後から追いやすい可読化文書として出力する。

使用例:
    from apsf.legacy.orchestration.transcript_generator import TranscriptGenerator

    gen = TranscriptGenerator()
    path = gen.write(Path("runs/2026-03-15_sochi-blocks_sns-post-template"))
    print(f"Written to: {path}")
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ...core.storage.artifact_repository import ArtifactRepository
from ...core.storage.text_artifact_codec import read_text_artifact


# transcript に含めるファイルの順序定義
# (filename, セクション見出しラベル)
# 存在しないファイルは自動的にスキップされる
TRANSCRIPT_SOURCE_ORDER: list[tuple[str, str]] = [
    ("execution-assignment.md", "Execution Assignment"),
    ("goal.md",                 "Goal"),
    ("plan.md",                 "Plan"),
    ("improve-plan.md",         "Improve Plan"),           # v0.2: なければスキップ
    ("plan_review.md",          "Plan Review (Rework)"),      # Added for completeness
    ("build.md",                "Build"),
    ("build_review.md",         "Build Review (Rework)"),     # Added for completeness
    ("review.md",               "Review"),
    ("review_review.md",        "Review Review (Rework)"),    # User added
    ("handoff.md",              "Handoff"),
    ("verify.md",               "Verify"),                 # v0.2: なければスキップ
    ("improve_review.md",       "Judge Review (Rework)"),     # User added
    ("improve.md",              "Improve / Judge Decision"),
    ("result.md",               "Result"),
]

# transcript 自身は入力対象外
_EXCLUDED_FILENAME = "transcript.md"


class TranscriptGenerator:
    def __init__(self) -> None:
        self._artifact_repo = ArtifactRepository()

    """
    run ディレクトリ内の md ファイルから transcript.md を生成する。

    - TRANSCRIPT_SOURCE_ORDER の順でファイルを処理
    - 存在しないファイルはスキップ
    - transcript.md 自身は入力対象にしない
    - 将来的に出力フォーマット（HTML 等）への拡張は write() を差し替えることで対応可能
    """

    def generate(self, run_dir: Path, run_name: str = "") -> str:
        """
        run_dir 内のファイルを連結して transcript.md の内容文字列を生成する。

        Args:
            run_dir:  run ディレクトリの Path
            run_name: transcript 見出しに使用する run 名（省略時は run_dir.name）

        Returns:
            transcript.md として書き込む Markdown 文字列
        """
        name = run_name or run_dir.name
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        sections: list[str] = []

        # ヘッダー
        sections.append(f"# Transcript: {name}\n")
        sections.append(f"Generated: {generated_at}\n")
        sections.append(
            "\n> このファイルは自動生成された二次成果物です。\n"
            "> 正確な情報は各 .md ファイル（一次記録）を参照してください。\n"
        )

        # 各ソースファイルをセクションとして追加
        included_count = 0
        for filename, label in TRANSCRIPT_SOURCE_ORDER:
            if filename == _EXCLUDED_FILENAME:
                continue
            path = run_dir / filename
            if not path.exists():
                continue

            content = read_text_artifact(path).strip()
            if not content:
                continue

            sections.append(f"\n---\n\n## {label}\n\n{content}\n")
            included_count += 1

        if included_count == 0:
            sections.append("\n---\n\n*No source files found.*\n")

        return "\n".join(sections)

    def write(self, run_dir: Path, run_name: str = "") -> Path:
        """
        transcript.md を run_dir に書き込む。

        既存の transcript.md は上書きする。

        Returns:
            書き込んだファイルの Path
        """
        content = self.generate(run_dir, run_name)
        output_path = run_dir / _EXCLUDED_FILENAME
        return self._artifact_repo.write(output_path, content)

    def list_sources(self, run_dir: Path) -> list[tuple[str, bool]]:
        """
        TRANSCRIPT_SOURCE_ORDER に沿ったファイル存在状況を返す。

        Returns:
            [(filename, exists), ...]
        """
        return [
            (filename, (run_dir / filename).exists())
            for filename, _ in TRANSCRIPT_SOURCE_ORDER
            if filename != _EXCLUDED_FILENAME
        ]
