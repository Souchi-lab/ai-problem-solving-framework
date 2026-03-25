from pathlib import Path

from apsf.cli.specialist_registry import (
    extract_primary_ctype,
    extract_primary_ptype,
    load_specialist_content,
    normalize_ctype,
    normalize_ptype,
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
