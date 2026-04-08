"""
GateService — 最小 gate 評価 (v1)

4 gate（completeness / schema_valid / consistency / human_approved）を評価する。
呼び出し側は evaluate_all(run_dir) に run_dir を渡すだけでよい。

v1 hard block:  schema_valid  (POST-write)  — corrupt JSON → cannot proceed
                consistency   (PRE-write)   — phase regression → cannot re-enter completed phase
                                              --force で bypass 可能
v1 advisory:    completeness  — manifest entry missing from disk（外部削除で false block になりうる）
                human_approved — handoff OFFERED のまま（auto-accept が先行するため通常フローでは発生しない）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ..domain.enums import GateType, HandoffStatus

# act_service が hard block 判定に使用する定数
HARD_BLOCK_GATE_TYPES: frozenset[str] = frozenset({
    GateType.SCHEMA_VALID.value,   # POST-write: corrupt JSON → cannot proceed
    GateType.CONSISTENCY.value,    # PRE-write:  phase regression → cannot re-enter completed phase
})


class GateService:
    """
    最小 gate を評価する。

    使用例:
        results = GateService().evaluate_all(run_dir)
        hard_failures = [r for r in results if not r.passed and r.gate_type == GateType.SCHEMA_VALID.value]
        advisory_failures = [r for r in results if not r.passed and r.gate_type != GateType.SCHEMA_VALID.value]
    """

    def evaluate_all(self, run_dir: Path) -> list:
        """
        全 gate を評価して GateResult リストを返す。
        内部で ManifestRepository / RunStateRepository / HandoffRepository を自己ロードする。
        """
        from ..manifest.manifest_repository import ManifestRepository
        from ..state.run_state_repository import RunStateRepository
        from ..handoff.handoff_repository import HandoffRepository

        run_state = RunStateRepository(run_dir).load()
        manifest = ManifestRepository(run_dir).load()
        handoff = HandoffRepository(run_dir).load()

        results: list = []
        results.extend(self.evaluate_schema_valid(run_dir, run_state, manifest, handoff))
        results.extend(self.evaluate_completeness(run_dir, manifest))
        results.extend(self.evaluate_consistency(run_state, manifest))
        results.extend(self.evaluate_human_approved(run_state, handoff))
        return results

    # ── completeness ─────────────────────────────────────────────────────────

    def evaluate_completeness(self, run_dir: Path, manifest: Optional[Any]) -> list:
        """
        manifest の各 entry について実ファイルが disk 上に存在するか確認する。

        - manifest が None（ファイル不在）の場合は評価をスキップ（passed）
        - entry にある artifact ファイルが run_dir に存在しない場合 → FAILED
        """
        from .gate_result import GateResult

        if manifest is None:
            return [GateResult(
                gate_type=GateType.COMPLETENESS.value,
                passed=True,
                subject="",
                reason="",
            )]

        results = []
        for artifact_name in manifest.entries:
            artifact_path = run_dir / artifact_name
            if not artifact_path.exists():
                results.append(GateResult(
                    gate_type=GateType.COMPLETENESS.value,
                    passed=False,
                    subject=artifact_name,
                    reason=f"{artifact_name} is in manifest but not found on disk",
                ))
            else:
                results.append(GateResult(
                    gate_type=GateType.COMPLETENESS.value,
                    passed=True,
                    subject=artifact_name,
                    reason="",
                ))

        if not results:
            results.append(GateResult(
                gate_type=GateType.COMPLETENESS.value,
                passed=True,
                subject="",
                reason="",
            ))
        return results

    # ── schema_valid ─────────────────────────────────────────────────────────

    def evaluate_schema_valid(
        self,
        run_dir: Path,
        run_state: Optional[Any],
        manifest: Optional[Any],
        handoff: Optional[Any],
    ) -> list:
        """
        canonical JSON ファイルの validity と必須フィールドの型を確認する。

        確認対象:
        - run_state.json: valid JSON かつ current_phase が空でないか
        - handoff.json: valid JSON かつ status が HandoffStatus 値か
        - artifact_manifest.json: valid JSON かつ entries が dict か
        """
        from .gate_result import GateResult

        results = []
        _valid_handoff_statuses = {s.value for s in HandoffStatus}

        # run_state.json
        run_state_path = run_dir / "run_state.json"
        if run_state_path.exists():
            if run_state is None:
                results.append(GateResult(
                    gate_type=GateType.SCHEMA_VALID.value,
                    passed=False,
                    subject="run_state",
                    reason="run_state.json exists but could not be parsed",
                ))
            elif not run_state.current_phase:
                results.append(GateResult(
                    gate_type=GateType.SCHEMA_VALID.value,
                    passed=False,
                    subject="run_state",
                    reason="run_state.current_phase is empty",
                ))
            else:
                results.append(GateResult(
                    gate_type=GateType.SCHEMA_VALID.value,
                    passed=True,
                    subject="run_state",
                ))

        # handoff.json
        handoff_path = run_dir / "handoff.json"
        if handoff_path.exists():
            if handoff is None:
                results.append(GateResult(
                    gate_type=GateType.SCHEMA_VALID.value,
                    passed=False,
                    subject="handoff",
                    reason="handoff.json exists but could not be parsed",
                ))
            elif handoff.status not in _valid_handoff_statuses:
                results.append(GateResult(
                    gate_type=GateType.SCHEMA_VALID.value,
                    passed=False,
                    subject="handoff",
                    reason=f"handoff.status '{handoff.status}' is not a valid HandoffStatus value",
                ))
            else:
                results.append(GateResult(
                    gate_type=GateType.SCHEMA_VALID.value,
                    passed=True,
                    subject="handoff",
                ))

        # artifact_manifest.json
        manifest_path = run_dir / "artifact_manifest.json"
        if manifest_path.exists():
            if manifest is None:
                results.append(GateResult(
                    gate_type=GateType.SCHEMA_VALID.value,
                    passed=False,
                    subject="artifact_manifest",
                    reason="artifact_manifest.json exists but could not be parsed",
                ))
            elif not isinstance(manifest.entries, dict):
                results.append(GateResult(
                    gate_type=GateType.SCHEMA_VALID.value,
                    passed=False,
                    subject="artifact_manifest",
                    reason="artifact_manifest.entries is not a dict",
                ))
            else:
                results.append(GateResult(
                    gate_type=GateType.SCHEMA_VALID.value,
                    passed=True,
                    subject="artifact_manifest",
                ))

        if not results:
            results.append(GateResult(
                gate_type=GateType.SCHEMA_VALID.value,
                passed=True,
                subject="",
            ))
        return results

    # ── consistency ──────────────────────────────────────────────────────────

    def evaluate_consistency(
        self,
        run_state: Optional[Any],
        manifest: Optional[Any],
    ) -> list:
        """
        run_state.current_phase と manifest entries の一貫性を確認する。

        矛盾パターン（前フェーズ artifact が manifest に記録済みなのに phase が戻っている）:
        - current_phase == PLAN_NEEDED かつ manifest に plan.md がある → inconsistent
        - current_phase == BUILD_NEEDED かつ manifest に build.md がある → inconsistent
        - current_phase == REVIEW_NEEDED かつ manifest に review.md がある → inconsistent
        """
        from .gate_result import GateResult

        if run_state is None or manifest is None:
            return [GateResult(
                gate_type=GateType.CONSISTENCY.value,
                passed=True,
                subject="",
            )]

        # phase → その phase が生成する artifact のマッピング
        _phase_artifact: dict[str, str] = {
            "PLAN_NEEDED":   "plan.md",
            "BUILD_NEEDED":  "build.md",
            "REVIEW_NEEDED": "review.md",
        }

        artifact_name = _phase_artifact.get(run_state.current_phase)
        if artifact_name and artifact_name in manifest.entries:
            return [GateResult(
                gate_type=GateType.CONSISTENCY.value,
                passed=False,
                subject=artifact_name,
                reason=(
                    f"run_state.current_phase is {run_state.current_phase} "
                    f"but {artifact_name} is already recorded in manifest "
                    f"(revision={manifest.entries[artifact_name].revision})"
                ),
            )]

        return [GateResult(
            gate_type=GateType.CONSISTENCY.value,
            passed=True,
            subject="",
        )]

    # ── human_approved ───────────────────────────────────────────────────────

    def evaluate_human_approved(
        self,
        run_state: Optional[Any],
        handoff: Optional[Any],
    ) -> list:
        """
        handoff.json が OFFERED のまま（未受理）で、
        to_role が run_state.current_owner と一致する場合 → acceptance 未済を検出。

        handoff がない / run_state がない場合はスキップ（passed）。
        """
        from .gate_result import GateResult

        if handoff is None or run_state is None:
            return [GateResult(
                gate_type=GateType.HUMAN_APPROVED.value,
                passed=True,
                subject="",
            )]

        if (
            handoff.status == HandoffStatus.OFFERED.value
            and handoff.to_role == run_state.current_owner
        ):
            return [GateResult(
                gate_type=GateType.HUMAN_APPROVED.value,
                passed=False,
                subject="handoff",
                reason=(
                    f"handoff {handoff.handoff_id[:8]}... is OFFERED to {handoff.to_role} "
                    f"but not yet accepted (current_owner={run_state.current_owner})"
                ),
            )]

        return [GateResult(
            gate_type=GateType.HUMAN_APPROVED.value,
            passed=True,
            subject="handoff",
        )]
