"""
ToolAdapter — ツール実行の最小 ABC

内部ツール（InternalToolAdapter）と MCP ツール（McpToolAdapter）を
同じ interface で扱えるようにする。

v1 の McpToolAdapter は MCP transport を実装せず、
呼び出し時に NotImplementedError を raise する。
これにより registry に MCP ツールを登録・参照はできるが、
実際の invoke は次段の transport 実装を待つ。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable


class ToolAdapter(ABC):
    """
    ツール実行の抽象基底クラス。

    サブクラス:
        InternalToolAdapter — Python callable をラップする
        McpToolAdapter      — MCP ツールの境界（v1 は未実装）
    """

    @abstractmethod
    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        ツールを実行して結果 dict を返す。

        Args:
            arguments: ツールへの引数（tool_name ごとに定義）

        Returns:
            {"result": ..., ...} のような結果 dict
        """
        ...


class InternalToolAdapter(ToolAdapter):
    """
    Python callable をラップする内部ツール adapter。

    使用例:
        adapter = InternalToolAdapter(fn=lambda phase: f"phase={phase}")
        result = adapter.invoke({"phase": "PLAN_NEEDED"})
    """

    def __init__(self, fn: Callable[..., Any]) -> None:
        self._fn = fn

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        result = self._fn(**arguments)
        return {"result": result}


class McpToolAdapter(ToolAdapter):
    """
    MCP ツールの境界を定義する adapter。

    v1 は transport を実装していないため invoke は NotImplementedError を raise する。
    registry への登録・descriptor 参照・permission 判定には使用できる。
    次段で transport 実装が入ったとき、このクラスに実装を追加する。
    """

    def __init__(self, server_name: str, tool_name: str) -> None:
        self._server_name = server_name
        self._tool_name = tool_name

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            f"MCP transport not implemented in v1. "
            f"Tool: {self._server_name}/{self._tool_name}"
        )
