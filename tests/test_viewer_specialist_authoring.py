from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from apsf.viewer import api
from apsf.legacy.cli import specialist_registry


def _make_registry_source(root: Path) -> Path:
    registry_path = root / "src" / "apsf" / "legacy" / "cli" / "specialist_registry.py"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        'PTYPE_TO_SPECIALIST: dict[str, str] = {\n'
        '    "P-01": "framework/agents/planners/feature-planner.md",\n'
        '}\n\n'
        'CTYPE_TO_SPECIALIST: dict[str, str] = {\n'
        '    "C-01": "framework/agents/critics/ux-flow-critic.md",\n'
        '}\n\n'
        'BTYPE_TO_SPECIALIST: dict[str, str] = {\n'
        '    "B-01": "framework/agents/builders/product-implementation-builder.md",\n'
        '}\n',
        encoding="utf-8",
    )
    return registry_path


def _make_repo_local_temp_root() -> Path:
    base = Path.cwd() / ".tmp-specialist-authoring-tests"
    base.mkdir(exist_ok=True)
    root = base / f"case-{uuid.uuid4().hex}"
    root.mkdir()
    return root


def test_create_specialist_library_asset_writes_markdown_and_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_repo_local_temp_root()
    try:
        registry_path = _make_registry_source(root)
        monkeypatch.setattr(api, "PROJECT_ROOT", root)

        response = api._create_specialist_library_asset(
            role="Critic",
            specialist_code="C-09",
            slug="workflow-integrity-critic",
            title="Workflow Integrity Critic",
            scope="Review workflow integrity and role-boundary coherence.",
            use_when="Use when the main risk is process drift or boundary confusion.",
            out_of_scope="Do not use for screen-level copy polish.",
            evaluation_criteria="Boundary clarity, policy alignment, and operator expectation safety.",
        )

        assert response.created is True
        assert response.relative_path == "framework/agents/critics/workflow-integrity-critic.md"
        created_path = root / response.relative_path
        assert created_path.exists()
        created_text = created_path.read_text(encoding="utf-8")
        assert "Workflow Integrity Critic" in created_text
        assert "## Scope" in created_text
        registry_text = registry_path.read_text(encoding="utf-8")
        assert '"C-09": "framework/agents/critics/workflow-integrity-critic.md"' in registry_text
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_create_specialist_library_asset_rolls_back_markdown_on_registry_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_repo_local_temp_root()
    try:
        _make_registry_source(root)
        monkeypatch.setattr(api, "PROJECT_ROOT", root)

        def _boom(*args, **kwargs):
            raise RuntimeError("registry patch failed")

        monkeypatch.setattr(api, "_patch_specialist_registry_source", _boom)

        with pytest.raises(RuntimeError, match="registry patch failed"):
            api._create_specialist_library_asset(
                role="Planner",
                specialist_code="P-13",
                slug="workflow-integrity-planner",
                title="Workflow Integrity Planner",
                scope="Plan around workflow integrity.",
                use_when="Use when the main problem is execution boundary design.",
                out_of_scope="Do not use for purely visual UI work.",
                evaluation_criteria="Boundary clarity and implementation readiness.",
            )

        assert not (root / "framework" / "agents" / "planners" / "workflow-integrity-planner.md").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_create_specialist_library_asset_rejects_role_prefix_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_repo_local_temp_root()
    try:
        _make_registry_source(root)
        monkeypatch.setattr(api, "PROJECT_ROOT", root)

        with pytest.raises(ValueError, match="does not match role"):
            api._create_specialist_library_asset(
                role="Builder",
                specialist_code="C-09",
                slug="bad-builder-code",
                title="Bad Builder Code",
                scope="x",
                use_when="x",
                out_of_scope="x",
                evaluation_criteria="x",
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_create_specialist_library_asset_updates_runtime_registry_for_immediate_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_repo_local_temp_root()
    code = "P-91"
    original = specialist_registry.specialist_mapping_for_role("Planner").get(code)
    try:
        _make_registry_source(root)
        monkeypatch.setattr(api, "PROJECT_ROOT", root)

        response = api._create_specialist_library_asset(
            role="Planner",
            specialist_code=code,
            slug="immediate-reuse-planner",
            title="Immediate Reuse Planner",
            scope="Focus on immediate specialist reuse verification.",
            use_when="Use when the main concern is post-create assignment continuity.",
            out_of_scope="Do not use for broad product planning.",
            evaluation_criteria="The created specialist is available immediately without restart.",
        )

        runtime_mapping = specialist_registry.specialist_mapping_for_role("Planner")
        assert runtime_mapping[code] == response.relative_path

        decision = specialist_registry.resolve_planner_specialist(
            "Immediate reuse verification for the newly created specialist.",
            f"## Planner Specialist\n- Primary P-TYPE: {code}\n",
            root,
        )
        assert decision.mode == "explicit"
        assert decision.ptype == code
        assert "Immediate Reuse Planner" in decision.specialist_content
    finally:
        mapping = specialist_registry.specialist_mapping_for_role("Planner")
        if original is None:
            mapping.pop(code, None)
        else:
            mapping[code] = original
        shutil.rmtree(root, ignore_errors=True)


def test_create_specialist_library_asset_rejects_duplicate_like_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_repo_local_temp_root()
    code = "P-91"
    original = specialist_registry.specialist_mapping_for_role("Planner").get(code)
    try:
        _make_registry_source(root)
        monkeypatch.setattr(api, "PROJECT_ROOT", root)

        existing_path = root / "framework" / "agents" / "planners" / "existing-verification-planner.md"
        existing_path.parent.mkdir(parents=True, exist_ok=True)
        existing_path.write_text(
            "# Specialist: Verification Planning Planner (P-91)\n\n"
            "## Scope\n\nFocus on smoke checks, evidence shape, and acceptance proof.\n\n"
            "## Use This Specialist When\n\nUse this specialist when a run is mainly about GUI verification and acceptance evidence.\n\n"
            "## Out of Scope\n\nDo not redesign the framework or expand unrelated planning scope.\n\n"
            "## Evaluation Criteria\n\nChecks are concrete, evidence-backed, and closure-ready.\n",
            encoding="utf-8",
        )
        specialist_registry.specialist_mapping_for_role("Planner")[code] = "framework/agents/planners/existing-verification-planner.md"

        with pytest.raises(ValueError, match="Duplicate-like specialist already exists"):
            api._create_specialist_library_asset(
                role="Planner",
                specialist_code="P-92",
                slug="verification-planning-planner-new",
                title="Verification Planning Planner",
                scope="Focus on smoke checks, evidence shape, and acceptance proof.",
                use_when="Use this specialist when a run is mainly about GUI verification and acceptance evidence.",
                out_of_scope="Do not redesign the framework or expand unrelated planning scope.",
                evaluation_criteria="Checks are concrete, evidence-backed, and closure-ready.",
            )
    finally:
        mapping = specialist_registry.specialist_mapping_for_role("Planner")
        if original is None:
            mapping.pop(code, None)
        else:
            mapping[code] = original
        shutil.rmtree(root, ignore_errors=True)
