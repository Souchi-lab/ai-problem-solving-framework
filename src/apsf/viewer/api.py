import asyncio
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None

from apsf.core.advisory import (
    CANONICAL_JUDGE_ADVISORY_SOURCE,
    JUDGE_ADVISORY_FILE as _JUDGE_ADVISORY_FILE_CORE,
    JUDGE_ADVISORY_RECOMMENDATIONS,
    canonical_judge_advisory_payload,
    write_canonical_judge_advisory,
)
from apsf.core.ownership import (
    BlockerOwnership,
    TransitionOutcomeRecord,
    TransitionType,
    write_transition_outcome,
)
from apsf.core.dependencies.run_dependencies import dependency_status_by_run
from apsf.core.storage.text_artifact_codec import (
    normalize_text_artifact_to_utf8,
    read_text_artifact,
)
from apsf.core.runs.child_run_initializer import initialize_child_run
from apsf.legacy.orchestration.phase_detector import PhaseDetector
from apsf.legacy.orchestration.rebuild_feedback import (
    get_build_gate_decision,
    latest_review_artifact,
)
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
VIEWER_CONFIG_PATH = PROJECT_ROOT / "viewer.config.json"
AGENT_OS_CANONICAL_SNAPSHOT_ARTIFACTS = (
    "goal.md",
    "plan.md",
    "build.md",
    "review.md",
    "result.md",
)

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
ACT_EXECUTION_MODES = {"wrapper", "provider"}
WRAPPER_BACKEND_ALIASES = {
    "claude": "claude-cli",
    "claude-cli": "claude-cli",
    "codex": "codex-cli",
    "codex-cli": "codex-cli",
}
ACT_WRAPPER_BACKENDS = {"claude-cli", "codex-cli"}
BUILD_WRAPPER_BACKENDS = {"claude-cli", "codex-cli"}
ACT_CODEX_BRIDGE_PHASES = frozenset({"PLAN_NEEDED"})

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
    human_blocker_active: bool = False


class ViewerConfigResponse(BaseModel):
    execution_mode: Literal["wrapper", "provider"]
    cli_tool_mode: Literal["claude", "codex", "both"]
    act_wrapper_backend: Literal["claude-cli", "codex-cli"]
    build_wrapper_backend: Literal["claude-cli", "codex-cli"]
    config_path: str
    config_exists: bool
    dotenv_path: str
    dotenv_exists: bool
    settings_path: str
    framework_root: str
    runs_dir: str
    template_dir: str
    default_openai_model: str
    default_anthropic_model: str
    default_gemini_model: str
    openai_api_key_configured: bool
    anthropic_api_key_configured: bool
    gemini_api_key_configured: bool
    execution_mode_source: Literal["env", "viewer_config", "default"]
    act_wrapper_backend_source: Literal["env", "viewer_config", "default"]
    build_wrapper_backend_source: Literal["env", "viewer_config", "default"]
    build_max_turns: int
    run_detail_refresh_ms: int


class ViewerConfigUpdateRequest(BaseModel):
    execution_mode: Optional[Literal["wrapper", "provider"]] = None
    cli_tool_mode: Optional[Literal["claude", "codex", "both"]] = None
    build_max_turns: Optional[int] = None
    run_detail_refresh_ms: Optional[int] = None


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
    execution_type: Literal["act", "build", "rerun", "human", "accept"]
    warning_level: Literal["none", "caution", "danger"] = "none"
    enabled: bool = True
    description: str = ""
    primary: bool = False
    comment_artifact: str | None = None
    requires_comment: bool = False


class SpecialistVisibility(BaseModel):
    """Assignment visibility for the current phase's specialist selection.

    mode:
    - explicit: P-TYPE / C-TYPE assigned explicitly in execution-assignment.md
    - inferred: selected by keyword match against goal.md
    - unresolved: no match; falls back to generic specialist content
    - not_applicable: phase does not use specialist selection

    has_gap is True when specialist is unresolved OR explicitly assigned but file is missing.
    """

    phase: str
    mode: Literal["explicit", "inferred", "unresolved", "not_applicable"]
    specialist_code: str  # e.g. "P-07", "C-01", or "" when not selected
    reason: str
    has_gap: bool


class ExecutionVisibility(BaseModel):
    role: str
    execution_type: Literal["cli", "human", "future-api", "not_applicable"]
    target: str
    workspace: str
    mode: Literal["explicit", "default", "not_applicable"]
    reason: str


class ModelVisibility(BaseModel):
    role: str
    provider: str
    model: str
    mode: Literal["explicit", "default", "human", "auto", "wrapper-backed", "unset", "not_applicable"]
    reason: str


class AssignmentSummary(BaseModel):
    phase: str
    role: str
    execution: ExecutionVisibility
    model: ModelVisibility


class JudgeRecommendation(BaseModel):
    decision: Literal["Adopt", "Revise", "Reject", "Unknown"]
    suggested_action_id: str | None = None
    suggested_action_label: str | None = None
    suggested_return_phase: str | None = None
    target_role: str | None = None
    target_execution_type: str | None = None
    target_provider: str | None = None
    target_model: str | None = None
    target_specialist_code: str | None = None
    target_specialist_mode: str | None = None
    confidence: Literal["low", "medium", "high"] = "low"
    rationale: str
    review_verdict: str | None = None
    counts_note: str | None = None
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    human_owned_blocker: bool = False
    human_blocker_summary: str | None = None
    human_blocker_source: str | None = None
    human_actions: List[str] = []
    ownership_status: str | None = None
    ownership_detail: str | None = None


class ReviewSummary(BaseModel):
    available: bool = False
    summary_status: Literal["blocking", "revise", "adopt", "unknown"] | None = None
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    review_verdict: str | None = None
    counts_note: str | None = None
    next_actions: List[str] = []
    source_artifact: str | None = None


class HumanBlockerStatus(BaseModel):
    active: bool = False
    summary: str | None = None
    source: str | None = None
    actions: List[str] = []
    ownership_status: str | None = None
    ownership_detail: str | None = None


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
    specialist_visibility: SpecialistVisibility
    assignment_summary: AssignmentSummary
    review_summary: ReviewSummary | None = None
    judge_recommendation: JudgeRecommendation | None = None
    human_blocker: HumanBlockerStatus | None = None
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
    depends_on: List[str] = []
    dependency_phases: dict[str, str] = {}
    has_incomplete_dependencies: bool = False


class CreateChildRunRequest(BaseModel):
    run_id: str
    taxonomy: str
    title: str
    goal: str


class CreateChildRunResponse(BaseModel):
    run_id: str
    path: str
    status: Literal["created"]


class ExecuteCommandRequest(BaseModel):
    action_id: str


class ExecuteAgentOSActionRequest(BaseModel):
    action_id: Literal[
        "act",
        "capture-snapshot",
        "capture-checkpoint",
        "apply-snapshot",
        "apply-checkpoint",
    ]
    snapshot_id: Optional[str] = None
    checkpoint_id: Optional[str] = None
    reason: Optional[str] = None
    confirmed: bool = False


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


class SpecialistCandidateItem(BaseModel):
    code: str           # e.g. "P-06" or "" for generic
    name: str           # e.g. "design-planner" or "generic"
    score: int
    reason: str
    use_when: str       # first line of "Use This Specialist When"
    path: str | None = None
    scope: str = ""
    out_of_scope: str = ""
    evaluation_criteria: str = ""
    is_recommended: bool
    is_current: bool    # True when this code is already explicitly confirmed


class SpecialistCandidatesResponse(BaseModel):
    phase: str
    role: str
    current_mode: str   # explicit | inferred | unresolved | not_applicable
    current_code: str   # "" if not confirmed
    candidates: List[SpecialistCandidateItem]


class ConfirmSpecialistRequest(BaseModel):
    role: Literal["Planner", "Builder", "Critic"] = "Planner"
    specialist_code: str   # e.g. "P-06" or "" for generic
    source: str = "operator-accept"
    provider: str = ""
    model: str = ""
    apply_model_assignment: bool = False


class ConfirmSpecialistResponse(BaseModel):
    written: bool
    specialist_code: str
    artifact_path: str
    target_run_name: str
    model_artifact_path: str | None = None


class CreateSpecialistRequest(BaseModel):
    role: Literal["Planner", "Builder", "Critic"]
    specialist_code: str
    slug: str
    title: str
    scope: str
    use_when: str
    out_of_scope: str
    evaluation_criteria: str
    source: str = "operator-authoring"


class CreateSpecialistResponse(BaseModel):
    created: bool
    role: Literal["Planner", "Builder", "Critic"]
    specialist_code: str
    title: str
    scope: str
    use_when: str
    out_of_scope: str
    evaluation_criteria: str
    relative_path: str
    registry_path: str
    mapping_name: str
    assigned_to_run: bool = False


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


# ── Agent OS models ────────────────────────────────────────────────────────

class RunStateInfo(BaseModel):
    run_id: str
    current_phase: str
    phase_status: str
    current_owner: str
    retry_count: int
    last_error: str
    active_handoff_id: str
    gate_failures: List[str] = []


class ArtifactEntryInfo(BaseModel):
    artifact_name: str
    artifact_type: str
    owner_role: str
    written_by: str
    status: str
    updated_at: str
    revision: int
    source_handoff_id: str


class GateResultInfo(BaseModel):
    gate_type: str
    passed: bool
    reason: str


class ForceAuditEntryInfo(BaseModel):
    timestamp: str
    command: str
    target_file: str
    role: str
    had_reason: bool
    reason: str
    override_kind: str


class RecoveryCheckpointInfo(BaseModel):
    checkpoint_id: str
    phase: str
    phase_status: str
    created_at: str
    related_event_id: Optional[str] = None
    summary: Optional[str] = None


class RecoverySnapshotInfo(BaseModel):
    snapshot_id: str
    source_phase: str
    captured_at: str
    file_count: int
    target_paths: List[str] = []
    content_hashes: List[str] = []


