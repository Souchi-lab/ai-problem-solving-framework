"""
ActService — apsf act のコアロジック

現在の phase を判定し、Human 担当 phase では停止、
Auto 担当 phase では LLM を呼び出して phase 文書を生成・保存する。

責務:
- Phase 判定（run_state.json canonical / PhaseDetector advisory fallback）
- Human / Auto 分類（HUMAN_OWNED_PHASES / AUTO_OWNED_PHASES）
- プロンプト構築（renderer.py 再利用）
- Provider 選択（AssignmentService 再利用 + API キー fallback）
- LLM 実行 + 結果保存

しないこと:
- 複数 phase の連続実行（1 phase ずつ）
- Human 担当 phase の自動生成
- transcript.md の生成（apsf transcript コマンドへ委譲）
"""

from __future__ import annotations

import dataclasses
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..config.settings import Settings, get_settings
from ...core.domain.models import Role
from ...core.domain.enums import GateType, HandoffStatus
from ...core.gates.gate_service import GateService, HARD_BLOCK_GATE_TYPES
from ...core.handoff.handoff_repository import HandoffRepository
from ...core.state.run_state import PhaseStatus, RunState
from ...core.state.run_state_repository import RunStateRepository
from ...core.state.transition_service import TransitionService
from ..cli.specialist_registry import resolve_critic_specialist, resolve_planner_specialist
from ..orchestration.next_instruction_builder import NextInstructionBuilder
from ..orchestration.phase_detector import (
    AUTO_OWNED_PHASES,
    HUMAN_OWNED_PHASES,
    Phase,
    PhaseDetector,
    PhaseInfo,
)
from ..prompts.renderer import render_build_prompt, render_plan_prompt, render_review_prompt
from ...core.providers.base import BaseProvider, GenerateRequest, ProviderError
from ...core.artifact_writer import ArtifactWriter
from ...core.storage.artifact_repository import ArtifactRepository


class ActError(Exception):
    """apsf act 実行中の回復不可能なエラー"""
    pass


@dataclass
class ActResult:
    """apsf act の実行結果。CLI はこれを受け取って表示する。"""

    phase: Phase
    mode: str           # "auto" | "human" | "already_filled" | "complete"
    next_role: str
    target_file: str
    files_read: list[str] = field(default_factory=list)
    stop_reason: str = ""
    prompt: str = ""    # LLM に渡すプロンプト全文（--dry-run / --print-prompt 用）
    generated: bool = False
    gate_results: list = field(default_factory=list)  # list[GateResult]


# Phase → Role のマッピング（プロバイダ選択に使用）
_PHASE_TO_ROLE: dict[Phase, Role] = {
    Phase.PLAN_NEEDED:   Role.PLANNER,
    Phase.BUILD_NEEDED:  Role.BUILDER,
    Phase.REVIEW_NEEDED: Role.CRITIC,
}

# Human 停止時の説明メッセージ
_HUMAN_STOP_REASONS: dict[Phase, str] = {
    Phase.SETUP_NEEDED:           "execution-assignment.md must be filled by Human before starting.",
    Phase.GOAL_NEEDED:            "goal.md must be authored by Human.",
    Phase.IMPROVE_PLAN_OPTIONAL:  "improve-plan.md (Judge scope) must be defined by Human (v0.2).",
    Phase.IMPROVE_NEEDED:         "improve.md is a Judge decision -- Human must evaluate review.md and decide.",
    Phase.VERIFY_OPTIONAL:        "verify.md (done-criteria check) must be reviewed by Human (v0.2).",
    Phase.RESULT_NEEDED:          "result.md is a Human retrospective. Please write the outcome and learnings.",
    Phase.TRANSCRIPT_RECOMMENDED: "Use: apsf transcript <run-name>  (transcript is a secondary artifact)",
    Phase.COMPLETE:               "This run is complete. Nothing to generate.",
}


