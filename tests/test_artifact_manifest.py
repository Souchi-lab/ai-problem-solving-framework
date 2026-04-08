"""
test_artifact_manifest.py — ArtifactEntry / ArtifactManifest / ManifestRepository / ArtifactRepository のテスト

テスト方針:
- ArtifactEntry の to_dict / from_dict round-trip
- 欠損フィールドはデフォルト値で補完される（前方互換）
- ArtifactManifest の round-trip
- ManifestRepository の save / load round-trip
- ManifestRepository: ファイル不在時は None
- ManifestRepository.update_entry(): 新規 entry 生成（revision=1）
- ManifestRepository.update_entry(): 2 回 update で revision=2
- ArtifactRepository.write() が run_dir あり + writing_role あり → manifest 更新
- ArtifactRepository.write() が run_dir なし → manifest 更新しない
- ArtifactRepository.write() が writing_role=None → manifest 更新しない
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsf.core.manifest.artifact_entry import ArtifactEntry, ArtifactManifest, _sha256
from apsf.core.manifest.manifest_repository import ManifestRepository


# ── ArtifactEntry round-trip ─────────────────────────────────────────────────

def test_artifact_entry_to_dict_round_trip() -> None:
    """to_dict / from_dict の round-trip が一致する。"""
    entry = ArtifactEntry(
        artifact_name="plan.md",
        artifact_type="markdown",
        owner_role="Planner",
        written_by="Planner",
        status="generated",
        checksum="abc123",
        revision=1,
        source_handoff_id="xyz",
    )
    restored = ArtifactEntry.from_dict(entry.to_dict())
    assert restored.artifact_name == "plan.md"
    assert restored.owner_role == "Planner"
    assert restored.checksum == "abc123"
    assert restored.revision == 1
    assert restored.source_handoff_id == "xyz"
    assert restored.updated_at == entry.updated_at


def test_artifact_entry_from_dict_missing_fields_use_defaults() -> None:
    """欠損フィールドはデフォルト値で補完される（前方互換）。"""
    minimal = {"artifact_name": "build.md"}
    entry = ArtifactEntry.from_dict(minimal)
    assert entry.artifact_name == "build.md"
    assert entry.artifact_type == "markdown"
    assert entry.owner_role == ""
    assert entry.written_by == ""
    assert entry.status == "generated"
    assert entry.checksum == ""
    assert entry.revision == 0
    assert entry.finalized_at == ""
    assert entry.finalized_by == ""
    assert entry.source_handoff_id == ""


# ── ArtifactManifest round-trip ──────────────────────────────────────────────

def test_artifact_manifest_to_dict_round_trip() -> None:
    """ArtifactManifest の to_dict / from_dict round-trip が一致する。"""
    entry = ArtifactEntry(artifact_name="plan.md", written_by="Planner", revision=1)
    manifest = ArtifactManifest(run_id="test-run", entries={"plan.md": entry})
    restored = ArtifactManifest.from_dict(manifest.to_dict())
    assert restored.run_id == "test-run"
    assert "plan.md" in restored.entries
    assert restored.entries["plan.md"].written_by == "Planner"
    assert restored.entries["plan.md"].revision == 1


# ── ManifestRepository ───────────────────────────────────────────────────────

def test_manifest_repository_save_and_load(tmp_path: Path) -> None:
    """save した ArtifactManifest が load で復元できる。"""
    repo = ManifestRepository(tmp_path)
    entry = ArtifactEntry(artifact_name="plan.md", written_by="Planner", revision=1)
    manifest = ArtifactManifest(run_id="test-run", entries={"plan.md": entry})
    repo.save(manifest)

    loaded = repo.load()
    assert loaded is not None
    assert loaded.run_id == "test-run"
    assert "plan.md" in loaded.entries
    assert loaded.entries["plan.md"].written_by == "Planner"


def test_manifest_repository_load_missing_returns_none(tmp_path: Path) -> None:
    """ファイルが存在しない場合は None を返す（例外 raise しない）。"""
    repo = ManifestRepository(tmp_path)
    assert repo.load() is None


def test_manifest_repository_update_entry_creates_entry(tmp_path: Path) -> None:
    """update_entry() が新規 entry を revision=1 で生成する。"""
    repo = ManifestRepository(tmp_path)
    entry = repo.update_entry(
        artifact_name="plan.md",
        writing_role="Planner",
        content="# Plan\n\nContent.",
        run_id="test-run",
    )
    assert entry.artifact_name == "plan.md"
    assert entry.revision == 1
    assert entry.written_by == "Planner"
    assert entry.checksum == _sha256("# Plan\n\nContent.")
    assert entry.source_handoff_id == ""

    # JSON にも反映されている
    loaded = repo.load()
    assert loaded is not None
    assert loaded.entries["plan.md"].revision == 1


def test_manifest_repository_update_entry_increments_revision(tmp_path: Path) -> None:
    """2 回 update_entry() すると revision が 2 になる。"""
    repo = ManifestRepository(tmp_path)
    repo.update_entry("plan.md", "Planner", "first content", "test-run")
    repo.update_entry("plan.md", "Planner", "second content", "test-run")

    loaded = repo.load()
    assert loaded is not None
    assert loaded.entries["plan.md"].revision == 2
    assert loaded.entries["plan.md"].checksum == _sha256("second content")


def test_manifest_repository_update_entry_owner_role_from_policy(tmp_path: Path) -> None:
    """ownership policy が存在する artifact は owner_role が policy から取得される。"""
    repo = ManifestRepository(tmp_path)
    entry = repo.update_entry("plan.md", "Planner", "content", "test-run")
    assert entry.owner_role == "Planner"  # ownership.py の plan.md owner_role


def test_manifest_repository_update_entry_source_handoff_id(tmp_path: Path) -> None:
    """source_handoff_id が entry に記録される。"""
    repo = ManifestRepository(tmp_path)
    entry = repo.update_entry(
        "build.md", "Builder", "content", "test-run", source_handoff_id="abc123"
    )
    assert entry.source_handoff_id == "abc123"


def test_manifest_repository_remove_entries_deletes_only_requested_artifacts(tmp_path: Path) -> None:
    """remove_entries() は指定 entry だけ削除する。"""
    repo = ManifestRepository(tmp_path)
    repo.update_entry("plan.md", "Planner", "plan", "test-run")
    repo.update_entry("build.md", "Builder", "build", "test-run")

    changed = repo.remove_entries(["build.md", "missing.md"])

    loaded = repo.load()
    assert changed is True
    assert loaded is not None
    assert "plan.md" in loaded.entries
    assert "build.md" not in loaded.entries


# ── ArtifactRepository manifest integration ──────────────────────────────────

def test_artifact_repository_write_updates_manifest_when_run_dir_set(tmp_path: Path) -> None:
    """run_dir あり + writing_role あり → write() が artifact_manifest.json を更新する。"""
    from apsf.core.storage.artifact_repository import ArtifactRepository

    run_dir = tmp_path / "test-run"
    run_dir.mkdir()

    repo = ArtifactRepository(writing_role="Planner", run_dir=run_dir)
    repo.write(run_dir / "plan.md", "# Plan\n\nContent.")

    manifest_path = run_dir / "artifact_manifest.json"
    assert manifest_path.exists(), "artifact_manifest.json が生成されていない"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "plan.md" in data["entries"]
    assert data["entries"]["plan.md"]["written_by"] == "Planner"
    assert data["entries"]["plan.md"]["revision"] == 1


def test_artifact_repository_write_skips_manifest_when_run_dir_none(tmp_path: Path) -> None:
    """run_dir なし → artifact_manifest.json を更新しない。"""
    from apsf.core.storage.artifact_repository import ArtifactRepository

    repo = ArtifactRepository(writing_role="Planner")  # run_dir=None
    repo.write(tmp_path / "plan.md", "# Plan\n\nContent.")

    assert not (tmp_path / "artifact_manifest.json").exists()


def test_artifact_repository_write_skips_manifest_when_role_none(tmp_path: Path) -> None:
    """writing_role=None → artifact_manifest.json を更新しない。"""
    from apsf.core.storage.artifact_repository import ArtifactRepository

    run_dir = tmp_path / "test-run"
    run_dir.mkdir()

    repo = ArtifactRepository(writing_role=None, run_dir=run_dir)
    repo.write(run_dir / "run_state.json", '{"run_id": "test"}')

    assert not (run_dir / "artifact_manifest.json").exists()
