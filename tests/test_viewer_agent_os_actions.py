from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import pytest

from apsf.core.ownership import (
    BlockerOwnership,
    get_transition_outcome,
    TransitionOutcomeRecord,
    TransitionType,
    write_transition_outcome,
)
from apsf.core.manifest.manifest_repository import ManifestRepository
from apsf.viewer import api


def _write_run_state(
    run_dir: Path,
    *,
    phase: str = "BUILD_NEEDED",
    phase_status: str = "in_progress",
    current_owner: str = "Builder",
    phase_entered_at: str = "",
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "current_phase": phase,
                "phase_status": phase_status,
                "current_owner": current_owner,
                "retry_count": 0,
                "last_error": "",
                "active_handoff_id": "",
                "gate_failures": [],
                "phase_entered_at": phase_entered_at,
            }
        ),
        encoding="utf-8",
    )


def _write_judge_advisory(
    run_dir: Path,
    *,
    recommendation: str | None,
    human_owned_blocker: bool | None,
    advisory_source: str = "judge_structured",
    run_id: str | None = None,
    phase: str = "IMPROVE_NEEDED",
    source: str = "judge_advisory.json",
    freshness_token: str | None = None,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "judge_advisory.json").write_text(
        json.dumps(
            {
                "recommendation": recommendation,
                "human_owned_blocker": human_owned_blocker,
                "advisory_source": advisory_source,
                "run_id": run_id or run_dir.name,
                "generated_at": "2026-04-12T00:00:00+00:00",
                "phase": phase,
                "source": source,
                "freshness_token": freshness_token,
            }
        ),
        encoding="utf-8",
    )


def _write_auto_loop_marker(
    run_dir: Path,
    *,
    pid: int,
    process_name: str | None = "powershell.exe",
    started_at: str | None = "2026-04-12T00:00:00+00:00",
    command_line: str | None = "powershell.exe -File scripts/apsf-auto-loop.ps1 work/run-073",
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / ".apsf_loop_pid").write_text(
        json.dumps(
            {
                "pid": pid,
                "process_name": process_name,
                "started_at": started_at,
                "command_line": command_line,
            }
        ),
        encoding="utf-8",
    )


