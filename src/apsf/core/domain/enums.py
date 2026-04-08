"""
APSF Agent OS v1 — canonical enum 定義

RunStatus / ArtifactStatus / HandoffStatus / GateType を一箇所で固定する。
これらは run_state.json / artifact_manifest.json / handoff.json が導入された際に
schema の型として使われる。

v1 時点では serialization 先ファイルはまだ存在しないが、
コード上の参照点として先に固定する。
"""

from __future__ import annotations

from enum import Enum


class RunStatus(str, Enum):
    NOT_STARTED           = "not_started"
    IN_PROGRESS           = "in_progress"
    BLOCKED               = "blocked"
    RETRYABLE_FAILURE     = "retryable_failure"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    COMPLETED             = "completed"
    SUPERSEDED            = "superseded"


class ArtifactStatus(str, Enum):
    MISSING    = "missing"
    DRAFT      = "draft"
    GENERATED  = "generated"
    REVIEWED   = "reviewed"
    FINAL      = "final"
    SUPERSEDED = "superseded"
    INVALID    = "invalid"


class HandoffStatus(str, Enum):
    DRAFT      = "draft"
    OFFERED    = "offered"
    ACCEPTED   = "accepted"
    REJECTED   = "rejected"
    SUPERSEDED = "superseded"


class GateType(str, Enum):
    COMPLETENESS   = "completeness"
    SCHEMA_VALID   = "schema_valid"
    CONSISTENCY    = "consistency"
    HUMAN_APPROVED = "human_approved"