class RecoveryApplyTraceInfo(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    status: str
    target_kind: str
    target_id: str
    reason: Optional[str] = None
    outcome_summary: Optional[str] = None


class AgentOSInfo(BaseModel):
    run_state: Optional[RunStateInfo] = None
    artifact_manifest: Optional[List[ArtifactEntryInfo]] = None
    gate_results: List[GateResultInfo] = []
    force_audit: Optional[List[ForceAuditEntryInfo]] = None
    recovery_checkpoints: List[RecoveryCheckpointInfo] = []
    recovery_snapshots: List[RecoverySnapshotInfo] = []
    recovery_apply_traces: List[RecoveryApplyTraceInfo] = []


def _safe_json_load(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _load_recovery_checkpoints(run_dir: Path) -> list[RecoveryCheckpointInfo]:
    checkpoints_dir = run_dir / "recovery" / "checkpoints"
    if not checkpoints_dir.exists():
        return []

    records: list[RecoveryCheckpointInfo] = []
    for path in sorted(checkpoints_dir.glob("*.json"), reverse=True):
        data = _safe_json_load(path)
        if data is None:
            continue
        checkpoint_id = str(data.get("checkpoint_id") or path.stem).strip()
        if not checkpoint_id:
            checkpoint_id = path.stem
        records.append(
            RecoveryCheckpointInfo(
                checkpoint_id=checkpoint_id,
                phase=str(data.get("phase", "")).strip(),
                phase_status=str(data.get("phase_status", "")).strip(),
                created_at=str(data.get("created_at", "")).strip(),
                related_event_id=str(data.get("related_event_id", "")).strip() or None,
                summary=str(data.get("summary", "")).strip() or None,
            )
        )
    return records


def _load_recovery_snapshots(run_dir: Path) -> list[RecoverySnapshotInfo]:
    snapshots_dir = run_dir / "recovery" / "snapshots"
    if not snapshots_dir.exists():
        return []

    records: list[RecoverySnapshotInfo] = []
    for snapshot_dir in sorted((p for p in snapshots_dir.iterdir() if p.is_dir()), reverse=True):
        metadata_path = snapshot_dir / "metadata.json"
        data = _safe_json_load(metadata_path)
        if data is None:
            continue
        target_paths_raw = data.get("target_paths")
        if isinstance(target_paths_raw, list):
            target_paths = [str(item).strip() for item in target_paths_raw if str(item).strip()]
        else:
            target_paths = []
        content_hashes_raw = data.get("content_hashes")
        if isinstance(content_hashes_raw, list):
            content_hashes = [str(item).strip() for item in content_hashes_raw if str(item).strip()]
        else:
            content_hashes = []
        file_count = data.get("file_count")
        if not isinstance(file_count, int):
            file_count = len(target_paths)
        records.append(
            RecoverySnapshotInfo(
                snapshot_id=str(data.get("snapshot_id") or snapshot_dir.name).strip() or snapshot_dir.name,
                source_phase=str(data.get("source_phase", "")).strip(),
                captured_at=str(data.get("captured_at", "")).strip(),
                file_count=file_count,
                target_paths=target_paths,
                content_hashes=content_hashes,
            )
        )
    return records


def _load_recovery_apply_traces(run_dir: Path) -> list[RecoveryApplyTraceInfo]:
    from ..core.session.session_event import (
        EVENT_CHECKPOINT_APPLY_FAILED,
        EVENT_CHECKPOINT_APPLY_SUCCEEDED,
    )
    from ..core.session.session_event_repository import SessionEventRepository

    trace_specs = {
        EVENT_CHECKPOINT_APPLY_SUCCEEDED: ("success", "checkpoint"),
        EVENT_CHECKPOINT_APPLY_FAILED: ("failure", "checkpoint"),
        "snapshot_apply_succeeded": ("success", "snapshot"),
        "snapshot_apply_failed": ("failure", "snapshot"),
    }

    records: list[RecoveryApplyTraceInfo] = []
    for event in reversed(SessionEventRepository(run_dir).load()):
        spec = trace_specs.get(event.event_type)
        if spec is None:
            continue

        status, target_kind = spec
        payload = event.payload if isinstance(event.payload, dict) else {}
        target_id_key = "checkpoint_id" if target_kind == "checkpoint" else "snapshot_id"
        target_id = str(payload.get(target_id_key, "")).strip()
        if not target_id:
            continue

        if status == "success":
            outcome_summary = " -> ".join(
                part
                for part in [
                    str(payload.get("phase", "")).strip(),
                    str(payload.get("phase_status", "")).strip(),
                    str(payload.get("current_owner", "")).strip(),
                ]
                if part
            ) or "apply succeeded"
        else:
            outcome_summary = str(payload.get("error", "")).strip() or "apply failed"

        records.append(
            RecoveryApplyTraceInfo(
                event_id=event.event_id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                status=status,
                target_kind=target_kind,
                target_id=target_id,
                reason=str(payload.get("apply_reason", "")).strip() or None,
                outcome_summary=outcome_summary,
            )
        )

    return records


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


def _load_viewer_config() -> dict[str, Any]:
    if not VIEWER_CONFIG_PATH.exists():
        return {}

    try:
        raw = json.loads(VIEWER_CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid viewer config JSON: {VIEWER_CONFIG_PATH}") from exc

    if not isinstance(raw, dict):
        raise RuntimeError(f"Viewer config must be a JSON object: {VIEWER_CONFIG_PATH}")
    return raw


def _save_viewer_config(config: dict[str, Any]) -> None:
    VIEWER_CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _resolve_source_kind(*, env_value: str, config_value: str) -> Literal["env", "viewer_config", "default"]:
    if env_value:
        return "env"
    if config_value:
        return "viewer_config"
    return "default"


def _resolve_act_execution_mode() -> Literal["wrapper", "provider"]:
    configured = os.getenv("APSF_VIEWER_ACT_EXECUTION_MODE", "").strip()
    if not configured:
        viewer_config = _load_viewer_config()
        execution_modes = viewer_config.get("execution_modes", {})
        if isinstance(execution_modes, dict):
            configured = str(execution_modes.get("act", "")).strip()

    if not configured:
        return "wrapper"

    mode = configured.lower()
    if mode not in ACT_EXECUTION_MODES:
        choices = ", ".join(sorted(ACT_EXECUTION_MODES))
        raise RuntimeError(f"Unsupported act execution mode: {configured!r}. Expected one of: {choices}")
    return mode


def _normalize_wrapper_backend(configured: str, *, supported: set[str], surface: str) -> str:
    normalized = WRAPPER_BACKEND_ALIASES.get(configured.strip().lower(), "")
    if not normalized:
        choices = ", ".join(sorted(supported))
        raise RuntimeError(f"Unsupported {surface} wrapper backend: {configured!r}. Expected one of: {choices}")
    if normalized not in supported:
        choices = ", ".join(sorted(supported))
        raise RuntimeError(
            f"Unsupported {surface} wrapper backend: {configured!r}. "
            f"Expected one of: {choices}"
        )
    return normalized


def _resolve_wrapper_backend(
    *,
    action: Literal["act", "build"],
    supported: set[str],
    default: str,
) -> str:
    env_var = f"APSF_VIEWER_{action.upper()}_WRAPPER_BACKEND"
    configured = os.getenv(env_var, "").strip()
    if not configured:
        viewer_config = _load_viewer_config()
        wrapper_backends = viewer_config.get("wrapper_backends", {})
        if isinstance(wrapper_backends, dict):
            configured = str(wrapper_backends.get(action, "")).strip()

    if not configured:
        return default
    return _normalize_wrapper_backend(configured, supported=supported, surface=action)


def _build_wrapper_command(script_name: str, run_name: str, backend: str) -> str:
    return f".\\scripts\\{script_name} {run_name} -Backend {backend}"


def _resolve_act_wrapper_backend() -> str:
    return _resolve_wrapper_backend(
        action="act",
        supported=ACT_WRAPPER_BACKENDS,
        default="claude-cli",
    )


def _resolve_build_wrapper_backend() -> str:
    return _resolve_wrapper_backend(
        action="build",
        supported=BUILD_WRAPPER_BACKENDS,
        default="claude-cli",
    )


def _resolve_phase_wrapper_backend(run_dir: Path | None, phase: str, action: Literal["act", "build"]) -> str | None:
    if run_dir is None:
        return None

    execution = _resolve_execution_visibility(run_dir, phase)
    if execution.execution_type != "cli":
        return None
    if action == "act":
        return _resolve_act_wrapper_backend()
    return _resolve_build_wrapper_backend()


def _build_act_command(run_name: str, phase: str | None = None, backend_hint: str | None = None) -> str:
    mode = _resolve_act_execution_mode()
    if mode == "provider":
        return f"apsf act {run_name}"
    backend = backend_hint or _resolve_act_wrapper_backend()
    return _build_wrapper_command("apsf-wrapper-act.ps1", run_name, backend)


def _build_build_command(run_name: str, backend_hint: str | None = None) -> str:
    viewer_config = _load_viewer_config()
    max_turns = int(viewer_config.get("build_max_turns", 10))
    cmd = _build_wrapper_command(
        "apsf-wrapper-build.ps1",
        run_name,
        backend_hint or _resolve_build_wrapper_backend(),
    )
    if max_turns != 10:
        cmd += f" -MaxTurns {max_turns}"
    return cmd


def _derive_cli_tool_mode(
    act_backend: str,
    build_backend: str,
) -> Literal["claude", "codex", "both"]:
    if act_backend == "claude-cli" and build_backend == "claude-cli":
        return "claude"
    if act_backend == "codex-cli" and build_backend == "codex-cli":
        return "codex"
    return "both"


def _resolve_viewer_config_response() -> ViewerConfigResponse:
    from apsf.legacy.config import settings as legacy_settings_module
    from apsf.legacy.config.settings import get_settings

    viewer_config = _load_viewer_config()
    execution_modes = viewer_config.get("execution_modes", {})
    if not isinstance(execution_modes, dict):
        execution_modes = {}
    wrapper_backends = viewer_config.get("wrapper_backends", {})
    if not isinstance(wrapper_backends, dict):
        wrapper_backends = {}

    execution_mode_env = os.getenv("APSF_VIEWER_ACT_EXECUTION_MODE", "").strip()
    execution_mode_config = str(execution_modes.get("act", "")).strip()
    act_backend_env = os.getenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", "").strip()
    act_backend_config = str(wrapper_backends.get("act", "")).strip()
    build_backend_env = os.getenv("APSF_VIEWER_BUILD_WRAPPER_BACKEND", "").strip()
    build_backend_config = str(wrapper_backends.get("build", "")).strip()

    execution_mode = _resolve_act_execution_mode()
    act_wrapper_backend = _resolve_act_wrapper_backend()
    build_wrapper_backend = _resolve_build_wrapper_backend()
    settings = get_settings()
    dotenv_path = PROJECT_ROOT / ".env"
    build_max_turns = max(1, min(50, int(viewer_config.get("build_max_turns", 10))))
    run_detail_refresh_ms = max(2000, min(60000, int(viewer_config.get("run_detail_refresh_ms", 10000))))
    return ViewerConfigResponse(
        execution_mode=execution_mode,
        cli_tool_mode=_derive_cli_tool_mode(act_wrapper_backend, build_wrapper_backend),
        act_wrapper_backend=act_wrapper_backend,
        build_wrapper_backend=build_wrapper_backend,
        config_path=str(VIEWER_CONFIG_PATH),
        config_exists=VIEWER_CONFIG_PATH.exists(),
        dotenv_path=str(dotenv_path),
        dotenv_exists=dotenv_path.exists(),
        settings_path=str(Path(legacy_settings_module.__file__).resolve()),
        framework_root=str(settings.framework_root),
        runs_dir=str(settings.runs_dir),
        template_dir=str(settings.template_dir),
        default_openai_model=settings.default_openai_model,
        default_anthropic_model=settings.default_anthropic_model,
        default_gemini_model=settings.default_gemini_model,
        openai_api_key_configured=bool(settings.openai_api_key),
        anthropic_api_key_configured=bool(settings.anthropic_api_key),
        gemini_api_key_configured=bool(settings.gemini_api_key),
        execution_mode_source=_resolve_source_kind(
            env_value=execution_mode_env,
            config_value=execution_mode_config,
        ),
        act_wrapper_backend_source=_resolve_source_kind(
            env_value=act_backend_env,
            config_value=act_backend_config,
        ),
        build_wrapper_backend_source=_resolve_source_kind(
            env_value=build_backend_env,
            config_value=build_backend_config,
        ),
        build_max_turns=build_max_turns,
        run_detail_refresh_ms=run_detail_refresh_ms,
    )


def _update_viewer_config(
    request: ViewerConfigUpdateRequest,
) -> ViewerConfigResponse:
    config = _load_viewer_config()
    execution_modes = config.get("execution_modes")
    if not isinstance(execution_modes, dict):
        execution_modes = {}
    wrapper_backends = config.get("wrapper_backends")
    if not isinstance(wrapper_backends, dict):
        wrapper_backends = {}

    if request.execution_mode is not None:
        execution_modes["act"] = request.execution_mode

    if request.cli_tool_mode is not None:
        if request.cli_tool_mode == "claude":
            wrapper_backends["act"] = "claude-cli"
            wrapper_backends["build"] = "claude-cli"
        elif request.cli_tool_mode == "codex":
            wrapper_backends["act"] = "codex-cli"
            wrapper_backends["build"] = "codex-cli"
        else:
            # "both" keeps both CLIs live with a stable default split:
            # Codex for lighter act flows, Claude for tool-enabled build flows.
            wrapper_backends["act"] = "codex-cli"
            wrapper_backends["build"] = "claude-cli"

    if request.build_max_turns is not None:
        config["build_max_turns"] = max(1, min(50, request.build_max_turns))

    if request.run_detail_refresh_ms is not None:
        config["run_detail_refresh_ms"] = max(2000, min(60000, request.run_detail_refresh_ms))

    config["execution_modes"] = execution_modes
    config["wrapper_backends"] = wrapper_backends
    _save_viewer_config(config)
    return _resolve_viewer_config_response()


def build_operator_actions(run_name: str, phase: str, run_dir: Path | None = None) -> List[OperatorAction]:
    actions: List[OperatorAction] = []
    # Use the full run_name (e.g. "work/run-name") so CLI tools can resolve it via RunRepository
    command_run_name = run_name
    act_backend_hint = _resolve_phase_wrapper_backend(run_dir, phase, "act")
    build_backend_hint = _resolve_phase_wrapper_backend(run_dir, phase, "build")

    if phase == "PLAN_NEEDED":
        actions.append(
            OperatorAction(
                id="phase-primary",
                label="Run Planner",
                command=_build_act_command(command_run_name, phase, act_backend_hint),
                execution_type="act",
                description="Run Planner and write plan.md.",
                primary=True,
            )
        )
    elif phase == "BUILD_NEEDED":
        actions.append(
            OperatorAction(
                id="phase-primary",
                label="Run Builder (Tool-Enabled)",
                command=_build_build_command(command_run_name, build_backend_hint),
                execution_type="build",
                warning_level="caution",
                description="BUILD_NEEDED uses the dedicated tool-enabled Builder path, not act.",
                primary=True,
            )
        )
        actions.append(
            OperatorAction(
                id="phase-build-guidance",
                label="CLI Alternative: apsf build",
                command=f"apsf build {command_run_name}",
                execution_type="human",
                warning_level="caution",
                enabled=False,
                description="Equivalent CLI entrypoint if you prefer running the Builder path directly.",
            )
        )
    elif phase == "REVIEW_NEEDED":
        actions.append(
            OperatorAction(
                id="phase-primary",
                label="Run Critic",
                command=_build_act_command(command_run_name, phase, act_backend_hint),
                execution_type="act",
                description="Run Critic and write review.md.",
                primary=True,
            )
        )
    elif phase == "IMPROVE_NEEDED":
        actions.append(
            OperatorAction(
                id="accept-improve",
                label="Judge and Proceed to Result",
                command="",
                execution_type="accept",
                description="Record the Judge acceptance in improve.md and advance the run to RESULT_NEEDED.",
                primary=True,
            )
        )
        actions.append(
            OperatorAction(
                id="phase-primary",
                label="Judge Decision",
                command=f"apsf next {command_run_name}",
                execution_type="human",
                warning_level="caution",
                enabled=False,
                description="CLI で判断を記録する場合はこちら。",
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
                label="Judge and Return to Plan",
                command=f".\\scripts\\apsf-rerun-plan.ps1 {command_run_name}",
                execution_type="rerun",
                warning_level="danger",
                description="After the Judge decision is clear, write feedback to plan_review.md and return this run to Planner at PLAN_NEEDED.",
                comment_artifact="plan_review.md",
                requires_comment=True,
            ),
            OperatorAction(
                id="rerun-build",
                label="Judge and Return to Build",
                command=f".\\scripts\\apsf-rerun-build.ps1 {command_run_name}",
                execution_type="rerun",
                warning_level="danger",
                description="After the Judge decision is clear, write feedback to build_review.md and return this run to Builder at BUILD_NEEDED.",
                comment_artifact="build_review.md",
                requires_comment=True,
            ),
            OperatorAction(
                id="rerun-review",
                label="Judge and Return to Review",
                command=f".\\scripts\\apsf-rerun-review.ps1 {command_run_name}",
                execution_type="rerun",
                warning_level="danger",
                description="After the Judge decision is clear, write feedback to review_review.md and return this run to Critic at REVIEW_NEEDED.",
                comment_artifact="review_review.md",
                requires_comment=True,
            ),
            OperatorAction(
                id="rerun-improve",
                label="Reopen Judge Decision",
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
        actions = build_operator_actions(full_name, info.phase.value, child_dir)
        primary_action = next((action for action in actions if action.primary), actions[0])
        depends_on, dependency_phases, has_incomplete_dependencies = dependency_status_by_run(
            project_root=PROJECT_ROOT,
            run_dir=child_dir,
        )
        children.append(
            ChildRunSummary(
                name=full_name,
                child_name=child_name,
                phase=info.phase.value,
                next_role=info.next_role,
                operator_command=primary_action.command,
                primary_action_label=primary_action.label,
                has_children=False,
                depends_on=depends_on,
                dependency_phases=dependency_phases,
                has_incomplete_dependencies=has_incomplete_dependencies,
            )
        )
    children.sort(
        key=lambda child: (
            not child.has_incomplete_dependencies,
            len(child.depends_on) == 0,
            child.child_name.lower(),
        )
    )
    return children


def _resolve_run_dir(taxonomy: str, run_name: str) -> Path:
    """Resolve the absolute path to a run directory, handling nested child runs."""
    if "/" in run_name:
        parent, child = run_name.split("/", 1)
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


def _classify_process_result(completed: subprocess.CompletedProcess[str]) -> Literal["SUCCESS", "PARTIAL", "FAILED", "HUMAN"]:
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    combined_lower = f"{stdout}\n{stderr}".lower()
    partial_markers = (
        "[partial]",
        "reached max turns",
        "reached max turns before completing the build",
        "partial file edits may exist",
        "claimed success, but the phase is still build_needed",
        "phase is still build_needed",
        "phase remains: build_needed",
    )
    if completed.returncode == 2 or any(marker in combined_lower for marker in partial_markers):
        return "PARTIAL"
    if completed.returncode == 0:
        return "SUCCESS"
    return "FAILED"


def _agent_os_now_suffix() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _resolve_agent_os_phase(run_dir: Path) -> str:
    from ..core.state.run_state_repository import RunStateRepository

    state = RunStateRepository(run_dir).load()
    if state is not None and state.current_phase:
        return str(state.current_phase)
    return str(PhaseDetector(run_dir).detect().phase.value)


def _phase_owner_name(phase: str) -> str:
    from apsf.legacy.orchestration.act_service import _phase_to_owner

    return _phase_to_owner(phase) or ""


def _remove_manifest_entries(run_dir: Path, artifact_names: list[str]) -> None:
    from apsf.core.manifest.manifest_repository import ManifestRepository

    ManifestRepository(run_dir).remove_entries(artifact_names)


def _pin_run_state_after_partial_build(run_dir: Path) -> None:
    """Re-pin canonical run_state after a partial build left stale review state."""
    from apsf.core.state.transition_service import TransitionService

    TransitionService().transition(
        run_dir,
        to_phase="BUILD_NEEDED",
        actor="system",
        reason="_pin_run_state_after_partial_build: partial build detected",
    )
    _remove_manifest_entries(run_dir, ["build.md"])


def _latest_execution_indicates_partial_build(taxonomy: str, run_name: str) -> bool:
    recent_rows = viewer_db.list_recent_executions_for_run(taxonomy, run_name, limit=5)
    for row in recent_rows:
        command = str(row.get("command", "")).strip().lower()
        if "apsf-wrapper-build.ps1" not in command:
            continue
        result_status = str(row.get("result_status", "")).strip().upper()
        stdout_summary = str(row.get("stdout_summary", "")).strip()
        # Guard-failure: wrapper ran when phase was not BUILD_NEEDED → exit 2 → classified
        # as PARTIAL (not FAILED). Skip these entries and keep scanning for a real build result.
        if result_status in ("PARTIAL", "FAILED") and "not BUILD_NEEDED" in stdout_summary:
            continue
        if result_status == "PARTIAL":
            return True
        return False
    return False


def _resolve_canonical_view_phase(taxonomy: str, run_name: str, run_dir: Path, detected_phase: str) -> str:
    canonical_state = _bootstrap_run_state_if_missing(run_dir)
    canonical_phase = canonical_state.current_phase if canonical_state is not None else detected_phase
    if _latest_execution_indicates_partial_build(taxonomy, run_name) and canonical_phase != "BUILD_NEEDED":
        _pin_run_state_after_partial_build(run_dir)
        return "BUILD_NEEDED"
    return canonical_phase


def _suppress_detector_mismatch_banner(run_dir: Path, canonical_phase: str) -> bool:
    from ..core.state.run_state_repository import RunStateRepository

    state = RunStateRepository(run_dir).load()
    if state is None:
        return False
    if state.phase_status != "completed":
        return False
    return canonical_phase in {"RESULT_WRITTEN", "COMPLETE", "COMPLETED", "TRANSCRIPT_RECOMMENDED"}


def _default_snapshot_targets(run_dir: Path) -> list[str]:
    return [name for name in AGENT_OS_CANONICAL_SNAPSHOT_ARTIFACTS if (run_dir / name).exists()]


# ── Agent OS action classification ──────────────────────────────────────────
# policy-aware: command resolved via execution mode policy (wrapper / provider).
# New actions that should respect wrapper/provider switching belong here.
_POLICY_AWARE_ACTIONS: frozenset[str] = frozenset({"act"})

# fixed: command is constant regardless of configuration.
# These are in-process service calls; the command string is a display/log representation.
_FIXED_ACTIONS: frozenset[str] = frozenset({
    "capture-checkpoint",
    "capture-snapshot",
    "apply-checkpoint",
    "apply-snapshot",
})

# human-only: no programmatic command; requires human action.
# Reserved — no actions classified here yet.
_HUMAN_ONLY_ACTIONS: frozenset[str] = frozenset()


def _build_agent_os_action_command(
    run_name: str,
    action_id: str,
    *,
    checkpoint_id: str | None = None,
    snapshot_id: str | None = None,
    reason: str | None = None,
    targets: list[str] | None = None,
) -> str:
    """Build the display/execution command for an Agent OS action.

    Classification (see module-level constants):
    - policy-aware (_POLICY_AWARE_ACTIONS): command resolved via execution mode policy
    - fixed (_FIXED_ACTIONS): command is constant regardless of configuration
    - human-only (_HUMAN_ONLY_ACTIONS): no programmatic command (reserved)

    ``act`` is the only policy-aware action. ``capture-*`` and ``apply-*`` are fixed
    actions executed in-process; their commands here serve as display/log representations.
    """
    executable = sys.executable.replace('"', '\\"')
    base = f'& "{executable}" -m apsf.legacy.cli.main'

    # policy-aware: delegate to execution mode policy resolver
    if action_id == "act":
        return _build_act_command(run_name)

    # fixed: constant commands, executed in-process by the corresponding service
    if action_id == "capture-checkpoint":
        return f'{base} capture-checkpoint "{run_name}" "{checkpoint_id or ""}" --note "captured from Agent OS GUI"'
    if action_id == "capture-snapshot":
        target_args = " ".join(f'"{target}"' for target in (targets or []))
        return (
            f'{base} capture-snapshot "{run_name}" "{snapshot_id or ""}" {target_args} '
            f'--source-phase "{_escape_ps_arg(reason or "")}"'
        ).strip()
    if action_id == "apply-checkpoint":
        return (
            f'{base} apply-checkpoint "{run_name}" "{checkpoint_id or ""}" '
            f'--apply-reason "{_escape_ps_arg(reason or "")}"'
        )
    if action_id == "apply-snapshot":
        return (
            f'{base} restore-snapshot "{run_name}" "{snapshot_id or ""}" '
            f'--restore-reason "{_escape_ps_arg(reason or "")}"'
        )

    raise ValueError(f"unknown Agent OS action: {action_id!r}")


def _escape_ps_arg(value: str) -> str:
    return value.replace('"', '\\"')


def _run_service_with_captured_stderr(fn: Any) -> tuple[Any, str]:
    stderr_buffer = io.StringIO()
    with contextlib.redirect_stderr(stderr_buffer):
        result = fn()
    return result, stderr_buffer.getvalue()


def _execute_agent_os_action(
    run_dir: Path,
    run_name: str,
    request: ExecuteAgentOSActionRequest,
) -> ExecuteCommandResponse:
    action_id = request.action_id

    if action_id == "act":
        command = _build_agent_os_action_command(run_name, action_id)
        completed = _run_powershell_command(command)
        status = _classify_process_result(completed)
        return ExecuteCommandResponse(
            action_id=action_id,
            command=command,
            status=status,
            exit_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )

    if action_id == "capture-checkpoint":
        from ..core.restore.checkpoint_capture_service import (
            CheckpointCaptureError,
            CheckpointCaptureService,
        )

        checkpoint_id = f"gui-cp-{_agent_os_now_suffix()}"
        phase = _resolve_agent_os_phase(run_dir)
        summary = "captured from Agent OS GUI"
        command = (
            f'capture-checkpoint run="{run_name}" checkpoint_id="{checkpoint_id}" '
            f'phase="{phase}"'
        )
        try:
            result = CheckpointCaptureService().capture(
                run_dir,
                checkpoint_id,
                summary=summary,
            )
        except CheckpointCaptureError as exc:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr=str(exc),
            )
        return ExecuteCommandResponse(
            action_id=action_id,
            command=command,
            status="SUCCESS",
            exit_code=0,
            stdout=(
                f"Captured checkpoint: {result.checkpoint_id}\n"
                f"phase: {result.phase}\n"
                f"phase_status: {result.phase_status}\n"
                f"related_event_id: {result.related_event_id or '(none)'}"
            ),
            stderr="",
        )

    if action_id == "capture-snapshot":
        from ..core.restore.snapshot_capture_service import (
            SnapshotCaptureError,
            SnapshotCaptureService,
        )

        target_paths = _default_snapshot_targets(run_dir)
        phase = _resolve_agent_os_phase(run_dir)
        snapshot_id = f"gui-snap-{_agent_os_now_suffix()}"
        command = (
            f'capture-snapshot run="{run_name}" snapshot_id="{snapshot_id}" '
            f'targets="{", ".join(target_paths)}" source_phase="{phase}"'
        )
        if not target_paths:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr="No canonical artifacts found to capture. Create at least one of goal.md, plan.md, build.md, review.md, or result.md first.",
            )
        try:
            result = SnapshotCaptureService().capture(
                run_dir=run_dir,
                snapshot_id=snapshot_id,
                target_paths=target_paths,
                source_phase=phase,
            )
        except SnapshotCaptureError as exc:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr=str(exc),
            )
        return ExecuteCommandResponse(
            action_id=action_id,
            command=command,
            status="SUCCESS",
            exit_code=0,
            stdout=(
                f"Captured snapshot: {result.snapshot_id}\n"
                + "\n".join(result.captured_paths)
            ),
            stderr="",
        )

    if action_id == "apply-checkpoint":
        from ..core.restore.checkpoint_apply_service import (
            CheckpointApplyError,
            CheckpointApplyService,
        )

        checkpoint_id = (request.checkpoint_id or "").strip()
        reason = (request.reason or "").strip()
        command = (
            f'apply-checkpoint run="{run_name}" checkpoint_id="{checkpoint_id}" '
            f'reason="{reason}" confirmed={str(request.confirmed).lower()}'
        )
        if not checkpoint_id:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr="Apply checkpoint is blocked: select a checkpoint candidate first.",
            )
        if not reason:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr="Apply checkpoint is blocked: reason is required.",
            )
        if not request.confirmed:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr="Apply checkpoint is blocked: explicit confirmation is required.",
            )
        try:
            result, warning_stderr = _run_service_with_captured_stderr(
                lambda: CheckpointApplyService().apply(run_dir, checkpoint_id, reason)
            )
        except CheckpointApplyError as exc:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr=str(exc),
            )
        return ExecuteCommandResponse(
            action_id=action_id,
            command=command,
            status="SUCCESS",
            exit_code=0,
            stdout=(
                f"Applied checkpoint: {result.checkpoint_id}\n"
                f"phase: {result.phase}\n"
                f"phase_status: {result.phase_status}\n"
                f"current_owner: {result.current_owner}\n"
                f"reason: {result.apply_reason}"
            ),
            stderr=warning_stderr,
        )

    if action_id == "apply-snapshot":
        from ..core.restore.restore_service import RestoreError, RestoreService

        snapshot_id = (request.snapshot_id or "").strip()
        reason = (request.reason or "").strip()
        command = (
            f'apply-snapshot run="{run_name}" snapshot_id="{snapshot_id}" '
            f'reason="{reason}" confirmed={str(request.confirmed).lower()}'
        )
        if not snapshot_id:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr="Apply snapshot is blocked: select a snapshot candidate first.",
            )
        if not reason:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr="Apply snapshot is blocked: reason is required.",
            )
        if not request.confirmed:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr="Apply snapshot is blocked: explicit confirmation is required.",
            )
        try:
            result, warning_stderr = _run_service_with_captured_stderr(
                lambda: RestoreService().apply_snapshot(run_dir, snapshot_id, reason)
            )
        except RestoreError as exc:
            return ExecuteCommandResponse(
                action_id=action_id,
                command=command,
                status="FAILED",
                exit_code=1,
                stdout="",
                stderr=str(exc),
            )
        return ExecuteCommandResponse(
            action_id=action_id,
            command=command,
            status="SUCCESS",
            exit_code=0,
            stdout=(
                f"Applied snapshot: {result.snapshot_id}\n"
                + "\n".join(result.restored_paths)
                + (f"\nreason: {result.restore_reason}" if result.restore_reason else "")
            ),
            stderr=warning_stderr,
        )

    # unknown action — explicit reject; all known actions have returned in their branches above
    return ExecuteCommandResponse(
        action_id=action_id,
        command=action_id,
        status="FAILED",
        exit_code=1,
        stdout="",
        stderr=f"unknown Agent OS action: {action_id!r}",
    )


