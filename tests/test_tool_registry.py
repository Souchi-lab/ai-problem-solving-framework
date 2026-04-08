"""
ToolRegistry / ToolAdapter / ToolDescriptor のテスト

カバー範囲:
  - ToolDescriptor: フィールド確認
  - InternalToolAdapter: invoke が fn を呼ぶ
  - McpToolAdapter: invoke が NotImplementedError を raise する
  - ToolRegistry: register / get / duplicate / list / __len__
  - build_default_registry: 組み込みツールの確認
  - 接続: registry の operation_type が permission matrix と整合する
"""

from __future__ import annotations

import pytest

from apsf.core.tools.tool_adapter import InternalToolAdapter, McpToolAdapter
from apsf.core.tools.tool_descriptor import KIND_INTERNAL, KIND_MCP, ToolDescriptor
from apsf.core.tools.tool_registry import ToolRegistry, build_default_registry
from apsf.core.permissions.permission_matrix import OP_WRITE, PermissionEvaluator, PermissionRequest, infer_target_scope


# ── ToolDescriptor ────────────────────────────────────────────────────────────

def test_descriptor_fields() -> None:
    d = ToolDescriptor(
        tool_name="write_phase",
        tool_kind=KIND_INTERNAL,
        operation_type=OP_WRITE,
        description="Test tool",
        requires_reason=False,
    )
    assert d.tool_name == "write_phase"
    assert d.tool_kind == KIND_INTERNAL
    assert d.operation_type == OP_WRITE
    assert d.requires_reason is False


# ── InternalToolAdapter ───────────────────────────────────────────────────────

def test_internal_adapter_invokes_fn() -> None:
    calls = []
    adapter = InternalToolAdapter(fn=lambda x: calls.append(x) or x)
    result = adapter.invoke({"x": "hello"})
    assert result == {"result": "hello"}
    assert calls == ["hello"]


def test_internal_adapter_no_args() -> None:
    adapter = InternalToolAdapter(fn=lambda: 42)
    result = adapter.invoke({})
    assert result == {"result": 42}


# ── McpToolAdapter ────────────────────────────────────────────────────────────

def test_mcp_adapter_invoke_raises_not_implemented() -> None:
    adapter = McpToolAdapter(server_name="my-server", tool_name="my-tool")
    with pytest.raises(NotImplementedError) as exc_info:
        adapter.invoke({})
    assert "MCP transport not implemented" in str(exc_info.value)
    assert "my-server" in str(exc_info.value)


# ── ToolRegistry ──────────────────────────────────────────────────────────────

def _make_descriptor(name: str = "test_tool") -> ToolDescriptor:
    return ToolDescriptor(
        tool_name=name,
        tool_kind=KIND_INTERNAL,
        operation_type=OP_WRITE,
    )


def _make_adapter() -> InternalToolAdapter:
    return InternalToolAdapter(fn=lambda: None)


def test_register_and_get() -> None:
    registry = ToolRegistry()
    desc = _make_descriptor("tool_a")
    adapter = _make_adapter()
    registry.register(desc, adapter)

    entry = registry.get("tool_a")
    assert entry.descriptor.tool_name == "tool_a"
    assert entry.adapter is adapter


def test_duplicate_registration_raises() -> None:
    registry = ToolRegistry()
    registry.register(_make_descriptor("dup"), _make_adapter())
    with pytest.raises(ValueError, match="already registered"):
        registry.register(_make_descriptor("dup"), _make_adapter())


def test_get_unknown_tool_raises() -> None:
    registry = ToolRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.get("nonexistent")


def test_list_returns_all_descriptors() -> None:
    registry = ToolRegistry()
    registry.register(_make_descriptor("tool_a"), _make_adapter())
    registry.register(_make_descriptor("tool_b"), _make_adapter())

    descriptors = registry.list()
    names = {d.tool_name for d in descriptors}
    assert names == {"tool_a", "tool_b"}


def test_len_reflects_registered_count() -> None:
    registry = ToolRegistry()
    assert len(registry) == 0
    registry.register(_make_descriptor("t1"), _make_adapter())
    assert len(registry) == 1
    registry.register(_make_descriptor("t2"), _make_adapter())
    assert len(registry) == 2


# ── build_default_registry ────────────────────────────────────────────────────

def test_default_registry_has_write_phase() -> None:
    registry = build_default_registry()
    entry = registry.get("write_phase")
    assert entry.descriptor.tool_kind == KIND_INTERNAL
    assert entry.descriptor.operation_type == OP_WRITE


def test_default_registry_has_act() -> None:
    registry = build_default_registry()
    entry = registry.get("act")
    assert entry.descriptor.tool_kind == KIND_INTERNAL
    assert entry.descriptor.operation_type == OP_WRITE


def test_default_registry_has_mcp_example() -> None:
    registry = build_default_registry()
    entry = registry.get("mcp_example")
    assert entry.descriptor.tool_kind == KIND_MCP
    assert entry.descriptor.requires_reason is True


def test_default_registry_mcp_example_invoke_raises() -> None:
    registry = build_default_registry()
    with pytest.raises(NotImplementedError):
        registry.get("mcp_example").adapter.invoke({})


# ── 接続: registry.operation_type → permission matrix ────────────────────────

def test_write_phase_descriptor_feeds_permission_matrix_own_phase() -> None:
    """registry の write_phase descriptor を使って Builder + build.md を評価すると auto allowed。"""
    registry = build_default_registry()
    descriptor = registry.get("write_phase").descriptor

    scope = infer_target_scope("Builder", "build.md")
    req = PermissionRequest(
        operation_type=descriptor.operation_type,
        target_scope=scope,
        role="Builder",
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is True


def test_write_phase_descriptor_feeds_permission_matrix_foreign_no_force() -> None:
    """registry の write_phase descriptor を使って Builder + plan.md（foreign）を評価すると denied。"""
    registry = build_default_registry()
    descriptor = registry.get("write_phase").descriptor

    scope = infer_target_scope("Builder", "plan.md")
    req = PermissionRequest(
        operation_type=descriptor.operation_type,
        target_scope=scope,
        role="Builder",
        force=False,
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is False


def test_write_phase_descriptor_feeds_permission_matrix_system_blocked() -> None:
    """registry の write_phase descriptor を使って run_state.json を評価すると blocked。"""
    registry = build_default_registry()
    descriptor = registry.get("write_phase").descriptor

    scope = infer_target_scope("Builder", "run_state.json")
    req = PermissionRequest(
        operation_type=descriptor.operation_type,
        target_scope=scope,
        role="Builder",
        force=True,
        force_reason="trying anyway",
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is False
