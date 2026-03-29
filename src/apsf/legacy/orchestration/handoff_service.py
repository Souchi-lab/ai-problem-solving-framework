"""
HandoffService — handoff.md の生成補助

role 間の受け渡しを構造化する。
「何が決まっているか」「何が未決か」「次の role がすること」を整理する。
"""

from __future__ import annotations

from pathlib import Path

from ...core.domain.models import Handoff, Role


class HandoffService:
    """
    Handoff オブジェクトを handoff.md として保存する。

    使用例:
        service = HandoffService()
        handoff = Handoff(
            from_role=Role.PLANNER,
            to_role=Role.BUILDER,
            current_state="Plan is complete.",
            decided=["Use Option A approach"],
            open_items=["Color scheme not decided"],
            next_actions=["Implement the SNS post templates"],
        )
        service.write(handoff, run_dir / "handoff.md")
    """

    def write(self, handoff: Handoff, path: Path) -> None:
        """Handoff オブジェクトを handoff.md として書き出す。"""
        content = self._render(handoff)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def read(self, path: Path) -> str:
        """handoff.md を文字列として読み込む。存在しない場合は空文字。"""
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _render(self, h: Handoff) -> str:
        """Handoff オブジェクトを Markdown テキストに変換する。"""
        lines = [
            "# Handoff\n",
            f"## From\n\n- Role: {h.from_role.value}\n\n",
            f"## To\n\n- Role: {h.to_role.value}\n\n",
            f"## Current State\n\n{h.current_state}\n\n",
        ]

        lines.append("## What Is Decided\n\n")
        if h.decided:
            for item in h.decided:
                lines.append(f"- [x] {item}\n")
        else:
            lines.append("- (none)\n")
        lines.append("\n")

        lines.append("## What Remains Open\n\n")
        if h.open_items:
            for item in h.open_items:
                lines.append(f"- [ ] {item}\n")
        else:
            lines.append("- (none)\n")
        lines.append("\n")

        lines.append("## What the Next Role Should Inspect First\n\n")
        if h.next_actions:
            for i, action in enumerate(h.next_actions, 1):
                lines.append(f"{i}. {action}\n")
        lines.append("\n")

        if h.constraints:
            lines.append("## Constraints / Cautions\n\n")
            for c in h.constraints:
                lines.append(f"- {c}\n")
            lines.append("\n")

        if h.notes:
            lines.append(f"## Optional Notes\n\n{h.notes}\n")

        return "".join(lines)

    def create_from_step(
        self,
        from_role: Role,
        to_role: Role,
        current_state: str,
        decided: list[str] | None = None,
        open_items: list[str] | None = None,
        next_actions: list[str] | None = None,
        constraints: list[str] | None = None,
    ) -> Handoff:
        """Handoff オブジェクトを生成するファクトリメソッド。"""
        return Handoff(
            from_role=from_role,
            to_role=to_role,
            current_state=current_state,
            decided=decided or [],
            open_items=open_items or [],
            next_actions=next_actions or [],
            constraints=constraints or [],
        )
