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


# run 命名規則のパターン: YYYY-MM-DD_case-key_topic または YYYY-MM-DD-NNN_case-key_topic
_RUN_NAME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(-\d+)?(_[a-z0-9-]+){2,}$")

# child run 命名規則のパターン: NNNcN_case-key_topic（親番号3桁以上 + c + 連番）
_CHILD_RUN_NAME_PATTERN = re.compile(r"^\d{3,}c\d+(_[a-z0-9-]+){2,}$")

# taxonomy ディレクトリ名（lookup 優先順）
_TAXONOMY_DIRS: tuple[str, ...] = ("fw-improvement", "work", "verification")

# completion semantics: state-first, result.md fallback
_COMPLETE_PHASES = frozenset({"COMPLETE", "TRANSCRIPT_RECOMMENDED"})


def _is_run_dir_completed(run_dir: Path) -> bool:
    """
    run ディレクトリが完了しているかを state-first で判定する。

    1. run_state.json が存在する場合 → current_phase が COMPLETE / TRANSCRIPT_RECOMMENDED なら True
    2. run_state.json が存在しない場合（legacy / bootstrap 前）→ result.md exists でフォールバック
    """
    from apsf.core.state.run_state_repository import RunStateRepository
    state = RunStateRepository(run_dir).load()
    if state is not None:
        return state.current_phase in _COMPLETE_PHASES
    return (run_dir / "result.md").exists()

