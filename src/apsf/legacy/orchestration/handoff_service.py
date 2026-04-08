"""
HandoffService — handoff.json 正本 + handoff.md view の生成

role 間の受け渡しを構造化する。
handoff.json が canonical source。handoff.md は render / view として残る。
「何が決まっているか」「何が未決か」「次の role がすること」を整理する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ...core.domain.models import Handoff, Role
from ...core.domain.enums import HandoffStatus
from ...core.handoff.handoff_record import HandoffRecord, _now_iso
from ...core.handoff.handoff_repository import HandoffRepository
from ...core.storage.artifact_repository import ArtifactRepository


class HandoffService:
    """
    Handoff オブジェクトを handoff.json（正本）+ handoff.md（view）として保存する。

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

    def __init__(self) -> None:
        self._artifact_repo = ArtifactRepository()

    def write(self, handoff: Handoff, path: Path) -> HandoffRecord:
        """
        Handoff オブジェクトを handoff.json（正本）と handoff.md（view）として書き出す。

        path は handoff.md のパスを期待する（既存 caller との互換を保つ）。
        run_dir は path.parent から導出する。

        Returns:
            HandoffRecord: 生成した正本レコード
        """
        run_dir = path.parent
        repo = HandoffRepository(run_dir)

        # 既存 offered/accepted handoff を superseded に更新
        supersedes_id = ""
        existing = repo.load()
        if existing is not None and existing.status in (
            HandoffStatus.OFFERED.value,
            HandoffStatus.DRAFT.value,
            HandoffStatus.ACCEPTED.value,
        ):
            supersedes_id = existing.handoff_id
            existing.status = HandoffStatus.SUPERSEDED.value
            repo.save(existing)

        # 新 HandoffRecord を生成（status=OFFERED）
        record = HandoffRecord(
            from_role=handoff.from_role.value if hasattr(handoff.from_role, "value") else str(handoff.from_role),
            to_role=handoff.to_role.value if hasattr(handoff.to_role, "value") else str(handoff.to_role),
            artifact_scope=list(getattr(handoff, "artifact_scope", [])),
            status=HandoffStatus.OFFERED.value,
            supersedes=supersedes_id,
        )
        repo.save(record)

        # handoff.md view（変更なし）
        content = self._render(handoff)
        self._artifact_repo.write(path, content)

        return record

    def accept(self, run_dir: Path, accepted_by: str) -> Optional[HandoffRecord]:
        """
        active handoff を accepted 状態に更新する。

        handoff.json が存在しない場合、または対象 status でない場合は None を返す。

        Args:
            run_dir:     run ディレクトリの Path
            accepted_by: 受理した role 名

        Returns:
            更新後の HandoffRecord、または None
        """
        repo = HandoffRepository(run_dir)
        record = repo.load()
        if record is None or record.status not in (
            HandoffStatus.OFFERED.value,
            HandoffStatus.DRAFT.value,
        ):
            return record
        record.status = HandoffStatus.ACCEPTED.value
        record.accepted_by_next_role = accepted_by
        record.accepted_at = _now_iso()
        repo.save(record)
        return record

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
