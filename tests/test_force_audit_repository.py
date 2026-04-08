"""
ForceAuditRepository のテスト

- reason あり / reason なしの両方が正しく記録される
- 複数 append で entries が蓄積される
- --force なし経路では force_audit.json が生成されない
- make_audit_entry が正しいフィールドを設定する
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsf.core.storage.force_audit_repository import (
    ForceAuditEntry,
    ForceAuditRepository,
    make_audit_entry,
)


# ── make_audit_entry ────────────────────────────────────────────────────────

def test_make_entry_with_reason() -> None:
    entry = make_audit_entry(
        command="write-phase",
        target_file="plan.md",
        role="Builder",
        reason="Planner requested re-plan",
        override_kind="overwrite",
    )
    assert entry.command == "write-phase"
    assert entry.target_file == "plan.md"
    assert entry.role == "Builder"
    assert entry.had_reason is True
    assert entry.reason == "Planner requested re-plan"
    assert entry.override_kind == "overwrite"
    assert entry.timestamp  # non-empty


def test_make_entry_without_reason() -> None:
    entry = make_audit_entry(
        command="act",
        target_file="build.md",
        role="Builder",
        reason=None,
        override_kind="consistency_gate_bypass",
    )
    assert entry.had_reason is False
    assert entry.reason == ""
    assert entry.override_kind == "consistency_gate_bypass"


# ── ForceAuditRepository ────────────────────────────────────────────────────

def test_append_creates_file(tmp_path: Path) -> None:
    repo = ForceAuditRepository(tmp_path)
    entry = make_audit_entry("write-phase", "plan.md", "Builder", None, "overwrite")

    repo.append(entry)

    assert (tmp_path / "force_audit.json").exists()


def test_append_stores_entry(tmp_path: Path) -> None:
    repo = ForceAuditRepository(tmp_path)
    entry = make_audit_entry("write-phase", "plan.md", "Builder", "forced reason", "overwrite")

    repo.append(entry)
    loaded = repo.load()

    assert len(loaded) == 1
    assert loaded[0].target_file == "plan.md"
    assert loaded[0].had_reason is True
    assert loaded[0].reason == "forced reason"


def test_append_accumulates_entries(tmp_path: Path) -> None:
    """複数 append で entries が蓄積されること。"""
    repo = ForceAuditRepository(tmp_path)

    repo.append(make_audit_entry("write-phase", "plan.md", "Builder", None, "overwrite"))
    repo.append(make_audit_entry("act", "build.md", "Builder", "fix", "consistency_gate_bypass"))

    loaded = repo.load()

    assert len(loaded) == 2
    assert loaded[0].command == "write-phase"
    assert loaded[1].command == "act"


def test_load_empty_when_no_file(tmp_path: Path) -> None:
    """force_audit.json が存在しない場合は空リストを返すこと。"""
    repo = ForceAuditRepository(tmp_path)
    assert repo.load() == []


def test_no_audit_file_without_force(tmp_path: Path) -> None:
    """force を使わない経路では force_audit.json が生成されないこと。"""
    repo = ForceAuditRepository(tmp_path)
    # 何も append しなければファイルが存在しない
    assert not (tmp_path / "force_audit.json").exists()


def test_json_structure(tmp_path: Path) -> None:
    """保存された JSON が {"entries": [...]} 構造であること。"""
    repo = ForceAuditRepository(tmp_path)
    repo.append(make_audit_entry("write-phase", "review.md", "Critic", None, "overwrite"))

    raw = json.loads((tmp_path / "force_audit.json").read_text(encoding="utf-8"))
    assert "entries" in raw
    assert isinstance(raw["entries"], list)
    assert len(raw["entries"]) == 1
    assert raw["entries"][0]["target_file"] == "review.md"


def test_had_reason_false_when_none(tmp_path: Path) -> None:
    """reason=None の場合 had_reason=False、reason="" で保存されること。"""
    repo = ForceAuditRepository(tmp_path)
    repo.append(make_audit_entry("act", "build.md", "Builder", None, "consistency_gate_bypass"))

    loaded = repo.load()
    assert loaded[0].had_reason is False
    assert loaded[0].reason == ""


def test_had_reason_true_when_provided(tmp_path: Path) -> None:
    """reason が渡された場合 had_reason=True で保存されること。"""
    repo = ForceAuditRepository(tmp_path)
    repo.append(make_audit_entry("write-phase", "plan.md", "Planner", "re-plan needed", "overwrite"))

    loaded = repo.load()
    assert loaded[0].had_reason is True
    assert loaded[0].reason == "re-plan needed"