# run 内の標準ファイル一覧（順序が workflow の順番に対応）
STANDARD_FILES = [
    "execution-assignment.md",
    "goal.md",
    "plan.md",
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
    "model-assignment.md",  # conditional: record only when model choice matters
    "handoff.md",          # conditional: create only when transfer context is needed
    "plan_review.md",   # optional: re-plan feedback for Planner
    "build_review.md",  # optional: re-build feedback for Builder
    "review_review.md", # optional: re-review feedback for Critic
    "improve_review.md",# optional: re-improve feedback for Judge
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

    def _resolve_run_root(self, run_name: str, taxonomy: Optional[str]) -> Path:
        """
        run_name の実際のディレクトリ Path を返す。

        taxonomy 指定時: runs/<taxonomy>/<run_name>（存在確認なし）
        taxonomy=None 時:
          - child run（_CHILD_RUN_NAME_PATTERN に一致）: 各 taxonomy dir の直下を
            走査して runs/<tax>/<parent>/<run_name> を探す。見つからなければ legacy。
          - top-level run: fw-improvement → work → legacy の順で探索する。
            見つからなければ legacy パスを返す。
        """
        if taxonomy is not None:
            return self._runs_dir / taxonomy / run_name
        # child run: taxonomy dirs 配下の parent ディレクトリを走査
        # 同名 child が複数の parent に存在する場合は taxonomy 優先順 × ソート順最初を返す
        if _CHILD_RUN_NAME_PATTERN.match(run_name):
            for tax in _TAXONOMY_DIRS:
                tax_dir = self._runs_dir / tax
                if not tax_dir.is_dir():
                    continue
                for parent_dir in sorted(tax_dir.iterdir()):
                    if not parent_dir.is_dir():
                        continue
                    candidate = parent_dir / run_name
                    if candidate.is_dir():
                        return candidate
            return self._runs_dir / run_name
        # top-level run: taxonomy fallback
        for tax in _TAXONOMY_DIRS:
            candidate = self._runs_dir / tax / run_name
            if candidate.is_dir():
                return candidate
        return self._runs_dir / run_name

    def validate_run_name(self, run_name: str) -> bool:
        """命名規則 YYYY-MM-DD_case-key_topic または YYYY-MM-DD-NNN_case-key_topic を確認する。"""
        return bool(_RUN_NAME_PATTERN.match(run_name))

    def next_run_seq(self, date: str, taxonomy: Optional[str] = None) -> int:
        """
        指定日の top-level run の次連番を返す。

        番号なし形式（YYYY-MM-DD_case-key_topic）は seq=0 とみなす。
        返却値は 1 始まり。
        """
        date_prefix = f"{date}_"
        seq_prefix = f"{date}-"
        max_seq = 0

        for name in self.list_all_runs(taxonomy=taxonomy):
            if "/" in name:
                continue
            if name.startswith(date_prefix):
                max_seq = max(max_seq, 0)
                continue
            if not name.startswith(seq_prefix):
                continue

            rest = name[len(seq_prefix):]
            seq_str, sep, _ = rest.partition("_")
            if sep and seq_str.isdigit():
                max_seq = max(max_seq, int(seq_str))

        return max_seq + 1

    def init_run(
        self,
        run_name: str,
        force: bool = False,
        taxonomy: Optional[str] = None,
    ) -> Path:
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
                "Expected format: YYYY-MM-DD_case-key_topic or YYYY-MM-DD-NNN_case-key_topic\n"
                "Example: 2026-03-15-001_sochi-blocks_sns-post-template"
            )

        if taxonomy is not None:
            run_dir = self._runs_dir / taxonomy / run_name
            run_dir.parent.mkdir(parents=True, exist_ok=True)
        else:
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

    def get_run_dir(self, run_name: str, taxonomy: Optional[str] = None) -> Path:
        """run ディレクトリの Path を返す（存在確認なし）。"""
        return self._resolve_run_root(run_name, taxonomy)

    def get_file_path(
        self, run_name: str, filename: str, taxonomy: Optional[str] = None
    ) -> Path:
        """run 内のファイルの Path を返す（存在確認なし）。"""
        return self._resolve_run_root(run_name, taxonomy) / filename

    def run_exists(self, run_name: str, taxonomy: Optional[str] = None) -> bool:
        """run ディレクトリが存在するかどうかを返す。"""
        return self._resolve_run_root(run_name, taxonomy).is_dir()

    def list_runs(self, taxonomy: Optional[str] = None) -> list[str]:
        """
        run 名一覧を返す（_template を除く）。

        taxonomy 指定時: runs/<taxonomy>/ 配下のみを返す。
        taxonomy=None 時: fw-improvement → work → legacy を横断して全 run を返す。
                          同名共存時は taxonomy 配下を優先（重複排除）。

        注意: taxonomy=None の挙動は旧 API（runs/ 直下列挙）とは異なる仕様更新。
        """
        if not self._runs_dir.exists():
            return []
        if taxonomy is not None:
            tax_dir = self._runs_dir / taxonomy
            if not tax_dir.exists():
                return []
            return [d.name for d in sorted(tax_dir.iterdir()) if d.is_dir()]
        # taxonomy=None: 全横断（fw-improvement → work → legacy）
        result: list[str] = []
        seen: set[str] = set()
        for tax in _TAXONOMY_DIRS:
            tax_dir = self._runs_dir / tax
            if tax_dir.exists():
                for d in sorted(tax_dir.iterdir()):
                    if d.is_dir() and d.name not in seen:
                        result.append(d.name)
                        seen.add(d.name)
        for d in sorted(self._runs_dir.iterdir()):
            if (
                d.is_dir()
                and d.name != "_template"
                and d.name not in _TAXONOMY_DIRS
                and d.name not in seen
            ):
                result.append(d.name)
                seen.add(d.name)
        return result

    def get_run_status(
        self, run_name: str, taxonomy: Optional[str] = None
    ) -> dict[str, bool]:
        """
        run 内の標準ファイルの存在状況を返す。
        result.md があれば完了とみなせる。

        NOTE: この判定はファイル存在（file-based）に基づいており、run_state.json を参照しない。
        run_state との一貫性は result.md 書込み時に ActService が run_state を更新することで担保される。
        """
        run_dir = self._resolve_run_root(run_name, taxonomy)
        return {filename: (run_dir / filename).exists() for filename in STANDARD_FILES}

    def is_completed(self, run_name: str, taxonomy: Optional[str] = None) -> bool:
        """
        run_state.json が存在する場合は current_phase が COMPLETE / TRANSCRIPT_RECOMMENDED なら完了。
        run_state.json が存在しない場合（legacy / bootstrap 前）は result.md exists でフォールバック。
        """
        return _is_run_dir_completed(self._resolve_run_root(run_name, taxonomy))

    def validate_child_run_name(self, name: str) -> bool:
        """命名規則 NNNcN_case-key_topic に従っているかを確認する。"""
        return bool(_CHILD_RUN_NAME_PATTERN.match(name))

    def format_child_run_name(
        self,
        parent_num: str,
        seq: int,
        case_key: str,
        topic: str,
    ) -> str:
        """
        child run 命名規則に従った run 名を生成する。

        Args:
            parent_num: 親 run の番号文字列（ゼロ埋め桁数は呼び出し側の責務）
            seq: child の連番（1 始まり）
            case_key: ケース名（kebab-case）
            topic: テーマ（kebab-case）

        Example:
            format_child_run_name("016", 1, "sochi-blocks", "x-thread-content")
            → "016c1_sochi-blocks_x-thread-content"
        """
        return f"{parent_num}c{seq}_{case_key}_{topic}"

    def get_child_run_dir(
        self, parent_name: str, child_name: str, taxonomy: Optional[str] = None
    ) -> Path:
        """runs/[taxonomy/]parent_name/child_name の Path を返す（存在確認なし）。"""
        return self._resolve_run_root(parent_name, taxonomy) / child_name

    def get_child_file_path(
        self,
        parent_name: str,
        child_name: str,
        filename: str,
        taxonomy: Optional[str] = None,
    ) -> Path:
        """runs/[taxonomy/]parent_name/child_name/filename の Path を返す（存在確認なし）。"""
        return self._resolve_run_root(parent_name, taxonomy) / child_name / filename

    def list_child_runs(
        self, parent_name: str, taxonomy: Optional[str] = None
    ) -> list[str]:
        """
        指定した parent_name 配下の child run 名一覧を返す。
        parent が存在しない場合は空リストを返す（例外なし）。
        返却値は child run 名のみ（"parent/" プレフィックスなし）。
        """
        parent_dir = self._resolve_run_root(parent_name, taxonomy)
        if not parent_dir.is_dir():
            return []
        return [
            d.name
            for d in sorted(parent_dir.iterdir())
            if d.is_dir() and self.validate_child_run_name(d.name)
        ]

    def list_all_runs(self, taxonomy: Optional[str] = None) -> list[str]:
        """
        全 run を返す。top-level run は run 名のみ、child run は "parent/child" 形式。

        taxonomy 指定時: runs/<taxonomy>/ 配下のみ。
        taxonomy=None 時: fw-improvement → work → legacy を横断して全 run を返す。
                          同名共存時は taxonomy 配下を優先（重複排除）。

        注意: この返却値は discovery / UI 向けの表示形式であり、
        repository 内部の正規識別子ではない。
        child run の path 解決には get_child_run_dir(parent_name, child_name) を使うこと。
        """
        if not self._runs_dir.exists():
            return []
        result: list[str] = []

        if taxonomy is not None:
            tax_dir = self._runs_dir / taxonomy
            if not tax_dir.exists():
                return []
            for top in sorted(tax_dir.iterdir()):
                if not top.is_dir():
                    continue
                result.append(top.name)
                for child in sorted(top.iterdir()):
                    if child.is_dir() and self.validate_child_run_name(child.name):
                        result.append(f"{top.name}/{child.name}")
            return result

        # taxonomy=None: 全横断（fw-improvement → work → legacy）
        seen: set[str] = set()
        for tax in _TAXONOMY_DIRS:
            tax_dir = self._runs_dir / tax
            if not tax_dir.exists():
                continue
            for top in sorted(tax_dir.iterdir()):
                if not top.is_dir() or top.name in seen:
                    continue
                seen.add(top.name)
                result.append(top.name)
                for child in sorted(top.iterdir()):
                    if child.is_dir() and self.validate_child_run_name(child.name):
                        result.append(f"{top.name}/{child.name}")
        # legacy: runs/ direct children（_template と taxonomy dirs を除く）
        for top in sorted(self._runs_dir.iterdir()):
            if (
                not top.is_dir()
                or top.name == "_template"
                or top.name in _TAXONOMY_DIRS
                or top.name in seen
            ):
                continue
            seen.add(top.name)
            result.append(top.name)
            for child in sorted(top.iterdir()):
                if child.is_dir() and self.validate_child_run_name(child.name):
                    result.append(f"{top.name}/{child.name}")
        return result

    def init_child_run(
        self,
        parent_name: str,
        child_name: str,
        *,
        force: bool = False,
        taxonomy: Optional[str] = None,
    ) -> Path:
        """
        parent run ディレクトリ直下に child run を作成する。

        Args:
            parent_name: 既存の top-level run 名
            child_name: 作成する child run 名
            force: True の場合、既存ディレクトリを上書きする
            taxonomy: parent run の taxonomy（None の場合は fallback 探索）

        Returns:
            作成した child run ディレクトリの Path

        Raises:
            ValueError: parent_name または child_name の命名規則違反
            FileNotFoundError: parent run ディレクトリが存在しない
            FileExistsError: child run がすでに存在する（force=False の場合）
        """
        # V-1: parent 名の命名規則確認
        if not self.validate_run_name(parent_name):
            raise ValueError(
                f"Invalid parent run name: '{parent_name}'\n"
                "Expected format: YYYY-MM-DD_case-key_topic or YYYY-MM-DD-NNN_case-key_topic"
            )
        # V-2: parent ディレクトリの存在確認（taxonomy-aware）
        parent_dir = self._resolve_run_root(parent_name, taxonomy)
        if not parent_dir.is_dir():
            raise FileNotFoundError(
                f"Parent run directory not found: {parent_dir}"
            )
        # V-3: child 名の命名規則確認
        if not self.validate_child_run_name(child_name):
            raise ValueError(
                f"Invalid child run name: '{child_name}'\n"
                "Expected format: NNNcN_case-key_topic\n"
                "Example: 016c1_sochi-blocks_x-thread-content"
            )
        # V-4: 重複確認
        child_dir = parent_dir / child_name
        if child_dir.exists() and not force:
            raise FileExistsError(
                f"Child run already exists: {child_dir}\n"
                "Use force=True to overwrite."
            )

        if not self._template_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found: {self._template_dir}"
            )

        if child_dir.exists():
            shutil.rmtree(child_dir)

        shutil.copytree(self._template_dir, child_dir)
        return child_dir

    def child_run_exists(
        self, parent_name: str, child_name: str, taxonomy: Optional[str] = None
    ) -> bool:
        """child run ディレクトリが存在するかどうかを返す。"""
        return self.get_child_run_dir(parent_name, child_name, taxonomy).is_dir()

    def get_child_run_status(
        self, parent_name: str, child_name: str, taxonomy: Optional[str] = None
    ) -> dict[str, bool]:
        """
        child run 内の標準ファイルの存在状況を返す。
        result.md があれば完了とみなせる。

        NOTE: file-based 判定。run_state.json を参照しない（get_run_status と同様）。
        """
        child_dir = self.get_child_run_dir(parent_name, child_name, taxonomy)
        return {filename: (child_dir / filename).exists() for filename in STANDARD_FILES}

    def is_child_completed(
        self, parent_name: str, child_name: str, taxonomy: Optional[str] = None
    ) -> bool:
        """
        run_state.json が存在する場合は current_phase が COMPLETE / TRANSCRIPT_RECOMMENDED なら完了。
        run_state.json が存在しない場合（legacy / bootstrap 前）は result.md exists でフォールバック。
        """
        return _is_run_dir_completed(self.get_child_run_dir(parent_name, child_name, taxonomy))

    def format_run_name(
        self, date: str, case_key: str, topic: str, seq: Optional[int] = None
    ) -> str:
        """
        命名規則に従った run 名を生成する。

        Args:
            date: YYYY-MM-DD 形式
            case_key: ケース名（kebab-case）
            topic: テーマ（kebab-case）

        Example:
            format_run_name("2026-03-15", "sochi-blocks", "sns-post-template")
            → "2026-03-15_sochi-blocks_sns-post-template"
            format_run_name("2026-03-15", "sochi-blocks", "sns-post-template", seq=1)
            → "2026-03-15-001_sochi-blocks_sns-post-template"
        """
        if seq is None:
            return f"{date}_{case_key}_{topic}"
        return f"{date}-{seq:03d}_{case_key}_{topic}"
