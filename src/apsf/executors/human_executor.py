"""
HumanExecutor — 人間が手動で実行する executor

「実行」とは、人間に対して「何をすべきか」の指示を返すこと。
コードは実際に何かを実行しない — 人間が正しいアクションを取るための指示を生成する。

Planner / Judge などの役割には人間が入ることで品質が安定する。
HumanExecutor はその「人間介入」をコード上でも表現する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..domain.models import ExecutionType, Role
from .base import BaseExecutor, ExecuteRequest, ExecuteResponse


# role ごとの出力ファイル名
_ROLE_OUTPUT_FILE: dict[Role, str] = {
    Role.PLANNER:       "plan.md",
    Role.JUNIOR_BUILDER: "build.md",
    Role.BUILDER:       "build.md",
    Role.CRITIC:        "review.md",
    Role.JUDGE:         "improve.md",
    Role.HUMAN:         "result.md",
}

# role ごとの handoff 残留ガイダンス
_ROLE_HANDOFF_GUIDE: dict[Role, list[str]] = {
    Role.PLANNER: [
        "決定事項: 問題の構造・解くべきサブタスクの一覧",
        "未解決: 判断が必要な制約・前提条件の曖昧な点",
        "Builder へ: 最優先タスク・品質基準・避けるべきアプローチ",
    ],
    Role.JUNIOR_BUILDER: [
        "決定事項: ドラフトの構造・試したアプローチの一覧",
        "未解決: 品質改善が必要な点・Builder に委ねる判断",
        "Builder へ: ドラフトの位置づけ・流用できる部分・捨てるべき部分",
    ],
    Role.BUILDER: [
        "決定事項: 成果物の内容・採用したアプローチと理由",
        "未解決: Critic に確認してほしい点・代替案の候補",
        "Critic へ: 評価の重点ポイント・懸念している箇所・比較軸",
    ],
    Role.CRITIC: [
        "決定事項: 問題点の一覧・重大度・修正が必要な箇所",
        "未解決: Judge に委ねる採用可否の判断",
        "Judge へ: 最重要指摘事項・推奨アクション（採用 / 修正 / 却下）",
    ],
    Role.JUDGE: [
        "決定事項: 採用・修正依頼・却下 の判断と理由",
        "未解決: 次サイクルで改善すべき点（result.md に記録）",
        "次へ: 採用なら result.md 作成、修正依頼なら Builder に差し戻し",
    ],
}


class HumanExecutor(BaseExecutor):
    """
    人間が手動で実行することを表現する executor。

    execute() は実際に何かを処理するのではなく、
    「何をすべきか」の指示テキストを生成して返す。

    使用例:
        executor = HumanExecutor(role=Role.PLANNER)
        response = executor.execute(ExecuteRequest(prompt="..."))
        # response.content に「plan.md を書くための手順」が入る
    """

    def __init__(self, role: Optional[Role] = None):
        """
        Args:
            role: この executor が担当する role（指示内容のカスタマイズに使う）
        """
        self._role = role

    @property
    def execution_type(self) -> ExecutionType:
        return ExecutionType.HUMAN

    def execute(self, request: ExecuteRequest) -> ExecuteResponse:
        """
        人間への実行指示を生成する。
        dry_run の有無に関係なく同じ内容を返す（人間が実行するため）。
        """
        instruction = self._build_instruction(request)
        return ExecuteResponse(
            content=instruction,
            execution_type=self.execution_type,
            success=True,
            dry_run=request.dry_run,
        )

    def _build_instruction(self, request: ExecuteRequest) -> str:
        """人間への実行指示テキストを生成する"""
        role_label = self._role.value.upper() if self._role else "HUMAN"
        output_file = _ROLE_OUTPUT_FILE.get(self._role, "<output>.md") if self._role else "<output>.md"
        handoff_items = _ROLE_HANDOFF_GUIDE.get(self._role, []) if self._role else []

        lines = [
            f"=== Human Action Required: {role_label} ===",
            "",
            ">> Task",
            "  " + request.prompt.replace("\n", "\n  "),
            "",
        ]

        # 1. 読むべきファイル
        if request.input_files:
            lines.append(">> Read These Files")
            for f in request.input_files:
                lines.append(f"  - {f}")
            lines.append("")
        elif request.system:
            lines.extend([
                ">> Context / Instructions",
                "  " + request.system.replace("\n", "\n  "),
                "",
            ])

        # 2. 作業ディレクトリ
        if request.working_dir:
            lines.extend([
                ">> Working Directory",
                f"  {request.working_dir}",
                "",
            ])

        # 3. 出力先ファイル
        lines.extend([
            ">> Update This File",
            f"  runs/<run-name>/{output_file}",
            "",
        ])

        # 4. handoff.md に残すべき内容（role 別ガイダンス）
        if handoff_items:
            lines.append(">> Update handoff.md -- Record These Items")
            for item in handoff_items:
                lines.append(f"  - {item}")
            lines.append("")

        # 5. 完了後チェックリスト
        lines.extend([
            ">> Done? Check These",
            f"  [ ] {output_file} を保存した",
            "  [ ] handoff.md を更新した（上記 3 項目）",
            "  [ ] 次の role に作業を引き継いだ",
        ])

        return "\n".join(lines)
