import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from apsf.legacy.orchestration.phase_detector import PhaseDetector
from apsf.legacy.storage.run_repository import RunRepository
from apsf.viewer.viewer_db import ViewerDB

app = FastAPI(title="APSF Viewer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "runs").exists() and (current / "src").exists():
            return current
        current = current.parent
    return Path(os.getcwd())


PROJECT_ROOT = find_project_root()
repo = RunRepository(
    runs_dir=PROJECT_ROOT / "runs",
    template_dir=PROJECT_ROOT / "runs" / "_template",
)
viewer_db = ViewerDB(PROJECT_ROOT / "viewer.db")
PRIORITY_INDEX_PATH = PROJECT_ROOT / "priority-index.yaml"

RERUN_ACTION_TO_ARTIFACT = {
    "rerun-plan": "plan_review.md",
    "rerun-build": "build_review.md",
    "rerun-review": "review_review.md",
    "rerun-improve": "improve_review.md",
}

RERUN_ACTION_TO_TEMPLATE = {
    "rerun-plan": PROJECT_ROOT / "framework" / "templates" / "plan-review.md",
    "rerun-build": PROJECT_ROOT / "framework" / "templates" / "build-review.md",
    "rerun-review": PROJECT_ROOT / "framework" / "templates" / "review-review.md",
    "rerun-improve": PROJECT_ROOT / "framework" / "templates" / "improve-review.md",
}

EXECUTION_TYPE_TO_ACTION_TYPE = {
    "act": "advance",
    "build": "advance",
    "rerun": "rollback",
    "human": "guidance",
}

CODEX_BRIDGE_PRESETS: dict[str, dict[str, Any]] = {
    "finish-after-build": {
        "role_mode": "architect",
        "allowed_phases": {"BUILD_NEEDED", "REVIEW_NEEDED"},
        "required_artifacts": {"goal.md", "plan.md"},
        "full_content_artifacts": ["goal.md", "plan.md", "build.md", "handoff.md"],
        "task": (
            "Inspect the run after build-oriented work and identify the minimum "
            "remaining work needed to reach review-ready or close-ready quality."
        ),
    },
    "review-and-close": {
        "role_mode": "finisher",
        "allowed_phases": {"REVIEW_NEEDED", "IMPROVE_NEEDED", "TRANSCRIPT_RECOMMENDED"},
        "required_artifacts": {"goal.md", "build.md"},
        "full_content_artifacts": ["goal.md", "build.md", "review.md", "improve.md", "result.md", "transcript.md"],
        "task": (
            "Assess closure quality, identify thin or missing close-out artifacts, "
            "and recommend the smallest set of changes needed to close the run cleanly."
        ),
    },
}


class RunSummary(BaseModel):
    name: str
    taxonomy: str
    phase: str
    next_role: str
    child_count: int
    has_plan_review: bool
    has_build_review: bool
    has_review_review: bool
    has_improve_review: bool
    last_modified: float
    priority: Literal["Now", "Next", "Later", "Unranked"] = "Unranked"
    priority_reason: Optional[str] = None


class ArtifactPreview(BaseModel):
    name: str
    exists: bool
    size: int
    mtime: float
    preview: str


class OperatorAction(BaseModel):
    id: str
    label: str
    command: str
    execution_type: Literal["act", "build", "rerun", "human"]
    warning_level: Literal["none", "caution", "danger"] = "none"
    enabled: bool = True
    description: str = ""
    primary: bool = False
    comment_artifact: str | None = None
    requires_comment: bool = False


class RunDetail(BaseModel):
    name: str
    taxonomy: str
    phase: str
    next_role: str
    decision_reason: str
    artifacts: List[ArtifactPreview]
    operator_command: str
    operator_actions: List[OperatorAction]
    children: List["ChildRunSummary"]
    priority: Literal["Now", "Next", "Later", "Unranked"] = "Unranked"
    priority_reason: Optional[str] = None


class ChildRunSummary(BaseModel):
    name: str
    child_name: str
    phase: str
    next_role: str
    operator_command: str
    primary_action_label: str
    has_children: bool


class ExecuteCommandRequest(BaseModel):
    action_id: str


class ExecuteCommandResponse(BaseModel):
    action_id: str
    command: str
    status: Literal["SUCCESS", "PARTIAL", "FAILED", "HUMAN"]
    exit_code: int
    stdout: str
    stderr: str


class SaveRerunCommentRequest(BaseModel):
    action_id: str
    comment_text: str


class SaveRerunCommentResponse(BaseModel):
    action_id: str
    artifact_name: str
    artifact_path: str
    appended_at: str


class ActionExecutionRecord(BaseModel):
    id: int
    taxonomy: str
    run_name: str
    action_id: str
    action_type: str
    command: str
    triggered_at: str
    finished_at: Optional[str]
    result_status: str
    exit_code: Optional[int]
    stdout_summary: Optional[str]
    stderr_summary: Optional[str]


class ExecutionLogResponse(BaseModel):
    execution_id: int
    available: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    stdout_summary: Optional[str] = None
    stderr_summary: Optional[str] = None


class RerunCommentRecord(BaseModel):
    id: int
    taxonomy: str
    run_name: str
    action_id: str
    execution_id: Optional[int]
    comment_artifact: str
    comment_body: str
    created_at: str


class RunHistoryResponse(BaseModel):
    latest_execution: Optional[ActionExecutionRecord]
    latest_rerun_comment: Optional[RerunCommentRecord]


class CodexBridgeRequest(BaseModel):
    preset_id: Literal["finish-after-build", "review-and-close"]


class CodexArtifactUpdate(BaseModel):
    artifact_name: str
    operation: Literal["propose"] = "propose"


class CodexBridgeResponse(BaseModel):
    status: Literal["completed", "review_required", "blocked"]
    summary: str
    next_steps: List[str]
    suggested_action_id: Optional[str] = None
    preset_id: str
    role_mode: Literal["architect", "finisher"]
    provider: str
    model: str
    artifact_updates: List[CodexArtifactUpdate] = []


class MatrixRow(BaseModel):
    name: str
    taxonomy: str
    phase: str
    next_role: str
    priority: Literal["Now", "Next", "Later", "Unranked"] = "Unranked"
    priority_reason: Optional[str] = None
    plan_action: Optional[OperatorAction] = None
    build_action: Optional[OperatorAction] = None
    review_action: Optional[OperatorAction] = None
    rerun_action: Optional[OperatorAction] = None


def load_priority_index() -> dict[str, dict[str, str]]:
    if not PRIORITY_INDEX_PATH.exists():
        return {}

    priorities: dict[str, dict[str, str]] = {}
    current_run: str | None = None
    in_runs = False

    for raw_line in PRIORITY_INDEX_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "runs:":
            in_runs = True
            continue
        if not in_runs:
            continue

        if line.startswith("  ") and stripped.endswith(":") and not line.startswith("    "):
            current_run = stripped[:-1]
            priorities[current_run] = {}
            continue

        if current_run and line.startswith("    ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            priorities[current_run][key.strip()] = value.strip().strip("'\"")

    return priorities


def resolve_priority(run_name: str, priority_index: dict[str, dict[str, str]]) -> tuple[str, Optional[str]]:
    record = priority_index.get(run_name, {})
    priority = record.get("priority", "Unranked")
    if priority not in {"Now", "Next", "Later"}:
        priority = "Unranked"
    return priority, record.get("reason")


def build_operator_actions(run_name: str, phase: str) -> List[OperatorAction]:
    actions: List[OperatorAction] = []
    # Use the full run_name (e.g. "work/run-name") so CLI tools can resolve it via RunRepository
    command_run_name = run_name

    if phase == "PLAN_NEEDED":
        actions.append(
            OperatorAction(
                id="phase-primary",
                label="Run Planner",
                command=f".\\scripts\\apsf-claude-act.ps1 {command_run_name}",
                execution_type="act",
                description="Run Planner and write plan.md.",
                primary=True,
            )
        )
    elif phase == "BUILD_NEEDED":
        actions.append(
            OperatorAction(
                id="phase-primary",
                label="Run Builder",
                command=f".\\scripts\\apsf-claude-build.ps1 {command_run_name}",
                execution_type="build",
                warning_level="caution",
                description="Run the dedicated Builder path for BUILD_NEEDED.",
                primary=True,
            )
        )
        actions.append(
            OperatorAction(
                id="phase-build-guidance",
                label="Show Build Guidance",
                command=f"apsf build {command_run_name}",
                execution_type="human",
                warning_level="caution",
                enabled=False,
                description="Guidance-only command that prints the recommended build path.",
            )
        )
    elif phase == "REVIEW_NEEDED":
        actions.append(
            OperatorAction(
                id="phase-primary",
                label="Run Critic",
                command=f".\\scripts\\apsf-claude-act.ps1 {command_run_name}",
                execution_type="act",
                description="Run Critic and write review.md.",
                primary=True,
            )
        )
    elif phase == "IMPROVE_NEEDED":
        actions.append(
            OperatorAction(
                id="phase-primary",
                label="Judge Manually",
                command=f"apsf next {command_run_name}",
                execution_type="human",
                warning_level="caution",
                enabled=False,
                description="Judge remains human-owned. Use apsf next for guidance.",
                primary=True,
            )
        )
    else:
        actions.append(
            OperatorAction(
                id="phase-primary",
                label="Show Next Guidance",
                command=f"apsf next {command_run_name}",
                execution_type="human",
                enabled=False,
                description="Use apsf next to inspect the next safe step.",
                primary=True,
            )
        )

    actions.extend(
        [
            OperatorAction(
                id="rerun-plan",
                label="Rerun Plan",
                command=f".\\scripts\\apsf-rerun-plan.ps1 {command_run_name}",
                execution_type="rerun",
                warning_level="danger",
                description="Write feedback to plan_review.md, then reset the run to PLAN_NEEDED.",
                comment_artifact="plan_review.md",
                requires_comment=True,
            ),
            OperatorAction(
                id="rerun-build",
                label="Rerun Build",
                command=f".\\scripts\\apsf-rerun-build.ps1 {command_run_name}",
                execution_type="rerun",
                warning_level="danger",
                description="Write feedback to build_review.md, then reset the run to BUILD_NEEDED.",
                comment_artifact="build_review.md",
                requires_comment=True,
            ),
            OperatorAction(
                id="rerun-review",
                label="Rerun Review",
                command=f".\\scripts\\apsf-rerun-review.ps1 {command_run_name}",
                execution_type="rerun",
                warning_level="danger",
                description="Write feedback to review_review.md, then reset the run to REVIEW_NEEDED.",
                comment_artifact="review_review.md",
                requires_comment=True,
            ),
            OperatorAction(
                id="rerun-improve",
                label="Rerun Improve",
                command=f".\\scripts\\apsf-rerun-improve.ps1 {command_run_name}",
                execution_type="rerun",
                warning_level="danger",
                description="Write feedback to improve_review.md, then reset the run to IMPROVE_NEEDED.",
                comment_artifact="improve_review.md",
                requires_comment=True,
            ),
        ]
    )

    return actions


def build_child_summaries(parent_name: str, taxonomy: str | None) -> List[ChildRunSummary]:
    children: List[ChildRunSummary] = []
    for child_name in repo.list_child_runs(parent_name, taxonomy=taxonomy):
        full_name = f"{parent_name}/{child_name}"
        child_dir = repo.get_child_run_dir(parent_name, child_name, taxonomy=taxonomy)
        info = PhaseDetector(child_dir).detect()
        actions = build_operator_actions(full_name, info.phase.value)
        primary_action = next((action for action in actions if action.primary), actions[0])
        children.append(
            ChildRunSummary(
                name=full_name,
                child_name=child_name,
                phase=info.phase.value,
                next_role=info.next_role,
                operator_command=primary_action.command,
                primary_action_label=primary_action.label,
                has_children=False,
            )
        )
    return children


def _resolve_run_dir(taxonomy: str, run_name: str) -> Path:
    if "/" in run_name:
        parent, child = run_name.split("/")
        return repo.get_child_run_dir(parent, child, taxonomy=taxonomy)
    return repo.get_run_dir(run_name, taxonomy=taxonomy)


def _ensure_review_artifact(run_dir: Path, action_id: str) -> Path:
    artifact_name = RERUN_ACTION_TO_ARTIFACT.get(action_id)
    if artifact_name is None:
        raise HTTPException(status_code=400, detail="Unknown rerun action")

    artifact_path = run_dir / artifact_name
    if artifact_path.exists():
        return artifact_path

    template_path = RERUN_ACTION_TO_TEMPLATE.get(action_id)
    if template_path is None:
        raise HTTPException(status_code=500, detail=f"No scaffold template mapping configured for {action_id}")
    if not template_path.exists():
        raise HTTPException(status_code=500, detail=f"Scaffold template not found: {template_path}")

    artifact_path.write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")
    return artifact_path


def _append_rerun_comment(run_dir: Path, action_id: str, comment_text: str) -> tuple[str, Path, str]:
    normalized = comment_text.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Comment text is required")

    artifact_path = _ensure_review_artifact(run_dir, action_id)
    artifact_name = artifact_path.name
    appended_at = datetime.now(timezone.utc).isoformat()
    block = (
        "\n\n## Rerun Comment\n"
        f"<!-- {appended_at} -->\n\n"
        f"{normalized}\n"
    )
    with artifact_path.open("a", encoding="utf-8") as handle:
        handle.write(block)

    return artifact_name, artifact_path, appended_at


def _run_powershell_command(command: str) -> subprocess.CompletedProcess[str]:
    powershell = os.path.join(
        os.environ.get("WINDIR", r"C:\Windows"),
        "System32",
        "WindowsPowerShell",
        "v1.0",
        "powershell.exe",
    )
    # Prefix the command with a process-level execution policy bypass to ensure scripts can run
    full_command = f"Set-ExecutionPolicy Bypass -Scope Process -Force; {command}"
    
    return subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", full_command],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )


def _read_artifact_preview(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")[:500]
    except Exception:
        return "[Error reading file]"


def _build_artifact_inventory(run_dir: Path) -> List[ArtifactPreview]:
    artifacts: List[ArtifactPreview] = []
    target_files = [
        "goal.md",
        "execution-assignment.md",
        "model-assignment.md",
        "plan_review.md",
        "plan.md",
        "handoff.md",
        "build_review.md",
        "build.md",
        "review_review.md",
        "review.md",
        "improve_review.md",
        "improve.md",
        "result.md",
        "transcript.md",
    ]

    for filename in target_files:
        path = run_dir / filename
        if path.exists():
            artifacts.append(
                ArtifactPreview(
                    name=filename,
                    exists=True,
                    size=path.stat().st_size,
                    mtime=path.stat().st_mtime,
                    preview=_read_artifact_preview(path),
                )
            )
        else:
            artifacts.append(
                ArtifactPreview(
                    name=filename,
                    exists=False,
                    size=0,
                    mtime=0,
                    preview="",
                )
            )
    return artifacts


def _collect_run_detail(taxonomy: str, run_name: str, run_dir: Path) -> RunDetail:
    info = PhaseDetector(run_dir).detect()
    actions = build_operator_actions(run_name, info.phase.value)
    primary_action = next((action for action in actions if action.primary), actions[0])
    child_summaries = []
    if "/" not in run_name:
        child_summaries = build_child_summaries(run_name, taxonomy)
    priority_index = load_priority_index()
    priority, priority_reason = resolve_priority(run_name, priority_index)
    return RunDetail(
        name=run_name,
        taxonomy=taxonomy,
        phase=info.phase.value,
        next_role=info.next_role,
        decision_reason=info.decision_reason,
        artifacts=_build_artifact_inventory(run_dir),
        operator_command=primary_action.command,
        operator_actions=actions,
        children=child_summaries,
        priority=priority,
        priority_reason=priority_reason,
    )


def _build_matrix_rows() -> list[MatrixRow]:
    priority_index = load_priority_index()
    rows: list[MatrixRow] = []
    for full_name in repo.list_all_runs(taxonomy=None):
        if "/" in full_name:
            continue

        run_dir = repo.get_run_dir(full_name)
        if not run_dir.exists():
            continue

        info = PhaseDetector(run_dir).detect()
        taxonomy = "legacy"
        if "fw-improvement" in str(run_dir):
            taxonomy = "fw-improvement"
        elif "work" in str(run_dir):
            taxonomy = "work"

        actions = build_operator_actions(full_name, info.phase.value)
        action_map = {action.id: action for action in actions}
        priority, priority_reason = resolve_priority(full_name, priority_index)
        rows.append(
            MatrixRow(
                name=full_name,
                taxonomy=taxonomy,
                phase=info.phase.value,
                next_role=info.next_role,
                priority=priority,
                priority_reason=priority_reason,
                plan_action=action_map.get("phase-primary") if info.phase.value == "PLAN_NEEDED" else None,
                build_action=action_map.get("phase-primary") if info.phase.value == "BUILD_NEEDED" else None,
                review_action=action_map.get("phase-primary") if info.phase.value == "REVIEW_NEEDED" else None,
                rerun_action=(
                    action_map.get("rerun-plan")
                    if info.phase.value == "PLAN_NEEDED"
                    else action_map.get("rerun-build")
                    if info.phase.value == "BUILD_NEEDED"
                    else action_map.get("rerun-review")
                    if info.phase.value == "REVIEW_NEEDED"
                    else action_map.get("rerun-improve")
                    if info.phase.value == "IMPROVE_NEEDED"
                    else None
                ),
            )
        )
    priority_order = {"Now": 0, "Next": 1, "Later": 2, "Unranked": 3}
    rows.sort(key=lambda item: (priority_order.get(item.priority, 3), item.name))
    return rows


def _artifact_exists(detail: RunDetail, artifact_name: str) -> bool:
    return any(artifact.name == artifact_name and artifact.exists for artifact in detail.artifacts)


def _load_run_history(taxonomy: str, run_name: str) -> RunHistoryResponse:
    latest_exec = viewer_db.get_latest_execution(taxonomy, run_name)
    latest_comment = viewer_db.get_latest_rerun_comment(taxonomy, run_name)
    return RunHistoryResponse(
        latest_execution=ActionExecutionRecord(**latest_exec) if latest_exec else None,
        latest_rerun_comment=RerunCommentRecord(**latest_comment) if latest_comment else None,
    )


def _get_codex_bridge_cli() -> tuple[str, str]:
    configured = os.getenv("CODEX_BRIDGE_CLI", "").strip()
    candidates = (
        [configured]
        if configured
        else [
            "claude.cmd",
            "claude",
            "claude.ps1",
            "codex.cmd",
            "codex",
            "codex.ps1",
        ]
    )

    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate)
        if resolved:
            stem = Path(resolved).stem
            if stem.lower() == "claude":
                default_label = "claude"
            elif stem.lower() == "codex":
                default_label = "codex"
            else:
                default_label = stem
            label = os.getenv("CODEX_BRIDGE_CLI_LABEL", "").strip() or default_label
            return resolved, label

    raise HTTPException(
        status_code=503,
        detail="No Codex bridge CLI found. Set CODEX_BRIDGE_CLI or install a supported CLI such as codex or claude.",
    )


def _build_codex_prompt(
    preset_id: str,
    preset: dict[str, Any],
    detail: RunDetail,
    history: RunHistoryResponse,
) -> str:
    full_content_artifacts: dict[str, str] = {}
    run_dir = _resolve_run_dir(detail.taxonomy, detail.name)
    for artifact_name in preset["full_content_artifacts"]:
        artifact_path = run_dir / artifact_name
        if artifact_path.exists():
            full_content_artifacts[artifact_name] = artifact_path.read_text(encoding="utf-8")

    bridge_payload = {
        "preset_id": preset_id,
        "role_mode": preset["role_mode"],
        "framework": {
            "name": "APSF",
            "operating_rules": [
                "Treat run artifacts as the source of truth.",
                "Respect current phase boundaries and do not widen scope.",
                "Prefer the smallest safe next step over broad redesign.",
                "Do not assume file edits or command execution unless explicitly requested later.",
                "When judging close quality, focus on missing artifacts, stale artifacts, and clear next actions.",
            ],
        },
        "run": {
            "taxonomy": detail.taxonomy,
            "name": detail.name,
            "phase": detail.phase,
            "next_role": detail.next_role,
            "decision_reason": detail.decision_reason,
        },
        "target": {
            "kind": "run",
            "name": detail.name,
        },
        "artifacts": [artifact.model_dump() for artifact in detail.artifacts if artifact.exists],
        "history": history.model_dump(),
        "children": [child.model_dump() for child in detail.children],
        "instructions": {
            "task": preset["task"],
            "write_scope": "advisory only; do not assume file writes",
            "safety_mode": "no-generic-orchestration",
        },
        "full_content_artifacts": full_content_artifacts,
    }

    return (
        "You are the APSF Viewer Codex bridge.\n"
        f"Preset: {preset_id}\n"
        f"Role mode: {preset['role_mode']}\n"
        "Stay within the narrow Codex bridge scope. Do not propose generic orchestration.\n"
        "Assume APSF is artifact-driven: goal/plan/build/review/improve/result files define the current truth.\n"
        "Do not reopen strategy or redesign the framework unless the artifacts explicitly show a blocker.\n"
        "Your job is to produce APSF-aware advisory output, not to perform actions directly.\n"
        "Return JSON only, with no markdown fences or extra commentary.\n"
        'Required JSON shape: {"summary":"string","next_steps":["string"],"status":"completed|review_required|blocked","suggested_action_id":"string|null","artifact_updates":[{"artifact_name":"string","operation":"propose"}]}\n'
        'Only emit `suggested_action_id` when you are confident it matches one existing APSF action ID for this target. Otherwise emit null. Valid v1 values: "phase-primary", "rerun-plan", "rerun-build", "rerun-review", "rerun-improve".\n'
        f"Context:\n{json.dumps(bridge_payload, ensure_ascii=False, indent=2)}"
    )


def _normalize_codex_bridge_response(raw_text: str) -> dict[str, Any]:
    raw_text = raw_text.strip()
    parsed: Any = None
    if raw_text:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(raw_text[start : end + 1])
                except json.JSONDecodeError:
                    parsed = None

    if not isinstance(parsed, dict):
        return {
            "summary": raw_text[:800] or "Codex bridge returned an empty response.",
            "next_steps": [],
            "status": "review_required" if raw_text else "blocked",
            "suggested_action_id": None,
            "artifact_updates": [],
        }

    summary = str(parsed.get("summary") or raw_text[:800] or "Codex response could not be summarized.").strip()
    status = parsed.get("status")
    if status not in {"completed", "review_required", "blocked"}:
        status = "review_required"

    normalized_steps = [str(step).strip() for step in (parsed.get("next_steps") or []) if str(step).strip()]
    suggested_action_id = parsed.get("suggested_action_id")
    if not isinstance(suggested_action_id, str) or not suggested_action_id.strip():
        suggested_action_id = None
    else:
        suggested_action_id = suggested_action_id.strip()
    normalized_updates: List[dict[str, str]] = []
    for item in parsed.get("artifact_updates") or []:
        if not isinstance(item, dict):
            continue
        artifact_name = str(item.get("artifact_name", "")).strip()
        if not artifact_name:
            continue
        normalized_updates.append({"artifact_name": artifact_name, "operation": "propose"})

    return {
        "summary": summary,
        "next_steps": normalized_steps,
        "status": status,
        "suggested_action_id": suggested_action_id,
        "artifact_updates": normalized_updates,
    }


def _run_codex_bridge_cli(prompt: str) -> tuple[str, str]:
    cli_path, cli_label = _get_codex_bridge_cli()
    cli_name = Path(cli_path).stem.lower()
    if cli_name == "codex":
        profile = os.getenv("CODEX_BRIDGE_PROFILE", "").strip()
        args = [cli_path, "exec", "-"]
        if profile:
            args.extend(["--profile", profile])
    else:
        args = [cli_path, "-p"]

    temp_root = PROJECT_ROOT / ".tmp" / "viewer-codex-bridge"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_path = Path(
        tempfile.mkstemp(prefix="bridge-", suffix=".prompt.md", dir=str(temp_root))[1]
    )
    temp_path.write_text(prompt, encoding="utf-8")

    try:
        completed = subprocess.run(
            args,
            input=temp_path.read_text(encoding="utf-8"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(PROJECT_ROOT),
            timeout=30,
        )
    except subprocess.TimeoutExpired as error:
        raise TimeoutError from error
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    combined = f"{stdout}\n{stderr}".strip()
    if completed.returncode != 0:
        raise HTTPException(status_code=502, detail=f"Codex bridge CLI failed: {combined[:800] or f'{cli_name} exited {completed.returncode}'}")

    return stdout, cli_label


async def _invoke_codex_bridge(detail: RunDetail, history: RunHistoryResponse, preset_id: str) -> CodexBridgeResponse:
    preset = CODEX_BRIDGE_PRESETS[preset_id]
    prompt = _build_codex_prompt(preset_id, preset, detail, history)

    try:
        content, cli_label = await asyncio.wait_for(asyncio.to_thread(_run_codex_bridge_cli, prompt), timeout=35)
    except TimeoutError:
        return CodexBridgeResponse(
            status="blocked",
            summary="Codex CLI invocation timed out.",
            next_steps=[],
            suggested_action_id=None,
            preset_id=preset_id,
            role_mode=preset["role_mode"],
            provider="cli",
            model="timeout",
            artifact_updates=[],
        )

    normalized = _normalize_codex_bridge_response(content)
    return CodexBridgeResponse(
        status=normalized["status"],
        summary=normalized["summary"],
        next_steps=normalized["next_steps"],
        suggested_action_id=normalized["suggested_action_id"],
        preset_id=preset_id,
        role_mode=preset["role_mode"],
        provider="cli",
        model=cli_label,
        artifact_updates=[CodexArtifactUpdate(**item) for item in normalized["artifact_updates"]],
    )


@app.get("/api/runs", response_model=List[RunSummary])
async def list_runs():
    runs: List[RunSummary] = []
    priority_index = load_priority_index()
    for full_name in repo.list_all_runs(taxonomy=None):
        if "/" in full_name:
            continue

        run_dir = repo.get_run_dir(full_name)
        name = full_name

        if not run_dir.exists():
            continue

        info = PhaseDetector(run_dir).detect()
        taxonomy = "legacy"
        if "fw-improvement" in str(run_dir):
            taxonomy = "fw-improvement"
        elif "work" in str(run_dir):
            taxonomy = "work"

        priority, priority_reason = resolve_priority(name, priority_index)
        runs.append(
            RunSummary(
                name=name,
                taxonomy=taxonomy,
                phase=info.phase.value,
                next_role=info.next_role,
                child_count=len(repo.list_child_runs(name, taxonomy=taxonomy)),
                has_plan_review=(run_dir / "plan_review.md").exists(),
                has_build_review=(run_dir / "build_review.md").exists(),
                has_review_review=(run_dir / "review_review.md").exists(),
                has_improve_review=(run_dir / "improve_review.md").exists(),
                last_modified=run_dir.stat().st_mtime,
                priority=priority,
                priority_reason=priority_reason,
            )
        )

    priority_order = {"Now": 0, "Next": 1, "Later": 2, "Unranked": 3}
    runs.sort(key=lambda item: (priority_order.get(item.priority, 3), -item.last_modified))
    return runs


@app.get("/api/operator-matrix", response_model=List[MatrixRow])
async def get_operator_matrix():
    return _build_matrix_rows()


@app.get("/api/executions/recent", response_model=List[ActionExecutionRecord])
async def get_recent_executions(limit: int = 12, top_level_only: bool = True):
    rows = viewer_db.list_recent_executions(limit=limit, top_level_only=top_level_only)
    return [ActionExecutionRecord(**row) for row in rows]


@app.get("/api/executions/{execution_id}/log", response_model=ExecutionLogResponse)
async def get_execution_log(execution_id: int):
    row = viewer_db.get_execution_log(execution_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    stdout_full = row.get("stdout_full") or ""
    stderr_full = row.get("stderr_full") or ""
    available = bool(stdout_full or stderr_full)
    return ExecutionLogResponse(
        execution_id=execution_id,
        available=available,
        stdout=stdout_full if available else None,
        stderr=stderr_full if available else None,
        stdout_summary=row.get("stdout_summary"),
        stderr_summary=row.get("stderr_summary"),
    )


@app.get("/api/runs/{taxonomy}/{run_name:path}/artifacts/{filename}")
async def get_artifact_content(taxonomy: str, run_name: str, filename: str):
    run_dir = _resolve_run_dir(taxonomy, run_name)
    path = run_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"content": path.read_text(encoding="utf-8")}


@app.get("/api/runs/{taxonomy}/{run_name:path}/history", response_model=RunHistoryResponse)
async def get_run_history(taxonomy: str, run_name: str):
    return _load_run_history(taxonomy, run_name)


@app.get("/api/runs/{taxonomy}/{run_name:path}", response_model=RunDetail)
async def get_run_detail(taxonomy: str, run_name: str):
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    return _collect_run_detail(taxonomy, run_name, run_dir)


@app.post("/api/runs/{taxonomy}/{run_name:path}/rerun-comment", response_model=SaveRerunCommentResponse)
async def save_rerun_comment(taxonomy: str, run_name: str, request: SaveRerunCommentRequest):
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    artifact_name, artifact_path, appended_at = _append_rerun_comment(run_dir, request.action_id, request.comment_text)

    comment_artifact = RERUN_ACTION_TO_ARTIFACT.get(request.action_id, "")
    viewer_db.insert_rerun_comment(
        taxonomy=taxonomy,
        run_name=run_name,
        action_id=request.action_id,
        comment_artifact=comment_artifact,
        comment_body=request.comment_text.strip(),
    )

    return SaveRerunCommentResponse(
        action_id=request.action_id,
        artifact_name=artifact_name,
        artifact_path=str(artifact_path),
        appended_at=appended_at,
    )


@app.post("/api/runs/{taxonomy}/{run_name:path}/commands/execute", response_model=ExecuteCommandResponse)
async def execute_operator_command(taxonomy: str, run_name: str, request: ExecuteCommandRequest):
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    info = PhaseDetector(run_dir).detect()
    actions = {action.id: action for action in build_operator_actions(run_name, info.phase.value)}
    action = actions.get(request.action_id)
    if action is None:
        raise HTTPException(status_code=400, detail="Unknown action")
    if not action.enabled or action.execution_type == "human":
        raise HTTPException(status_code=400, detail="Action is guidance-only and cannot be executed")

    action_type = EXECUTION_TYPE_TO_ACTION_TYPE.get(action.execution_type, "advance")
    execution_id = viewer_db.insert_execution_pending(
        taxonomy=taxonomy,
        run_name=run_name,
        action_id=action.id,
        action_type=action_type,
        command=action.command,
    )

    completed = await asyncio.to_thread(_run_powershell_command, action.command)
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    combined = f"{stdout}\n{stderr}"
    combined_lower = combined.lower()
    partial_markers = (
        "reached max turns",
        "reached max turns before completing the build",
        "partial file edits may exist",
    )
    if completed.returncode == 2 or any(marker in combined_lower for marker in partial_markers):
        status: Literal["SUCCESS", "PARTIAL", "FAILED", "HUMAN"] = "PARTIAL"
    elif completed.returncode == 0:
        status = "SUCCESS"
    else:
        status = "FAILED"

    viewer_db.update_execution_result(
        execution_id=execution_id,
        result_status=status,
        exit_code=completed.returncode,
        stdout=stdout,
        stderr=stderr,
    )

    return ExecuteCommandResponse(
        action_id=action.id,
        command=action.command,
        status=status,
        exit_code=completed.returncode,
        stdout=stdout,
        stderr=stderr,
    )


@app.post("/api/runs/{taxonomy}/{run_name:path}/codex-bridge", response_model=CodexBridgeResponse)
async def invoke_codex_bridge(taxonomy: str, run_name: str, request: CodexBridgeRequest):
    preset = CODEX_BRIDGE_PRESETS.get(request.preset_id)
    if preset is None:
        raise HTTPException(status_code=400, detail="Unknown preset")

    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    detail = _collect_run_detail(taxonomy, run_name, run_dir)
    if detail.phase not in preset["allowed_phases"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "preset_not_allowed_in_phase",
                "current_phase": detail.phase,
                "allowed_phases": sorted(preset["allowed_phases"]),
            },
        )

    missing_artifacts = sorted(
        artifact_name
        for artifact_name in preset["required_artifacts"]
        if not _artifact_exists(detail, artifact_name)
    )
    if missing_artifacts:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_required_artifacts",
                "missing_artifacts": missing_artifacts,
            },
        )

    history = _load_run_history(taxonomy, run_name)
    return await _invoke_codex_bridge(detail, history, request.preset_id)


frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
else:

    @app.get("/")
    async def root():
        return {"message": "APSF Viewer API is running. Frontend not built. Run 'npm run build' in src/apsf/viewer/frontend"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
