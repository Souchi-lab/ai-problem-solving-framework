from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path

from apsf.core.state.run_state_repository import RunStateRepository
from apsf.core.storage.text_artifact_codec import read_text_artifact
from apsf.legacy.orchestration.phase_detector import PhaseDetector
from apsf.legacy.storage.run_repository import RunRepository


DEFAULT_DEPENDENCY_LINE_LIMIT = 100


class DependencyError(Exception):
    pass


class DependencyNotFoundError(DependencyError):
    pass


class ArtifactNotFoundError(DependencyError):
    pass


class IncompleteDependencyError(DependencyError):
    pass


@dataclass(frozen=True)
class DependencySpec:
    run_id: str
    artifact: str
    reason: str = ""


_DEPENDENCY_HEADING_RE = re.compile(r"^##\s+(depends_on|dependencies)\s*$", re.IGNORECASE)
_NEXT_HEADING_RE = re.compile(r"^##\s+")
_KV_LINE_RE = re.compile(r"^\s*-\s*(run|run_id|artifact|reason)\s*:\s*(.+?)\s*$", re.IGNORECASE)
_INDENTED_KV_LINE_RE = re.compile(r"^\s{2,}(run|run_id|artifact|reason)\s*:\s*(.+?)\s*$", re.IGNORECASE)


def parse_dependency_specs(assignment_text: str) -> list[DependencySpec]:
    section_lines = _extract_dependency_section(assignment_text)
    if not section_lines:
        return []

    specs = _parse_dependency_blocks(section_lines)
    if specs:
        return specs

    return _parse_dependency_table(section_lines)


def inject_dependency_context(
    *,
    project_root: Path,
    run_dir: Path,
    prompt_text: str,
    max_lines: int = DEFAULT_DEPENDENCY_LINE_LIMIT,
) -> str:
    assignment_path = run_dir / "execution-assignment.md"
    if not assignment_path.exists():
        return prompt_text

    specs = parse_dependency_specs(assignment_path.read_text(encoding="utf-8"))
    if not specs:
        return prompt_text

    repo = RunRepository(
        runs_dir=project_root / "runs",
        template_dir=project_root / "runs" / "_template",
    )

    injected_sections: list[str] = []
    for spec in specs:
        dep_dir = _resolve_dependency_run_dir(repo, run_dir, spec.run_id)
        phase = _read_dependency_phase(dep_dir)
        if phase != "COMPLETE":
            raise IncompleteDependencyError(
                f"dependency '{spec.run_id}' is not COMPLETE (phase={phase})"
            )
        artifact_excerpt = _read_dependency_artifact(dep_dir, spec.artifact, max_lines=max_lines)
        label = f"Dependency: {spec.run_id} -> {spec.artifact}"
        if spec.reason:
            label += f"\nReason: {spec.reason}"
        injected_sections.append(f"## {label}\n\n{artifact_excerpt}")

    return prompt_text.rstrip() + "\n\n---\n\n## Dependency Inputs\n\n" + "\n\n---\n\n".join(injected_sections) + "\n"


def dependency_status_by_run(
    *,
    project_root: Path,
    run_dir: Path,
) -> tuple[list[str], dict[str, str], bool]:
    assignment_path = run_dir / "execution-assignment.md"
    if not assignment_path.exists():
        return [], {}, False

    specs = parse_dependency_specs(assignment_path.read_text(encoding="utf-8"))
    if not specs:
        return [], {}, False

    repo = RunRepository(
        runs_dir=project_root / "runs",
        template_dir=project_root / "runs" / "_template",
    )

    depends_on: list[str] = []
    dependency_phases: dict[str, str] = {}
    has_incomplete = False
    for spec in specs:
        depends_on.append(spec.run_id)
        try:
            dep_dir = _resolve_dependency_run_dir(repo, run_dir, spec.run_id)
            phase = _read_dependency_phase(dep_dir)
        except DependencyError:
            phase = "MISSING"
        dependency_phases[spec.run_id] = phase
        if phase != "COMPLETE":
            has_incomplete = True

    return depends_on, dependency_phases, has_incomplete


def _extract_dependency_section(assignment_text: str) -> list[str]:
    lines = assignment_text.lstrip("\ufeff").splitlines()
    start_index: int | None = None
    for index, line in enumerate(lines):
        if _DEPENDENCY_HEADING_RE.match(line.strip()):
            start_index = index + 1
            break
    if start_index is None:
        return []

    section_lines: list[str] = []
    for line in lines[start_index:]:
        if _NEXT_HEADING_RE.match(line):
            break
        section_lines.append(line.rstrip("\n"))
    return section_lines


