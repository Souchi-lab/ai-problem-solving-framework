"""
GateResult — 単一 gate 評価の結果

gate_type / passed / subject / reason を持つ。
GateService が list[GateResult] を返す。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GateResult:
    """
    単一 gate 評価の結果。

    Fields:
        gate_type: GateType value ("completeness" / "schema_valid" / "consistency" / "human_approved")
        passed:    True if gate passed
        subject:   artifact_name / "handoff" / "run_state" / "" （gate の評価対象）
        reason:    block reason（passed=True のとき ""）
    """

    gate_type: str
    passed:    bool
    subject:   str = ""
    reason:    str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_type": self.gate_type,
            "passed":    self.passed,
            "subject":   self.subject,
            "reason":    self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GateResult":
        """前方互換デシリアライズ。欠損フィールドはデフォルト値で補完。"""
        return cls(
            gate_type=data.get("gate_type", ""),
            passed=bool(data.get("passed", True)),
            subject=data.get("subject", ""),
            reason=data.get("reason", ""),
        )
