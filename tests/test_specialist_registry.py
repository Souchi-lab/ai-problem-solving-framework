from pathlib import Path

from apsf.legacy.cli.specialist_registry import (
    derive_specialist_relative_path,
    extract_primary_btype,
    extract_primary_ctype,
    extract_primary_ptype,
    load_specialist_content,
    normalize_btype,
    normalize_ctype,
    normalize_ptype,
    normalize_specialist_code_for_role,
    slugify_specialist_name,
    specialist_path_for_btype,
    specialist_path_for_ctype,
    specialist_path_for_ptype,
)


def test_normalize_ptype_extracts_code() -> None:
    assert normalize_ptype("P-02 Bug Fix") == "P-02"
    assert normalize_ptype("primary ptype: p-05 docs") == "P-05"
    assert normalize_ptype("no match") == ""


def test_normalize_ctype_extracts_code() -> None:
    assert normalize_ctype("C-02 Copy Clarity") == "C-02"
    assert normalize_ctype("primary ctype: c-01 ux") == "C-01"
    assert normalize_ctype("no match") == ""


def test_extract_primary_ptype_from_assignment_text() -> None:
    text = """
## Planner Specialist
- Primary P-TYPE: P-06 Design-only
- Specialist Path: framework/agents/planners/design-planner.md
"""
    assert extract_primary_ptype(text) == "P-06"


def test_extract_primary_ctype_from_assignment_text() -> None:
    text = """
## Critic Specialist
- Primary C-TYPE: C-02 Copy Clarity
- Specialist Path: framework/agents/critics/copy-clarity-critic.md
"""
    assert extract_primary_ctype(text) == "C-02"


def test_specialist_path_for_ptype() -> None:
    root = Path("C:/repo")
    path = specialist_path_for_ptype("P-02 Bug Fix", root)
    assert path is not None
    assert path.as_posix().endswith("/framework/agents/planners/bugfix-planner.md")


def test_specialist_path_for_new_ptype() -> None:
    root = Path("C:/repo")
    path = specialist_path_for_ptype("P-09 Integration", root)
    assert path is not None
    assert path.as_posix().endswith("/framework/agents/planners/integration-planner.md")


def test_specialist_path_for_ctype() -> None:
    root = Path("C:/repo")
    path = specialist_path_for_ctype("C-01 UX Flow", root)
    assert path is not None
    assert path.as_posix().endswith("/framework/agents/critics/ux-flow-critic.md")


def test_specialist_path_for_new_ctype() -> None:
    root = Path("C:/repo")
    path = specialist_path_for_ctype("C-05 Bilingual UI", root)
    assert path is not None
    assert path.as_posix().endswith("/framework/agents/critics/bilingual-ui.md")


def test_specialist_path_for_product_positioning_ctype() -> None:
    root = Path("C:/repo")
    path = specialist_path_for_ctype("C-07 Product Positioning", root)
    assert path is not None
    assert path.as_posix().endswith("/framework/agents/critics/product-positioning-critic.md")


def test_specialist_path_for_puzzle_difficulty_ctype() -> None:
    root = Path("C:/repo")
    path = specialist_path_for_ctype("C-08 Puzzle Difficulty", root)
    assert path is not None
    assert path.as_posix().endswith("/framework/agents/critics/puzzle-difficulty-critic.md")


def test_load_specialist_content_returns_empty_when_missing() -> None:
    root = Path(__file__).parent / "fixtures" / "missing_specialist_root"
    assert load_specialist_content("P-02", root) == ""


# ── B-TYPE ────────────────────────────────────────────────────────────────────

def test_normalize_btype_extracts_code() -> None:
    assert normalize_btype("B-01 Product Implementation") == "B-01"
    assert normalize_btype("primary btype: b-04 frontend") == "B-04"
    assert normalize_btype("no match") == ""


def test_normalize_btype_rejects_non_b_codes() -> None:
    assert normalize_btype("P-01") == ""
    assert normalize_btype("C-02") == ""


def test_extract_primary_btype_from_assignment_text() -> None:
    text = """
## Builder Specialist
- Primary B-TYPE: B-03 Refactor / Migration
- Specialist Path: framework/agents/builders/refactor-migration-builder.md
"""
    assert extract_primary_btype(text) == "B-03"


def test_extract_primary_btype_returns_empty_when_absent() -> None:
    text = """
## Planner Specialist
- Primary P-TYPE: P-01 Feature
"""
    assert extract_primary_btype(text) == ""


def test_specialist_path_for_btype_b01() -> None:
    root = Path("C:/repo")
    path = specialist_path_for_btype("B-01", root)
    assert path is not None
    assert path.as_posix().endswith("/framework/agents/builders/product-implementation-builder.md")


def test_specialist_path_for_btype_b04() -> None:
    root = Path("C:/repo")
    path = specialist_path_for_btype("B-04 Frontend", root)
    assert path is not None
    assert path.as_posix().endswith("/framework/agents/builders/frontend-ux-polish-builder.md")


def test_specialist_path_for_btype_all_seven() -> None:
    root = Path("C:/repo")
    codes = ["B-01", "B-02", "B-03", "B-04", "B-05", "B-06", "B-07", "B-08"]
    for code in codes:
        path = specialist_path_for_btype(code, root)
        assert path is not None, f"Missing path for {code}"


def test_specialist_path_for_btype_unknown_returns_none() -> None:
    root = Path("C:/repo")
    path = specialist_path_for_btype("B-99", root)
    assert path is None


def test_load_specialist_content_btype_returns_content() -> None:
    root = Path(__file__).parent.parent
    content = load_specialist_content("B-01", root)
    assert "Product Implementation" in content


def test_load_specialist_content_btype_auto_mapping() -> None:
    root = Path(__file__).parent.parent
    for code in ["B-02", "B-03", "B-04", "B-05", "B-06", "B-07", "B-08"]:
        content = load_specialist_content(code, root)
        assert content != "", f"Empty content for {code}"


def test_slugify_specialist_name_normalizes_free_text() -> None:
    assert slugify_specialist_name(" Workflow Integrity Critic ") == "workflow-integrity-critic"
    assert slugify_specialist_name("copy___clarity!!") == "copy-clarity"


def test_normalize_specialist_code_for_role_enforces_prefix() -> None:
    assert normalize_specialist_code_for_role("Planner", "p-13") == "P-13"
    assert normalize_specialist_code_for_role("Critic", "P-13") == ""


def test_derive_specialist_relative_path_is_role_aware() -> None:
    assert derive_specialist_relative_path("Planner", "P-13", "workflow-integrity-planner") == (
        "framework/agents/planners/workflow-integrity-planner.md"
    )
    assert derive_specialist_relative_path("Builder", "B-08", "api-contract-builder") == (
        "framework/agents/builders/api-contract-builder.md"
    )
