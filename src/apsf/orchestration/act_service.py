"""
ActService — apsf act のコアロジック

現在の phase を判定し、Human 担当 phase では停止、
Auto 担当 phase では LLM を呼び出して phase 文書を生成・保存する。

責務:
- Phase 判定（PhaseDetector 再利用）
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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..config.settings import Settings, get_settings
from ..core.domain.models import Role
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
from ..core.providers.base import BaseProvider, GenerateRequest, ProviderError


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


class ActService:
    """
    apsf act のコアロジック。CLI から呼び出される。

    使用例:
        service = ActService()
        result = service.execute(run_dir, run_name)
        if result.mode == "auto" and result.generated:
            print(f"Saved: {result.target_file}")
    """

    def execute(
        self,
        run_dir: Path,
        run_name: str,
        force: bool = False,
        dry_run: bool = False,
        settings: Optional[Settings] = None,
    ) -> ActResult:
        """
        現在の phase を判定し、Auto 担当なら LLM で生成・保存する。

        Args:
            run_dir:  run ディレクトリの Path
            run_name: run 名（表示・プロンプト用）
            force:    既存コンテンツを上書きするか
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

        detector = PhaseDetector(run_dir)
        info = detector.detect()
        instruction = NextInstructionBuilder().build(info, run_name)

        target_file = instruction.target_file

        # ── Human 停止 ──────────────────────────────────────────────────────
        if info.phase in HUMAN_OWNED_PHASES:
            return ActResult(
                phase=info.phase,
                mode="complete" if info.phase == Phase.COMPLETE else "human",
                next_role=instruction.next_role,
                target_file=target_file,
                stop_reason=_HUMAN_STOP_REASONS.get(info.phase, "Human action required."),
            )

        # ── 上書き保護 ───────────────────────────────────────────────────────
        if not force and target_file != "(none)" and detector._has_any_content(target_file):
            return ActResult(
                phase=info.phase,
                mode="already_filled",
                next_role=instruction.next_role,
                target_file=target_file,
                stop_reason=f"{target_file} already has content. Use --force to overwrite.",
            )

        # ── コンテキストファイル読み込み & プロンプト構築（dry-run でも実施）────
        # --dry-run / --print-prompt でもプロンプト全文を返せるように dry-run 判定より前に実行
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

        # ── Provider 取得 ─────────────────────────────────────────────────────
        provider = self._get_provider(info.phase, run_dir, settings)

        # ── LLM 実行 ──────────────────────────────────────────────────────────
        try:
            response = provider.generate(GenerateRequest(prompt=prompt))
        except ProviderError as exc:
            raise ActError(f"LLM generation failed: {exc}") from exc

        content = response.content.strip()
        if not PhaseDetector.is_meaningful_text(content):
            raise ActError(
                f"LLM returned empty or template-only content for {target_file}. "
                "Nothing saved."
            )

        # ── 保存 ─────────────────────────────────────────────────────────────
        target_path = run_dir / target_file
        target_path.write_text(content, encoding="utf-8")

        return ActResult(
            phase=info.phase,
            mode="auto",
            next_role=instruction.next_role,
            target_file=target_file,
            files_read=files_read,
            generated=True,
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

    def _get_provider(
        self, phase: Phase, run_dir: Path, settings: Settings
    ) -> BaseProvider:
        """
        プロバイダを取得する。

        優先順位:
        1. model-assignment.md が存在すれば AssignmentService で role を参照
        2. なければ API キーが設定されている最初のプロバイダを使用
           （Anthropic → OpenAI → Gemini）

        Raises:
            ActError: API キーが一切設定されていない場合
        """
        from ..orchestration.assignment_service import AssignmentService
        from ..legacy.providers.anthropic_provider import AnthropicProvider
        from ..legacy.providers.gemini_provider import GeminiProvider
        from ..legacy.providers.openai_provider import OpenAIProvider

        assignment_path = run_dir / "model-assignment.md"
        role = _PHASE_TO_ROLE.get(phase)

        if assignment_path.exists() and role is not None:
            service = AssignmentService(settings=settings)
            context = service.load_from_file(assignment_path, run_dir)
            provider = service.create_provider(context, role)
            if provider is not None:
                return provider
            # assignment が human 指定の場合は fallback へ

        # API キー fallback
        if settings.anthropic_api_key:
            return AnthropicProvider(
                model=settings.default_anthropic_model,
                api_key=settings.anthropic_api_key,
            )
        if settings.openai_api_key:
            return OpenAIProvider(
                model=settings.default_openai_model,
                api_key=settings.openai_api_key,
            )
        if settings.gemini_api_key:
            return GeminiProvider(
                model=settings.default_gemini_model,
                api_key=settings.gemini_api_key,
            )

        raise ActError(
            "No API key configured. Set ANTHROPIC_API_KEY (or OPENAI_API_KEY / GEMINI_API_KEY) "
            "to use apsf act."
        )
