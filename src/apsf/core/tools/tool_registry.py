"""
ToolRegistry — ToolDescriptor と ToolAdapter のペアを管理する最小 registry

責務:
  - register / get / list の 3 操作
  - 重複登録の検出
  - permission matrix へのメタデータ供給（descriptor.operation_type 経由）

しないこと:
  - permission 判定（permission_matrix が担う）
  - ツールの実行ポリシー管理（adapter が担う）
  - dynamic discovery / network transport（次段以降）

build_default_registry():
  APSF の組み込みツールを事前登録した registry を返すファクトリ。
  write-phase / act など既存の主要経路を内部ツールとして登録する。
"""

from __future__ import annotations

from dataclasses import dataclass

from ..permissions.permission_matrix import OP_WRITE
from .tool_adapter import InternalToolAdapter, McpToolAdapter, ToolAdapter
from .tool_descriptor import KIND_INTERNAL, KIND_MCP, ToolDescriptor


@dataclass
class RegistryEntry:
    """registry に格納される 1 エントリ。"""
    descriptor: ToolDescriptor
    adapter:    ToolAdapter


class ToolRegistry:
    """
    ツールの register / get / list を提供する最小 registry。

    使用例:
        registry = ToolRegistry()
        registry.register(descriptor, adapter)
        entry = registry.get("write_phase")
        op_type = entry.descriptor.operation_type  # → "write"
    """

    def __init__(self) -> None:
        self._entries: dict[str, RegistryEntry] = {}

    def register(self, descriptor: ToolDescriptor, adapter: ToolAdapter) -> None:
        """
        ツールを registry に追加する。

        Raises:
            ValueError: 同じ tool_name が既に登録されている場合
        """
        if descriptor.tool_name in self._entries:
            raise ValueError(
                f"Tool '{descriptor.tool_name}' is already registered. "
                "Use a different tool_name or create a new registry."
            )
        self._entries[descriptor.tool_name] = RegistryEntry(descriptor, adapter)

    def get(self, tool_name: str) -> RegistryEntry:
        """
        tool_name で RegistryEntry を返す。

        Raises:
            KeyError: tool_name が登録されていない場合
        """
        if tool_name not in self._entries:
            raise KeyError(f"Tool '{tool_name}' is not registered.")
        return self._entries[tool_name]

    def list(self) -> list[ToolDescriptor]:
        """登録済み全ツールの ToolDescriptor リストを返す。"""
        return [entry.descriptor for entry in self._entries.values()]

    def __len__(self) -> int:
        return len(self._entries)


# ── factory ──────────────────────────────────────────────────────────────────

def build_default_registry() -> ToolRegistry:
    """
    APSF の組み込みツールを事前登録した ToolRegistry を返す。

    登録ツール:
      write_phase — 現 phase の artifact ファイルへの書き込み（internal）
      act         — LLM による phase 実行 + artifact 書き込み（internal）
      mcp_example — MCP ツールの境界を示すプレースホルダ（mcp / v1 未実装）

    呼び出し側は registry.get("write_phase").descriptor.operation_type を参照して
    permission matrix に渡す PermissionRequest を組み立てることができる。
    """
    registry = ToolRegistry()

    # write_phase: write-phase コマンドが行う artifact 書き込み
    registry.register(
        ToolDescriptor(
            tool_name="write_phase",
            tool_kind=KIND_INTERNAL,
            operation_type=OP_WRITE,
            description="Write the phase artifact file for the current APSF phase.",
            requires_reason=False,
        ),
        InternalToolAdapter(fn=lambda **_: None),  # placeholder; CLI が実装を持つ
    )

    # act: ActService.execute() が行う LLM 起動 + artifact 書き込み
    registry.register(
        ToolDescriptor(
            tool_name="act",
            tool_kind=KIND_INTERNAL,
            operation_type=OP_WRITE,
            description="Execute the current phase via LLM and write the phase artifact.",
            requires_reason=False,
        ),
        InternalToolAdapter(fn=lambda **_: None),  # placeholder; ActService が実装を持つ
    )

    # mcp_example: MCP ツールの境界を示すプレースホルダ（transport 未実装）
    registry.register(
        ToolDescriptor(
            tool_name="mcp_example",
            tool_kind=KIND_MCP,
            operation_type=OP_WRITE,
            description="Placeholder for future MCP tool integration.",
            requires_reason=True,
        ),
        McpToolAdapter(server_name="example-mcp-server", tool_name="example_tool"),
    )

    return registry