def test_capture_snapshot_uses_existing_canonical_artifacts_only(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-073"
    _write_run_state(run_dir, phase="REVIEW_NEEDED")
    (run_dir / "goal.md").write_text("goal", encoding="utf-8")
    (run_dir / "plan.md").write_text("plan", encoding="utf-8")
    (run_dir / "notes.md").write_text("ignore", encoding="utf-8")

    response = api._execute_agent_os_action(
        run_dir,
        "fw-improvement/run-073",
        api.ExecuteAgentOSActionRequest(action_id="capture-snapshot"),
    )

    assert response.status == "SUCCESS"
    snapshot_dirs = list((run_dir / "recovery" / "snapshots").iterdir())
    assert len(snapshot_dirs) == 1
    metadata = json.loads((snapshot_dirs[0] / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["source_phase"] == "REVIEW_NEEDED"
    assert metadata["target_paths"] == ["goal.md", "plan.md"]


def test_apply_checkpoint_blocks_when_candidate_not_selected(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-073"
    _write_run_state(run_dir)

    response = api._execute_agent_os_action(
        run_dir,
        "fw-improvement/run-073",
        api.ExecuteAgentOSActionRequest(
            action_id="apply-checkpoint",
            reason="resume builder",
            confirmed=True,
        ),
    )

    assert response.status == "FAILED"
    assert "select a checkpoint candidate first" in response.stderr


def test_start_auto_loop_normalizes_legacy_log_to_utf8(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-encoding"
    _write_run_state(run_dir, phase="BUILD_NEEDED", phase_status="pending", current_owner="Builder")
    log_path = run_dir / "auto_loop.log"
    original = "自動ループ継続\n"
    log_path.write_bytes(original.encode("cp932"))

    class DummyProc:
        def __init__(self) -> None:
            self.pid = 4321

        def poll(self):
            return None

    monkeypatch.setattr(api, "_resolve_run_dir", lambda taxonomy, run_name: run_dir)
    monkeypatch.setattr(api, "_is_auto_loop_running", lambda taxonomy, run_name: False)
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: DummyProc())

    response = asyncio.run(api.start_auto_loop("work", "run-encoding", api.AutoLoopOptions()))

    assert response["status"] == "started"
    assert log_path.read_text(encoding="utf-8").startswith(original)
    api._close_auto_loop_log(api._auto_loop_key("work", "run-encoding"))


def test_is_auto_loop_running_validates_pid_marker_with_live_powershell_process(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-loop-marker"
    _write_auto_loop_marker(run_dir, pid=9999)

    monkeypatch.setattr(api, "_resolve_run_dir", lambda taxonomy, run_name: run_dir)
    monkeypatch.setattr(api, "_pid_exists", lambda pid: pid == 9999)
    monkeypatch.setattr(
        api,
        "_process_identity_for_pid",
        lambda pid: {
            "pid": pid,
            "name": "powershell.exe",
            "started_at": "2026-04-12T00:00:00+00:00",
            "command_line": "powershell.exe -File scripts/apsf-auto-loop.ps1 work/run-073",
        },
    )

    assert api._is_auto_loop_running("work", "run-loop-marker") is True


def test_is_auto_loop_running_returns_false_when_pid_marker_is_stale(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-loop-stale"
    _write_auto_loop_marker(run_dir, pid=9999)

    monkeypatch.setattr(api, "_resolve_run_dir", lambda taxonomy, run_name: run_dir)
    monkeypatch.setattr(api, "_pid_exists", lambda pid: False)

    assert api._is_auto_loop_running("work", "run-loop-stale") is False


def test_is_auto_loop_running_rejects_pid_reuse_for_non_powershell_process(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-loop-pid-reuse"
    _write_auto_loop_marker(run_dir, pid=9999)

    monkeypatch.setattr(api, "_resolve_run_dir", lambda taxonomy, run_name: run_dir)
    monkeypatch.setattr(api, "_pid_exists", lambda pid: True)
    monkeypatch.setattr(
        api,
        "_process_identity_for_pid",
        lambda pid: {
            "pid": pid,
            "name": "notepad.exe",
            "started_at": "2026-04-12T00:00:00+00:00",
            "command_line": "notepad.exe",
        },
    )

    assert api._is_auto_loop_running("work", "run-loop-pid-reuse") is False


def test_is_auto_loop_running_rejects_pid_reuse_for_different_powershell_identity(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-loop-pid-reuse-powershell"
    _write_auto_loop_marker(run_dir, pid=9999)

    monkeypatch.setattr(api, "_resolve_run_dir", lambda taxonomy, run_name: run_dir)
    monkeypatch.setattr(api, "_pid_exists", lambda pid: True)
    monkeypatch.setattr(
        api,
        "_process_identity_for_pid",
        lambda pid: {
            "pid": pid,
            "name": "powershell.exe",
            "started_at": "2026-04-12T01:00:00+00:00",
            "command_line": "powershell.exe -NoProfile",
        },
    )

    assert api._is_auto_loop_running("work", "run-loop-pid-reuse-powershell") is False


def test_refresh_judge_advisory_record_reads_existing_canonical_payload(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-judge-advisory-build"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_judge_advisory(run_dir, recommendation="Return to Build", human_owned_blocker=False)
    monkeypatch.setattr(api, "_resolve_agent_os_phase", lambda _: "IMPROVE_NEEDED")
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )
    monkeypatch.setattr(
        api,
        "_derive_judge_recommendation",
        lambda run_dir, phase: (_ for _ in ()).throw(AssertionError("review-derived advisory must not be consulted")),
    )

    payload = api._refresh_judge_advisory_record(run_dir)

    assert payload["recommendation"] == "Return to Build"
    assert payload["human_owned_blocker"] is False
    assert payload["advisory_source"] == "judge_structured"
    assert payload["run_id"] == run_dir.name
    assert payload["phase"] == "IMPROVE_NEEDED"


def test_refresh_judge_advisory_record_reports_missing_payload_without_derivation(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-judge-advisory-human"
    run_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(api, "_resolve_agent_os_phase", lambda _: "IMPROVE_NEEDED")
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "HUMAN", "detail": "goal-owner sign-off", "source": "transition_outcome.json"},
    )
    monkeypatch.setattr(
        api,
        "_derive_judge_recommendation",
        lambda run_dir, phase: (_ for _ in ()).throw(AssertionError("review-derived advisory must not be consulted")),
    )

    payload = api._refresh_judge_advisory_record(run_dir)

    assert payload["recommendation"] is None
    assert payload["human_owned_blocker"] is None
    assert payload["advisory_source"] == "judge_advisory_missing"
    assert payload["ownership_status"] == "HUMAN"


_CYCLE_TOKEN = "2026-04-12T10:00:00+00:00"  # shared freshness token for decision tests


def test_evaluate_improve_auto_loop_decision_returns_build_reroute_for_canonical_advisory(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-improve-build"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=_CYCLE_TOKEN)
    _write_judge_advisory(run_dir, recommendation="Return to Build", human_owned_blocker=False,
                          freshness_token=_CYCLE_TOKEN)
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "BUILD_NEEDED"
    assert decision["reason"] == "auto_reroute_build"
    assert decision["recommendation"] == "Return to Build"
    assert decision["log_line"].endswith("action=BUILD_NEEDED reason=auto_reroute_build")


def test_evaluate_improve_auto_loop_decision_returns_plan_reroute_for_canonical_advisory(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-improve-plan"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=_CYCLE_TOKEN)
    _write_judge_advisory(run_dir, recommendation="Return to Plan", human_owned_blocker=False,
                          freshness_token=_CYCLE_TOKEN)
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "PLAN_NEEDED"
    assert decision["reason"] == "auto_reroute_plan"
    assert decision["recommendation"] == "Return to Plan"
    assert decision["log_line"].endswith("action=PLAN_NEEDED reason=auto_reroute_plan")


def test_evaluate_improve_auto_loop_decision_stops_on_accept(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-improve-accept"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=_CYCLE_TOKEN)
    _write_judge_advisory(run_dir, recommendation="Accept", human_owned_blocker=False,
                          freshness_token=_CYCLE_TOKEN)
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "accept_is_human_owned"
    assert decision["log_line"].endswith("action=STOP reason=accept_is_human_owned")


def test_evaluate_improve_auto_loop_decision_stops_when_recommendation_is_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-improve-missing"
    run_dir.mkdir(parents=True, exist_ok=True)

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "advisory_missing"
    assert decision["stop_reason"] == "advisory_missing"
    assert decision["log_line"].endswith("action=STOP reason=advisory_missing")


def test_evaluate_improve_auto_loop_decision_stops_when_recommendation_is_unknown(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-improve-unknown"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=_CYCLE_TOKEN)
    _write_judge_advisory(run_dir, recommendation="Ship It", human_owned_blocker=False,
                          freshness_token=_CYCLE_TOKEN)
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "advisory_unrecognized"
    assert decision["log_line"].endswith("action=STOP reason=advisory_unrecognized")


def test_evaluate_improve_auto_loop_decision_stops_when_human_owned_blocker_is_true(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-improve-human"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=_CYCLE_TOKEN)
    _write_judge_advisory(run_dir, recommendation="Return to Build", human_owned_blocker=True,
                          freshness_token=_CYCLE_TOKEN)
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "human_owned_blocker"
    assert decision["log_line"].endswith("action=STOP reason=human_owned_blocker")


def test_evaluate_improve_auto_loop_decision_stops_when_run_id_mismatches(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-improve-stale"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=_CYCLE_TOKEN)
    _write_judge_advisory(run_dir, recommendation="Return to Build", human_owned_blocker=False,
                          run_id="other-run", freshness_token=_CYCLE_TOKEN)
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "advisory_source_invalid"
    assert decision["stop_reason"] == "advisory_source_invalid"
    assert decision["log_line"].endswith("action=STOP reason=advisory_source_invalid")


def test_evaluate_improve_auto_loop_decision_stops_when_ownership_status_is_unrecorded(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-improve-unrecorded"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=_CYCLE_TOKEN)
    _write_judge_advisory(run_dir, recommendation="Return to Build", human_owned_blocker=False,
                          freshness_token=_CYCLE_TOKEN)
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "UNRECORDED", "detail": "missing", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "ownership_unrecorded"
    assert decision["stop_reason"] == "ownership_unrecorded"
    assert decision["log_line"].endswith("action=STOP reason=ownership_unrecorded")


def test_evaluate_improve_auto_loop_decision_stops_when_ownership_status_is_corrupt(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-improve-corrupt"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=_CYCLE_TOKEN)
    _write_judge_advisory(run_dir, recommendation="Return to Plan", human_owned_blocker=False,
                          freshness_token=_CYCLE_TOKEN)
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "CORRUPT", "detail": "bad-json", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "ownership_corrupt"
    assert decision["stop_reason"] == "ownership_corrupt"
    assert decision["log_line"].endswith("action=STOP reason=ownership_corrupt")


def test_apply_snapshot_blocks_without_confirmation(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-073"
    _write_run_state(run_dir)

    response = api._execute_agent_os_action(
        run_dir,
        "fw-improvement/run-073",
        api.ExecuteAgentOSActionRequest(
            action_id="apply-snapshot",
            snapshot_id="snap-001",
            reason="rollback plan",
            confirmed=False,
        ),
    )

    assert response.status == "FAILED"
    assert "explicit confirmation is required" in response.stderr


def test_apply_checkpoint_succeeds_and_updates_run_state(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-073"
    _write_run_state(run_dir, phase="PLAN_NEEDED", phase_status="pending", current_owner="Planner")
    (run_dir / "recovery" / "checkpoints").mkdir(parents=True, exist_ok=True)
    (run_dir / "recovery" / "checkpoints" / "cp-001.json").write_text(
        json.dumps(
            {
                "checkpoint_id": "cp-001",
                "run_id": "run-073",
                "phase": "BUILD_NEEDED",
                "phase_status": "in_progress",
                "current_owner": "Builder",
                "related_event_id": "",
                "created_at": "2026-04-02T00:00:00+00:00",
                "summary": "resume build",
            }
        ),
        encoding="utf-8",
    )

    response = api._execute_agent_os_action(
        run_dir,
        "fw-improvement/run-073",
        api.ExecuteAgentOSActionRequest(
            action_id="apply-checkpoint",
            checkpoint_id="cp-001",
            reason="resume builder",
            confirmed=True,
        ),
    )

    updated_state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    assert response.status == "SUCCESS"
    assert updated_state["current_phase"] == "BUILD_NEEDED"
    assert updated_state["phase_status"] == "in_progress"
    assert updated_state["current_owner"] == "Builder"


def test_build_operator_actions_defaults_act_to_wrapper(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", tmp_path / "viewer.config.json")
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)

    actions = api.build_operator_actions("work/run-073", "PLAN_NEEDED")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == ".\\scripts\\apsf-wrapper-act.ps1 work/run-073 -Backend claude-cli"


def test_build_operator_actions_plan_can_use_codex_wrapper_backend(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"wrapper_backends": {"act": "codex-cli"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)

    actions = api.build_operator_actions("work/run-073", "PLAN_NEEDED")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == ".\\scripts\\apsf-wrapper-act.ps1 work/run-073 -Backend codex-cli"


def test_build_operator_actions_can_use_provider_mode_from_config(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"execution_modes": {"act": "provider"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)

    actions = api.build_operator_actions("work/run-073", "REVIEW_NEEDED")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == "apsf act work/run-073"


def test_build_operator_actions_env_overrides_configured_act_mode(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"execution_modes": {"act": "provider"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.setenv("APSF_VIEWER_ACT_EXECUTION_MODE", "wrapper")
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)

    actions = api.build_operator_actions("work/run-073", "PLAN_NEEDED")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == ".\\scripts\\apsf-wrapper-act.ps1 work/run-073 -Backend claude-cli"


def test_build_operator_actions_build_defaults_to_claude_wrapper_backend(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", tmp_path / "viewer.config.json")
    monkeypatch.delenv("APSF_VIEWER_BUILD_WRAPPER_BACKEND", raising=False)

    actions = api.build_operator_actions("work/run-073", "BUILD_NEEDED")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == ".\\scripts\\apsf-wrapper-build.ps1 work/run-073 -Backend claude-cli"


def test_build_operator_actions_build_can_use_codex_backend_from_config(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"wrapper_backends": {"build": "codex-cli"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.delenv("APSF_VIEWER_BUILD_WRAPPER_BACKEND", raising=False)

    actions = api.build_operator_actions("work/run-073", "BUILD_NEEDED")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == ".\\scripts\\apsf-wrapper-build.ps1 work/run-073 -Backend codex-cli"


def test_build_operator_actions_build_env_overrides_configured_backend(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"wrapper_backends": {"build": "claude-cli"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.setenv("APSF_VIEWER_BUILD_WRAPPER_BACKEND", "codex")

    actions = api.build_operator_actions("work/run-073", "BUILD_NEEDED")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == ".\\scripts\\apsf-wrapper-build.ps1 work/run-073 -Backend codex-cli"


def test_build_operator_actions_review_keeps_codex_wrapper_command(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"wrapper_backends": {"act": "codex-cli"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)

    actions = api.build_operator_actions("work/run-073", "REVIEW_NEEDED")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == ".\\scripts\\apsf-wrapper-act.ps1 work/run-073 -Backend codex-cli"


def test_build_operator_actions_plan_prefers_config_backend_over_stale_local_assignment(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"wrapper_backends": {"act": "codex-cli"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)
    monkeypatch.setattr(
        api,
        "_resolve_execution_visibility",
        lambda run_dir, phase: api.ExecutionVisibility(
            role="Planner",
            execution_type="cli",
            target="claude",
            workspace="workspaces/planner/",
            mode="explicit",
            reason="execution-assignment.md specifies stale claude target",
        ),
    )

    actions = api.build_operator_actions("work/run-073", "PLAN_NEEDED", tmp_path / "run-073")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == ".\\scripts\\apsf-wrapper-act.ps1 work/run-073 -Backend codex-cli"


def test_build_operator_actions_build_prefers_env_over_config_and_stale_local_assignment(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"wrapper_backends": {"build": "claude-cli"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.setenv("APSF_VIEWER_BUILD_WRAPPER_BACKEND", "codex")
    monkeypatch.setattr(
        api,
        "_resolve_execution_visibility",
        lambda run_dir, phase: api.ExecutionVisibility(
            role="Builder",
            execution_type="cli",
            target="claude",
            workspace="workspaces/builder/",
            mode="explicit",
            reason="execution-assignment.md specifies stale claude target",
        ),
    )

    actions = api.build_operator_actions("work/run-073", "BUILD_NEEDED", tmp_path / "run-073")

    primary = next(action for action in actions if action.id == "phase-primary")
    assert primary.command == ".\\scripts\\apsf-wrapper-build.ps1 work/run-073 -Backend codex-cli"


def test_build_operator_actions_improve_uses_judge_decision_labels() -> None:
    actions = api.build_operator_actions("work/run-073", "IMPROVE_NEEDED")

    action_map = {action.id: action for action in actions}

    assert action_map["phase-primary"].label == "Judge Decision"
    assert action_map["rerun-plan"].label == "Judge and Return to Plan"
    assert action_map["rerun-build"].label == "Judge and Return to Build"
    assert action_map["rerun-review"].label == "Judge and Return to Review"
    assert action_map["rerun-improve"].label == "Reopen Judge Decision"


def test_derive_judge_recommendation_prefers_plan_when_critical_review_hits_plan_boundary(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-073"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Overall Verdict",
                "**Conditional Pass**",
                "",
                "### Critical",
                "",
                "**C-1: plan.md leaves scope unresolved**",
                "",
                "Planner cannot safely continue until goal.md and scope are corrected.",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Revise"
    assert recommendation.suggested_action_id == "rerun-plan"
    assert recommendation.suggested_action_label == "Judge and Return to Plan"
    assert recommendation.suggested_return_phase == "PLAN_NEEDED"
    assert recommendation.critical_count == 1


def test_derive_judge_recommendation_parses_markdown_issue_headings_and_not_accepted_verdict(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-judge-markdown"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "## Review",
                "",
                "### Issues",
                "",
                "#### CRITICAL-1 — acceptance gate not satisfied",
                "",
                "problem text",
                "",
                "#### MAJOR-1 — fallback path missing",
                "",
                "problem text",
                "",
                "#### MAJOR-2 — field assumption unverified",
                "",
                "problem text",
                "",
                "### Minor Issues",
                "",
                "#### MINOR-1 — return assumption undocumented",
                "",
                "problem text",
                "",
                "#### MINOR-2 — trading calendar dependency missing",
                "",
                "problem text",
                "",
                "### Acceptance Decision",
                "",
                "**Not accepted.** Critical and major issues remain.",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Revise"
    assert recommendation.critical_count == 1
    assert recommendation.major_count == 2
    assert recommendation.minor_count == 2
    assert recommendation.review_verdict is not None
    assert "Not accepted" in recommendation.review_verdict


def test_derive_judge_recommendation_parses_criterion_status_style_review(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-criterion-status"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "## Review: Build Output vs. Goal Success Criteria",
                "",
                "### Criterion 1",
                "",
                "**Status: Major**",
                "",
                "details",
                "",
                "### Criterion 2",
                "",
                "**Status: Minor**",
                "",
                "details",
                "",
                "### Criterion 4",
                "",
                "**Status: Critical**",
                "",
                "details",
                "",
                "### Verdict",
                "",
                "Not accepted.",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Revise"
    assert recommendation.critical_count == 1
    assert recommendation.major_count == 1
    assert recommendation.minor_count == 1


def test_derive_judge_recommendation_parses_decision_accept_and_coded_issue_headings(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-decision-accept"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Decision",
                "",
                "ACCEPT",
                "",
                "## Minor Issues",
                "",
                "### m-01: wording cleanup",
                "",
                "details",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Adopt"
    assert recommendation.minor_count == 1
    assert recommendation.review_verdict == "ACCEPT"


def test_collect_run_detail_includes_judge_recommendation(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run-073"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending", current_owner="Judge")
    (run_dir / "goal.md").write_text("goal", encoding="utf-8")
    (run_dir / "plan.md").write_text("plan", encoding="utf-8")
    (run_dir / "build.md").write_text("build", encoding="utf-8")
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Overall Verdict",
                "**Conditional Pass**",
                "",
                "### Critical",
                "",
                "**C-1: build.md needs revision**",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(api, "load_priority_index", lambda: {})
    monkeypatch.setattr(api.repo, "list_child_runs", lambda parent_name, taxonomy=None: [])

    detail = api._collect_run_detail("work", "work/run-073", run_dir)

    assert detail.review_summary is not None
    assert detail.review_summary.available is True
    assert detail.review_summary.summary_status == "revise"
    assert detail.review_summary.critical_count == 1
    assert detail.review_summary.source_artifact == "review.md"
    assert any("build_review.md" in action for action in detail.review_summary.next_actions)
    assert detail.judge_recommendation is not None
    assert detail.judge_recommendation.decision == "Revise"
    assert detail.judge_recommendation.review_verdict == "**Conditional Pass**"


def test_derive_review_summary_returns_none_without_review_artifact(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-no-review-summary"
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = api._derive_review_summary(run_dir, "IMPROVE_NEEDED")

    assert summary is None


def test_derive_review_summary_marks_human_blocker_as_blocking(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-review-summary-blocking"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", current_owner="Human")
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at="2026-04-13T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase="IMPROVE_NEEDED",
            target_phase="IMPROVE_NEEDED",
        ),
    )
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Overall Verdict",
                "**Conditional Pass**",
                "",
                "### Major",
                "",
                "**M-1: human approval required**",
            ]
        ),
        encoding="utf-8",
    )

    summary = api._derive_review_summary(run_dir, "IMPROVE_NEEDED")

    assert summary is not None
    assert summary.available is True
    assert summary.summary_status == "blocking"
    assert summary.major_count == 1
    assert any("human-owned blocker" in action.lower() for action in summary.next_actions)


def test_derive_review_summary_marks_adopt_for_minor_only_review(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-review-summary-adopt"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Verdict",
                "Accept",
                "",
                "### m-1: clarify note",
            ]
        ),
        encoding="utf-8",
    )

    summary = api._derive_review_summary(run_dir, "IMPROVE_NEEDED")

    assert summary is not None
    assert summary.available is True
    assert summary.summary_status == "adopt"
    assert summary.minor_count == 1
    assert any("close-out" in action.lower() for action in summary.next_actions)


def test_derive_review_summary_uses_fallback_actions_for_review_needed_phase(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-review-summary-review-needed"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Overall Verdict",
                "**Conditional Pass**",
                "",
                "### Major",
                "",
                "**M-1: one issue remains**",
            ]
        ),
        encoding="utf-8",
    )

    summary = api._derive_review_summary(run_dir, "REVIEW_NEEDED")

    assert summary is not None
    assert summary.available is True
    assert summary.summary_status == "revise"
    assert summary.major_count == 1
    assert any("finish the review cycle" in action.lower() for action in summary.next_actions)


def test_derive_review_summary_marks_unknown_for_zero_count_no_adopt_signal(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-review-summary-unknown"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Summary of review",
                "Manual review required.",
                "",
                "## Critical Issues",
                "- none",
                "",
                "## Major Issues",
                "- none",
                "",
                "## Minor Issues",
                "- none",
            ]
        ),
        encoding="utf-8",
    )

    summary = api._derive_review_summary(run_dir, "IMPROVE_NEEDED")

    assert summary is not None
    assert summary.available is True
    assert summary.summary_status == "unknown"
    assert summary.critical_count == 0
    assert summary.major_count == 0
    assert summary.minor_count == 0


def test_collect_run_detail_prefers_run_state_phase_for_actions_and_assignment(
    tmp_path: Path, monkeypatch
) -> None:
    run_dir = tmp_path / "run-detail-canonical-phase"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_run_state(run_dir, phase="BUILD_NEEDED", phase_status="pending", current_owner="Builder")
    (run_dir / "goal.md").write_text("goal", encoding="utf-8")
    monkeypatch.setattr(api, "load_priority_index", lambda: {})
    monkeypatch.setattr(api.repo, "list_child_runs", lambda parent_name, taxonomy=None: [])

    class _PhaseValue:
        value = "REVIEW_NEEDED"

    class _FakeInfo:
        phase = _PhaseValue()
        next_role = "Critic"
        decision_reason = "file-based detector"

    class _FakeDetector:
        def __init__(self, _run_dir: Path) -> None:
            pass

        def detect(self):
            return _FakeInfo()

    monkeypatch.setattr(api, "PhaseDetector", _FakeDetector)

    detail = api._collect_run_detail("work", "work/run-detail-canonical-phase", run_dir)

    assert detail.phase == "BUILD_NEEDED"
    assert detail.next_role == "Builder"
    assert detail.operator_actions[0].label == "Run Builder (Tool-Enabled)"
    assert detail.assignment_summary.phase == "BUILD_NEEDED"


def test_collect_run_detail_suppresses_detector_mismatch_for_completed_result_written(
    tmp_path: Path, monkeypatch
) -> None:
    run_dir = tmp_path / "run-detail-result-written"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_run_state(run_dir, phase="RESULT_WRITTEN", phase_status="completed", current_owner="Judge")
    (run_dir / "goal.md").write_text("goal", encoding="utf-8")
    (run_dir / "improve.md").write_text("# Improve\n\nAccepted.\n", encoding="utf-8")
    (run_dir / "result.md").write_text("# Result\n\nClosed.\n", encoding="utf-8")
    monkeypatch.setattr(api, "load_priority_index", lambda: {})
    monkeypatch.setattr(api.repo, "list_child_runs", lambda parent_name, taxonomy=None: [])

    class _PhaseValue:
        value = "IMPROVE_NEEDED"

    class _FakeInfo:
        phase = _PhaseValue()
        next_role = "Human"
        decision_reason = "improve.md filled; result.md not filled"

    class _FakeDetector:
        def __init__(self, _run_dir: Path) -> None:
            pass

        def detect(self):
            return _FakeInfo()

    monkeypatch.setattr(api, "PhaseDetector", _FakeDetector)

    detail = api._collect_run_detail("work", "work/run-detail-result-written", run_dir)

    assert detail.phase == "RESULT_WRITTEN"
    assert detail.decision_reason == "improve.md filled; result.md not filled"


def test_execute_operator_command_pins_build_needed_after_partial_build(monkeypatch, tmp_path: Path) -> None:
    run_dir = tmp_path / "run-partial-build"
    _write_run_state(run_dir, phase="BUILD_NEEDED", phase_status="pending", current_owner="Builder")
    state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    state["retry_count"] = 2
    state["active_handoff_id"] = "handoff-123"
    state["gate_failures"] = ["stale gate"]
    state["last_error"] = "old error"
    (run_dir / "run_state.json").write_text(json.dumps(state), encoding="utf-8")
    ManifestRepository(run_dir).update_entry("build.md", "Builder", "stale build", run_dir.name)

    class _PhaseValue:
        value = "BUILD_NEEDED"

    class _FakeInfo:
        phase = _PhaseValue()
        next_role = "Builder"
        decision_reason = "build pending"
        file_to_write = "build.md"

    class _FakeDetector:
        def __init__(self, _run_dir: Path) -> None:
            pass

        def detect(self):
            return _FakeInfo()

    monkeypatch.setattr(api, "_resolve_run_dir", lambda taxonomy, run_name: run_dir)
    monkeypatch.setattr(api, "PhaseDetector", _FakeDetector)
    monkeypatch.setattr(
        api,
        "build_operator_actions",
        lambda run_name, phase, run_dir=None: [
            api.OperatorAction(
                id="phase-primary",
                label="Run Builder (Tool-Enabled)",
                command="apsf-wrapper-build.ps1 work/run-partial-build -Backend claude-cli",
                execution_type="build",
                enabled=True,
                primary=True,
            )
        ],
    )
    monkeypatch.setattr(api.viewer_db, "insert_execution_pending", lambda **kwargs: 1)
    monkeypatch.setattr(api.viewer_db, "update_execution_result", lambda **kwargs: None)

    def _fake_run(_command: str) -> subprocess.CompletedProcess[str]:
        (run_dir / "build.md").write_text("partial build artifact", encoding="utf-8")
        _write_run_state(run_dir, phase="REVIEW_NEEDED", phase_status="pending", current_owner="Critic")
        return subprocess.CompletedProcess(
            args=["powershell"],
            returncode=0,
            stdout="[PARTIAL] Reached max turns before completing the build.\nPhase remains: REVIEW_NEEDED",
            stderr="",
        )

    monkeypatch.setattr(api, "_run_powershell_command", _fake_run)

    response = asyncio.run(
        api.execute_operator_command(
            "work",
            "run-partial-build",
            api.ExecuteCommandRequest(action_id="phase-primary"),
        )
    )

    pinned_state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))

    assert response.status == "PARTIAL"
    assert pinned_state["current_phase"] == "BUILD_NEEDED"
    assert pinned_state["phase_status"] == "pending"
    assert pinned_state["current_owner"] == "Builder"
    assert pinned_state["retry_count"] == 0
    assert pinned_state["active_handoff_id"] == ""
    assert pinned_state["gate_failures"] == []
    assert pinned_state["last_error"] == ""
    manifest = ManifestRepository(run_dir).load()
    assert manifest is not None
    assert "build.md" not in manifest.entries


def test_execute_operator_command_rerun_build_preserves_canonical_build_needed(
    monkeypatch, tmp_path: Path
) -> None:
    run_dir = tmp_path / "run-rerun-build"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending", current_owner="Judge")
    state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    state["retry_count"] = 4
    state["last_error"] = "stale judge blocker"
    state["active_handoff_id"] = "handoff-999"
    state["gate_failures"] = ["old blocker"]
    (run_dir / "run_state.json").write_text(json.dumps(state), encoding="utf-8")

    monkeypatch.setattr(api, "_resolve_run_dir", lambda taxonomy, run_name: run_dir)

    class _PhaseValue:
        value = "IMPROVE_NEEDED"

    class _FakeInfo:
        phase = _PhaseValue()
        next_role = "Human"
        decision_reason = "judge review pending"

    class _FakeDetector:
        def __init__(self, _run_dir: Path) -> None:
            pass

        def detect(self):
            return _FakeInfo()

    monkeypatch.setattr(api, "PhaseDetector", _FakeDetector)
    monkeypatch.setattr(
        api,
        "build_operator_actions",
        lambda run_name, phase, run_dir=None: [
            api.OperatorAction(
                id="rerun-build",
                label="Judge and Return to Build",
                command=".\\scripts\\apsf-rerun-build.ps1 work/run-rerun-build",
                execution_type="rerun",
                enabled=True,
            )
        ],
    )
    monkeypatch.setattr(api.viewer_db, "insert_execution_pending", lambda **kwargs: 1)
    monkeypatch.setattr(api.viewer_db, "update_execution_result", lambda **kwargs: None)

    def _fake_run(_command: str) -> subprocess.CompletedProcess[str]:
        _write_run_state(run_dir, phase="BUILD_NEEDED", phase_status="pending", current_owner="Builder")
        return subprocess.CompletedProcess(
            args=["powershell"],
            returncode=0,
            stdout="Reset to BUILD_NEEDED",
            stderr="",
        )

    monkeypatch.setattr(api, "_run_powershell_command", _fake_run)

    response = asyncio.run(
        api.execute_operator_command(
            "work",
            "run-rerun-build",
            api.ExecuteCommandRequest(action_id="rerun-build"),
        )
    )

    updated_state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))

    assert response.status == "SUCCESS"
    assert updated_state["current_phase"] == "BUILD_NEEDED"
    assert updated_state["phase_status"] == "pending"
    assert updated_state["current_owner"] == "Builder"


def test_collect_run_detail_self_heals_stale_review_needed_after_partial_build(
    tmp_path: Path, monkeypatch
) -> None:
    run_dir = tmp_path / "run-self-heal-partial"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_run_state(run_dir, phase="REVIEW_NEEDED", phase_status="pending", current_owner="Critic")
    state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    state["retry_count"] = 1
    state["active_handoff_id"] = "handoff-456"
    state["gate_failures"] = ["old consistency failure"]
    state["last_error"] = "stale"
    (run_dir / "run_state.json").write_text(json.dumps(state), encoding="utf-8")
    (run_dir / "goal.md").write_text("goal", encoding="utf-8")
    (run_dir / "build.md").write_text("partial build artifact", encoding="utf-8")
    ManifestRepository(run_dir).update_entry("build.md", "Builder", "partial build artifact", run_dir.name)

    class _PhaseValue:
        value = "REVIEW_NEEDED"

    class _FakeInfo:
        phase = _PhaseValue()
        next_role = "Critic"
        decision_reason = "build.md filled; review.md not filled"

    class _FakeDetector:
        def __init__(self, _run_dir: Path) -> None:
            pass

        def detect(self):
            return _FakeInfo()

    monkeypatch.setattr(api, "PhaseDetector", _FakeDetector)
    monkeypatch.setattr(api, "load_priority_index", lambda: {})
    monkeypatch.setattr(api.repo, "list_child_runs", lambda parent_name, taxonomy=None: [])
    monkeypatch.setattr(
        api.viewer_db,
        "list_recent_executions_for_run",
        lambda taxonomy, run_name, limit=5: [
            {
                "result_status": "PARTIAL",
                "command": ".\\scripts\\apsf-wrapper-build.ps1 work/run-self-heal-partial -Backend claude-cli",
                "stdout_summary": "[PARTIAL] Reached max turns",
            }
        ],
    )

    detail = api._collect_run_detail("work", "work/run-self-heal-partial", run_dir)
    healed_state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))

    assert detail.phase == "BUILD_NEEDED"
    assert detail.next_role == "Builder"
    assert detail.operator_actions[0].label == "Run Builder (Tool-Enabled)"
    assert healed_state["current_phase"] == "BUILD_NEEDED"
    assert healed_state["current_owner"] == "Builder"
    assert healed_state["retry_count"] == 0
    assert healed_state["active_handoff_id"] == ""
    assert healed_state["gate_failures"] == []
    assert healed_state["last_error"] == ""
    manifest = ManifestRepository(run_dir).load()
    assert manifest is not None
    assert "build.md" not in manifest.entries


def test_latest_execution_indicates_partial_build_skips_guard_failure_partial(
    monkeypatch, tmp_path: Path
) -> None:
    """Guard-failure exit (phase not BUILD_NEEDED → exit 2 → PARTIAL) must not trigger self-heal."""
    monkeypatch.setattr(
        api.viewer_db,
        "list_recent_executions_for_run",
        lambda taxonomy, run_name, limit=5: [
            {
                # Most recent: guard-failure classified as PARTIAL
                "result_status": "PARTIAL",
                "command": ".\\scripts\\apsf-wrapper-build.ps1 work/run-x -Backend claude-cli",
                "stdout_summary": "[Warn] Current phase is 'REVIEW_NEEDED', not BUILD_NEEDED.",
            }
        ],
    )

    result = api._latest_execution_indicates_partial_build("work", "run-x")

    assert result is False


def test_latest_execution_indicates_partial_build_returns_true_after_skipping_guard_failure(
    monkeypatch, tmp_path: Path
) -> None:
    """After skipping a guard-failure entry, a real PARTIAL in an older row is still detected."""
    monkeypatch.setattr(
        api.viewer_db,
        "list_recent_executions_for_run",
        lambda taxonomy, run_name, limit=5: [
            {
                "result_status": "PARTIAL",
                "command": ".\\scripts\\apsf-wrapper-build.ps1 work/run-x -Backend claude-cli",
                "stdout_summary": "[Warn] Current phase is 'REVIEW_NEEDED', not BUILD_NEEDED.",
            },
            {
                "result_status": "PARTIAL",
                "command": ".\\scripts\\apsf-wrapper-build.ps1 work/run-x -Backend claude-cli",
                "stdout_summary": "[PARTIAL] Reached max turns before completing the build.",
            },
        ],
    )

    result = api._latest_execution_indicates_partial_build("work", "run-x")

    assert result is True


def test_latest_execution_indicates_partial_build_not_triggered_after_success(
    monkeypatch, tmp_path: Path
) -> None:
    """A SUCCESS build exec stops the scan; no self-heal even if older rows had PARTIAL."""
    monkeypatch.setattr(
        api.viewer_db,
        "list_recent_executions_for_run",
        lambda taxonomy, run_name, limit=5: [
            {
                "result_status": "SUCCESS",
                "command": ".\\scripts\\apsf-wrapper-build.ps1 work/run-x -Backend claude-cli",
                "stdout_summary": "[SUCCESS] Build complete and phase advanced to: REVIEW_NEEDED",
            },
            {
                "result_status": "PARTIAL",
                "command": ".\\scripts\\apsf-wrapper-build.ps1 work/run-x -Backend claude-cli",
                "stdout_summary": "[PARTIAL] Reached max turns",
            },
        ],
    )

    result = api._latest_execution_indicates_partial_build("work", "run-x")

    assert result is False


# ── run-077: Agent OS action / operator action command alignment ──────────────

def test_agent_os_act_command_defaults_to_wrapper(monkeypatch, tmp_path: Path) -> None:
    """Agent OS action 'act' の default command が wrapper に揃っていること。"""
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", tmp_path / "viewer.config.json")
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)

    command = api._build_agent_os_action_command("work/run-077", "act")

    assert command == ".\\scripts\\apsf-wrapper-act.ps1 work/run-077 -Backend claude-cli"


def test_agent_os_act_command_uses_provider_when_configured(monkeypatch, tmp_path: Path) -> None:
    """Agent OS action 'act' が provider mode 設定を反映すること。"""
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"execution_modes": {"act": "provider"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)

    command = api._build_agent_os_action_command("work/run-077", "act")

    assert command == "apsf act work/run-077"


def test_agent_os_act_and_operator_act_use_same_command(monkeypatch, tmp_path: Path) -> None:
    """Agent OS action と通常 operator action が同じ execution mode policy から同じ command を返すこと。"""
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(json.dumps({"execution_modes": {"act": "provider"}}), encoding="utf-8")
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)

    agent_os_cmd = api._build_agent_os_action_command("work/run-077", "act")
    operator_actions = api.build_operator_actions("work/run-077", "PLAN_NEEDED")
    operator_cmd = next(a for a in operator_actions if a.id == "phase-primary").command

    assert agent_os_cmd == operator_cmd


# ── run-078: action classification structure ─────────────────────────────────

def test_act_is_classified_as_policy_aware() -> None:
    """act は policy-aware action として分類される。"""
    assert "act" in api._POLICY_AWARE_ACTIONS


def test_fixed_actions_classified_correctly() -> None:
    """capture-* / apply-* は fixed action として分類される。"""
    expected_fixed = {"capture-checkpoint", "capture-snapshot", "apply-checkpoint", "apply-snapshot"}
    assert expected_fixed == api._FIXED_ACTIONS


def test_fixed_actions_are_not_policy_aware() -> None:
    """fixed action は policy-aware の集合と重複しない。"""
    assert api._FIXED_ACTIONS.isdisjoint(api._POLICY_AWARE_ACTIONS)


def test_policy_aware_and_fixed_are_disjoint_from_human_only() -> None:
    """3 分類に重複がない。"""
    all_actions = api._POLICY_AWARE_ACTIONS | api._FIXED_ACTIONS | api._HUMAN_ONLY_ACTIONS
    assert len(all_actions) == len(api._POLICY_AWARE_ACTIONS) + len(api._FIXED_ACTIONS) + len(api._HUMAN_ONLY_ACTIONS)


def test_fixed_action_command_uses_python_executable() -> None:
    """fixed action の command は sys.executable を含む base command から構成される。"""
    import sys

    command = api._build_agent_os_action_command(
        "work/run-078", "capture-checkpoint", checkpoint_id="cp-001"
    )

    assert "apsf.legacy.cli.main" in command
    assert "capture-checkpoint" in command
    assert "work/run-078" in command


def test_unknown_action_raises_value_error() -> None:
    """未知の action_id は ValueError を送出する（黙って通らない）。"""
    import pytest

    with pytest.raises(ValueError, match="unknown Agent OS action"):
        api._build_agent_os_action_command("work/run-079", "unknown-future-action")


# ── run-081: executor unknown action alignment ───────────────────────────────

def test_executor_unknown_action_returns_failed_response(tmp_path: Path) -> None:
    """executor 側の unknown action は FAILED response を返す（apply-snapshot に流れ込まない）。
    Pydantic Literal が通常の gate だが、直接呼び出しへの defense-in-depth として確認する。
    model_construct() で Pydantic validation をバイパスして executor を直接テストする。
    """
    run_dir = tmp_path / "run-081"
    _write_run_state(run_dir)

    request = api.ExecuteAgentOSActionRequest.model_construct(action_id="unknown-future-action")
    response = api._execute_agent_os_action(
        run_dir,
        "fw-improvement/run-081",
        request,
    )

    assert response.status == "FAILED"
    assert "unknown Agent OS action" in response.stderr
    assert response.action_id == "unknown-future-action"


def test_apply_snapshot_still_blocks_without_confirmation(tmp_path: Path) -> None:
    """apply-snapshot が if ガード追加後も正常に動作する（既存 semantics 維持）。"""
    run_dir = tmp_path / "run-081"
    _write_run_state(run_dir)

    response = api._execute_agent_os_action(
        run_dir,
        "fw-improvement/run-081",
        api.ExecuteAgentOSActionRequest(
            action_id="apply-snapshot",
            snapshot_id="snap-001",
            reason="rollback",
            confirmed=False,
        ),
    )

    assert response.status == "FAILED"
    assert "explicit confirmation is required" in response.stderr


def test_derive_judge_recommendation_adopts_ready_to_close_review_with_explicit_zero_sections(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-201"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Critical Issues",
                "None.",
                "",
                "## Major Issues",
                "None.",
                "",
                "## Minor Issues",
                "None.",
                "",
                "## Overall Classification",
                "",
                "| Severity | Count |",
                "|---|---|",
                "| Critical | 0 |",
                "| Major | 0 |",
                "| Minor | 0 |",
                "",
                "**Verdict: Ready to close.** Proceed to Adopt.",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "RESULT_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Adopt"
    assert recommendation.review_verdict == "Ready to close."
    assert recommendation.critical_count == 0
    assert recommendation.major_count == 0
    assert recommendation.minor_count == 0


def test_derive_judge_recommendation_adopts_accept_judgment_with_dash_nashi_sections(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-202"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Summary of review",
                "**判定: Accept**",
                "",
                "## Critical Issues",
                "",
                "- なし",
                "",
                "## Major Issues",
                "",
                "- なし",
                "",
                "## Minor Issues",
                "",
                "- なし",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Adopt"
    assert recommendation.review_verdict == "Accept"
    assert recommendation.critical_count == 0
    assert recommendation.major_count == 0
    assert recommendation.minor_count == 0


def test_derive_judge_recommendation_reads_acceptable_prose_findings(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-203"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Verdict",
                "",
                "Acceptable.",
                "",
                "## Findings",
                "",
                "No critical findings in the implementation boundary.",
                "",
                "Major risks to watch during the actual build:",
                "",
                "- over-tuning copy before use validates the direction",
                "",
                "Minor note:",
                "",
                "- a small badge cleanup can still be reasonable",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "COMPLETE")

    assert recommendation is not None
    assert recommendation.decision == "Revise"
    assert recommendation.review_verdict == "Acceptable"
    assert recommendation.critical_count == 0
    assert recommendation.major_count == 1
    assert recommendation.minor_count == 1


def test_derive_judge_recommendation_reads_disposition_and_inline_findings_summary(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-204"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Findings",
                "",
                "- Critical: none - Major: none - Minor: 1",
                "  - taxonomy wording is still a polish follow-up",
                "",
                "## Disposition",
                "",
                "- Accept",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Adopt"
    assert recommendation.review_verdict == "Accept"
    assert recommendation.critical_count == 0
    assert recommendation.major_count == 0
    assert recommendation.minor_count == 1


def test_derive_judge_recommendation_handles_not_ready_to_close_and_bold_coded_findings(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-205b"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "## Review",
                "",
                "### Summary",
                "",
                "Not ready to close.",
                "",
                "### Findings",
                "",
                "#### Critical",
                "",
                "**[C-1] Contract evidence not written back**",
                "",
                "details",
                "",
                "#### Major",
                "",
                "**[M-1] v2 field mapping not reconciled**",
                "",
                "details",
                "",
                "**[M-2] Universe still provisional**",
                "",
                "details",
                "",
                "#### Minor",
                "",
                "**[m-1] Calendar fallback source is TBD**",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Revise"
    assert recommendation.review_verdict == "Not ready to close"
    assert recommendation.critical_count == 1
    assert recommendation.major_count == 2
    assert recommendation.minor_count == 1


def test_derive_judge_recommendation_does_not_adopt_when_review_only_says_partially_met(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-205c"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "# Review",
                "",
                "## Criterion-by-Criterion Assessment",
                "",
                "| # | Success Criterion | Status | Classification |",
                "|---|---|---|---|",
                "| 1 | Example | **Met** | — |",
                "| 2 | Example | **Partially Met** | — |",
                "",
                "## Overall Verdict",
                "",
                "Partially met. Another iteration is required.",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Revise"
    assert recommendation.suggested_return_phase == "BUILD_NEEDED"


def test_classify_process_result_marks_partial_on_wrapper_partial_markers() -> None:
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout="[PARTIAL] Claude claimed success, but the phase is still BUILD_NEEDED.",
        stderr="",
    )

    assert api._classify_process_result(completed) == "PARTIAL"


def test_derive_judge_recommendation_counts_dash_separated_issue_ids_and_prefers_build_for_contract_review(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-205d"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "## Review of Build Output vs. Goal Success Criteria",
                "",
                "### Criterion Assessment Summary",
                "",
                "| # | Success Criterion | Build Status | Severity |",
                "|---|---|---|---|",
                "| 3 | Automation feasibility confirmed | **Formally Unmet in artifact** | **Critical** |",
                "| 4 | One universe + data source selected with rationale | **Partially Met** | **Major** |",
                "",
                "## Critical",
                "",
                "### C-1 — Criterion 3 Formal Status Unresolved in Build Artifact",
                "",
                "The build artifact and contract must be updated.",
                "",
                "## Major",
                "",
                "### M-1 — Universe remains provisional",
                "",
                "The contract still labels the universe PROVISIONAL.",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Revise"
    assert recommendation.suggested_return_phase == "BUILD_NEEDED"
    assert recommendation.critical_count == 1
    assert recommendation.major_count == 1


def test_detect_run_human_blocker_prefers_latest_review(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-205"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="human",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase="REVIEW_NEEDED",
            target_phase="REVIEW_NEEDED",
        ),
    )
    (run_dir / "build_review.md").write_text(
        "# Build Review\n\n## Summary\n\n- stale scaffold\n",
        encoding="utf-8",
    )
    (run_dir / "review_rerun_20260406_160000.md").write_text(
        "\n".join(
            [
                "**Verdict: CONDITIONAL PASS — Critical human-owned blocker persists**",
                "",
                "**Required action (human-owned):**",
                "Option (a): Register J-Quants free account and run a live API test.",
                "Neither option is Builder-executable.",
            ]
        ),
        encoding="utf-8",
    )

    blocker = api._detect_run_human_blocker(run_dir)

    assert blocker is not None
    assert blocker.active is True
    assert blocker.source == "review_rerun_20260406_160000.md"
    assert blocker.actions == ["Register J-Quants free account and run a live API test."]


def test_detect_run_human_blocker_prefers_build_review_judge_override(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-205"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.BUILD_NEEDED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.SYSTEM,
            source_phase="REVIEW_NEEDED",
            target_phase="BUILD_NEEDED",
        ),
    )
    (run_dir / "build_review.md").write_text(
        "\n".join(
            [
                "# Build Review",
                "",
                "## Rerun Comment",
                "",
                "**Judge 判断: BUILD_NEEDED**",
                "",
                "Builder への指示:",
                "1. v2 endpoint に統一",
                "2. contract を更新",
                "",
                "これらが完了すれば Critical は解消し、Review に進める。",
            ]
        ),
        encoding="utf-8",
    )
    (run_dir / "review_rerun_20260406_160000.md").write_text(
        "\n".join(
            [
                "**Verdict: CONDITIONAL PASS - Critical human-owned blocker persists**",
                "",
                "**Required action (human-owned):**",
                "Option (a): Register J-Quants free account and run a live API test.",
                "Neither option is Builder-executable.",
            ]
        ),
        encoding="utf-8",
    )

    blocker = api._detect_run_human_blocker(run_dir)

    assert blocker is None


def test_detect_run_human_blocker_returns_invalid_status_without_marking_active(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-205-invalid"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "transition_outcome.json").write_text("{bad json}", encoding="utf-8")

    blocker = api._detect_run_human_blocker(run_dir)

    assert blocker is not None
    assert blocker.active is False
    assert blocker.ownership_status == "CORRUPT"


def test_record_human_blocked_comment_outcome_writes_canonical_human_record(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-judge-human"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", current_owner="Human")

    written = api._record_human_blocked_comment_outcome(
        run_dir,
        "**Goal-owner decision: HUMAN_BLOCKED**\nblocker_owner=HUMAN\n人間判断待ち",
    )

    assert written is True
    outcome = get_transition_outcome(run_dir)
    assert outcome.transition_type == TransitionType.HUMAN_BLOCKED
    assert outcome.blocker_owner == BlockerOwnership.HUMAN
    assert outcome.source_phase == "IMPROVE_NEEDED"
    assert outcome.target_phase == "IMPROVE_NEEDED"


def test_derive_judge_recommendation_uses_canonical_system_state_for_blocker_flag(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-judge-system"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", current_owner="Human")
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.BUILD_NEEDED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.SYSTEM,
            source_phase="REVIEW_NEEDED",
            target_phase="BUILD_NEEDED",
        ),
    )
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "**Verdict: CONDITIONAL PASS - Critical human-owned blocker persists**",
                "",
                "### MAJOR Issues",
                "#### M-1 Contract update required",
                "",
                "**Required action (human-owned):**",
                "Option (a): Goal-owner sign-off.",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Revise"
    assert recommendation.human_owned_blocker is False
    assert recommendation.ownership_status == "SUPERSEDED"


def test_derive_judge_recommendation_surfaces_corrupt_ownership_state(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-judge-corrupt"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", current_owner="Human")
    (run_dir / "transition_outcome.json").write_text("{bad json}", encoding="utf-8")
    (run_dir / "review.md").write_text(
        "\n".join(
            [
                "**Verdict: CONDITIONAL PASS - Critical human-owned blocker persists**",
                "",
                "### MAJOR Issues",
                "#### M-1 Contract update required",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.human_owned_blocker is False
    assert recommendation.ownership_status == "CORRUPT"
    assert recommendation.ownership_detail is not None


def test_classify_process_result_marks_partial_on_reached_max_turns() -> None:
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout="Reached max turns before completing the build.",
        stderr="",
    )
    assert api._classify_process_result(completed) == "PARTIAL"


def test_classify_process_result_marks_partial_on_phase_remains_build_needed() -> None:
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout="Phase remains: BUILD_NEEDED",
        stderr="",
    )
    assert api._classify_process_result(completed) == "PARTIAL"


def test_classify_process_result_marks_partial_on_exit_code_2() -> None:
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=2,
        stdout="",
        stderr="",
    )
    assert api._classify_process_result(completed) == "PARTIAL"


def test_derive_judge_recommendation_uses_review_rerun_when_no_review_md(tmp_path: Path) -> None:
    """_derive_judge_recommendation falls back to review_rerun_*.md when review.md is absent."""
    run_dir = tmp_path / "run-206"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "review_rerun_20260407_184939.md").write_text(
        "\n".join(
            [
                "## Critical",
                "",
                "### C-1 — Artifact not updated with live-check evidence",
                "",
                "The build artifact has not been updated to incorporate this evidence.",
                "",
                "**Required action:** Update docs/data_contract_v0.1.md.",
                "",
                "## Major",
                "",
                "### M-1 — Universe remains PROVISIONAL",
                "",
                "details",
            ]
        ),
        encoding="utf-8",
    )

    recommendation = api._derive_judge_recommendation(run_dir, "IMPROVE_NEEDED")

    assert recommendation is not None
    assert recommendation.decision == "Revise"
    assert recommendation.suggested_return_phase == "BUILD_NEEDED"
    assert recommendation.critical_count == 1
    assert recommendation.major_count == 1


def test_derive_judge_recommendation_001c2_review_parses_as_revise_build_needed() -> None:
    """Sanity: the 001c2 review format (C-1, M-1/2/3, m-1/2/3) gives Revise / BUILD_NEEDED / 1-3-3."""
    review_text = "\n".join(
        [
            "## Review of Build Output vs. Goal Success Criteria",
            "",
            "### Criterion Assessment Summary",
            "",
            "| # | Success Criterion | Build Status | Severity |",
            "|---|---|---|---|",
            "| 3 | Automation feasibility confirmed | **Formally Unmet in artifact** | **Critical** |",
            "| 4 | One universe + data source selected with rationale | **Partially Met** | **Major** |",
            "",
            "## Critical",
            "",
            "### C-1 \u2014 Criterion 3 Formal Status Unresolved in Build Artifact",
            "",
            "The build artifact has not been updated to incorporate this evidence.",
            "Confirmed ToS findings must be materialized into the contract.",
            "",
            "**Required action:** Update docs/data_contract_v0.1.md to incorporate live-check findings.",
            "",
            "## Major",
            "",
            "### M-1 \u2014 Universe Remains PROVISIONAL; Criterion 4 Incompletely Met",
            "",
            "details",
            "",
            "### M-2 \u2014 v1/v2 Field-Mapping Reconciliation Undocumented",
            "",
            "details",
            "",
            "### M-3 \u2014 Trading Calendar Endpoint Verification Still Open",
            "",
            "details",
            "",
            "## Minor",
            "",
            "### m-1 \u2014 ADTV Threshold Is a Working Assumption",
            "",
            "details",
            "",
            "### m-2 \u2014 ADTV Gap Not Risk-Annotated",
            "",
            "details",
            "",
            "### m-3 \u2014 Q-5 Total-Return vs. Price-Return Left Open",
            "",
            "details",
        ]
    )
    critical, major, minor, _ = api._extract_review_issue_counts(review_text)

    assert critical == 1
    assert major == 3
    assert minor == 3


def test_detect_human_owned_blocker_does_not_fire_for_builder_executable_contract_update(
    tmp_path: Path,
) -> None:
    """Builder-executable action (update contract) should NOT trigger human-owned blocker."""
    from apsf.legacy.orchestration.rebuild_feedback import detect_human_owned_blocker

    review_text = "\n".join(
        [
            "## Critical",
            "",
            "### C-1 \u2014 Criterion 3 Formal Status Unresolved",
            "",
            "The build artifact has not been updated to incorporate this evidence.",
            "Confirmed ToS findings must be materialized into the contract.",
            "",
            "**Required action:** Update docs/data_contract_v0.1.md to incorporate live-check findings.",
            "",
            "## Major",
            "",
            "### M-1 \u2014 Universe Remains PROVISIONAL",
            "",
            "Either (a) child run 1 closes Q-6 and the contract is updated to CONFIRMED universe,",
            "or (b) goal-owner accepts PROVISIONAL as the v0.1 planning gate definition.",
        ]
    )

    blocker = detect_human_owned_blocker(review_text)

    assert blocker is None, f"Expected no human-owned blocker, got: {blocker}"


def test_emphatic_verdict_with_trailing_text_is_captured_correctly() -> None:
    """**Verdict: X.** followed by other text on same line should still capture X."""
    review_text = "**Verdict: Ready to close.** Proceed to Adopt."
    verdict = api._extract_review_verdict(review_text)
    assert verdict == "Ready to close."


# ---------------------------------------------------------------------------
# Freshness token — staleness checks
# ---------------------------------------------------------------------------

def test_evaluate_improve_auto_loop_decision_stops_when_advisory_freshness_token_is_stale(
    tmp_path: Path, monkeypatch
) -> None:
    """Advisory written for a prior cycle (different freshness_token) must stop auto-loop."""
    run_dir = tmp_path / "run-improve-stale-token"
    cycle_token = "2026-04-12T10:00:00+00:00"
    old_token = "2026-04-12T09:00:00+00:00"  # prior cycle
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=cycle_token)
    _write_judge_advisory(
        run_dir,
        recommendation="Return to Build",
        human_owned_blocker=False,
        freshness_token=old_token,  # stale: does not match current cycle
    )
    monkeypatch.setattr(
        api, "get_build_gate_decision",
        lambda _: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "advisory_stale"
    assert decision["stop_reason"] == "advisory_stale"
    assert "advisory_stale" in decision["log_line"]


def test_evaluate_improve_auto_loop_decision_stops_when_advisory_has_no_freshness_token(
    tmp_path: Path, monkeypatch
) -> None:
    """Advisory with no freshness_token is treated as stale when run_state has phase_entered_at."""
    run_dir = tmp_path / "run-improve-no-token"
    cycle_token = "2026-04-12T10:00:00+00:00"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=cycle_token)
    _write_judge_advisory(
        run_dir,
        recommendation="Return to Build",
        human_owned_blocker=False,
        freshness_token=None,  # no freshness_token — legacy or missing
    )
    monkeypatch.setattr(
        api, "get_build_gate_decision",
        lambda _: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "advisory_stale"


def test_evaluate_improve_auto_loop_decision_reroutes_when_freshness_token_matches(
    tmp_path: Path, monkeypatch
) -> None:
    """Advisory with matching freshness_token should still allow auto-reroute."""
    run_dir = tmp_path / "run-improve-fresh-token"
    cycle_token = "2026-04-12T10:00:00+00:00"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=cycle_token)
    _write_judge_advisory(
        run_dir,
        recommendation="Return to Build",
        human_owned_blocker=False,
        freshness_token=cycle_token,  # matches current cycle
    )
    monkeypatch.setattr(
        api, "get_build_gate_decision",
        lambda _: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "BUILD_NEEDED"
    assert decision["reason"] == "auto_reroute_build"


def test_evaluate_improve_auto_loop_decision_stops_when_both_tokens_absent_legacy_run(
    tmp_path: Path, monkeypatch
) -> None:
    """Fail-closed: if run_state has no phase_entered_at and advisory has no freshness_token,
    auto-reroute is blocked. Legacy runs must re-enter IMPROVE_NEEDED to establish an anchor."""
    run_dir = tmp_path / "run-improve-legacy-state"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at="")  # legacy — no token
    _write_judge_advisory(
        run_dir,
        recommendation="Return to Build",
        human_owned_blocker=False,
        freshness_token=None,  # also no token
    )
    monkeypatch.setattr(
        api, "get_build_gate_decision",
        lambda _: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    # Both tokens absent: fail-closed — stale advisory must not drive auto-reroute.
    assert decision["action"] == "STOP"
    assert decision["reason"] == "advisory_stale"


def test_evaluate_improve_auto_loop_decision_stops_when_advisory_has_token_but_run_state_does_not(
    tmp_path: Path, monkeypatch
) -> None:
    """Fail-closed: advisory has freshness_token but run_state has no phase_entered_at.
    Freshness cannot be verified — treat as stale."""
    run_dir = tmp_path / "run-improve-unverifiable"
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at="")  # old run_state, no anchor
    _write_judge_advisory(
        run_dir,
        recommendation="Return to Build",
        human_owned_blocker=False,
        freshness_token="2026-04-12T10:00:00+00:00",  # token present but unverifiable
    )
    monkeypatch.setattr(
        api, "get_build_gate_decision",
        lambda _: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "advisory_stale"


# ---------------------------------------------------------------------------
# E2E: REVIEW → IMPROVE_NEEDED cycle — advisory stub written, then rerouted
# ---------------------------------------------------------------------------

def test_write_improve_cycle_stub_writes_advisory_with_freshness_token(tmp_path: Path) -> None:
    """write_improve_cycle_stub() writes advisory stub with matching freshness_token."""
    from apsf.core.advisory import write_improve_cycle_stub

    run_dir = tmp_path / "run-cycle-stub"
    run_dir.mkdir(parents=True, exist_ok=True)
    phase_entered_at = "2026-04-12T10:00:00+00:00"

    write_improve_cycle_stub(run_dir, phase_entered_at)

    advisory = json.loads((run_dir / "judge_advisory.json").read_text(encoding="utf-8"))
    assert advisory["advisory_source"] == "improve_cycle_started"
    assert advisory["recommendation"] is None
    assert advisory["freshness_token"] == phase_entered_at
    assert advisory["run_id"] == run_dir.name
    assert advisory["phase"] == "IMPROVE_NEEDED"


def test_e2e_review_to_improve_cycle_stub_then_judge_advisory_then_reroute(
    tmp_path: Path, monkeypatch
) -> None:
    """Full cycle: stub written on IMPROVE_NEEDED entry → judge writes advisory → auto-loop reroutes.

    This is the end-to-end-near test required by goal-owner item 7:
    REVIEW → IMPROVE_NEEDED cycle establishes advisory, judge records Return to Build,
    auto-loop evaluates and reroutes without human intervention.
    """
    from apsf.core.advisory import write_improve_cycle_stub

    run_dir = tmp_path / "run-e2e-improve-cycle"
    cycle_token = "2026-04-12T11:00:00+00:00"

    # Step 1: Transition to IMPROVE_NEEDED — write cycle stub (simulates write-phase review.md)
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=cycle_token)
    write_improve_cycle_stub(run_dir, cycle_token)

    # Verify stub was written correctly
    stub = json.loads((run_dir / "judge_advisory.json").read_text(encoding="utf-8"))
    assert stub["advisory_source"] == "improve_cycle_started"
    assert stub["freshness_token"] == cycle_token
    assert stub["recommendation"] is None

    # Step 2: Auto-loop reaches IMPROVE_NEEDED — should stop because no canonical recommendation yet
    monkeypatch.setattr(
        api, "get_build_gate_decision",
        lambda _: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )
    decision = api._evaluate_improve_auto_loop_decision(run_dir)
    assert decision["action"] == "STOP"
    assert decision["reason"] == "advisory_source_invalid"  # stub source != judge_structured

    # Step 3: Judge records Return to Build (via _write_judge_advisory_record)
    monkeypatch.setattr(api, "_resolve_agent_os_phase", lambda _: "IMPROVE_NEEDED")
    api._write_judge_advisory_record(
        run_dir,
        recommendation="Return to Build",
        human_owned_blocker=False,
        phase="IMPROVE_NEEDED",
        source="judge_decision",
        freshness_token=cycle_token,  # same cycle token
    )

    # Step 4: Auto-loop evaluates again — should reroute
    decision = api._evaluate_improve_auto_loop_decision(run_dir)
    assert decision["action"] == "BUILD_NEEDED"
    assert decision["reason"] == "auto_reroute_build"
    assert decision["log_line"].endswith("action=BUILD_NEEDED reason=auto_reroute_build")


def test_e2e_stale_advisory_from_prior_cycle_does_not_reroute(
    tmp_path: Path, monkeypatch
) -> None:
    """Stale advisory from a prior IMPROVE_NEEDED cycle must not trigger reroute in the new cycle."""
    run_dir = tmp_path / "run-e2e-stale-cycle"
    old_token = "2026-04-12T09:00:00+00:00"
    new_token = "2026-04-12T12:00:00+00:00"

    # Advisory from prior cycle
    _write_judge_advisory(
        run_dir,
        recommendation="Return to Build",
        human_owned_blocker=False,
        freshness_token=old_token,
    )

    # New cycle entered (run went BUILD → REVIEW → IMPROVE again)
    _write_run_state(run_dir, phase="IMPROVE_NEEDED", phase_status="pending",
                     current_owner="Human", phase_entered_at=new_token)

    monkeypatch.setattr(
        api, "get_build_gate_decision",
        lambda _: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "advisory_stale"


# ---------------------------------------------------------------------------
# Operational verification: start_auto_loop → running=true → stop → running=false
# ---------------------------------------------------------------------------

def test_auto_loop_operational_start_then_running_then_stop(tmp_path: Path, monkeypatch) -> None:
    """Operational verification: start loop → running=true → process exits → running=false."""
    run_dir = tmp_path / "run-op-verify"
    _write_run_state(run_dir, phase="BUILD_NEEDED", phase_status="pending", current_owner="Builder")

    alive = {"value": True}
    fake_pid = 12345

    class FakeProc:
        pid = fake_pid

        def poll(self):
            return None if alive["value"] else 0

    monkeypatch.setattr(api, "_resolve_run_dir", lambda tax, name: run_dir)
    monkeypatch.setattr(api, "_is_auto_loop_running", lambda tax, name: False)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: FakeProc())

    # Start the loop
    result = asyncio.run(api.start_auto_loop("work", "run-op-verify", api.AutoLoopOptions()))
    assert result["status"] == "started"
    assert result["pid"] == fake_pid

    # While process is alive, Popen-based check reports running=true
    key = api._auto_loop_key("work", "run-op-verify")
    assert api._auto_loop_procs[key].poll() is None

    # Process exits
    alive["value"] = False
    assert api._auto_loop_procs[key].poll() == 0

    # _is_auto_loop_running now removes the proc and returns False
    # (restore real function for this check)
    monkeypatch.undo()
    assert api._is_auto_loop_running("work", "run-op-verify") is False

    api._close_auto_loop_log(key)


def test_parse_review_judge_advisory_reads_structured_block() -> None:
    from apsf.core.advisory import parse_review_judge_advisory

    payload = parse_review_judge_advisory(
        "# Review\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Build","human_owned_blocker":false}\n'
        "```\n"
    )

    assert payload == {
        "recommendation": "Return to Build",
        "human_owned_blocker": False,
    }


def test_parse_review_judge_advisory_fails_when_block_is_missing() -> None:
    from apsf.core.advisory import parse_review_judge_advisory

    with pytest.raises(ValueError, match="exactly one"):
        parse_review_judge_advisory("# Review\n\nNo advisory block here.\n")


def test_parse_review_judge_advisory_fails_when_duplicate_identical_blocks_exist() -> None:
    from apsf.core.advisory import parse_review_judge_advisory

    review_text = (
        "# Review\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Build","human_owned_blocker":false}\n'
        "```\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Build","human_owned_blocker":false}\n'
        "```\n"
    )

    with pytest.raises(ValueError, match="multiple blocks are not allowed"):
        parse_review_judge_advisory(review_text)


def test_parse_review_judge_advisory_fails_when_duplicate_conflicting_blocks_exist() -> None:
    from apsf.core.advisory import parse_review_judge_advisory

    review_text = (
        "# Review\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Build","human_owned_blocker":false}\n'
        "```\n\n"
        "```apsf-judge-advisory\n"
        '{"recommendation":"Return to Plan","human_owned_blocker":true}\n'
        "```\n"
    )

    with pytest.raises(ValueError, match="multiple blocks are not allowed"):
        parse_review_judge_advisory(review_text)


def test_evaluate_improve_auto_loop_decision_stops_when_human_owned_blocker_is_missing(
    tmp_path: Path, monkeypatch
) -> None:
    run_dir = tmp_path / "run-improve-blocker-missing"
    _write_run_state(
        run_dir,
        phase="IMPROVE_NEEDED",
        phase_status="pending",
        current_owner="Human",
        phase_entered_at=_CYCLE_TOKEN,
    )
    (run_dir / "judge_advisory.json").write_text(
        json.dumps(
            {
                "recommendation": "Return to Build",
                "advisory_source": "judge_structured",
                "run_id": run_dir.name,
                "generated_at": "2026-04-12T00:00:00+00:00",
                "phase": "IMPROVE_NEEDED",
                "source": "write-phase review completion",
                "freshness_token": _CYCLE_TOKEN,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda run_dir: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "STOP"
    assert decision["reason"] == "human_owned_blocker_invalid"
    assert decision["stop_reason"] == "human_owned_blocker_invalid"
    assert decision["log_line"].endswith("action=STOP reason=human_owned_blocker_invalid")


def test_e2e_review_completion_advisory_reroutes_without_manual_judge_write(
    tmp_path: Path, monkeypatch
) -> None:
    run_dir = tmp_path / "run-e2e-review-completion"
    cycle_token = "2026-04-12T11:00:00+00:00"

    _write_run_state(
        run_dir,
        phase="IMPROVE_NEEDED",
        phase_status="pending",
        current_owner="Human",
        phase_entered_at=cycle_token,
    )
    monkeypatch.setattr(
        api,
        "get_build_gate_decision",
        lambda _: {"status": "SYSTEM", "detail": "", "source": "transition_outcome.json"},
    )
    monkeypatch.setattr(api, "_resolve_agent_os_phase", lambda _: "IMPROVE_NEEDED")
    api._write_judge_advisory_record(
        run_dir,
        recommendation="Return to Plan",
        human_owned_blocker=False,
        phase="IMPROVE_NEEDED",
        source="write-phase review completion",
        freshness_token=cycle_token,
    )

    advisory = json.loads((run_dir / "judge_advisory.json").read_text(encoding="utf-8"))
    assert advisory["advisory_source"] == "judge_structured"
    assert advisory["source"] == "write-phase review completion"
    assert advisory["freshness_token"] == cycle_token

    decision = api._evaluate_improve_auto_loop_decision(run_dir)

    assert decision["action"] == "PLAN_NEEDED"
    assert decision["reason"] == "auto_reroute_plan"
    assert decision["log_line"].endswith("action=PLAN_NEEDED reason=auto_reroute_plan")