def _phase_to_owner(phase: Phase) -> str:
    """Phase から current_owner 文字列を返す。Human phase は "Human"。"""
    _map: dict[Phase, str] = {
        Phase.PLAN_NEEDED:   "Planner",
        Phase.BUILD_NEEDED:  "Builder",
        Phase.REVIEW_NEEDED: "Critic",
    }
    if phase in HUMAN_OWNED_PHASES:
        return "Human"
    return _map.get(phase, "")


class ActService:
    """
    apsf act のコアロジック。CLI から呼び出される。

    使用例:
        service = ActService()
        result = service.execute(run_dir, run_name)
        if result.mode == "auto" and result.generated:
            print(f"Saved: {result.target_file}")
    """

    def __init__(self) -> None:
        self._artifact_repo = ArtifactRepository()

    def execute(
        self,
        run_dir: Path,
        run_name: str,
        force: bool = False,
        force_reason: Optional[str] = None,
        dry_run: bool = False,
        settings: Optional[Settings] = None,
    ) -> ActResult:
        """
        現在の phase を判定し、Auto 担当なら LLM で生成・保存する。

        Phase routing:
            run_state.json が存在する場合 → current_phase を canonical routing source として使用。
            run_state.json が存在しない場合 → PhaseDetector（heuristic）で bootstrap し、
            run_state.json を生成する（後方互換）。

        Args:
            run_dir:  run ディレクトリの Path
            run_name: run 名（表示・プロンプト用）
            force:    既存コンテンツを上書きするか
            force_reason: force override の理由
            dry_run:  保存せずに何を生成するかだけ表示する
            settings: 省略時は get_settings() を使用

        Returns:
            ActResult: mode / phase / files_read / generated 等の実行結果

        Raises:
            ActError: LLM が空のレスポンスを返した場合 / API キー未設定の場合
        """
        if settings is None:
            settings = get_settings()
        self._settings = settings

        state_repo = RunStateRepository(run_dir)
        detector = PhaseDetector(run_dir)

        # ── Phase routing: canonical state → advisory detector fallback ─────
        existing_state = state_repo.load()
        if existing_state is not None:
            # Canonical routing: run_state.current_phase が source of truth
            try:
                canonical_phase = Phase[existing_state.current_phase]
            except KeyError:
                # run_state に不正な phase 値 → advisory detector にフォールバック
                canonical_phase = detector.detect_advisory().phase
            # Advisory scan: PhaseInfo metadata (files_to_read 等) を取得する。
            # Phase routing は canonical_phase が source of truth; detector は metadata 専用。
            advisory_info = detector.detect_advisory()
            info = dataclasses.replace(advisory_info, phase=canonical_phase)
            run_state = existing_state

            # ── Human phase 自動前進 ──────────────────────────────────────────
            # canonical state が HUMAN_OWNED かつ advisory が前進していれば run_state を sync する
            # （human がアクションを完了したが run_state が追いついていない場合）
            if (
                canonical_phase in HUMAN_OWNED_PHASES
                and canonical_phase not in (Phase.COMPLETE, Phase.TRANSCRIPT_RECOMMENDED)
                and advisory_info.phase != canonical_phase
            ):
                canonical_phase = advisory_info.phase
                info = advisory_info
                if not dry_run:
                    TransitionService().transition(
                        run_dir,
                        to_phase=canonical_phase.value,
                        actor="system",
                        reason="human phase auto-advance: advisory detector found completed human work",
                    )
                    refreshed_state = state_repo.load()
                    if refreshed_state is not None:
                        run_state = refreshed_state
                else:
                    run_state = dataclasses.replace(
                        run_state,
                        current_phase=canonical_phase.value,
                        current_owner=_phase_to_owner(canonical_phase),
                        phase_status=PhaseStatus.PENDING.value,
                    )
        else:
            # Bootstrap: run_state.json なし → advisory detector で初期 run_state を生成
            info = detector.detect_advisory()
            canonical_phase = info.phase
            owner = _phase_to_owner(canonical_phase)
            run_state = RunState(
                run_id=run_name,
                current_phase=canonical_phase.value,
                phase_status=PhaseStatus.PENDING.value,
                current_owner=owner,
                retry_count=0,
                last_error="",
                active_handoff_id="",
                gate_failures=[],
            )
            if not dry_run:
                TransitionService().bootstrap(
                    run_dir, run_name, canonical_phase.value,
                    actor="system",
                    reason="ActService bootstrap: run_state.json missing",
                    current_owner=owner,
                )
                refreshed_state = state_repo.load()
                if refreshed_state is not None:
                    run_state = refreshed_state

        instruction = NextInstructionBuilder().build(info, run_name)
        target_file = instruction.target_file

        # ── handoff auto-accept: offered handoff の to_role が現 phase と一致する場合 ──
        if not dry_run:
            current_owner = _phase_to_owner(canonical_phase)
            handoff_repo = HandoffRepository(run_dir)
            offered_record = handoff_repo.load()
            if (
                offered_record is not None
                and offered_record.status == HandoffStatus.OFFERED.value
                and offered_record.to_role == current_owner
            ):
                from ..orchestration.handoff_service import HandoffService
                accepted = HandoffService().accept(run_dir, current_owner)
                if accepted is not None:
                    latest_state = state_repo.load()
                    if latest_state is not None:
                        TransitionService().set_active_handoff_id(
                            run_dir,
                            accepted.handoff_id,
                            actor="system",
                            reason="handoff auto-accept: bind active_handoff_id",
                        )
                        latest_state = state_repo.load()
                        run_state = latest_state

        # ── Human 停止 ──────────────────────────────────────────────────────
        if info.phase in HUMAN_OWNED_PHASES:
            return ActResult(
                phase=info.phase,
                mode="complete" if info.phase == Phase.COMPLETE else "human",
                next_role=instruction.next_role,
                target_file=target_file,
                stop_reason=_HUMAN_STOP_REASONS.get(info.phase, "Human action required."),
            )

        # ── Pre-write consistency gate (hard block, --force bypass) ─────────
        # PRE-write で評価することで初回書き込みは通過し、phase 逆戻りのみ検出する。
        # POST-write での consistency 評価は常に FAIL するため advisory からも除外する（下記参照）。
        if not force:
            from ...core.manifest.manifest_repository import ManifestRepository
            _pre_manifest = ManifestRepository(run_dir).load()
            _consistency_results = GateService().evaluate_consistency(run_state, _pre_manifest)
            _consistency_failures = [r for r in _consistency_results if not r.passed]
            if _consistency_failures:
                TransitionService().set_status(
                    run_dir, PhaseStatus.FAILED.value,
                    actor="system",
                    reason="consistency gate failure",
                    last_error=_consistency_failures[0].reason,
                )
                run_state = dataclasses.replace(
                    run_state,
                    phase_status=PhaseStatus.FAILED.value,
                    last_error=_consistency_failures[0].reason,
                )
                raise ActError(f"consistency gate failed: {_consistency_failures[0].reason}")
        else:
            if not force_reason:
                raise ActError("--force-reason is required when using --force.")
            # --force: consistency gate bypass を audit に記録する
            from ...core.storage.force_audit_repository import (
                ForceAuditRepository,
                make_audit_entry,
            )
            ForceAuditRepository(run_dir).append(
                make_audit_entry(
                    command="act",
                    target_file=target_file,
                    role=_phase_to_owner(canonical_phase),
                    reason=force_reason,
                    override_kind="consistency_gate_bypass",
                )
            )

        # ── 上書き保護 ───────────────────────────────────────────────────────
        if (
            not dry_run
            and not force
            and target_file != "(none)"
            and detector._has_any_content(target_file)
        ):
            return ActResult(
                phase=info.phase,
                mode="already_filled",
                next_role=instruction.next_role,
                target_file=target_file,
                stop_reason=f"{target_file} already has content. Use --force to overwrite.",
            )

        # ── コンテキストファイル読み込み & プロンプト構築（dry-run でも実施）────
        files_read = [f for f in info.files_to_read if (run_dir / f).exists()]
        context = self._read_context_files(info, run_dir)
        prompt = self._build_prompt(info.phase, context)

        # ── dry-run ─────────────────────────────────────────────────────────
        if dry_run:
            return ActResult(
                phase=info.phase,
                mode="auto",
                next_role=instruction.next_role,
                target_file=target_file,
                files_read=files_read,
                prompt=prompt,
                generated=False,
            )

        # ── phase_status を in_progress に更新 ────────────────────────────────
        TransitionService().set_status(
            run_dir, PhaseStatus.IN_PROGRESS.value,
            actor="system",
            reason="LLM generation in progress",
        )
        run_state = dataclasses.replace(
            run_state,
            phase_status=PhaseStatus.IN_PROGRESS.value,
        )

        # ── session event: act_started ────────────────────────────────────────
        from ...core.session.session_event import make_act_started_event
        from ...core.session.session_event_repository import SessionEventRepository
        _session_repo = SessionEventRepository(run_dir)
        event_log_warning_emitted = False

        def _warn_event_log_failure(exc: Exception) -> None:
            nonlocal event_log_warning_emitted
            if event_log_warning_emitted:
                return
            sys.stderr.write(
                "[Warn] Failed to append session event log "
                f"({SessionEventRepository.FILENAME}): {exc}. "
                "Continuing without blocking act.\n"
            )
            event_log_warning_emitted = True

        try:
            _session_repo.append(make_act_started_event(
                run_id=run_name,
                phase=canonical_phase.value,
                target_file=target_file,
                owner=_phase_to_owner(canonical_phase),
            ))
        except Exception as exc:
            _warn_event_log_failure(exc)

        # ── Provider 取得 ─────────────────────────────────────────────────────
        provider = self._get_provider(info.phase, run_dir, settings)

        # ── LLM 実行 ──────────────────────────────────────────────────────────
        try:
            response = provider.generate(GenerateRequest(prompt=prompt))
        except ProviderError as exc:
            # 失敗記録
            TransitionService().set_status(
                run_dir, PhaseStatus.FAILED.value,
                actor="system",
                reason="LLM generation failed",
                last_error=str(exc),
                increment_retry=True,
            )
            try:
                from ...core.session.session_event import make_act_failed_event
                _session_repo.append(make_act_failed_event(
                    run_id=run_name,
                    phase=canonical_phase.value,
                    target_file=target_file,
                    error=str(exc),
                ))
            except Exception as event_exc:
                _warn_event_log_failure(event_exc)
            raise ActError(f"LLM generation failed: {exc}") from exc

        content = response.content.strip()
        if not PhaseDetector.is_meaningful_text(content):
            err_msg = (
                f"LLM returned empty or template-only content for {target_file}. "
                "Nothing saved."
            )
            TransitionService().set_status(
                run_dir, PhaseStatus.FAILED.value,
                actor="system",
                reason="empty or template-only LLM output",
                last_error=err_msg,
                increment_retry=True,
            )
            try:
                from ...core.session.session_event import make_act_failed_event
                _session_repo.append(make_act_failed_event(
                    run_id=run_name,
                    phase=canonical_phase.value,
                    target_file=target_file,
                    error=err_msg,
                ))
            except Exception as event_exc:
                _warn_event_log_failure(event_exc)
            raise ActError(err_msg)

        # ── 保存 ─────────────────────────────────────────────────────────────
        from ..cli.role_rules import role_from_phase as _role_name_from_phase
        writing_role = _role_name_from_phase(info.phase.value)
        target_path = run_dir / target_file
        if writing_role is None:
            ArtifactRepository().write(target_path, content)
        else:
            ArtifactWriter().write(
                path=target_path,
                content=content,
                writing_role=writing_role,
                run_dir=run_dir,
            )

        # ── Gate 評価 ─────────────────────────────────────────────────────────
        gate_results = GateService().evaluate_all(run_dir)
        schema_failures = [
            r for r in gate_results
            if not r.passed and r.gate_type == GateType.SCHEMA_VALID.value
        ]
        if schema_failures:
            TransitionService().set_status(
                run_dir, PhaseStatus.FAILED.value,
                actor="system",
                reason="schema_valid gate failure",
                last_error=schema_failures[0].reason,
            )
            raise ActError(f"schema_valid gate failed: {schema_failures[0].reason}")

        # consistency は PRE-write hard block で評価済みのため除外する。
        # POST-write で consistency を評価すると phase advance 前の run_state と
        # 書き込み直後の manifest が一致して常に FAIL するため、advisory にも含めない。
        advisory_failures = [
            r for r in gate_results
            if not r.passed and r.gate_type not in HARD_BLOCK_GATE_TYPES
        ]
        run_state.gate_failures = [r.reason for r in advisory_failures]

        # ── run_state を次 phase へ更新 ──────────────────────────────────────
        # advisory scan: 成果物書き込み後のファイル状態から次 phase を推定する。
        next_info = PhaseDetector(run_dir).detect_advisory()
        TransitionService().transition(
            run_dir,
            to_phase=next_info.phase.value,
            actor="system",
            reason="act_service phase advance after artifact write",
            gate_failures=run_state.gate_failures,
        )

        # ── session event: act_completed ──────────────────────────────────────
        try:
            from ...core.session.session_event import make_act_completed_event
            _session_repo.append(make_act_completed_event(
                run_id=run_name,
                phase=canonical_phase.value,
                target_file=target_file,
                next_phase=next_info.phase.value,
            ))
        except Exception as exc:
            _warn_event_log_failure(exc)

        return ActResult(
            phase=info.phase,
            mode="auto",
            next_role=instruction.next_role,
            target_file=target_file,
            files_read=files_read,
            generated=True,
            gate_results=gate_results,
        )

    # ── Internal helpers ────────────────────────────────────────────────────

    def _read_context_files(self, info: PhaseInfo, run_dir: Path) -> dict[str, str]:
        """files_to_read のうち存在するファイルを読み込んで返す。"""
        context: dict[str, str] = {}
        files_to_read = list(info.files_to_read)
        if "execution-assignment.md" not in files_to_read and (run_dir / "execution-assignment.md").exists():
            files_to_read.append("execution-assignment.md")
        for filename in files_to_read:
            path = run_dir / filename
            if path.exists():
                context[filename] = path.read_text(encoding="utf-8")
        return context

    def _build_prompt(self, phase: Phase, context: dict[str, str]) -> str:
        """
        renderer.py の既存関数を phase ごとに呼び分けてプロンプトを組み立てる。
        存在しないファイルは空文字列でフォールバック。
        """
        def _get(filename: str) -> str:
            return context.get(filename, "")

        if phase == Phase.PLAN_NEEDED:
            assignment_content = _get("execution-assignment.md")
            goal_content = _get("goal.md")
            selection = resolve_planner_specialist(
                goal_text=goal_content,
                assignment_text=assignment_content,
                framework_root=self._settings.framework_root,
            )
            selection_note = (
                f"- Mode: {selection.mode}\n"
                f"- Selected P-TYPE: {selection.ptype or '(none)'}\n"
                f"- Specialist Path: {selection.specialist_path.as_posix() if selection.specialist_path else '(none)'}\n"
                f"- Reason: {selection.reason}\n"
            )
            return render_plan_prompt(
                goal_content=goal_content,
                specialist_content=selection.specialist_content,
                specialist_selection_note=selection_note,
                plan_review_content=_get("plan_review.md"),
            )
        elif phase == Phase.BUILD_NEEDED:
            return render_build_prompt(
                plan_content=_get("plan.md"),
                handoff_content=_get("handoff.md"),
                build_review_content=_get("build_review.md"),
            )
        elif phase == Phase.REVIEW_NEEDED:
            assignment_content = _get("execution-assignment.md")
            goal_content = _get("goal.md")
            selection = resolve_critic_specialist(
                goal_text=goal_content,
                assignment_text=assignment_content,
                framework_root=self._settings.framework_root,
            )
            selection_note = (
                f"- Mode: {selection.mode}\n"
                f"- Selected C-TYPE: {selection.ptype or '(none)'}\n"
                f"- Specialist Path: {selection.specialist_path.as_posix() if selection.specialist_path else '(none)'}\n"
                f"- Reason: {selection.reason}\n"
            )
            return render_review_prompt(
                goal_content=goal_content,
                build_content=_get("build.md"),
                handoff_content=_get("handoff.md"),
                specialist_content=selection.specialist_content,
                specialist_selection_note=selection_note,
                review_review_content=_get("review_review.md"),
            )
        else:
            # AUTO_OWNED_PHASES に追加された未実装 phase への安全なフォールバック
            raise ActError(
                f"No prompt builder defined for phase: {phase}. "
                "This is a bug -- please report it."
            )

    def _read_execution_type_for_phase(
        self, phase: Phase, run_dir: Path, settings: Settings
    ) -> str:
        """execution-assignment.md から current phase の execution_type を読む。未指定時は空文字。"""
        from .execution_assignment_service import ExecutionAssignmentService

        role = _PHASE_TO_ROLE.get(phase)
        if role is None:
            return ""
        ea_path = run_dir / "execution-assignment.md"
        if not ea_path.exists():
            return ""
        service = ExecutionAssignmentService(settings=settings)
        context = service.load_from_file(ea_path, run_dir)
        assignment = context.get_execution_assignment(role)
        if assignment is None:
            return ""
        return assignment.execution_type.value

    def _get_provider(
        self, phase: Phase, run_dir: Path, settings: Settings
    ) -> BaseProvider:
        """
        プロバイダを取得する。

        優先順位:
        1. execution-assignment.md で cli (wrapper) 指定の場合は ActError（wrapper ツールを使用）
        2. model-assignment.md が存在すれば AssignmentService で role を参照
        3. なければ API キーが設定されている最初のプロバイダを使用
           （Anthropic → OpenAI → Gemini）

        Raises:
            ActError: cli execution が設定されている場合 / API キーが一切設定されていない場合
        """
        from .assignment_service import AssignmentService
        from ..providers.anthropic_provider import AnthropicProvider
        from ..providers.gemini_provider import GeminiProvider
        from ..providers.openai_provider import OpenAIProvider

        execution_type = self._read_execution_type_for_phase(phase, run_dir, settings)
        role = _PHASE_TO_ROLE.get(phase)

        # cli (wrapper) execution は apsf act の管轄外
        if execution_type == "cli":
            role_label = role.value if role is not None else phase.value
            raise ActError(
                f"cli execution is configured for {role_label}; "
                "apsf act does not execute cli-backed phases directly. "
                "Use the wrapper tool (e.g., apsf-claude-build.ps1)."
            )

        if execution_type == "human":
            role_label = role.value if role is not None else phase.value
            raise ActError(
                f"human execution is configured for {role_label}; "
                "apsf act does not execute human-owned phases directly. "
                "Follow the run guidance or update execution-assignment.md first."
            )

        service = AssignmentService(settings=settings)
        context = service.load_from_file(run_dir / "model-assignment.md", run_dir)

        if role is not None:
            resolved = service.resolve_assignment(context, role, execution_type=execution_type)
            # auto-selected assignment を durable artifact として write-back する
            service.write_back_auto_selection(run_dir, role, resolved)
            provider = service.create_provider(context, role, execution_type=execution_type)
            if provider is not None:
                return provider
            # assignment が human 指定の場合は fallback へ

        # API キー fallback（cli / human 以外の execution のみ到達、role=None の safety path）
        if settings.has_api_key("anthropic"):
            return AnthropicProvider(
                model=settings.default_anthropic_model,
                api_key=settings.anthropic_api_key,
            )
        if settings.has_api_key("openai"):
            return OpenAIProvider(
                model=settings.default_openai_model,
                api_key=settings.openai_api_key,
            )
        if settings.has_api_key("gemini"):
            return GeminiProvider(
                model=settings.default_gemini_model,
                api_key=settings.gemini_api_key,
            )

        raise ActError(
            "No API key configured. Set ANTHROPIC_API_KEY (or OPENAI_API_KEY / GEMINI_API_KEY) "
            "to use apsf act."
        )