def _read_artifact_preview(path: Path) -> str:
    try:
        return read_text_artifact(path, errors="replace")[:500]
    except Exception:
        return "[Error reading file]"


def _bootstrap_run_state_if_missing(run_dir: Path):
    from apsf.core.state.run_state_repository import RunStateRepository
    from apsf.core.state.transition_service import TransitionService
    from apsf.legacy.orchestration.act_service import _phase_to_owner

    state_repo = RunStateRepository(run_dir)
    existing = state_repo.load()
    if existing is not None:
        return existing

    info = PhaseDetector(run_dir).detect_advisory()
    owner = _phase_to_owner(info.phase)
    TransitionService().bootstrap(
        run_dir, run_dir.name, info.phase.value,
        actor="system",
        reason="_bootstrap_run_state_if_missing: viewer bootstrap",
        current_owner=owner,
    )
    return state_repo.load()


def _read_text_if_exists(path: Path) -> str:
    try:
        return read_text_artifact(path) if path.exists() else ""
    except OSError:
        return ""


def _extract_review_verdict(review_text: str) -> str | None:
    standalone_emphasis_match = re.search(r"^\*\*(ACCEPT|ADOPT|REVISE|REJECT)\*\*", review_text, flags=re.IGNORECASE | re.MULTILINE)
    if standalone_emphasis_match:
        verdict = standalone_emphasis_match.group(1).strip()
        return verdict[:240] if verdict else None

    match = re.search(r"## Overall Verdict\s+(.+)", review_text, flags=re.IGNORECASE)
    if match:
        verdict = match.group(1).strip()
        return verdict[:240] if verdict else None

    emphatic_verdict_match = re.search(
        r"^\*\*(?:Verdict|判定|推奨)\s*[:：]\s*(.+?)\*\*",
        review_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if emphatic_verdict_match:
        verdict = emphatic_verdict_match.group(1).strip()
        return verdict[:240] if verdict else None

    verdict_heading_match = re.search(r"^##\s+Verdict:\s*(.+)$", review_text, flags=re.IGNORECASE | re.MULTILINE)
    if verdict_heading_match:
        verdict = verdict_heading_match.group(1).strip()
        return verdict[:240] if verdict else None

    verdict_section_recommendation = re.search(
        r"^##\s+Verdict\s*$\s*(?:\n|.)*?^\s*-\s*Recommendation:\s*(.+)$",
        review_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if verdict_section_recommendation:
        verdict = verdict_section_recommendation.group(1).strip()
        return verdict[:240] if verdict else None

    decision_match = re.search(r"^##\s+Decision\s*$\s*(?:\n|.)*?\n([A-Z][A-Z _-]+)\s*$", review_text, flags=re.MULTILINE)
    if decision_match:
        verdict = decision_match.group(1).strip()
        return verdict[:240] if verdict else None

    acceptance_match = re.search(
        r"^###\s+Acceptance Decision\s*$\s*(?:\n|.)*?\n\*\*(.+?)\*\*",
        review_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if acceptance_match:
        verdict = acceptance_match.group(1).strip()
        return verdict[:240] if verdict else None

    disposition_match = re.search(
        r"^##\s+Disposition\s*$\s*(?:\n|.)*?^\s*-\s*(Accept|Accepted|Adopt|Revise|Reject)\s*$",
        review_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if disposition_match:
        verdict = disposition_match.group(1).strip()
        return verdict[:240] if verdict else None

    recommendation_match = re.search(r"(?:判定|推奨|Recommendation)\s*[:：]\s*(Accept|Accepted|Adopt|Revise|Reject)\b", review_text, flags=re.IGNORECASE)
    if recommendation_match:
        verdict = recommendation_match.group(1).strip()
        return verdict[:240] if verdict else None

    parenthetical_adopt_match = re.search(r"\((Adopt|Revise|Reject|Accept)\)", review_text, flags=re.IGNORECASE)
    if parenthetical_adopt_match:
        verdict = parenthetical_adopt_match.group(1).strip()
        return verdict[:240] if verdict else None

    acceptable_match = re.search(r"^\s*Acceptable\.\s*$", review_text, flags=re.IGNORECASE | re.MULTILINE)
    if acceptable_match:
        return "Acceptable"

    not_ready_to_close_match = re.search(r"\bnot ready to close\b", review_text, flags=re.IGNORECASE)
    if not_ready_to_close_match:
        return "Not ready to close"

    ready_to_close_match = re.search(r"ready to close", review_text, flags=re.IGNORECASE)
    if ready_to_close_match:
        return "Ready to close"

    accept_minor_revisions_match = re.search(r"accept with minor revisions recommended", review_text, flags=re.IGNORECASE)
    if accept_minor_revisions_match:
        return "Accept with Minor revisions recommended"

    conditional_pass_match = re.search(r"conditional pass", review_text, flags=re.IGNORECASE)
    if conditional_pass_match:
        return "Conditional Pass"

    return None


def _count_section_bullets(review_text: str, heading: str) -> int:
    pattern = re.compile(
        rf"^##+\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##+\s+|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(review_text)
    if not match:
        return 0
    body = match.group("body")
    count = 0
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        normalized = stripped.lstrip("-").strip().strip("*").strip().rstrip(".")
        if not normalized:
            continue
        if normalized.lower() in {"none", "n/a"}:
            continue
        if normalized in {"なし", "縺ｪ縺・", "‚È‚µ"}:
            continue
        count += 1
    return count


def _extract_review_issue_count(review_text: str, prefix: str) -> int:
    legacy = len(re.findall(rf"\*\*{re.escape(prefix)}-\d+:", review_text))
    if legacy:
        return legacy

    if prefix == "C":
        coded_patterns = [r"^\*\*\[C-\d+\]", r"^\*\*C-\d+\b"]
    elif prefix == "M":
        coded_patterns = [r"^\*\*\[M-\d+\]", r"^\*\*M-\d+\b"]
    else:
        coded_patterns = [r"^\*\*\[m-\d+\]", r"^\*\*m-\d+\b"]

    coded_count = sum(len(re.findall(pattern, review_text, flags=re.MULTILINE)) for pattern in coded_patterns)
    if coded_count:
        return coded_count

    if prefix == "C":
        style_groups = [
            [r"^####(?!#)\s+CRITICAL-\d+\b"],
            [r"^###(?!#)\s+\[(?:critical)\]\s+"],
            [r"^###(?!#)\s+Critical\b"],
        ]
    elif prefix == "M":
        style_groups = [
            [r"^####(?!#)\s+MAJOR-\d+\b"],
            [r"^###(?!#)\s+\[(?:major)\]\s+"],
            [r"^###(?!#)\s+Major\b"],
        ]
    else:
        style_groups = [
            [r"^####(?!#)\s+MINOR-\d+\b"],
            [r"^###(?!#)\s+\[(?:minor)\]\s+"],
            [r"^###(?!#)\s+Minor\b"],
        ]

    for patterns in style_groups:
        count = sum(
            len(re.findall(pattern, review_text, flags=re.IGNORECASE | re.MULTILINE))
            for pattern in patterns
        )
        if count:
            return count
    return 0


def _extract_review_issue_counts(review_text: str) -> tuple[int, int, int, str | None]:
    critical = _extract_review_issue_count(review_text, "C")
    major = _extract_review_issue_count(review_text, "M")
    minor = _extract_review_issue_count(review_text, "m")
    if critical or major or minor:
        return critical, major, minor, "Counts derived from issue section headings."

    findings_numbered_counts = {
        "critical": len(re.findall(r"^\d+\.\s+Critical:", review_text, flags=re.IGNORECASE | re.MULTILINE)),
        "major": len(re.findall(r"^\d+\.\s+Major:", review_text, flags=re.IGNORECASE | re.MULTILINE)),
        "minor": len(re.findall(r"^\d+\.\s+Minor:", review_text, flags=re.IGNORECASE | re.MULTILINE)),
    }
    if any(findings_numbered_counts.values()):
        return (
            findings_numbered_counts["critical"],
            findings_numbered_counts["major"],
            findings_numbered_counts["minor"],
            "Counts derived from numbered findings.",
        )

    status_counts = {
        "critical": len(re.findall(r"\*\*Status:\s*Critical\*\*", review_text, flags=re.IGNORECASE)),
        "major": len(re.findall(r"\*\*Status:\s*Major\*\*", review_text, flags=re.IGNORECASE)),
        "minor": len(re.findall(r"\*\*Status:\s*Minor\*\*", review_text, flags=re.IGNORECASE)),
    }
    if any(status_counts.values()):
        return (
            status_counts["critical"],
            status_counts["major"],
            status_counts["minor"],
            "Counts derived from criterion status markers.",
        )

    code_heading_counts = {
        "critical": len(re.findall(r"^###\s+C-\d+\s*(?::|—|-)", review_text, flags=re.MULTILINE)),
        "major": len(re.findall(r"^###\s+M-\d+\s*(?::|—|-)", review_text, flags=re.MULTILINE)),
        "minor": len(re.findall(r"^###\s+m-\d+\s*(?::|—|-)", review_text, flags=re.MULTILINE)),
    }
    if any(code_heading_counts.values()):
        return (
            code_heading_counts["critical"],
            code_heading_counts["major"],
            code_heading_counts["minor"],
            "Counts derived from coded issue headings.",
        )

    issue_section_bullets = {
        "critical": _count_section_bullets(review_text, "Critical Issues"),
        "major": _count_section_bullets(review_text, "Major Issues"),
        "minor": _count_section_bullets(review_text, "Minor Issues"),
    }
    if any(issue_section_bullets.values()):
        return (
            issue_section_bullets["critical"],
            issue_section_bullets["major"],
            issue_section_bullets["minor"],
            "Counts derived from issue bullet sections.",
        )

    explicit_zero_sections = re.search(
        r"##\s+Critical Issues\s*(?:\n|.)*?(?:None\.|-\s*なし)\s*(?:\n|.)*?##\s+Major Issues\s*(?:\n|.)*?(?:None\.|-\s*なし)\s*(?:\n|.)*?##\s+Minor Issues\s*(?:\n|.)*?(?:None\.|-\s*なし)",
        review_text,
        flags=re.IGNORECASE,
    )
    if explicit_zero_sections:
        return 0, 0, 0, "Counts derived from explicit zero-issue sections."

    issue_summary_counts = {
        "critical": len(re.findall(r"^\|\s*C-\d+\s*\|.*\bCRITICAL\b", review_text, flags=re.IGNORECASE | re.MULTILINE)),
        "major": len(re.findall(r"^\|\s*M-\d+\s*\|.*\bMAJOR\b", review_text, flags=re.IGNORECASE | re.MULTILINE)),
        "minor": len(re.findall(r"^\|\s*m-\d+\s*\|.*\bMinor\b", review_text, flags=re.IGNORECASE | re.MULTILINE)),
    }
    if any(issue_summary_counts.values()):
        return (
            issue_summary_counts["critical"],
            issue_summary_counts["major"],
            issue_summary_counts["minor"],
            "Counts derived from issue classification summary table.",
        )

    generic_table_counts = {
        "critical": len(re.findall(r"^\|\s*[^|\n]+\|\s*Critical\s*\|", review_text, flags=re.IGNORECASE | re.MULTILINE)),
        "major": len(re.findall(r"^\|\s*[^|\n]+\|\s*Major\s*\|", review_text, flags=re.IGNORECASE | re.MULTILINE)),
        "minor": len(re.findall(r"^\|\s*[^|\n]+\|\s*Minor\s*\|", review_text, flags=re.IGNORECASE | re.MULTILINE)),
    }
    if any(generic_table_counts.values()):
        return (
            generic_table_counts["critical"],
            generic_table_counts["major"],
            generic_table_counts["minor"],
            "Counts derived from generic issue summary table.",
        )

    summary_match = re.search(
        r"\|\s*Critical\s*\|\s*(\d+)\s*\|.*\n.*\|\s*Major\s*\|\s*(\d+)\s*\|.*\n.*\|\s*Minor\s*\|\s*(\d+)\s*\|",
        review_text,
        flags=re.IGNORECASE,
    )
    if summary_match:
        return (
            int(summary_match.group(1)),
            int(summary_match.group(2)),
            int(summary_match.group(3)),
            "Counts derived from the review summary table.",
        )

    verdict_bullets = re.search(
        r"^##\s+Verdict\s*$\s*(?:\n|.)*?^\s*-\s*Critical:\s*(\d+)\s*$\s*(?:\n|.)*?^\s*-\s*Major:\s*(\d+)\s*$\s*(?:\n|.)*?^\s*-\s*Minor:\s*(\d+)\s*$",
        review_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if verdict_bullets:
        return (
            int(verdict_bullets.group(1)),
            int(verdict_bullets.group(2)),
            int(verdict_bullets.group(3)),
            "Counts derived from verdict bullet summary.",
        )

    inline_findings_summary = re.search(
        r"Critical:\s*(\d+|none|なし|縺ｪ縺・|‚È‚µ).*?Major:\s*(\d+|none|なし|縺ｪ縺・|‚È‚µ).*?Minor:\s*(\d+|none|なし|縺ｪ縺・|‚È‚µ)",
        review_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if inline_findings_summary:
        def _severity_value(raw: str) -> int:
            raw_lower = raw.lower()
            if raw_lower == "none" or raw in {"なし", "縺ｪ縺・", "‚È‚µ"}:
                return 0
            return int(raw)

        return (
            _severity_value(inline_findings_summary.group(1)),
            _severity_value(inline_findings_summary.group(2)),
            _severity_value(inline_findings_summary.group(3)),
            "Counts derived from inline findings summary.",
        )

    prose_findings_counts = {
        "major": len(re.findall(r"\bmajor risks? to watch\b|\*\*\[Major\]", review_text, flags=re.IGNORECASE)),
        "minor": len(re.findall(r"\bminor note\s*:|\*\*\[Minor\]", review_text, flags=re.IGNORECASE)),
    }
    explicit_no_critical = bool(
        re.search(r"\b(?:no critical (?:gaps|findings)|critical issues?\s*:\s*none)\b", review_text, flags=re.IGNORECASE)
    )
    if explicit_no_critical or any(prose_findings_counts.values()):
        return (
            0,
            prose_findings_counts["major"],
            prose_findings_counts["minor"],
            "Counts derived from prose findings markers.",
        )

    return 0, 0, 0, "Structured severity markers were not detected; counts may be incomplete."


def _extract_review_completion_flags(review_text: str) -> tuple[bool, bool]:
    has_not_met = bool(
        re.search(
            r"\bnot met\b|open\s+[—-]\s+critical|\*\*status:\s*not met\*\*",
            review_text,
            flags=re.IGNORECASE,
        )
    )
    has_partially_met = bool(
        re.search(
            r"\bpartially met\b|\*\*status:\s*partially met\*\*|\bpartial(?:ly)?\s+met\b",
            review_text,
            flags=re.IGNORECASE,
        )
    )
    return has_not_met, has_partially_met


def _derive_judge_recommendation(run_dir: Path, phase: str) -> JudgeRecommendation | None:
    if phase not in {"IMPROVE_NEEDED", "RESULT_NEEDED", "TRANSCRIPT_RECOMMENDED", "COMPLETE"}:
        return None

    review_path = latest_review_artifact(run_dir)
    review_text = _read_text_if_exists(review_path).strip() if review_path else ""
    if not review_text:
        return None

    blocker_decision = get_build_gate_decision(run_dir)
    ownership_status = str(blocker_decision.get("status") or "")
    ownership_detail = str(blocker_decision.get("detail") or "").strip() or None
    human_blocker = blocker_decision.get("blocker") if ownership_status == "HUMAN" else None
    human_blocker_actions = [str(action) for action in blocker_decision.get("actions", [])]
    human_blocker_summary = str(blocker_decision.get("summary") or "").strip() or None
    human_blocker_source = str(blocker_decision.get("source") or "").strip() or None

    critical_count, major_count, minor_count, counts_note = _extract_review_issue_counts(review_text)
    verdict = _extract_review_verdict(review_text)
    review_lower = review_text.lower()
    verdict_lower = (verdict or "").lower()
    has_not_met, has_partially_met = _extract_review_completion_flags(review_text)

    plan_score = sum(
        review_lower.count(token)
        for token in ("plan.md", "goal.md", "planner", "planning", "scope", "strategy", "spec")
    )
    build_score = sum(
        review_lower.count(token)
        for token in ("build.md", "builder", "implementation", "writeback", "build record", "build artifact", "contract", "raw field contract")
    )
    build_artifact_focus = sum(
        review_lower.count(token)
        for token in ("build artifact", "contract", "build record", "criterion 3 formal status", "raw field contract")
    ) >= 2

    if "reject" in verdict_lower:
        return JudgeRecommendation(
            decision="Reject",
            suggested_action_id="rerun-plan",
            suggested_action_label="Judge and Return to Plan",
            suggested_return_phase="PLAN_NEEDED",
            confidence="high",
            rationale="review.md already marks the outcome as reject-level. Record that judgment, reflect the findings, and send the run back to Planner with a fresh plan boundary.",
            review_verdict=verdict,
            counts_note=counts_note,
            critical_count=critical_count,
            major_count=major_count,
            minor_count=minor_count,
            human_owned_blocker=human_blocker is not None,
            human_blocker_summary=human_blocker_summary,
            human_blocker_source=human_blocker_source,
            human_actions=human_blocker_actions,
            ownership_status=ownership_status,
            ownership_detail=ownership_detail,
        )

    if critical_count > 0:
        plan_heavy = plan_score >= build_score and not build_artifact_focus
        return JudgeRecommendation(
            decision="Revise",
            suggested_action_id="rerun-plan" if plan_heavy else "rerun-build",
            suggested_action_label="Judge and Return to Plan" if plan_heavy else "Judge and Return to Build",
            suggested_return_phase="PLAN_NEEDED" if plan_heavy else "BUILD_NEEDED",
            confidence="high" if plan_heavy else "medium",
            rationale=(
                "Critical issues are present. Record the judgment, reflect the review findings, and send the run back to Planner to correct planning and scope."
                if plan_heavy
                else "Critical issues are present. Record the judgment, reflect the review findings, and send the run back to Builder to correct the build artifacts."
            ),
            review_verdict=verdict,
            counts_note=counts_note,
            critical_count=critical_count,
            major_count=major_count,
            minor_count=minor_count,
            human_owned_blocker=human_blocker is not None,
            human_blocker_summary=human_blocker_summary,
            human_blocker_source=human_blocker_source,
            human_actions=human_blocker_actions,
            ownership_status=ownership_status,
            ownership_detail=ownership_detail,
        )

    if major_count > 0:
        plan_heavy = plan_score > build_score and plan_score > 0 and not build_artifact_focus
        return JudgeRecommendation(
            decision="Revise",
            suggested_action_id="rerun-plan" if plan_heavy else "rerun-build",
            suggested_action_label="Judge and Return to Plan" if plan_heavy else "Judge and Return to Build",
            suggested_return_phase="PLAN_NEEDED" if plan_heavy else "BUILD_NEEDED",
            confidence="medium",
            rationale=(
                "Major issues remain. Record the judgment, reflect the review findings, and send the run back to Planner because the dominant gaps are planning-boundary issues."
                if plan_heavy
                else "Major issues remain. Record the judgment, reflect the review findings, and send the run back to Builder because no planning-boundary blocker dominates the review."
            ),
            review_verdict=verdict,
            counts_note=counts_note,
            critical_count=critical_count,
            major_count=major_count,
            minor_count=minor_count,
            human_owned_blocker=human_blocker is not None,
            human_blocker_summary=human_blocker_summary,
            human_blocker_source=human_blocker_source,
            human_actions=human_blocker_actions,
            ownership_status=ownership_status,
            ownership_detail=ownership_detail,
        )

    if has_not_met or has_partially_met:
        plan_heavy = plan_score > build_score and plan_score > 0 and not build_artifact_focus
        return JudgeRecommendation(
            decision="Revise",
            suggested_action_id="rerun-plan" if plan_heavy else "rerun-build",
            suggested_action_label="Judge and Return to Plan" if plan_heavy else "Judge and Return to Build",
            suggested_return_phase="PLAN_NEEDED" if plan_heavy else "BUILD_NEEDED",
            confidence="medium",
            rationale=(
                "Review text still contains not-met or partially-met success criteria. Record the judgment and return the run for another iteration instead of adopting."
            ),
            review_verdict=verdict,
            counts_note=counts_note,
            critical_count=critical_count,
            major_count=major_count,
            minor_count=minor_count,
            human_owned_blocker=human_blocker is not None,
            human_blocker_summary=human_blocker_summary,
            human_blocker_source=human_blocker_source,
            human_actions=human_blocker_actions,
            ownership_status=ownership_status,
            ownership_detail=ownership_detail,
        )

    if (
        minor_count > 0
        or "conditional pass" in verdict_lower
        or "adopt" in verdict_lower
        or verdict_lower.startswith("accept")
        or verdict_lower == "acceptable"
        or "ready to close" in verdict_lower
        or verdict_lower == "accept"
        or verdict_lower == "accepted"
        or verdict_lower == "adopt"
        or verdict_lower == "pass"
        or verdict_lower == "pass with issues"
        or "proceed to adopt" in review_lower
    ):
        return JudgeRecommendation(
            decision="Adopt",
            confidence="medium" if minor_count > 0 else "low",
            rationale="Only minor follow-ups are visible in review.md. Judge can likely adopt, capture any notes in improve.md, and keep the run moving forward without returning it.",
            review_verdict=verdict,
            counts_note=counts_note,
            critical_count=critical_count,
            major_count=major_count,
            minor_count=minor_count,
            human_owned_blocker=human_blocker is not None,
            human_blocker_summary=human_blocker_summary,
            human_blocker_source=human_blocker_source,
            human_actions=human_blocker_actions,
            ownership_status=ownership_status,
            ownership_detail=ownership_detail,
        )

    return JudgeRecommendation(
        decision="Unknown",
        confidence="low",
        rationale="review.md exists, but the advisory could not infer a clear return path from the parsed review structure. Manual Judge review is still required.",
        review_verdict=verdict,
        counts_note=counts_note,
        critical_count=critical_count,
        major_count=major_count,
        minor_count=minor_count,
        human_owned_blocker=human_blocker is not None,
        human_blocker_summary=human_blocker_summary,
        human_blocker_source=human_blocker_source,
        human_actions=human_blocker_actions,
        ownership_status=ownership_status,
        ownership_detail=ownership_detail,
    )


def _build_review_summary_next_actions(recommendation: JudgeRecommendation) -> list[str]:
    if recommendation.human_owned_blocker:
        actions = ["Resolve the human-owned blocker before attempting any reroute."]
        if recommendation.suggested_return_phase == "PLAN_NEEDED":
            actions.append("After the blocker is resolved, record Judge feedback and return the run to Planner.")
        elif recommendation.suggested_return_phase == "BUILD_NEEDED":
            actions.append("After the blocker is resolved, record Judge feedback and return the run to Builder.")
        else:
            actions.append("After the blocker is resolved, record the Judge decision in improve.md.")
        return actions

    if recommendation.decision == "Reject" or recommendation.suggested_return_phase == "PLAN_NEEDED":
        return [
            "Record the Judge decision in improve.md.",
            "Write feedback to plan_review.md and return the run to Planner at PLAN_NEEDED.",
        ]
    if recommendation.decision == "Revise" and recommendation.suggested_return_phase == "BUILD_NEEDED":
        return [
            "Record the Judge decision in improve.md.",
            "Write feedback to build_review.md and return the run to Builder at BUILD_NEEDED.",
        ]
    if recommendation.decision == "Adopt":
        return [
            "Review any remaining minor issues and capture notes in improve.md.",
            "Proceed toward result close-out when the Judge decision is final.",
        ]
    return [
        "Read review.md in full and make a manual Judge decision.",
        "Record the decision in improve.md before rerouting the run.",
    ]


def _review_verdict_looks_adoptable(review_text: str, verdict: str | None) -> bool:
    verdict_lower = (verdict or "").lower()
    review_lower = review_text.lower()
    return bool(
        "conditional pass" in verdict_lower
        or "adopt" in verdict_lower
        or verdict_lower.startswith("accept")
        or verdict_lower == "acceptable"
        or "ready to close" in verdict_lower
        or verdict_lower == "accept"
        or verdict_lower == "accepted"
        or verdict_lower == "pass"
        or verdict_lower == "pass with issues"
        or "proceed to adopt" in review_lower
    )


def _derive_review_summary_status(
    review_text: str,
    verdict: str | None,
    critical_count: int,
    major_count: int,
    minor_count: int,
    has_not_met: bool,
    has_partially_met: bool,
    recommendation: JudgeRecommendation | None,
) -> Literal["blocking", "revise", "adopt", "unknown"]:
    if recommendation is not None and recommendation.human_owned_blocker:
        return "blocking"
    if recommendation is not None and recommendation.decision in {"Reject", "Revise"}:
        return "revise"
    if recommendation is not None and recommendation.decision == "Adopt":
        return "adopt"
    if critical_count > 0 or major_count > 0 or has_not_met or has_partially_met:
        return "revise"
    if minor_count > 0:
        return "adopt"
    if _review_verdict_looks_adoptable(review_text, verdict):
        return "adopt"
    return "unknown"


def _build_fallback_review_summary_next_actions(
    summary_status: Literal["blocking", "revise", "adopt", "unknown"],
    phase: str,
) -> list[str]:
    if summary_status == "blocking":
        return [
            "Resolve the human-owned blocker before attempting any reroute.",
            "After the blocker is resolved, record the decision and continue the workflow manually.",
        ]
    if summary_status == "revise":
        if phase == "REVIEW_NEEDED":
            return [
                "Finish the review cycle and confirm the final review artifact.",
                "When Judge begins, use the review findings to decide whether the run returns to Plan or Build.",
            ]
        return [
            "Read review.md in full and decide whether the run should return to Plan or Build.",
            "Record the Judge decision before rerouting the run.",
        ]
    if summary_status == "adopt":
        return [
            "Review any remaining minor issues and capture notes in improve.md when needed.",
            "Proceed toward close-out once the human decision is final.",
        ]
    return [
        "Read review.md in full and make a manual decision.",
        "Do not infer a reroute until the phase owner confirms the next step.",
    ]


def _derive_review_summary(run_dir: Path, phase: str) -> ReviewSummary | None:
    """Return backend-owned review summary data.

    `None` means no readable review artifact exists for the run.
    `ReviewSummary.available=True` means a review artifact exists and the backend
    produced a display-safe summary for it, even if `summary_status` remains
    `"unknown"`.
    """
    review_path = latest_review_artifact(run_dir)
    review_text = _read_text_if_exists(review_path).strip() if review_path else ""
    if not review_text:
        return None

    critical_count, major_count, minor_count, counts_note = _extract_review_issue_counts(review_text)
    verdict = _extract_review_verdict(review_text)
    has_not_met, has_partially_met = _extract_review_completion_flags(review_text)
    recommendation = _derive_judge_recommendation(run_dir, phase)
    status = _derive_review_summary_status(
        review_text,
        verdict,
        critical_count,
        major_count,
        minor_count,
        has_not_met,
        has_partially_met,
        recommendation,
    )

    return ReviewSummary(
        available=True,
        summary_status=status,
        critical_count=critical_count,
        major_count=major_count,
        minor_count=minor_count,
        review_verdict=verdict,
        counts_note=counts_note,
        next_actions=(
            _build_review_summary_next_actions(recommendation)
            if recommendation is not None
            else _build_fallback_review_summary_next_actions(status, phase)
        ),
        source_artifact=review_path.name if review_path else None,
    )


def _comment_declares_human_blocked(comment_text: str) -> bool:
    normalized = comment_text.strip()
    if not normalized:
        return False
    patterns = (
        r"\bHUMAN_BLOCKED\b",
        r"\bblocker_owner\s*=\s*HUMAN\b",
        r"人間判断待ち",
        r"human[- ]owned blocker",
    )
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns)


def _record_human_blocked_comment_outcome(run_dir: Path, comment_text: str) -> bool:
    if not _comment_declares_human_blocked(comment_text):
        return False

    canonical_phase = _resolve_agent_os_phase(run_dir)
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at=datetime.now(timezone.utc).isoformat(),
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase=canonical_phase,
            target_phase=canonical_phase,
        ),
    )
    return True


def _hydrate_judge_recommendation_targets(run_dir: Path, recommendation: JudgeRecommendation | None) -> JudgeRecommendation | None:
    if recommendation is None or not recommendation.suggested_return_phase:
        return recommendation

    assignment = _resolve_assignment_summary(run_dir, recommendation.suggested_return_phase)
    specialist = _resolve_specialist_visibility(run_dir, recommendation.suggested_return_phase)
    recommendation.target_role = assignment.role or None
    recommendation.target_execution_type = assignment.execution.execution_type or None
    recommendation.target_provider = assignment.model.provider or None
    recommendation.target_model = assignment.model.model or None
    recommendation.target_specialist_code = specialist.specialist_code or "(generic)"
    recommendation.target_specialist_mode = specialist.mode or None
    return recommendation


def _detect_run_human_blocker(run_dir: Path) -> HumanBlockerStatus | None:
    blocker_decision = get_build_gate_decision(run_dir)
    status = str(blocker_decision.get("status") or "")
    if status == "SYSTEM":
        return None
    return HumanBlockerStatus(
        active=status == "HUMAN",
        summary=str(blocker_decision.get("summary") or ""),
        source=str(blocker_decision.get("source") or "") or None,
        actions=[str(action) for action in blocker_decision.get("actions", [])],
        ownership_status=status or None,
        ownership_detail=str(blocker_decision.get("detail") or "") or None,
    )


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


_SPECIALIST_PHASES = frozenset({"PLAN_NEEDED", "REVIEW_NEEDED", "BUILD_NEEDED"})


def _resolve_specialist_visibility(
    run_dir: Path,
    phase: str,
    framework_root: Path = PROJECT_ROOT,
) -> SpecialistVisibility:
    """Resolve the specialist assignment state for the current phase.

    Reads goal.md and execution-assignment.md from run_dir, then delegates to
    specialist_registry to determine mode (explicit / inferred / unresolved).
    Phases that do not use specialist selection return mode="not_applicable".
    """
    if phase not in _SPECIALIST_PHASES:
        return SpecialistVisibility(
            phase=phase,
            mode="not_applicable",
            specialist_code="",
            reason=f"specialist selection is not applicable for phase {phase}",
            has_gap=False,
        )

    from ..legacy.cli.specialist_registry import (
        resolve_builder_specialist,
        resolve_critic_specialist,
        resolve_planner_specialist,
    )

    def _read(filename: str) -> str:
        path = run_dir / filename
        try:
            return path.read_text(encoding="utf-8") if path.exists() else ""
        except OSError:
            return ""

    goal_text = _read("goal.md")
    assignment_text = _read("execution-assignment.md")

    if phase == "PLAN_NEEDED":
        selection = resolve_planner_specialist(goal_text, assignment_text, framework_root)
    elif phase == "BUILD_NEEDED":
        selection = resolve_builder_specialist(goal_text, assignment_text, framework_root)
    else:  # REVIEW_NEEDED
        selection = resolve_critic_specialist(goal_text, assignment_text, framework_root)

    # has_gap: unresolved = no specialist match; explicit + missing file = assigned but broken
    has_gap = selection.mode == "unresolved" or (
        selection.mode == "explicit"
        and bool(selection.ptype)
        and not selection.specialist_content
    )

    return SpecialistVisibility(
        phase=phase,
        mode=selection.mode,
        specialist_code=selection.ptype or "",
        reason=selection.reason,
        has_gap=has_gap,
    )


def _assignment_role_for_phase(phase: str):
    from apsf.core.domain.models import Role

    return {
        "PLAN_NEEDED": Role.PLANNER,
        "BUILD_NEEDED": Role.BUILDER,
        "REVIEW_NEEDED": Role.CRITIC,
    }.get(phase)


def _resolve_execution_visibility(run_dir: Path, phase: str) -> ExecutionVisibility:
    role = _assignment_role_for_phase(phase)
    if role is None:
        return ExecutionVisibility(
            role="",
            execution_type="not_applicable",
            target="",
            workspace="",
            mode="not_applicable",
            reason=f"execution assignment is not applicable for phase {phase}",
        )

    from apsf.core.domain.models import ExecutionType
    from apsf.legacy.config.settings import get_settings
    from apsf.legacy.orchestration.execution_assignment_service import ExecutionAssignmentService

    service = ExecutionAssignmentService(settings=get_settings())
    context = service.load_from_file(run_dir / "execution-assignment.md", run_dir)
    assignment = context.get_execution_assignment(role)

    if assignment is None:
        return ExecutionVisibility(
            role=role.value,
            execution_type="human",
            target="human",
            workspace="",
            mode="default",
            reason=f"no explicit execution assignment for {role.value}; defaulting to human",
        )

    target = assignment.tool.strip()
    if assignment.execution_type == ExecutionType.CLI:
        target = target or "claude"
    elif assignment.execution_type == ExecutionType.HUMAN:
        target = target or "human"
    else:
        target = target or "future-api"

    return ExecutionVisibility(
        role=role.value,
        execution_type=assignment.execution_type.value,
        target=target,
        workspace=assignment.workspace,
        mode="explicit",
        reason=f"execution-assignment.md specifies {assignment.execution_type.value} for {role.value}",
    )


def _resolve_model_visibility(run_dir: Path, phase: str, execution: ExecutionVisibility | None = None) -> ModelVisibility:
    role = _assignment_role_for_phase(phase)
    if role is None:
        return ModelVisibility(
            role="",
            provider="",
            model="",
            mode="not_applicable",
            reason=f"model assignment is not applicable for phase {phase}",
        )

    from apsf.legacy.config.settings import get_settings
    from apsf.legacy.orchestration.assignment_service import AssignmentService

    execution_type = execution.execution_type if execution is not None else ""
    settings = get_settings()
    service = AssignmentService(settings=settings)
    context = service.load_from_file(run_dir / "model-assignment.md", run_dir)
    resolved = service.resolve_assignment(context, role, execution_type=execution_type)

    if resolved.mode == "wrapper-backed":
        wrapper_provider = execution.target if execution is not None and execution.execution_type == "cli" else ""
        return ModelVisibility(
            role=role.value,
            provider=wrapper_provider,
            model="",
            mode="wrapper-backed",
            reason=resolved.reason if not wrapper_provider else f"{resolved.reason}; provider shown as CLI target",
        )

    if resolved.mode == "unset" or resolved.provider is None and not resolved.is_human:
        return ModelVisibility(
            role=role.value,
            provider="unset",
            model="",
            mode="unset",
            reason=resolved.reason,
        )

    if resolved.is_human:
        return ModelVisibility(
            role=role.value,
            provider="human",
            model="",
            mode="human",
            reason=resolved.reason,
        )

    return ModelVisibility(
        role=role.value,
        provider=resolved.provider.value,
        model=resolved.model,
        mode=resolved.mode,  # explicit / default / auto
        reason=resolved.reason,
    )


def _resolve_assignment_summary(run_dir: Path, phase: str) -> AssignmentSummary:
    role = _assignment_role_for_phase(phase)
    execution = _resolve_execution_visibility(run_dir, phase)
    model = _resolve_model_visibility(run_dir, phase, execution=execution)
    return AssignmentSummary(
        phase=phase,
        role=role.value if role is not None else "",
        execution=execution,
        model=model,
    )


def _collect_run_detail(taxonomy: str, run_name: str, run_dir: Path) -> RunDetail:
    info = PhaseDetector(run_dir).detect()
    canonical_phase = _resolve_canonical_view_phase(taxonomy, run_name, run_dir, info.phase.value)
    suppress_mismatch_banner = _suppress_detector_mismatch_banner(run_dir, canonical_phase)
    actions = build_operator_actions(run_name, canonical_phase, run_dir)
    primary_action = next((action for action in actions if action.primary), actions[0])
    judge_recommendation = _hydrate_judge_recommendation_targets(
        run_dir,
        _derive_judge_recommendation(run_dir, canonical_phase),
    )
    review_summary = _derive_review_summary(run_dir, canonical_phase)
    human_blocker = _detect_run_human_blocker(run_dir)
    child_summaries = []
    if "/" not in run_name:
        child_summaries = build_child_summaries(run_name, taxonomy)
    priority_index = load_priority_index()
    priority, priority_reason = resolve_priority(run_name, priority_index)
    return RunDetail(
        name=run_name,
        taxonomy=taxonomy,
        phase=canonical_phase,
        next_role=_phase_owner_name(canonical_phase) or info.next_role,
        decision_reason=(
            f"Phase pinned to {canonical_phase} by workflow state (artifact detector suggests {info.phase.value})"
            if canonical_phase != info.phase.value and not suppress_mismatch_banner
            else info.decision_reason
        ),
        artifacts=_build_artifact_inventory(run_dir),
        operator_command=primary_action.command,
        operator_actions=actions,
        children=child_summaries,
        specialist_visibility=_resolve_specialist_visibility(run_dir, canonical_phase),
        assignment_summary=_resolve_assignment_summary(run_dir, canonical_phase),
        review_summary=review_summary,
        judge_recommendation=judge_recommendation,
        human_blocker=human_blocker,
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

        canonical_phase = _resolve_canonical_view_phase(taxonomy, full_name, run_dir, info.phase.value)
        actions = build_operator_actions(full_name, canonical_phase, run_dir)
        action_map = {action.id: action for action in actions}
        priority, priority_reason = resolve_priority(full_name, priority_index)
        rows.append(
            MatrixRow(
                name=full_name,
                taxonomy=taxonomy,
                phase=canonical_phase,
                next_role=_phase_owner_name(canonical_phase) or info.next_role,
                priority=priority,
                priority_reason=priority_reason,
                plan_action=action_map.get("phase-primary") if canonical_phase == "PLAN_NEEDED" else None,
                build_action=action_map.get("phase-primary") if canonical_phase == "BUILD_NEEDED" else None,
                review_action=action_map.get("phase-primary") if canonical_phase == "REVIEW_NEEDED" else None,
                rerun_action=(
                    action_map.get("rerun-plan")
                    if canonical_phase == "PLAN_NEEDED"
                    else action_map.get("rerun-build")
                    if canonical_phase == "BUILD_NEEDED"
                    else action_map.get("rerun-review")
                    if canonical_phase == "REVIEW_NEEDED"
                    else action_map.get("rerun-improve")
                    if canonical_phase == "IMPROVE_NEEDED"
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


def _resolve_judge_chat_cli() -> tuple[list[str], str]:
    configured = os.getenv("APSF_VIEWER_JUDGE_CHAT_CLI", "").strip().lower()
    if configured in {"codex", "codex-cli"}:
        preferred = "codex"
    elif configured in {"claude", "claude-cli"}:
        preferred = "claude"
    else:
        try:
            viewer_config = _resolve_viewer_config_response()
            preferred = "codex" if viewer_config.cli_tool_mode in {"codex", "both"} else "claude"
        except Exception:
            preferred = "claude"

    if preferred == "codex":
        codex_path = shutil.which("codex.cmd") or shutil.which("codex") or shutil.which("codex.ps1")
        if codex_path:
            return [codex_path, "exec", "-"], "codex"
        claude_path = shutil.which("claude.cmd") or shutil.which("claude") or shutil.which("claude.ps1")
        if claude_path:
            return [claude_path, "-p"], "claude"
    else:
        claude_path = shutil.which("claude.cmd") or shutil.which("claude") or shutil.which("claude.ps1")
        if claude_path:
            return [claude_path, "-p"], "claude"
        codex_path = shutil.which("codex.cmd") or shutil.which("codex") or shutil.which("codex.ps1")
        if codex_path:
            return [codex_path, "exec", "-"], "codex"

    raise HTTPException(
        status_code=503,
        detail="No judge chat CLI found. Install codex or claude, or set APSF_VIEWER_JUDGE_CHAT_CLI.",
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

        canonical_phase = _resolve_canonical_view_phase(taxonomy, name, run_dir, info.phase.value)
        priority, priority_reason = resolve_priority(name, priority_index)
        runs.append(
            RunSummary(
                name=name,
                taxonomy=taxonomy,
                phase=canonical_phase,
                next_role=_phase_owner_name(canonical_phase) or info.next_role,
                child_count=len(repo.list_child_runs(name, taxonomy=taxonomy)),
                has_plan_review=(run_dir / "plan_review.md").exists(),
                has_build_review=(run_dir / "build_review.md").exists(),
                has_review_review=(run_dir / "review_review.md").exists(),
                has_improve_review=(run_dir / "improve_review.md").exists(),
                last_modified=run_dir.stat().st_mtime,
                priority=priority,
                priority_reason=priority_reason,
                human_blocker_active=_detect_run_human_blocker(run_dir) is not None,
            )
        )

    priority_order = {"Now": 0, "Next": 1, "Later": 2, "Unranked": 3}
    runs.sort(key=lambda item: (priority_order.get(item.priority, 3), -item.last_modified))
    return runs


@app.get("/api/viewer-config", response_model=ViewerConfigResponse)
async def get_viewer_config():
    return _resolve_viewer_config_response()


@app.post("/api/viewer-config", response_model=ViewerConfigResponse)
async def update_viewer_config(request: ViewerConfigUpdateRequest):
    try:
        return _update_viewer_config(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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



@app.post(
    "/api/runs/{taxonomy}/{run_name:path}/specialists/create",
    response_model=CreateSpecialistResponse,
)
async def create_specialist(
    taxonomy: str, run_name: str, request: CreateSpecialistRequest
):
    """Create a new specialist library artifact and register it."""
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    try:
        return _create_specialist_library_asset(
            role=request.role,
            specialist_code=request.specialist_code,
            slug=request.slug,
            title=request.title,
            scope=request.scope,
            use_when=request.use_when,
            out_of_scope=request.out_of_scope,
            evaluation_criteria=request.evaluation_criteria,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to create specialist: {exc}"
        ) from exc


@app.post(
    "/api/runs/{taxonomy}/{run_name:path}/confirm-specialist",
    response_model=ConfirmSpecialistResponse,
)
async def confirm_specialist(
    taxonomy: str, run_name: str, request: ConfirmSpecialistRequest
):
    """Write the operator-confirmed specialist code and optional model override."""
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    artifact_path = _write_confirmed_specialist(
        run_dir, request.role, request.specialist_code, request.source
    )
    execution_artifact_path = _write_execution_target_override(
        run_dir,
        request.role,
        request.provider,
    )
    if execution_artifact_path is not None:
        artifact_path = execution_artifact_path
    model_artifact_path: str | None = None
    if request.apply_model_assignment:
        model_artifact_path = _write_model_assignment_override(
            run_dir,
            request.role,
            request.provider,
            request.model,
        )
    return ConfirmSpecialistResponse(
        written=True,
        specialist_code=request.specialist_code,
        artifact_path=artifact_path,
        target_run_name=run_name,
        model_artifact_path=model_artifact_path,
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


@app.get("/api/runs/{taxonomy}/{run_name:path}/agent-os", response_model=AgentOSInfo)
async def get_agent_os_info(taxonomy: str, run_name: str):
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    from apsf.core.state.run_state_repository import RunStateRepository
    from apsf.core.manifest.manifest_repository import ManifestRepository
    from apsf.core.gates.gate_service import GateService
    from apsf.core.storage.force_audit_repository import ForceAuditRepository

    # run_state
    run_state_data = _bootstrap_run_state_if_missing(run_dir)
    run_state = None
    if run_state_data is not None:
        run_state = RunStateInfo(
            run_id=run_state_data.run_id,
            current_phase=run_state_data.current_phase,
            phase_status=run_state_data.phase_status,
            current_owner=run_state_data.current_owner,
            retry_count=run_state_data.retry_count,
            last_error=run_state_data.last_error,
            active_handoff_id=run_state_data.active_handoff_id,
            gate_failures=run_state_data.gate_failures or [],
        )

    # artifact_manifest
    manifest = ManifestRepository(run_dir).load()
    artifact_manifest = None
    if manifest is not None:
        artifact_manifest = [
            ArtifactEntryInfo(
                artifact_name=e.artifact_name,
                artifact_type=e.artifact_type,
                owner_role=e.owner_role,
                written_by=e.written_by,
                status=e.status,
                updated_at=e.updated_at,
                revision=e.revision,
                source_handoff_id=e.source_handoff_id,
            )
            for e in manifest.entries.values()
        ]

    # gate_results — only meaningful when run_state.json exists (Agent OS v1 run)
    gate_results: list[GateResultInfo] = []
    if run_state_data is not None:
        try:
            raw_gates = GateService().evaluate_all(run_dir)
            gate_results = [
                GateResultInfo(gate_type=r.gate_type, passed=r.passed, reason=r.reason)
                for r in raw_gates
            ]
        except Exception:
            gate_results = []

    # force_audit (optional)
    raw_audit = ForceAuditRepository(run_dir).load()
    force_audit = [
        ForceAuditEntryInfo(
            timestamp=e.timestamp,
            command=e.command,
            target_file=e.target_file,
            role=e.role,
            had_reason=e.had_reason,
            reason=e.reason,
            override_kind=e.override_kind,
        )
        for e in raw_audit
    ] if raw_audit else None

    recovery_checkpoints = _load_recovery_checkpoints(run_dir)
    recovery_snapshots = _load_recovery_snapshots(run_dir)
    recovery_apply_traces = _load_recovery_apply_traces(run_dir)

    return AgentOSInfo(
        run_state=run_state,
        artifact_manifest=artifact_manifest,
        gate_results=gate_results,
        force_audit=force_audit,
        recovery_checkpoints=recovery_checkpoints,
        recovery_snapshots=recovery_snapshots,
        recovery_apply_traces=recovery_apply_traces,
    )


@app.post("/api/runs/{taxonomy}/{run_name:path}/rerun-comment", response_model=SaveRerunCommentResponse)
async def save_rerun_comment(taxonomy: str, run_name: str, request: SaveRerunCommentRequest):
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    artifact_name, artifact_path, appended_at = _append_rerun_comment(run_dir, request.action_id, request.comment_text)
    _record_human_blocked_comment_outcome(run_dir, request.comment_text)

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
    canonical_phase = _resolve_agent_os_phase(run_dir)
    actions = {action.id: action for action in build_operator_actions(run_name, canonical_phase, run_dir)}
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
    status = _classify_process_result(completed)

    viewer_db.update_execution_result(
        execution_id=execution_id,
        result_status=status,
        exit_code=completed.returncode,
        stdout=stdout,
        stderr=stderr,
    )
    if action.execution_type == "build" and status == "PARTIAL":
        _pin_run_state_after_partial_build(run_dir)

    return ExecuteCommandResponse(
        action_id=action.id,
        command=action.command,
        status=status,
        exit_code=completed.returncode,
        stdout=stdout,
        stderr=stderr,
    )


@app.post("/api/runs/{taxonomy}/{run_name:path}/agent-os/actions/execute", response_model=ExecuteCommandResponse)
async def execute_agent_os_operator_action(
    taxonomy: str,
    run_name: str,
    request: ExecuteAgentOSActionRequest,
):
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    action_type = "agent-os"
    command = f"agent-os:{request.action_id}"
    execution_id = viewer_db.insert_execution_pending(
        taxonomy=taxonomy,
        run_name=run_name,
        action_id=request.action_id,
        action_type=action_type,
        command=command,
    )

    response = await asyncio.to_thread(_execute_agent_os_action, run_dir, run_name, request)

    viewer_db.update_execution_result(
        execution_id=execution_id,
        result_status=response.status,
        exit_code=response.exit_code,
        stdout=response.stdout,
        stderr=response.stderr,
        command=response.command,
    )

    return response


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


_PHASE_TO_SPECIALIST_ROLE: dict[str, str] = {
    "PLAN_NEEDED": "Planner",
    "BUILD_NEEDED": "Builder",
    "REVIEW_NEEDED": "Critic",
}


@app.get(
    "/api/runs/{taxonomy}/{run_name:path}/specialist-candidates",
    response_model=SpecialistCandidatesResponse,
)
async def get_specialist_candidates(taxonomy: str, run_name: str, phase: str | None = None):
    """Return ranked specialist candidates for the current or requested phase, scored against goal.md."""
    from apsf.legacy.cli.specialist_registry import (
        rank_builder_specialists,
        rank_critic_specialists,
        rank_planner_specialists,
        specialist_display_name,
        extract_use_when_first_line,
        extract_primary_ptype,
        extract_primary_btype,
        extract_primary_ctype,
        selection_sections,
    )

    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    info = PhaseDetector(run_dir).detect()
    phase_value = (phase or info.phase.value).strip().upper()

    if phase_value not in _PHASE_TO_SPECIALIST_ROLE:
        return SpecialistCandidatesResponse(
            phase=phase_value,
            role="",
            current_mode="not_applicable",
            current_code="",
            candidates=[],
        )

    role = _PHASE_TO_SPECIALIST_ROLE[phase_value]

    def _read(filename: str) -> str:
        p = run_dir / filename
        try:
            return p.read_text(encoding="utf-8") if p.exists() else ""
        except OSError:
            return ""

    goal_text = _read("goal.md")
    assignment_text = _read("execution-assignment.md")

    # current explicit code (if any)
    if phase_value == "PLAN_NEEDED":
        explicit_code = extract_primary_ptype(assignment_text)
        ranked = rank_planner_specialists(goal_text, PROJECT_ROOT)
    elif phase_value == "BUILD_NEEDED":
        explicit_code = extract_primary_btype(assignment_text)
        ranked = rank_builder_specialists(goal_text, PROJECT_ROOT)
    else:
        explicit_code = extract_primary_ctype(assignment_text)
        ranked = rank_critic_specialists(goal_text, PROJECT_ROOT)

    current_mode = "explicit" if explicit_code else ("inferred" if ranked and ranked[0].score > 0 else "unresolved")
    current_code = explicit_code or (ranked[0].ptype if ranked and ranked[0].score > 0 else "")

    candidates: list[SpecialistCandidateItem] = []
    for i, s in enumerate(ranked):
        sections = selection_sections(s.specialist_content)
        candidates.append(
            SpecialistCandidateItem(
                code=s.ptype,
                name=specialist_display_name(s.ptype),
                score=s.score,
                reason=s.reason,
                use_when=extract_use_when_first_line(s.specialist_content),
                path=str(s.specialist_path.relative_to(PROJECT_ROOT)) if s.specialist_path is not None else None,
                scope=_summarize_markdown_line(sections.get("scope", "")),
                out_of_scope=_summarize_markdown_line(sections.get("out_of_scope", "")),
                evaluation_criteria=_summarize_markdown_line(sections.get("evaluation_criteria", "")),
                is_recommended=(i == 0 and s.score > 0),
                is_current=(s.ptype == explicit_code),
            )
        )
    # always add generic option
    candidates.append(
        SpecialistCandidateItem(
            code="",
            name="generic",
            score=0,
            reason="no specialist — use generic Planner/Builder/Critic prompt",
            use_when="When no specialist closely matches the goal",
            path=None,
            scope="Use the generic role prompt without specialist-specific library guidance.",
            out_of_scope="Does not create or expand the specialist library.",
            evaluation_criteria="Fallback choice when explicit specialist fit is weak or intentionally unnecessary.",
            is_recommended=False,
            is_current=(explicit_code == "" and current_mode == "explicit"),
        )
    )

    return SpecialistCandidatesResponse(
        phase=phase_value,
        role=role,
        current_mode=current_mode,
        current_code=current_code,
        candidates=candidates,
    )



_CONFIRM_SECTION_HEADER = "## Confirmed Specialist"
_CONFIRM_ROLE_MARKER = {
    "Planner": "P-TYPE",
    "Builder": "B-TYPE",
    "Critic": "C-TYPE",
}


def _extract_confirmed_section_lines(content: str) -> list[str]:
    """Extract the body lines of ## Confirmed Specialist section (excludes the header line)."""
    lines = content.splitlines()
    in_section = False
    body: list[str] = []
    for line in lines:
        if line.strip() == _CONFIRM_SECTION_HEADER:
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            body.append(line)
    return body


_TYPE_MARKERS = {"P-TYPE", "B-TYPE", "C-TYPE"}


def _merge_confirmed_section(existing_body: list[str], marker: str, code_line: str) -> list[str]:
    """Return updated TYPE-only body lines with the given marker replaced or appended.

    Only TYPE lines (P-TYPE / B-TYPE / C-TYPE) are preserved from the existing body.
    Metadata lines (Confirmed-By, Confirmed-At, blank) are discarded — they are
    re-written at the section level by the caller for the latest write.
    """
    type_lines: dict[str, str] = {}
    for line in existing_body:
        upper = line.upper()
        for m in _TYPE_MARKERS:
            if upper.startswith(m + ":"):
                type_lines[m] = line
                break
    type_lines[marker.upper()] = code_line
    # Preserve stable order: P-TYPE → B-TYPE → C-TYPE
    return [type_lines[m] for m in ("P-TYPE", "B-TYPE", "C-TYPE") if m in type_lines]


def _write_confirmed_specialist(
    run_dir: Path, role: str, specialist_code: str, source: str
) -> str:
    """
    Write specialist confirmation to execution-assignment.md.

    Maintains one '## Confirmed Specialist' section shared across all roles.
    Each role writes its own TYPE line (P-TYPE / B-TYPE / C-TYPE); existing
    lines for other roles are preserved, so confirming Builder does not erase
    a previously confirmed Planner.
    Returns the artifact path.
    """
    from datetime import date

    assignment_path = run_dir / "execution-assignment.md"
    marker = _CONFIRM_ROLE_MARKER.get(role, "P-TYPE")
    code_line = f"{marker}: {specialist_code}" if specialist_code else f"{marker}: NONE"
    today = date.today().isoformat()

    if assignment_path.exists():
        content = assignment_path.read_text(encoding="utf-8")
        if _CONFIRM_SECTION_HEADER in content:
            # Merge: update only the marker line for this role, keep others
            existing_body = _extract_confirmed_section_lines(content)
            merged_body = _merge_confirmed_section(existing_body, marker, code_line)
            # Update Confirmed-By / Confirmed-At if they appear in the body, else they
            # stay from the previous write — acceptable since each role's code line
            # has its own timestamp context via the commit.  Keep it simple.
            # Remove the old section entirely and re-write merged
            lines = content.splitlines(keepends=True)
            out: list[str] = []
            skip = False
            for line in lines:
                if line.strip() == _CONFIRM_SECTION_HEADER:
                    skip = True
                    continue
                if skip and line.startswith("## "):
                    skip = False
                if not skip:
                    out.append(line)
            base = "".join(out).rstrip("\n")
            body_text = "\n".join(merged_body).strip()
            new_section = (
                f"\n{_CONFIRM_SECTION_HEADER}\n\n"
                f"{body_text}\n"
                f"Confirmed-By: {source}\n"
                f"Confirmed-At: {today}\n"
            )
            content = base + new_section
        else:
            if not content.endswith("\n"):
                content += "\n"
            content += (
                f"\n{_CONFIRM_SECTION_HEADER}\n\n"
                f"{code_line}\n"
                f"Confirmed-By: {source}\n"
                f"Confirmed-At: {today}\n"
            )
    else:
        # Create a minimal execution-assignment.md
        content = (
            "# Execution Assignment\n\n"
            "| Role | Execution Type | Tool / Method | Workspace | Notes |\n"
            "|---|---|---|---|---|\n"
            f"\n{_CONFIRM_SECTION_HEADER}\n\n"
            f"{code_line}\n"
            f"Confirmed-By: {source}\n"
            f"Confirmed-At: {today}\n"
        )

    assignment_path.write_text(content, encoding="utf-8")
    try:
        return str(assignment_path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(assignment_path)


_MODEL_ROLE_DISPLAY = {
    "Planner": "Planner",
    "Builder": "Builder",
    "Critic": "Critic",
    "Judge": "Judge",
    "JuniorBuilder": "JuniorBuilder",
}

_CLI_TOOL_BY_PROVIDER = {
    "anthropic": ("cli", "claude"),
    "openai": ("cli", "codex"),
    "gemini": ("cli", "gemini-cli"),
    "human": ("human", "human"),
}


def _write_execution_target_override(run_dir: Path, role: str, provider: str) -> str | None:
    provider_value = (provider or "").strip().lower()
    override = _CLI_TOOL_BY_PROVIDER.get(provider_value)
    if override is None:
        return None

    assignment_path = run_dir / "execution-assignment.md"
    if not assignment_path.exists():
        return None

    role_display = _MODEL_ROLE_DISPLAY.get(role, role)
    new_execution_type, new_tool = override
    lines = assignment_path.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    updated = False

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            out.append(line)
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 4 or cells[0] != role_display:
            out.append(line)
            continue
        cells[1] = new_execution_type
        cells[2] = new_tool
        if len(cells) >= 5:
            out.append(f"| {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} | {cells[4]} |\n")
        else:
            out.append(f"| {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |\n")
        updated = True

    if not updated:
        return None

    assignment_path.write_text("".join(out), encoding="utf-8")
    try:
        return str(assignment_path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(assignment_path)


def _write_model_assignment_override(
    run_dir: Path,
    role: str,
    provider: str,
    model: str,
) -> str:
    assignment_path = run_dir / "model-assignment.md"
    role_display = _MODEL_ROLE_DISPLAY.get(role, role)
    provider_value = (provider or "").strip().lower()
    model_value = (model or "").strip()

    if provider_value == "unset":
        provider_value = ""
        model_value = ""

    is_human = provider_value == "human"
    notes = (
        "operator-selected from Select Specialist"
        if provider_value or model_value or is_human
        else "operator-cleared from Select Specialist"
    )
    row = (
        f"| {role_display} | {provider_value} | {model_value} | "
        f"{'yes' if is_human else 'no'} | {notes} |\n"
    )

    if assignment_path.exists():
        lines = assignment_path.read_text(encoding="utf-8").splitlines(keepends=True)
    else:
        lines = [
            "# Model Assignment\n",
            "\n",
            "## Run Name\n",
            "\n",
            f"{run_dir.name}\n",
            "\n",
            "## Goal Summary\n",
            "\n",
            "\n",
            "---\n",
            "\n",
            "## Role Assignments\n",
            "\n",
            "| Role | Provider | Model | Human? | Notes |\n",
            "|---|---|---|---|---|\n",
        ]

    out: list[str] = []
    replaced = False
    for line in lines:
        if line.strip().startswith(f"| {role_display} |"):
            if not replaced:
                out.append(row)
                replaced = True
            continue
        out.append(line)

    if not replaced:
        insert_at = None
        for idx, line in enumerate(out):
            if line.strip() == "|---|---|---|---|---|":
                insert_at = idx + 1
                break
        if insert_at is None:
            if out and not out[-1].endswith("\n"):
                out[-1] += "\n"
            out.extend(
                [
                    "\n## Role Assignments\n",
                    "\n",
                    "| Role | Provider | Model | Human? | Notes |\n",
                    "|---|---|---|---|---|\n",
                    row,
                ]
            )
        else:
            out.insert(insert_at, row)

    assignment_path.write_text("".join(out), encoding="utf-8")
    try:
        return str(assignment_path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(assignment_path)


def _summarize_markdown_line(text: str) -> str:
    for line in (text or "").splitlines():
        stripped = line.strip().lstrip("-").strip()
        if stripped:
            return stripped
    return ""


def _build_specialist_markdown(
    *,
    role: str,
    specialist_code: str,
    title: str,
    scope: str,
    use_when: str,
    out_of_scope: str,
    evaluation_criteria: str,
) -> str:
    role_label = {
        "Planner": "Planner",
        "Builder": "Builder",
        "Critic": "Critic",
    }.get(role, role)
    return (
        f"# Specialist: {title} ({specialist_code})\n\n"
        f"You are the {title}.\n\n"
        f"## Scope\n\n{scope.strip()}\n\n"
        f"## Use This Specialist When\n\n{use_when.strip()}\n\n"
        f"## Out of Scope\n\n{out_of_scope.strip()}\n\n"
        f"## Evaluation Criteria\n\n{evaluation_criteria.strip()}\n\n"
        f"## Output Style\n\n"
        f"- Stay within the {role_label} role boundary.\n"
        f"- Keep recommendations concrete, scoped, and reviewable.\n"
    )


def _patch_specialist_registry_source(
    registry_path: Path,
    *,
    role: str,
    specialist_code: str,
    relative_path: str,
) -> str:
    from apsf.legacy.cli.specialist_registry import (
        specialist_mapping_name_for_role,
    )

    mapping_name = specialist_mapping_name_for_role(role)
    if not mapping_name:
        raise ValueError(f"Unsupported specialist role: {role}")
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry source not found: {registry_path}")

    content = registry_path.read_text(encoding="utf-8")
    if f'"{specialist_code}"' in content:
        raise ValueError(f"Specialist code already exists in registry: {specialist_code}")

    marker = f"{mapping_name}: dict[str, str] = {{"
    start = content.find(marker)
    if start == -1:
        raise RuntimeError(f"Registry mapping not found: {mapping_name}")

    close_index = content.find("\n}", start)
    if close_index == -1:
        raise RuntimeError(f"Registry mapping closing brace not found: {mapping_name}")

    insertion = f'    "{specialist_code}": "{relative_path}",\n'
    updated = content[:close_index] + insertion + content[close_index:]
    registry_path.write_text(updated, encoding="utf-8")
    return mapping_name


def _register_specialist_runtime_mapping(
    *,
    role: str,
    specialist_code: str,
    relative_path: str,
) -> None:
    from apsf.legacy.cli import specialist_registry

    mapping = specialist_registry.specialist_mapping_for_role(role)
    mapping[specialist_code] = relative_path


def _normalize_duplicate_guard_text(raw: str) -> str:
    return " ".join((raw or "").strip().lower().split())


def _find_duplicate_like_specialist(
    *,
    role: str,
    title: str,
    scope: str,
    use_when: str,
    out_of_scope: str,
    evaluation_criteria: str,
) -> tuple[str, str] | None:
    from apsf.legacy.cli.specialist_registry import (
        load_specialist_content,
        selection_sections,
        specialist_mapping_for_role,
    )

    expected_title = _normalize_duplicate_guard_text(title)
    expected_sections = {
        "scope": _normalize_duplicate_guard_text(scope),
        "use_when": _normalize_duplicate_guard_text(use_when),
        "out_of_scope": _normalize_duplicate_guard_text(out_of_scope),
        "evaluation_criteria": _normalize_duplicate_guard_text(evaluation_criteria),
    }
    mapping = specialist_mapping_for_role(role)
    for code, relative_path in mapping.items():
        content = load_specialist_content(code, PROJECT_ROOT, mapping)
        if not content:
            continue
        sections = selection_sections(content)
        heading = next((line.strip() for line in content.splitlines() if line.startswith("# Specialist: ")), "")
        existing_title = heading.replace("# Specialist: ", "", 1).split("(", 1)[0].strip()
        if _normalize_duplicate_guard_text(existing_title) != expected_title:
            continue
        existing_sections = {
            "scope": _normalize_duplicate_guard_text(sections.get("scope", "")),
            "use_when": _normalize_duplicate_guard_text(sections.get("use_this_specialist_when", "")),
            "out_of_scope": _normalize_duplicate_guard_text(sections.get("out_of_scope", "")),
            "evaluation_criteria": _normalize_duplicate_guard_text(sections.get("evaluation_criteria", "")),
        }
        if existing_sections == expected_sections:
            return code, relative_path
    return None


def _create_specialist_library_asset(
    *,
    role: str,
    specialist_code: str,
    slug: str,
    title: str,
    scope: str,
    use_when: str,
    out_of_scope: str,
    evaluation_criteria: str,
) -> CreateSpecialistResponse:
    from apsf.legacy.cli.specialist_registry import (
        derive_specialist_relative_path,
        normalize_specialist_code_for_role,
    )

    normalized_code = normalize_specialist_code_for_role(role, specialist_code)
    if not normalized_code:
        raise ValueError(f"Specialist code does not match role {role}: {specialist_code}")

    relative_path = derive_specialist_relative_path(role, normalized_code, slug)
    if not relative_path:
        raise ValueError("Unable to derive specialist path from role, code, and slug")

    target_path = PROJECT_ROOT / relative_path
    registry_path = PROJECT_ROOT / "src" / "apsf" / "legacy" / "cli" / "specialist_registry.py"

    if target_path.exists():
        raise ValueError(f"Specialist file already exists: {relative_path}")

    duplicate = _find_duplicate_like_specialist(
        role=role,
        title=title.strip(),
        scope=scope,
        use_when=use_when,
        out_of_scope=out_of_scope,
        evaluation_criteria=evaluation_criteria,
    )
    if duplicate is not None:
        duplicate_code, duplicate_path = duplicate
        raise ValueError(
            f"Duplicate-like specialist already exists for {role}: {duplicate_code} ({duplicate_path})"
        )

    markdown = _build_specialist_markdown(
        role=role,
        specialist_code=normalized_code,
        title=title.strip(),
        scope=scope,
        use_when=use_when,
        out_of_scope=out_of_scope,
        evaluation_criteria=evaluation_criteria,
    )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(markdown, encoding="utf-8")
    try:
        mapping_name = _patch_specialist_registry_source(
            registry_path,
            role=role,
            specialist_code=normalized_code,
            relative_path=relative_path,
        )
        _register_specialist_runtime_mapping(
            role=role,
            specialist_code=normalized_code,
            relative_path=relative_path,
        )
    except Exception:
        with contextlib.suppress(OSError):
            if target_path.exists():
                target_path.unlink()
        raise

    return CreateSpecialistResponse(
        created=True,
        role=role,
        specialist_code=normalized_code,
        title=title.strip(),
        scope=scope.strip(),
        use_when=use_when.strip(),
        out_of_scope=out_of_scope.strip(),
        evaluation_criteria=evaluation_criteria.strip(),
        relative_path=relative_path,
        registry_path=str(registry_path),
        mapping_name=mapping_name,
        assigned_to_run=False,
    )


class JudgeChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class JudgeChatRequest(BaseModel):
    messages: List[JudgeChatMessage]


class JudgeChatResponse(BaseModel):
    reply: str


def _build_judge_chat_context(run_dir: Path) -> str:
    """Read run artifacts and compose a context string for the Judge AI assistant."""
    sections: list[str] = []

    for filename, label in [
        ("goal.md", "GOAL"),
        ("plan.md", "PLAN"),
        ("build.md", "BUILD RECORD"),
    ]:
        path = run_dir / filename
        if path.exists():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                sections.append(f"## {label}\n\n{text}")

    review_path = latest_review_artifact(run_dir)
    if review_path is not None:
        text = review_path.read_text(encoding="utf-8").strip()
        if text:
            sections.append(f"## LATEST REVIEW ({review_path.name})\n\n{text}")

    build_review = run_dir / "build_review.md"
    if build_review.exists():
        text = build_review.read_text(encoding="utf-8").strip()
        if text:
            sections.append(f"## BUILD REVIEW (accumulated feedback)\n\n{text}")

    return "\n\n---\n\n".join(sections)


JUDGE_CHAT_SYSTEM_PROMPT = """You are the Judge AI assistant inside the APSF (AI Problem Solving Framework) Viewer.

Your role is to help the Goal-owner (human Judge) understand the Critic's review findings and make clear decisions so the run can proceed.

The APSF workflow is: Goal → Plan → Build → Review → (Improve or Result)
- Builder produces artifacts
- Critic reviews and raises Critical / Major / Minor issues
- Judge (human) decides: accept, or return to Builder/Planner with instructions

Your job in this chat:
1. Explain what each Critical/Major issue actually means in plain language
2. Ask targeted questions to help the Goal-owner make decisions
3. When the Goal-owner has decided, summarize the decisions as a ready-to-paste Builder comment in this format:

```
**Goal-owner 決定: BUILD_NEEDED**

[numbered list of decisions and Builder instructions]
```

Rules:
- Be concise. One issue at a time if there are many.
- Always ground your explanation in the actual review text provided.
- When the Goal-owner makes a decision, immediately record it and move to the next open issue.
- Use Japanese when the user writes in Japanese, English when they write in English.
- When all Critical and Major issues have decisions, offer the final composed Builder comment.
"""


@app.post(
    "/api/runs/{taxonomy}/{run_name:path}/judge-chat",
    response_model=JudgeChatResponse,
)
async def judge_chat(taxonomy: str, run_name: str, request: JudgeChatRequest):
    """Judge AI assistant: invokes Codex/Claude CLI with run context and conversation history."""
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    context = _build_judge_chat_context(run_dir)

    # Build the full prompt: system prompt + context + conversation history + latest user message
    history_lines: list[str] = []
    for msg in request.messages[:-1]:
        prefix = "Judge" if msg.role == "user" else "Assistant"
        history_lines.append(f"[{prefix}]: {msg.content}")

    last_user = request.messages[-1].content if request.messages else ""

    prompt = "\n\n".join([
        JUDGE_CHAT_SYSTEM_PROMPT,
        "# RUN CONTEXT",
        context,
        "# CONVERSATION SO FAR",
        "\n".join(history_lines) if history_lines else "(this is the first message)",
        "# LATEST MESSAGE FROM JUDGE",
        last_user,
        "# YOUR RESPONSE (as Judge AI assistant)",
    ])

    cli_args, cli_label = _resolve_judge_chat_cli()

    # Pass prompt via stdin (not as a CLI argument) to avoid Windows command-line length limits.
    result = await asyncio.to_thread(
        subprocess.run,
        cli_args,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"{cli_label} CLI error: {result.stderr[:300]}")

    reply = result.stdout.strip()
    if not reply:
        stderr_hint = result.stderr.strip()[:200] if result.stderr else "no stderr"
        raise HTTPException(
            status_code=500,
            detail=f"{cli_label} CLI returned empty response (stderr: {stderr_hint})",
        )

    return JudgeChatResponse(reply=reply)


# ---------------------------------------------------------------------------
# Conversation stream (SSE) — watches build*.md / review*.md for changes
# ---------------------------------------------------------------------------

def _extract_conversation_summary(path: Path, role: str) -> str:
    """Extract a concise summary from a build or review artifact."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

    lines = text.splitlines()

    # Try to find meaningful sections by heading
    section_keywords = {
        "Builder": [
            "## summary", "## what was built", "## build summary", "## decision", "## changes", "## implementation",
            "## 概要", "## 実装内容", "## 変更内容", "## 判断", "## ビルド概要", "## 実施内容", "## 成果物",
        ],
        "Critic": [
            "## overall", "## assessment", "## summary", "## verdict", "## judgment", "## findings",
            "## 総評", "## 評価", "## 概要", "## 判定", "## 所見", "## レビュー結果", "## 結論",
        ],
    }
    target_keys = section_keywords.get(role, [])

    in_section = False
    collected: list[str] = []
    for line in lines:
        ll = line.strip().lower()
        if any(ll.startswith(k) for k in target_keys):
            in_section = True
            collected = []
            continue
        if in_section:
            if line.startswith("## "):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                collected.append(stripped)
            if len(collected) >= 8:
                break

    if collected:
        summary = " ".join(collected)
        return summary[:400] + ("…" if len(summary) > 400 else "")

    # Fallback: first meaningful paragraph after front matter
    body_lines: list[str] = []
    skip_header = True
    for line in lines:
        stripped = line.strip()
        if skip_header and (stripped.startswith("#") or stripped.startswith("<!--") or not stripped):
            continue
        skip_header = False
        if stripped:
            body_lines.append(stripped)
        if len(body_lines) >= 5:
            break

    fallback = " ".join(body_lines)
    return fallback[:300] + ("…" if len(fallback) > 300 else "")


def _get_conversation_events(run_dir: Path) -> list[dict]:
    """Return all conversation events (build + review artifacts) sorted by mtime."""
    events: list[dict] = []

    build_patterns = ["build.md", "build_rerun_*.md"]
    review_patterns = ["review.md", "review_rerun_*.md"]

    skip_names = {"build_review.md", "review_review.md"}

    for pattern, role in [(p, "Builder") for p in build_patterns] + [(p, "Critic") for p in review_patterns]:
        for f in sorted(run_dir.glob(pattern), key=lambda p: p.stat().st_mtime):
            if f.name in skip_names:
                continue
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            summary = _extract_conversation_summary(f, role)
            if summary:
                events.append({
                    "role": role,
                    "file": f.name,
                    "summary": summary,
                    "mtime": mtime,
                })

    events.sort(key=lambda e: e["mtime"])
    return events


@app.get("/api/runs/{taxonomy}/{run_name:path}/conversation-stream")
async def conversation_stream(taxonomy: str, run_name: str):
    """SSE endpoint: streams conversation events from build/review artifact changes."""
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    async def generate():
        sent_keys: set[str] = set()  # "filename:mtime"
        last_phase = ""
        last_stop_pending = False

        while True:
            # Phase change event
            try:
                from apsf.core.state.run_state_repository import RunStateRepository
                state = RunStateRepository(run_dir).load()
                phase = state.current_phase if state else ""
            except Exception:
                phase = ""

            if phase != last_phase:
                last_phase = phase
                payload = json.dumps({"type": "phase", "phase": phase})
                yield f"data: {payload}\n\n"

            # Stop signal change event
            stop_pending = (run_dir / _STOP_SIGNAL_FILE).exists()
            if stop_pending != last_stop_pending:
                last_stop_pending = stop_pending
                payload = json.dumps({"type": "stop_signal", "pending": stop_pending})
                yield f"data: {payload}\n\n"

            # File change events
            try:
                events = _get_conversation_events(run_dir)
            except Exception:
                events = []

            for ev in events:
                key = f"{ev['file']}:{ev['mtime']}"
                if key not in sent_keys:
                    sent_keys.add(key)
                    payload = json.dumps({
                        "type": "message",
                        "role": ev["role"],
                        "file": ev["file"],
                        "summary": ev["summary"],
                        "mtime": ev["mtime"],
                    })
                    yield f"data: {payload}\n\n"

            await asyncio.sleep(3)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Auto-loop management
# ---------------------------------------------------------------------------

_STOP_SIGNAL_FILE = ".apsf_stop_requested"
_LOOP_PID_FILE = ".apsf_loop_pid"
_JUDGE_ADVISORY_FILE = "judge_advisory.json"
_AUTO_LOOP_LOG_FILE = "auto_loop.log"
_auto_loop_procs: dict[str, subprocess.Popen[str]] = {}  # key: "taxonomy/run_name"
_auto_loop_logs: dict[str, object] = {}
_CANONICAL_JUDGE_ADVISORY_SOURCE = CANONICAL_JUDGE_ADVISORY_SOURCE
_AUTO_LOOP_RECOMMENDATION_ALLOWLIST = JUDGE_ADVISORY_RECOMMENDATIONS
_AUTO_LOOP_EXPECTED_PROCESS_NAMES = frozenset({"powershell.exe", "pwsh.exe"})


def _auto_loop_key(taxonomy: str, run_name: str) -> str:
    return f"{taxonomy}/{run_name}"


def _judge_advisory_path(run_dir: Path) -> Path:
    return run_dir / _JUDGE_ADVISORY_FILE


def _judge_advisory_payload(
    run_dir: Path,
    *,
    recommendation: str | None,
    human_owned_blocker: bool | None,
    advisory_source: str,
    phase: str,
    generated_at: str | None = None,
    source: str | None = None,
    ownership_status: str | None = None,
    ownership_detail: str | None = None,
    run_id: str | None = None,
    freshness_token: str | None = None,
    human_owned_blocker_state: str | None = None,
) -> dict[str, Any]:
    return canonical_judge_advisory_payload(
        run_dir,
        recommendation=recommendation,
        human_owned_blocker=human_owned_blocker,
        human_owned_blocker_state=human_owned_blocker_state,
        advisory_source=advisory_source,
        phase=phase,
        generated_at=generated_at,
        source=source,
        ownership_status=ownership_status,
        ownership_detail=ownership_detail,
        run_id=run_id,
        freshness_token=freshness_token,
    )


def _get_phase_entered_at(run_dir: Path) -> str:
    """Read phase_entered_at from run_state.json. Returns "" if unavailable."""
    try:
        from apsf.core.state.run_state_repository import RunStateRepository
        state = RunStateRepository(run_dir).load()
        if state is not None:
            return str(getattr(state, "phase_entered_at", "") or "").strip()
    except Exception:
        pass
    return ""


def _write_judge_advisory_record(
    run_dir: Path,
    *,
    recommendation: str | None,
    human_owned_blocker: bool | None,
    phase: str,
    source: str,
    advisory_source: str = _CANONICAL_JUDGE_ADVISORY_SOURCE,
    ownership_status: str | None = None,
    ownership_detail: str | None = None,
    freshness_token: str | None = None,
) -> dict[str, Any]:
    token = freshness_token or _get_phase_entered_at(run_dir) or None
    return write_canonical_judge_advisory(
        run_dir,
        recommendation=recommendation,
        human_owned_blocker=human_owned_blocker,
        phase=phase,
        source=source,
        advisory_source=advisory_source,
        ownership_status=ownership_status,
        ownership_detail=ownership_detail,
        freshness_token=token,
    )


def _refresh_judge_advisory_record(run_dir: Path) -> dict[str, Any]:
    canonical_phase = _resolve_agent_os_phase(run_dir)
    blocker_decision = get_build_gate_decision(run_dir)
    ownership_status = str(blocker_decision.get("status") or "").strip() or None
    ownership_detail = str(blocker_decision.get("detail") or "").strip() or None
    path = _judge_advisory_path(run_dir)

    if not path.exists():
        return _judge_advisory_payload(
            run_dir,
            recommendation=None,
            human_owned_blocker=None,
            human_owned_blocker_state=None,
            advisory_source="judge_advisory_missing",
            phase=canonical_phase,
            source=f"{_JUDGE_ADVISORY_FILE}:missing",
            ownership_status=ownership_status,
            ownership_detail=ownership_detail,
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _judge_advisory_payload(
            run_dir,
            recommendation=None,
            human_owned_blocker=None,
            human_owned_blocker_state=None,
            advisory_source="judge_advisory_invalid",
            phase=canonical_phase,
            source=f"{_JUDGE_ADVISORY_FILE}:invalid-json",
            ownership_status=ownership_status,
            ownership_detail=ownership_detail,
        )

    recommendation = payload.get("recommendation")
    if recommendation is not None:
        recommendation = str(recommendation).strip() or None
    if recommendation is not None and recommendation not in _AUTO_LOOP_RECOMMENDATION_ALLOWLIST:
        raw_human_owned_blocker = payload.get("human_owned_blocker")
        human_owned_blocker_state = "valid" if isinstance(raw_human_owned_blocker, bool) else "invalid"
        return _judge_advisory_payload(
            run_dir,
            recommendation=recommendation,
            human_owned_blocker=raw_human_owned_blocker if isinstance(raw_human_owned_blocker, bool) else None,
            human_owned_blocker_state=human_owned_blocker_state,
            advisory_source=str(payload.get("advisory_source") or "judge_advisory_invalid"),
            phase=str(payload.get("phase") or canonical_phase),
            generated_at=str(payload.get("generated_at") or datetime.now(timezone.utc).isoformat()),
            source=f"{_JUDGE_ADVISORY_FILE}:unrecognized-recommendation",
            ownership_status=ownership_status,
            ownership_detail=ownership_detail,
            run_id=str(payload.get("run_id") or run_dir.name),
            freshness_token=str(payload.get("freshness_token") or "").strip() or None,
        )

    human_owned_blocker_state = "valid"
    if "human_owned_blocker" not in payload:
        human_owned_blocker = None
        human_owned_blocker_state = "invalid"
    else:
        human_owned_blocker = payload.get("human_owned_blocker")
        if not isinstance(human_owned_blocker, bool):
            human_owned_blocker = None
            human_owned_blocker_state = "invalid"

    freshness_token = str(payload.get("freshness_token") or "").strip() or None

    return _judge_advisory_payload(
        run_dir,
        recommendation=recommendation,
        human_owned_blocker=human_owned_blocker,
        human_owned_blocker_state=human_owned_blocker_state,
        advisory_source=str(payload.get("advisory_source") or "judge_advisory_invalid"),
        phase=str(payload.get("phase") or canonical_phase),
        generated_at=str(payload.get("generated_at") or datetime.now(timezone.utc).isoformat()),
        source=str(payload.get("source") or path.name),
        ownership_status=ownership_status,
        ownership_detail=ownership_detail,
        run_id=str(payload.get("run_id") or run_dir.name),
        freshness_token=freshness_token,
    )


def _evaluate_improve_auto_loop_decision(run_dir: Path) -> dict[str, Any]:
    advisory = _refresh_judge_advisory_record(run_dir)
    recommendation = advisory.get("recommendation")
    if recommendation is not None:
        recommendation = str(recommendation).strip() or None
    advisory_source = str(advisory.get("advisory_source") or "").strip()
    advisory_run_id = str(advisory.get("run_id") or "").strip()
    ownership_status = str(advisory.get("ownership_status") or "").strip() or None
    human_owned_blocker = advisory.get("human_owned_blocker")
    human_owned_blocker_state = str(advisory.get("human_owned_blocker_state") or "").strip() or None

    # Freshness check: advisory must belong to the current IMPROVE_NEEDED cycle.
    # Fail-closed policy: BOTH tokens must be present and match.
    # If either token is absent (legacy run / legacy advisory) or they mismatch,
    # the advisory is treated as stale and auto-reroute is blocked.
    # Legacy runs without phase_entered_at must re-enter IMPROVE_NEEDED via a new
    # REVIEW cycle to establish a freshness anchor before auto-loop will reroute.
    advisory_freshness_token = str(advisory.get("freshness_token") or "").strip() or None
    current_phase_entered_at = _get_phase_entered_at(run_dir)
    advisory_is_stale = not (
        advisory_freshness_token is not None
        and current_phase_entered_at != ""
        and advisory_freshness_token == current_phase_entered_at
    )

    action = "STOP"
    reason = "advisory_missing"

    if recommendation is None and advisory_source == "judge_advisory_missing":
        reason = "advisory_missing"
    elif recommendation is None and advisory_source == "judge_advisory_invalid":
        reason = "advisory_source_invalid"
    elif advisory_source != _CANONICAL_JUDGE_ADVISORY_SOURCE or advisory_run_id != run_dir.name:
        reason = "advisory_source_invalid"
    elif advisory_is_stale:
        reason = "advisory_stale"
    elif ownership_status == "UNRECORDED":
        reason = "ownership_unrecorded"
    elif ownership_status == "CORRUPT":
        reason = "ownership_corrupt"
    elif human_owned_blocker_state != "valid":
        reason = "human_owned_blocker_invalid"
    elif human_owned_blocker is True:
        reason = "human_owned_blocker"
    elif recommendation == "Return to Build":
        action = "BUILD_NEEDED"
        reason = "auto_reroute_build"
    elif recommendation == "Return to Plan":
        action = "PLAN_NEEDED"
        reason = "auto_reroute_plan"
    elif recommendation == "Accept":
        reason = "accept_is_human_owned"
    elif recommendation is None:
        reason = "advisory_missing"
    else:
        reason = "advisory_unrecognized"

    return {
        **advisory,
        "action": action,
        "reason": reason,
        "stop_reason": _improve_auto_loop_stop_reason(reason),
        "log_line": _format_improve_auto_loop_log_line(
            {
                **advisory,
                "action": action,
                "reason": reason,
            }
        ),
    }


def _improve_auto_loop_stop_reason(reason: str) -> str | None:
    if reason in {
        "advisory_missing",
        "advisory_source_invalid",
        "advisory_stale",
        "ownership_unrecorded",
        "ownership_corrupt",
        "human_owned_blocker_invalid",
    }:
        return reason
    if reason:
        return "human_phase"
    return None


def _format_improve_auto_loop_log_line(decision: dict[str, Any]) -> str:
    advisory_source = str(decision.get("advisory_source") or "").strip()
    recommendation = str(decision.get("recommendation") or "").strip()
    human_owned_blocker = decision.get("human_owned_blocker")
    action = str(decision.get("action") or "STOP").strip() or "STOP"
    reason = str(decision.get("reason") or "advisory_missing").strip() or "advisory_missing"
    return (
        f"[IMPROVE_NEEDED] advisory_source={advisory_source} "
        f"recommendation={recommendation} "
        f"human_owned_blocker={human_owned_blocker} "
        f"action={action} reason={reason}"
    )


def _read_auto_loop_marker(run_dir: Path) -> dict[str, Any] | None:
    pid_file = run_dir / _LOOP_PID_FILE
    try:
        raw = pid_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not raw:
        return None

    with contextlib.suppress(json.JSONDecodeError):
        payload = json.loads(raw)
        if isinstance(payload, dict):
            pid = payload.get("pid")
            try:
                pid = int(pid)
            except (TypeError, ValueError):
                return None
            if pid <= 0:
                return None
            command_line = payload.get("command_line")
            if isinstance(command_line, list):
                command_line = [str(part) for part in command_line]
            elif command_line is not None:
                command_line = str(command_line).strip() or None
            else:
                command_line = None
            process_name = str(payload.get("process_name") or "").strip() or None
            started_at = str(payload.get("started_at") or "").strip() or None
            return {
                "pid": pid,
                "process_name": process_name,
                "started_at": started_at,
                "command_line": command_line,
            }

    try:
        pid = int(raw)
    except ValueError:
        return None
    if pid <= 0:
        return None
    return {"pid": pid, "process_name": None, "started_at": None, "command_line": None}


def _tasklist_row_for_pid(pid: int) -> list[str] | None:
    try:
        completed = subprocess.run(
            [
                "tasklist",
                "/FI",
                f"PID eq {pid}",
                "/FO",
                "CSV",
                "/NH",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None

    if completed.returncode != 0:
        return None

    stdout = completed.stdout.strip()
    if not stdout or "No tasks are running" in stdout:
        return None

    with contextlib.suppress(Exception):
        import csv

        row = next(csv.reader([stdout]))
        if row:
            return row
    return None


def _pid_exists(pid: int) -> bool:
    if psutil is not None:
        with contextlib.suppress(Exception):
            return bool(psutil.pid_exists(pid))
    return _tasklist_row_for_pid(pid) is not None


def _powershell_process_identity_for_pid(pid: int) -> dict[str, Any] | None:
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "$p = Get-CimInstance Win32_Process -Filter \"ProcessId = "
                    f"{pid}\"; "
                    "if ($null -eq $p) { exit 1 }; "
                    "[pscustomobject]@{"
                    "name=$p.Name;"
                    "command_line=$p.CommandLine;"
                    "started_at=$p.CreationDate"
                    "} | ConvertTo-Json -Compress"
                ),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None

    if completed.returncode != 0:
        return None

    with contextlib.suppress(json.JSONDecodeError):
        payload = json.loads(completed.stdout)
        if isinstance(payload, dict):
            return {
                "name": str(payload.get("name") or "").strip() or None,
                "command_line": str(payload.get("command_line") or "").strip() or None,
                "started_at": str(payload.get("started_at") or "").strip() or None,
            }
    return None


def _process_name_for_pid(pid: int) -> str | None:
    if psutil is not None:
        with contextlib.suppress(Exception):
            process = psutil.Process(pid)
            return str(process.name()).strip() or None

    row = _tasklist_row_for_pid(pid)
    if not row:
        return None
    name = str(row[0]).strip()
    return name or None


def _is_expected_auto_loop_process_name(process_name: str | None) -> bool:
    if process_name is None:
        return False
    return process_name.lower() in _AUTO_LOOP_EXPECTED_PROCESS_NAMES


def _process_identity_for_pid(pid: int) -> dict[str, Any] | None:
    if psutil is not None:
        with contextlib.suppress(Exception):
            process = psutil.Process(pid)
            return {
                "pid": pid,
                "name": str(process.name()).strip() or None,
                "command_line": [str(part) for part in process.cmdline()],
                "started_at": datetime.fromtimestamp(process.create_time(), tz=timezone.utc).isoformat(),
            }

    fallback = _powershell_process_identity_for_pid(pid)
    if fallback is None:
        return None
    return {
        "pid": pid,
        "name": fallback.get("name"),
        "command_line": fallback.get("command_line"),
        "started_at": fallback.get("started_at"),
    }


def _normalize_command_line(value: Any) -> str | None:
    if isinstance(value, list):
        parts = [str(part).strip() for part in value if str(part).strip()]
        return " ".join(parts) if parts else None
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _matches_auto_loop_marker(marker: dict[str, Any], identity: dict[str, Any] | None) -> bool:
    if identity is None:
        return False

    process_name = str(identity.get("name") or identity.get("process_name") or "").strip() or None
    if not _is_expected_auto_loop_process_name(process_name):
        return False

    marker_name = str(marker.get("process_name") or "").strip() or None
    if marker_name is not None and process_name is not None and marker_name.lower() != process_name.lower():
        return False

    marker_started_at = str(marker.get("started_at") or "").strip() or None
    identity_started_at = str(identity.get("started_at") or "").strip() or None
    if marker_started_at is not None and identity_started_at != marker_started_at:
        return False

    marker_command_line = _normalize_command_line(marker.get("command_line"))
    identity_command_line = _normalize_command_line(identity.get("command_line"))
    if marker_command_line is not None and identity_command_line != marker_command_line:
        return False

    return True


def _close_auto_loop_log(key: str) -> None:
    handle = _auto_loop_logs.pop(key, None)
    if handle is None:
        return
    try:
        handle.close()
    except Exception:
        pass


def _is_auto_loop_running(taxonomy: str, run_name: str) -> bool:
    key = _auto_loop_key(taxonomy, run_name)
    proc = _auto_loop_procs.get(key)
    if proc is not None:
        if proc.poll() is None:
            return True
        del _auto_loop_procs[key]
        _close_auto_loop_log(key)

    # Fallback: validate PID marker against an actual PowerShell process.
    try:
        run_dir = _resolve_run_dir(taxonomy, run_name)
        marker = _read_auto_loop_marker(run_dir)
        if marker is None:
            return False
        pid = int(marker["pid"])
        if not _pid_exists(pid):
            return False
        return _matches_auto_loop_marker(marker, _process_identity_for_pid(pid))
    except Exception:
        pass

    return False


def _clear_auto_loop_markers(run_dir: Path) -> None:
    """Remove stale auto-loop marker files after the loop is confirmed stopped."""
    try:
        (run_dir / _LOOP_PID_FILE).unlink(missing_ok=True)
    except Exception:
        pass
    try:
        (run_dir / _STOP_SIGNAL_FILE).unlink(missing_ok=True)
    except Exception:
        pass


class AutoLoopOptions(BaseModel):
    plan_script: str = "apsf-codex-plan.ps1"
    build_script: str = "apsf-codex-build.ps1"
    review_script: str = "apsf-claude-act.ps1"
    max_cycles: int = 10


class JudgeAdvisoryResponse(BaseModel):
    recommendation: str | None = None
    human_owned_blocker: bool | None = None
    advisory_source: str
    run_id: str
    generated_at: str
    phase: str
    ownership_status: str | None = None
    ownership_detail: str | None = None
    source: str | None = None
    freshness_token: str | None = None


@app.post("/api/runs/{taxonomy}/{run_name:path}/start-auto-loop")
async def start_auto_loop(taxonomy: str, run_name: str, options: AutoLoopOptions = AutoLoopOptions()):
    """Spawn apsf-auto-loop.ps1 as a background process."""
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    if _is_auto_loop_running(taxonomy, run_name):
        return {"status": "already_running"}

    # Remove stale stop signal if present
    stop_file = run_dir / _STOP_SIGNAL_FILE
    if stop_file.exists():
        stop_file.unlink()

    script = PROJECT_ROOT / "scripts" / "apsf-auto-loop.ps1"
    powershell = os.path.join(
        os.environ.get("WINDIR", r"C:\Windows"),
        "System32", "WindowsPowerShell", "v1.0", "powershell.exe",
    )

    # Build the run name argument (taxonomy/run_name style)
    run_arg = f"{taxonomy}/{run_name}"
    log_path = run_dir / _AUTO_LOOP_LOG_FILE
    log_handle = None
    try:
        normalize_text_artifact_to_utf8(log_path)
        log_handle = log_path.open("a", encoding="utf-8", errors="replace")
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        log_handle.write(
            f"\n=== auto-loop start {timestamp} ===\n"
            f"run={run_arg}\n"
            f"plan_script={options.plan_script}\n"
            f"build_script={options.build_script}\n"
            f"review_script={options.review_script}\n"
            f"max_cycles={options.max_cycles}\n\n"
        )
        log_handle.flush()
    except Exception:
        log_handle = None

    proc = subprocess.Popen(
        [
            powershell, "-NoProfile", "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-File", str(script),
            run_arg,
            "-PlanScript", options.plan_script,
            "-BuildScript", options.build_script,
            "-ReviewScript", options.review_script,
            "-MaxCycles", str(options.max_cycles),
        ],
        cwd=str(PROJECT_ROOT),
        stdout=log_handle if log_handle is not None else subprocess.DEVNULL,
        stderr=subprocess.STDOUT if log_handle is not None else subprocess.DEVNULL,
    )
    key = _auto_loop_key(taxonomy, run_name)
    _auto_loop_procs[key] = proc
    if log_handle is not None:
        _auto_loop_logs[key] = log_handle
    return {"status": "started", "pid": proc.pid, "log_path": str(log_path)}


@app.get("/api/runs/{taxonomy}/{run_name:path}/judge-advisory", response_model=JudgeAdvisoryResponse)
async def get_judge_advisory(taxonomy: str, run_name: str):
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    return JudgeAdvisoryResponse(**_refresh_judge_advisory_record(run_dir))


class WriteJudgeAdvisoryRequest(BaseModel):
    recommendation: str  # "Return to Build" | "Return to Plan" | "Accept"
    human_owned_blocker: bool = False
    source: str = "judge_decision"


@app.post("/api/runs/{taxonomy}/{run_name:path}/judge-advisory", response_model=JudgeAdvisoryResponse)
async def write_judge_advisory(taxonomy: str, run_name: str, request: WriteJudgeAdvisoryRequest):
    """Write a canonical judge advisory for the current IMPROVE_NEEDED cycle.

    The advisory source is always judge_structured. freshness_token is derived
    from the current run_state.phase_entered_at so it is valid for this cycle only.
    """
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    blocker_decision = get_build_gate_decision(run_dir)
    ownership_status = str(blocker_decision.get("status") or "").strip() or None
    ownership_detail = str(blocker_decision.get("detail") or "").strip() or None

    try:
        payload = _write_judge_advisory_record(
            run_dir,
            recommendation=request.recommendation,
            human_owned_blocker=request.human_owned_blocker,
            phase=_resolve_agent_os_phase(run_dir),
            source=request.source,
            ownership_status=ownership_status,
            ownership_detail=ownership_detail,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return JudgeAdvisoryResponse(**payload)


def _read_auto_loop_stop_info(run_dir: Path) -> dict:
    """Read last stop_reason and exit code from auto_loop.log tail."""
    log_path = run_dir / _AUTO_LOOP_LOG_FILE
    if not log_path.exists():
        return {}
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = lines[-30:]
        stop_reason: str | None = None
        last_exit: int | None = None
        for line in reversed(tail):
            if stop_reason is None:
                m = re.search(r"stop_reason=(\S+)", line)
                if m:
                    stop_reason = m.group(1)
            if last_exit is None:
                m = re.search(r"\bexit=(-?\d+)", line)
                if m:
                    last_exit = int(m.group(1))
            if stop_reason is not None and last_exit is not None:
                break
        return {k: v for k, v in {"stop_reason": stop_reason, "last_exit": last_exit}.items() if v is not None}
    except Exception:
        return {}


@app.get("/api/runs/{taxonomy}/{run_name:path}/auto-loop-status")
async def auto_loop_status(taxonomy: str, run_name: str):
    """Check whether auto-loop is running for this run."""
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    running = _is_auto_loop_running(taxonomy, run_name)
    stop_pending = False
    if running:
        try:
            stop_pending = (run_dir / _STOP_SIGNAL_FILE).exists()
        except Exception:
            pass
    else:
        _clear_auto_loop_markers(run_dir)
        stop_pending = False

    result: dict = {"running": running, "stop_pending": stop_pending}
    if not running:
        result.update(_read_auto_loop_stop_info(run_dir))
    return result


@app.post("/api/runs/{taxonomy}/{run_name:path}/request-stop")
async def request_stop(taxonomy: str, run_name: str):
    """Write stop-signal file so apsf-auto-loop.ps1 halts after the current phase."""
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    (run_dir / _STOP_SIGNAL_FILE).write_text("stop requested\n", encoding="utf-8")
    return {"status": "stop_requested"}


@app.delete("/api/runs/{taxonomy}/{run_name:path}/request-stop")
async def cancel_stop(taxonomy: str, run_name: str):
    """Remove stop-signal file (cancel a pending stop request)."""
    run_dir = _resolve_run_dir(taxonomy, run_name)
    sig = run_dir / _STOP_SIGNAL_FILE
    if sig.exists():
        sig.unlink()
    return {"status": "cancelled"}


class AcceptImproveRequest(BaseModel):
    comment: str = ""  # Judge's acceptance note (optional)


@app.post("/api/runs/{taxonomy}/{run_name:path}/accept")
async def accept_improve(taxonomy: str, run_name: str, request: AcceptImproveRequest):
    """Write improve.md with Judge acceptance note and advance to RESULT_NEEDED.

    Also writes judge_advisory.json with recommendation=Accept so the advisory
    record reflects the Judge's decision at completion time.
    """
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    note = request.comment.strip() or "採用。RESULT_NEEDED に進む。"
    improve_content = f"# Improve\n\n## Judge Decision\n\n採用 — RESULT_NEEDED に進む。\n\n## Comment\n\n{note}\n"
    (run_dir / "improve.md").write_text(improve_content, encoding="utf-8")

    # Record canonical advisory before transitioning so the advisory reflects
    # the Judge's Accept decision for this IMPROVE_NEEDED cycle.
    blocker_decision = get_build_gate_decision(run_dir)
    with contextlib.suppress(Exception):
        _write_judge_advisory_record(
            run_dir,
            recommendation="Accept",
            human_owned_blocker=False,
            phase="IMPROVE_NEEDED",
            source="accept_improve",
            ownership_status=str(blocker_decision.get("status") or "").strip() or None,
            ownership_detail=str(blocker_decision.get("detail") or "").strip() or None,
        )

    from apsf.core.state.transition_service import TransitionService, TransitionError
    try:
        result = TransitionService().transition(
            run_dir,
            to_phase="RESULT_NEEDED",
            actor="Judge",
            reason=f"Accepted via GUI: {note[:80]}",
        )
    except TransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not result.success:
        raise HTTPException(status_code=409, detail=result.error or "Transition failed")

    return {"status": "ok", "phase": "RESULT_NEEDED"}


class GenerateResultRequest(BaseModel):
    comment: str  # Goal-owner's OK comment / summary to include in result.md


class GenerateResultResponse(BaseModel):
    result_path: str
    content: str


_GENERATE_RESULT_PROMPT_TEMPLATE = """You are writing result.md for an APSF (AI Problem Solving Framework) run.

APSF workflow: Goal → Plan → Build → Review → Result

The Goal-owner has approved this run. Your job is to write a concise, factual result.md that records:
1. What was built / decided
2. Whether all Success Criteria were met
3. Key findings or decisions the Goal-owner wants to remember
4. Lessons learned or patterns to reuse

## RUN ARTIFACTS

{context}

## GOAL-OWNER'S OK COMMENT

{comment}

## INSTRUCTIONS

Write result.md now. Use this structure:

# Result

## 総合判定

[Pass / Conditional Pass / Partial — one line]

## 成果物

[Bullet list of what was built / produced]

## Success Criteria

| Criterion | Status | Notes |
|---|---|---|
[fill in from goal.md]

## Goal-owner コメント

{comment}

## Lessons Learned

[2-4 bullet points: what worked, what to reuse, what to watch for next time]

Write only the result.md content. No preamble, no explanation outside the document.
"""


@app.post(
    "/api/runs/{taxonomy}/{run_name:path}/generate-result",
    response_model=GenerateResultResponse,
)
async def generate_result(taxonomy: str, run_name: str, request: GenerateResultRequest):
    """Generate result.md from run artifacts + goal-owner comment, then close the run."""
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    context = _build_judge_chat_context(run_dir)

    # Also include improve.md if present
    improve_path = run_dir / "improve.md"
    if improve_path.exists():
        text = improve_path.read_text(encoding="utf-8").strip()
        if text:
            context += f"\n\n---\n\n## IMPROVE\n\n{text}"

    prompt = _GENERATE_RESULT_PROMPT_TEMPLATE.format(
        context=context,
        comment=request.comment.strip(),
    )

    cli_args, cli_label = _resolve_judge_chat_cli()

    result = await asyncio.to_thread(
        subprocess.run,
        cli_args,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"{cli_label} CLI error: {result.stderr[:300]}")

    content = result.stdout.strip()
    if not content:
        stderr_hint = result.stderr.strip()[:200] if result.stderr else "no stderr"
        raise HTTPException(
            status_code=500,
            detail=f"{cli_label} CLI returned empty response (stderr: {stderr_hint})",
        )

    # Save result.md
    result_path = run_dir / "result.md"
    result_path.write_text(content, encoding="utf-8")

    # Advance phase to COMPLETE
    from apsf.core.state.transition_service import TransitionService, TransitionError
    try:
        tr = TransitionService().transition(
            run_dir,
            to_phase="COMPLETE",
            actor="Judge",
            reason=f"Result approved via GUI: {request.comment[:80]}",
        )
        if not tr.success:
            raise HTTPException(status_code=409, detail=tr.error or "Phase transition to COMPLETE failed")
    except TransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return GenerateResultResponse(result_path=str(result_path), content=content)


@app.post(
    "/api/runs/{taxonomy}/{parent_run_id}/child-runs",
    response_model=CreateChildRunResponse,
)
async def create_child_run(taxonomy: str, parent_run_id: str, request: CreateChildRunRequest):
    if request.taxonomy != taxonomy:
        raise HTTPException(status_code=400, detail="taxonomy mismatch")

    parent_dir = repo.get_run_dir(parent_run_id, taxonomy=taxonomy)
    if not parent_dir.exists():
        raise HTTPException(status_code=404, detail="Parent run not found")

    try:
        child_dir = initialize_child_run(
            repo=repo,
            parent_run=parent_run_id,
            child_run=request.run_id,
            taxonomy=taxonomy,
            title=request.title,
            goal_text=request.goal,
            force=False,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CreateChildRunResponse(
        run_id=request.run_id,
        path=str(child_dir),
        status="created",
    )


@app.get("/api/runs/{taxonomy}/{run_name:path}", response_model=RunDetail)
async def get_run_detail(taxonomy: str, run_name: str):
    run_dir = _resolve_run_dir(taxonomy, run_name)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    return _collect_run_detail(taxonomy, run_name, run_dir)


frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.responses import FileResponse

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(
            str(frontend_dist / "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
else:

    @app.get("/")
    async def root():
        return {"message": "APSF Viewer API is running. Frontend not built. Run 'npm run build' in src/apsf/viewer/frontend"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