def _parse_dependency_blocks(section_lines: list[str]) -> list[DependencySpec]:
    specs: list[DependencySpec] = []
    current: dict[str, str] = {}

    def flush_current() -> None:
        run_id = current.get("run") or current.get("run_id") or ""
        artifact = current.get("artifact") or ""
        if run_id and artifact:
            specs.append(
                DependencySpec(
                    run_id=run_id.strip().strip("`"),
                    artifact=artifact.strip().strip("`"),
                    reason=current.get("reason", "").strip(),
                )
            )

    for raw_line in section_lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        match = _KV_LINE_RE.match(line) or _INDENTED_KV_LINE_RE.match(line)
        if match is None:
            continue
        key = match.group(1).lower()
        value = match.group(2).strip()
        if key in {"run", "run_id"} and current:
            flush_current()
            current = {}
        current[key] = value

    if current:
        flush_current()

    return specs


def _parse_dependency_table(section_lines: list[str]) -> list[DependencySpec]:
    specs: list[DependencySpec] = []
    table_lines = [line.strip() for line in section_lines if line.strip().startswith("|")]
    if len(table_lines) < 2:
        return specs

    header_cells = [cell.strip().lower() for cell in table_lines[0].strip("|").split("|")]
    try:
        run_index = header_cells.index("run")
        artifact_index = header_cells.index("artifact")
    except ValueError:
        return specs
    reason_index = header_cells.index("reason") if "reason" in header_cells else None

    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) <= max(run_index, artifact_index):
            continue
        run_id = cells[run_index].strip("`")
        artifact = cells[artifact_index].strip("`")
        if not run_id or not artifact:
            continue
        reason = cells[reason_index] if reason_index is not None and len(cells) > reason_index else ""
        specs.append(DependencySpec(run_id=run_id, artifact=artifact, reason=reason))
    return specs


def _resolve_dependency_run_dir(repo: RunRepository, current_run_dir: Path, run_id: str) -> Path:
    normalized = run_id.strip().strip("`")
    if not normalized:
        raise DependencyNotFoundError("dependency run id is empty")

    if "/" in normalized:
        parts = [part for part in normalized.split("/") if part]
        if len(parts) == 2:
            candidate = current_run_dir.parent / parts[1]
            if candidate.is_dir():
                return candidate
        if len(parts) == 3 and parts[0] in {"work", "fw-improvement", "verification"}:
            candidate = repo.runs_dir / parts[0] / parts[1] / parts[2]
            if candidate.is_dir():
                return candidate

    sibling_candidate = current_run_dir.parent / normalized
    if sibling_candidate.is_dir():
        return sibling_candidate

    candidate = repo.get_run_dir(normalized)
    if candidate.is_dir():
        return candidate

    raise DependencyNotFoundError(f"dependency run not found: {run_id}")


def _read_dependency_phase(run_dir: Path) -> str:
    state = RunStateRepository(run_dir).load()
    if state is not None and state.current_phase:
        return state.current_phase
    return PhaseDetector(run_dir).detect().phase.value


def _read_dependency_artifact(run_dir: Path, artifact_spec: str, *, max_lines: int) -> str:
    spec = artifact_spec.strip().strip("`")
    artifact_path = run_dir / spec
    section_name = ""
    if "#" in spec:
        file_part, section_part = spec.split("#", 1)
        artifact_path = run_dir / file_part
        section_name = section_part.strip()

    if not artifact_path.exists() or not artifact_path.is_file():
        raise ArtifactNotFoundError(f"artifact not found: {artifact_spec}")

    text = read_text_artifact(artifact_path)
    if section_name:
        extracted = _extract_markdown_section(text, section_name)
        if extracted:
            return extracted
    return _first_lines(text, max_lines=max_lines)


def _extract_markdown_section(text: str, section_name: str) -> str:
    heading_re = re.compile(rf"^##+\s+{re.escape(section_name)}\s*$", re.IGNORECASE)
    next_heading_re = re.compile(r"^##+\s+")
    lines = text.splitlines()
    collecting = False
    collected: list[str] = []
    for line in lines:
        if not collecting and heading_re.match(line.strip()):
            collecting = True
            collected.append(line)
            continue
        if collecting and next_heading_re.match(line.strip()):
            break
        if collecting:
            collected.append(line)
    return "\n".join(collected).strip()


def _first_lines(text: str, *, max_lines: int) -> str:
    lines = text.splitlines()
    return "\n".join(lines[:max_lines]).strip()
