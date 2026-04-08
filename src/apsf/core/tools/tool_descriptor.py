"""
ToolDescriptor — 内部ツールと MCP ツールを同じ抽象で表現する最小 schema

責務:
  - ツールの識別情報（name / kind）
  - permission matrix に渡すメタデータ（operation_type）
  - UI / audit 向けのヒント（description / requires_reason）

このモジュールはツールの「実体」を持たない。
実行は ToolAdapter が担い、permission 判定は permission_matrix が担う。

tool_kind:
  "internal" — APSF 内部の Python 関数として実装されているツール
  "mcp"      — MCP protocol 越しに呼ぶ外部ツール（v1 は transport 未実装）

operation_type:
  permission_matrix の OP_* 定数と対応させること。
  v1 では "write" のみ。"read" / "command" / "network" は次段で追加。
"""

from __future__ import annotations

from dataclasses import dataclass, field

# tool_kind 定数
KIND_INTERNAL = "internal"
KIND_MCP = "mcp"


@dataclass
class ToolDescriptor:
    """
    ツールの静的メタデータ。

    Fields:
        tool_name:      一意なツール識別名（例: "write_phase"）
        tool_kind:      "internal" | "mcp"
        operation_type: permission matrix の operation_type と対応
                        （例: "write"）
        description:    人間向けの説明（UI / build.md 記録用）
        requires_reason: このツールの呼び出しが force_reason を要求するか
                         （permission matrix の requires_reason とは別の hint）
    """

    tool_name:      str
    tool_kind:      str
    operation_type: str
    description:    str = ""
    requires_reason: bool = False
