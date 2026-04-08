"""
APSF Agent OS v1 — artifact ownership policy (canonical layer)

ArtifactOwnershipPolicy がどの artifact を誰が書けるかの canonical 定義。
role_rules.py はこのモジュールを読んで enforcement を行う adapter。

設計方針:
- この dict が ownership の single source of truth
- artifact_manifest.json (Step 5) が入った際もここを参照する
- role_rules.py の ROLE_FORBIDDEN はここから導出する（手書き不要）

フィールド説明:
- owner_role:             この artifact の canonical な所有 role
- allowed_writers:        書き込みが許可された role 名のタプル
- finalizer_role:         final status を付与できる role
- requires_handoff_from:  こ�� artifact を書く前に必要な handoff の from_role（Step 4 以降）
- requires_approval_from: final 前に承認が必要な role（Step 6 以降）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ArtifactOwnershipPolicy:
    artifact_name:          str
    owner_role:             str
    allowed_writers:        tuple[str, ...]
    finalizer_role:         str
    requires_handoff_from:  Optional[str] = None
    requires_approval_from: Optional[str] = None


# ---------------------------------------------------------------------------
# Canonical ownership defaults
#
# allowed_writers に含まれない role が書こうとした場合 = cross-role overwrite 違反。
# ---------------------------------------------------------------------------
ARTIFACT_OWNERSHIP_DEFAULTS: dict[str, ArtifactOwnershipPolicy] = {
    "plan.md": ArtifactOwnershipPolicy(
        artifact_name="plan.md",
        owner_role="Planner",
        allowed_writers=("Planner",),
        finalizer_role="Planner",
    ),
    "build.md": ArtifactOwnershipPolicy(
        artifact_name="build.md",
        owner_role="Builder",
        allowed_writers=("Builder",),
        finalizer_role="Builder",
        requires_handoff_from="Planner",
    ),
    "review.md": ArtifactOwnershipPolicy(
        artifact_name="review.md",
        owner_role="Critic",
        allowed_writers=("Critic",),
        finalizer_role="Critic",
        requires_handoff_from="Builder",
    ),
    "handoff.md": ArtifactOwnershipPolicy(
        artifact_name="handoff.md",
        owner_role="Builder",
        allowed_writers=("Builder", "Planner"),
        finalizer_role="Builder",
    ),
    "improve.md": ArtifactOwnershipPolicy(
        artifact_name="improve.md",
        owner_role="Human",
        allowed_writers=("Human",),
        finalizer_role="Human",
        requires_approval_from="Human",
    ),
    "result.md": ArtifactOwnershipPolicy(
        artifact_name="result.md",
        owner_role="Human",
        allowed_writers=("Human",),
        finalizer_role="Human",
    ),
    "execution-assignment.md": ArtifactOwnershipPolicy(
        artifact_name="execution-assignment.md",
        owner_role="Human",
        allowed_writers=("Human", "Planner"),
        finalizer_role="Human",
    ),
}


def get_policy(artifact_name: str) -> Optional[ArtifactOwnershipPolicy]:
    """artifact 名に対応する ownership policy を返す。定義なければ None。"""
    return ARTIFACT_OWNERSHIP_DEFAULTS.get(artifact_name)


def is_allowed_writer(role: str, artifact_name: str) -> bool:
    """role が artifact_name に書き込み可能かどうかを返す。policy 未定義の場合は True（寛容）。"""
    policy = get_policy(artifact_name)
    if policy is None:
        return True
    return role in policy.allowed_writers
