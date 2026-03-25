"""
PhaseDetector — run ディレクトリのファイル存在からフェーズを推定する

使用例:
    from apsf.orchestration.phase_detector import PhaseDetector

    detector = PhaseDetector(Path("runs/2026-03-15_sochi-blocks_sns-post-template"))
    info = detector.detect()
    print(info.phase, info.decision_reason)
    print(info.filled_files)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Phase(str, Enum):
    SETUP_NEEDED           = "SETUP_NEEDED"           # execution-assignment.md が未記入
    GOAL_NEEDED            = "GOAL_NEEDED"
    PLAN_NEEDED            = "PLAN_NEEDED"
    IMPROVE_PLAN_OPTIONAL  = "IMPROVE_PLAN_OPTIONAL"  # v0.2: improve-plan.md が存在・未記入
    BUILD_NEEDED           = "BUILD_NEEDED"
    REVIEW_NEEDED          = "REVIEW_NEEDED"
    IMPROVE_NEEDED         = "IMPROVE_NEEDED"          # Judge フェーズ
    VERIFY_OPTIONAL        = "VERIFY_OPTIONAL"         # v0.2: verify.md が存在・未記入
    RESULT_NEEDED          = "RESULT_NEEDED"
    TRANSCRIPT_RECOMMENDED = "TRANSCRIPT_RECOMMENDED"
    COMPLETE               = "COMPLETE"


# apsf act の Human vs Auto 責務分担（1 箇所で見渡せる定義）
#
# Human が必須の phase: 内容の判断・問題定義・最終評価を人間が担う
# Auto が可能な phase : Planner / Builder / Critic の役割を LLM が担える
HUMAN_OWNED_PHASES: frozenset[Phase] = frozenset({
    Phase.SETUP_NEEDED,           # execution-assignment.md: 実行モデル定義（人間が決める）
    Phase.GOAL_NEEDED,            # goal.md: 問題定義（人間のみ）
    Phase.IMPROVE_PLAN_OPTIONAL,  # improve-plan.md: Judge スコープ定義（v0.2）
    Phase.IMPROVE_NEEDED,         # improve.md: Judge 最終判断（人間のみ）
    Phase.VERIFY_OPTIONAL,        # verify.md: 完了条件確認（v0.2）
    Phase.RESULT_NEEDED,          # result.md: 振り返り（人間のみ）
    Phase.TRANSCRIPT_RECOMMENDED, # apsf transcript コマンドへ誘導
    Phase.COMPLETE,               # 完了 - 何もしない
})

AUTO_OWNED_PHASES: frozenset[Phase] = frozenset({
    Phase.PLAN_NEEDED,    # Planner → plan.md
    Phase.BUILD_NEEDED,   # Builder → build.md
    Phase.REVIEW_NEEDED,  # Critic  → review.md
})


# フェーズ検出で走査する既知ファイル一覧（ワークフロー順）
_KNOWN_FILES: list[str] = [
    "execution-assignment.md",
    "model-assignment.md",
    "goal.md",
    "plan_review.md",
    "plan.md",
    "handoff.md",
    "build_review.md",
    "improve-plan.md",
    "build.md",
    "review.md",
    "improve_review.md",
    "improve.md",
    "verify.md",
    "result.md",
    "transcript.md",
]


@dataclass
class PhaseInfo:
    phase: Phase
    evidence: list[str]
    next_role: str
    files_to_read: list[str]
    file_to_write: str
    instruction_template: str
    handoff_hint: Optional[str] = None
    # 判定根拠フィールド（デフォルト空でも既存コードに影響しない）
    existing_files:  list[str] = field(default_factory=list)
    filled_files:    list[str] = field(default_factory=list)
    unfilled_files:  list[str] = field(default_factory=list)
    decision_reason: str = ""


class PhaseDetector:
    """
    run ディレクトリ内のファイル存在・充填状態からフェーズを推定する。

    判定基準:
    - ファイルの存在有無（_exists）
    - ファイルに意味のある内容があるか（_is_filled）:
      コメント行・区切り行を除いて 4 行以上あれば「充填済み」とみなす

    注意: この検出は推定であり、ファイルを少ししか書いていない場合は
    誤検知する可能性がある。迷ったら直接ファイルを確認すること。

    オプショナルフェーズ（IMPROVE_PLAN_OPTIONAL / VERIFY_OPTIONAL）は、
    対応ファイルが存在するが未記入の場合のみ返す。
    v0.1 フロー（これらのファイルを使わない）では検出されない。
    """

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir

    def _exists(self, filename: str) -> bool:
        return (self.run_dir / filename).exists()

    def _find_runs_root(self) -> Optional[Path]:
        """run_dir から runs/ ルートを辿る。見つからなければ None。"""
        for parent in [self.run_dir, *self.run_dir.parents]:
            if parent.name == "runs":
                return parent
        return None

    def _matches_run_template(self, filename: str) -> bool:
        """
        run ファイルが runs/_template 側テンプレートと完全一致しているか。

        start-run 直後の copied file は phase 判定・overwrite 判定のどちらでも
        「まだ実成果物ではない」と扱う。
        """
        path = self.run_dir / filename
        if not path.exists():
            return False

        runs_root = self._find_runs_root()
        if runs_root is None:
            return False

        template_path = runs_root / "_template" / filename
        if not template_path.exists():
            framework_template_path = runs_root.parent / "framework" / "templates" / filename
            if framework_template_path.exists():
                template_path = framework_template_path
            else:
                return False

        try:
            return path.read_text(encoding="utf-8") == template_path.read_text(encoding="utf-8")
        except OSError:
            return False

    @staticmethod
    def _count_meaningful_lines(text: str) -> int:
        """
        テキスト中の「意味のある行」の数を返す。

        以下を除いた行をカウントする:
        - 空行
        - HTML コメントブロック（<!-- ... --> 複数行対応）
        - Markdown 区切り行（---/***/___ 3文字以上）
        - Markdown 見出し行（# で始まる）
        - 裸の箇条書き（- のみ）
        - 未チェックのチェックボックス（- [ ] ...）
        - テーブル区切り行（|---|---|）
        - 空テーブル行（| | | 全セル空）
        - テーブルヘッダー行（次行が |---|---| の場合 -- Markdown テーブル構造）
        - "なし / none / N/A" プレースホルダー箇条書き（- なし / - none 等）
        - 太字ラベル行（**Label** / **Label**: のみ）
        - 短いプレースホルダー箇条書き（- 概要: / - H1: 等）
        - コードフェンス行（``` / ~~~）
        - 全角括弧プレースホルダー行（（...） のみ）
        - ボックス描画文字行（═══ 等）
        """
        lines = text.splitlines()
        count = 0
        in_html_comment = False

        for i, line in enumerate(lines):
            s = line.strip()

            # ── HTML comment block tracking ─────────────────────────────
            if in_html_comment:
                if "-->" in line:
                    in_html_comment = False
                continue
            if "<!--" in s:
                if "-->" not in s:
                    in_html_comment = True
                continue

            # ── 空行 ─────────────────────────────────────────────────────
            if not s:
                continue

            # ── 見出し ───────────────────────────────────────────────────
            if s.startswith("#"):
                continue

            # ── 水平区切り (---/***/___ 3文字以上) ──────────────────────
            if re.match(r'^[-*_]{3,}$', s):
                continue

            # ── 裸の箇条書き "- " ─────────────────────────────────────
            if re.match(r'^-\s*$', s):
                continue

            # ── 未チェックのチェックボックス "- [ ] ..." ────────────────
            if re.match(r'^-\s*\[\s*\]', s):
                continue

            # ── "なし / none / N/A" プレースホルダー箇条書き ─────────────
            # テンプレートの「何もない」表現（Critical: なし 等）をスキップ
            if re.match(r'^-\s*(なし|none|N/A)\s*$', s, re.IGNORECASE):
                continue

            # ── テーブル行 ───────────────────────────────────────────────
            if s.startswith('|') and s.endswith('|'):
                cells = s[1:-1].split('|')
                # テーブル区切り行: |---|---| (セルが -/:/ = /空白 のみ)
                if all(re.match(r'^[\s:\-=]+$', cell) for cell in cells):
                    continue
                # 空テーブル行: 全セルが空
                if all(cell.strip() == '' for cell in cells):
                    continue
                # テーブルヘッダー行: 次行がテーブル区切り行の場合
                # Markdown テーブル構造: ヘッダー行 → |---|---| 区切り行 → データ行
                # ヘッダー行は列名（ラベル）なのでコンテンツとは見なさない
                if i + 1 < len(lines):
                    next_s = lines[i + 1].strip()
                    if next_s.startswith('|') and next_s.endswith('|'):
                        next_cells = next_s[1:-1].split('|')
                        if all(re.match(r'^[\s:\-=]+$', cell) for cell in next_cells):
                            continue  # テーブルヘッダー行 -- スキップ

            # ── 太字ラベル行 "**Label**" / "**Label**:" ─────────────────
            if re.match(r'^\*\*[^*]+\*\*:?\s*$', s):
                continue

            # ── 短いプレースホルダー箇条書き "- 概要:" / "- H1:" ────────
            # 箇条書き記号 + 1〜6文字の非空白 + コロン のみの行
            if re.match(r'^-\s+\S{1,6}:\s*$', s):
                continue

            # ── コードフェンス行 "```" / "~~~" ───────────────────────────
            if re.match(r'^[`~]{3,}', s):
                continue

            # ── 全角括弧プレースホルダー "（...）" のみの行 ──────────────
            if re.match(r'^（.+）$', s):
                continue

            # ── ボックス描画文字行（═══ 等）───────────────────────────
            if re.match(r'^[═─━╔╗╚╝║╠╣╦╩╬]+$', s):
                continue

            count += 1

        return count

    def _is_filled(self, filename: str) -> bool:
        """ファイルに意味のある内容があるか（4 行以上）を判定する。"""
        path = self.run_dir / filename
        if not path.exists():
            return False
        if self._matches_run_template(filename):
            return False
        content = path.read_text(encoding="utf-8")
        # transcript.md はテンプレートが豊富な説明文を持つため content 行数では判定できない。
        # TranscriptGenerator が必ず "Generated:" 行を追加するので、その有無で判定する。
        if filename == "transcript.md":
            return "Generated:" in content
        return PhaseDetector._count_meaningful_lines(content) > 3

    @classmethod
    def is_meaningful_text(cls, text: str) -> bool:
        """
        テキストに意味のある内容があるかを判定する（外部向け公開 API）。

        write-phase での入力バリデーションなどに使用する。
        _is_filled と同一フィルタロジックを適用し、4 行以上で True を返す。
        """
        return cls._count_meaningful_lines(text) > 3

    def _has_any_content(self, filename: str) -> bool:
        """
        ファイルにテンプレート骨格を超えるコンテンツが 1 行以上あるかを返す。

        write-phase の上書き保護に使用する。
        _is_filled（4行以上）よりも低い閾値で、部分的な記入も検出する。
        """
        path = self.run_dir / filename
        if not path.exists():
            return False
        if self._matches_run_template(filename):
            return False
        return PhaseDetector._count_meaningful_lines(
            path.read_text(encoding="utf-8")
        ) > 0

    @staticmethod
    def _extract_planner_satisfiability(plan_text: str) -> Optional[tuple[str, str]]:
        """
        plan.md 内に Planner が明示した Satisfiability Classification があれば読む。
        """
        state_match = re.search(
            r"Classification:\s*`?(SATISFIED|EXPLORATORY|UNSATISFIED)`?",
            plan_text,
            re.IGNORECASE,
        )
        if not state_match:
            return None

        state = state_match.group(1).upper()
        rationale_match = re.search(r"Rationale:\s*(.+)", plan_text)
        unresolved_match = re.search(
            r"Required unresolved prerequisites \(if any\):\s*(.+)", plan_text
        )

        details: list[str] = []
        if rationale_match:
            details.append(rationale_match.group(1).strip())
        if unresolved_match:
            unresolved = unresolved_match.group(1).strip()
            if unresolved and unresolved.lower() not in {"none", "なし", "-"}:
                details.append(f"Required unresolved prerequisites: {unresolved}")

        return state, " ".join(details).strip()

    @staticmethod
    def _goal_requires_execution_ready(goal_text: str) -> bool:
        patterns = [
            r"strict feasibility verification",
            r"strictly verified",
            r"execution-ready",
            r"verified output",
            r"production-ready",
            r"shipped output",
            r"厳密.*実現可能性",
            r"厳密.*検証",
            r"実現可能性.*厳密",
        ]
        return any(re.search(pattern, goal_text, re.IGNORECASE) for pattern in patterns)

    @staticmethod
    def _goal_allows_exploratory(goal_text: str) -> bool:
        patterns = [
            r"allows provisional",
            r"allows investigative",
            r"allows exploratory",
            r"provisional output",
            r"investigative output",
            r"exploratory output",
            r"design-only",
            r"暫定.*許",
            r"探索.*許",
            r"調査.*許",
        ]
        return any(re.search(pattern, goal_text, re.IGNORECASE) for pattern in patterns)

    @staticmethod
    def _plan_has_unresolved_prereqs(plan_text: str) -> bool:
        patterns = [
            r"required prerequisite",
            r"unresolved",
            r"blocking",
            r"\bTBD\b",
            r"must locate",
            r"must confirm",
            r"未解決",
            r"未確定",
            r"要確認",
            r"前提.*未",
        ]
        return any(re.search(pattern, plan_text, re.IGNORECASE) for pattern in patterns)

    def classify_satisfiability(self) -> tuple[str, str]:
        """
        goal.md と plan.md から additive warning 用の satisfiability state を返す。
        Planner の明示分類があればそれを優先し、なければ軽い fallback で補完する。
        """
        if not self._is_filled("goal.md") or not self._is_filled("plan.md"):
            return "SATISFIED", ""

        goal_text = (self.run_dir / "goal.md").read_text(encoding="utf-8")
        plan_text = (self.run_dir / "plan.md").read_text(encoding="utf-8")

        declared = self._extract_planner_satisfiability(plan_text)
        if declared:
            state, rationale = declared
            if state == "SATISFIED":
                return state, ""
            if rationale:
                return state, rationale
            if state == "EXPLORATORY":
                return state, "Goal explicitly allows provisional or investigative output."
            return state, "Goal requires execution-ready output while required prerequisites remain unresolved."

        requires_ready = self._goal_requires_execution_ready(goal_text)
        allows_exploratory = self._goal_allows_exploratory(goal_text)
        unresolved = self._plan_has_unresolved_prereqs(plan_text)

        if requires_ready and unresolved:
            return (
                "UNSATISFIED",
                "Goal success criteria require execution-ready or strictly verified output, but the plan still leaves required prerequisites unresolved.",
            )
        if allows_exploratory and unresolved:
            return (
                "EXPLORATORY",
                "Goal allows provisional or investigative output, and unresolved items remain within that exploratory scope.",
            )
        return "SATISFIED", ""

    def _append_satisfiability_reason(self, info: PhaseInfo) -> PhaseInfo:
        """
        phase を変えずに decision_reason へ additive satisfiability signal を付ける。
        """
        state, message = self.classify_satisfiability()
        if state == "SATISFIED":
            return info

        marker = f"[SATISFIABILITY: {state}]"
        suffix = marker if not message else f"{marker} {message}"
        if info.decision_reason:
            info.decision_reason = f"{info.decision_reason}\n{suffix}"
        else:
            info.decision_reason = suffix
        return info

    def detect(self) -> PhaseInfo:
        """run の現在フェーズを推定して PhaseInfo を返す。"""

        # 既知ファイルを一括スキャン（デバッグ情報用）
        existing = [f for f in _KNOWN_FILES if self._exists(f)]
        filled   = [f for f in _KNOWN_FILES if self._is_filled(f)]
        unfilled = [f for f in existing if f not in filled]

        def _info(
            phase: Phase,
            evidence: list[str],
            next_role: str,
            files_to_read: list[str],
            file_to_write: str,
            instruction_template: str,
            handoff_hint: Optional[str] = None,
            decision_reason: str = "",
        ) -> PhaseInfo:
            info = PhaseInfo(
                phase=phase,
                evidence=evidence,
                next_role=next_role,
                files_to_read=files_to_read,
                file_to_write=file_to_write,
                instruction_template=instruction_template,
                handoff_hint=handoff_hint,
                existing_files=existing,
                filled_files=filled,
                unfilled_files=unfilled,
                decision_reason=decision_reason,
            )
            return self._append_satisfiability_reason(info)

        # --- SETUP ---
        # execution-assignment.md が未記入の場合でも、goal.md 以降が記入済みなら
        # セットアップは完了している（または以前のバージョンで不要だった）とみなしてスキップする。
        if not self._is_filled("execution-assignment.md"):
            if not any(self._is_filled(f) for f in ["goal.md", "plan.md", "build.md", "review.md", "result.md"]):
                return _info(
                    phase=Phase.SETUP_NEEDED,
                    evidence=["execution-assignment.md が未記入または存在しない"],
                    next_role="Human",
                    files_to_read=["framework/templates/execution-assignment.md"],
                    file_to_write="execution-assignment.md",
                    instruction_template=(
                        "run 開始前の設定が必要です。\n\n"
                        "1. execution-assignment.md を記入してください（各 role の execution type 等）\n"
                        "2. model-assignment.md が mandatory / recommended / optional のどれか判断してください。必要な run の場合だけ framework/templates/model-assignment.md から作成してください\n"
                        "3. 完了後に `apsf next <run-name>` を再実行してください"
                    ),
                    decision_reason="execution-assignment.md is missing or unfilled",
                )

        # --- GOAL ---
        if not self._is_filled("goal.md"):
            return _info(
                phase=Phase.GOAL_NEEDED,
                evidence=["execution-assignment.md 記入済み", "goal.md が未記入または存在しない"],
                next_role="Human",
                files_to_read=["framework/templates/goal.md"],
                file_to_write="goal.md",
                instruction_template=(
                    "goal.md を記入してください。\n\n"
                    "含めるべき内容:\n"
                    "- Goal Statement（何を解くか・1 文）\n"
                    "- Background（なぜ今解くか）\n"
                    "- Success Criteria（検証可能な完了条件）\n"
                    "- Notes for Planner（あれば）"
                ),
                decision_reason="execution-assignment.md filled; goal.md not filled",
            )

        # --- PLAN ---
        if not self._is_filled("plan.md"):
            return _info(
                phase=Phase.PLAN_NEEDED,
                evidence=["goal.md 記入済み", "plan.md が未記入または存在しない"],
                next_role="Planner",
                files_to_read=["goal.md", "execution-assignment.md", "plan_review.md"],
                file_to_write="plan.md",
                instruction_template=(
                    "あなたは Planner です。goal.md を読んで plan.md を作成してください。\n\n"
                    "含めるべき内容:\n"
                    "- Problem Structure（問題の分解）\n"
                    "- Selected Approach（採用アプローチと理由）\n"
                    "- Build Instructions（Builder への指示）\n"
                    "- Quality Criteria（Critic への評価軸）\n\n"
                    "完了後: Builder に追加 transfer context が必要な場合だけ handoff.md を更新してください。ファイルが無ければ framework/templates/handoff.md から作成してください。"
                ),
                handoff_hint="Builder に追加 transfer context が必要な場合だけ handoff.md（Planner → Builder）を更新すること",
                decision_reason="goal.md filled; plan.md not filled",
            )

        # --- BUILD ---
        if not self._is_filled("build.md"):
            return _info(
                phase=Phase.BUILD_NEEDED,
                evidence=["plan.md 記入済み", "build.md が未記入または存在しない"],
                next_role="Builder",
                files_to_read=["plan.md", *(["handoff.md"] if self._exists("handoff.md") else []), "build_review.md", "execution-assignment.md"],
                file_to_write="build.md",
                instruction_template=(
                    "あなたは Builder です。plan.md を読み、handoff.md がある場合は追加 transfer context として参照して build.md を作成してください。\n\n"
                    "含めるべき内容:\n"
                    "- What was built（成果物の一覧）\n"
                    "- Decisions made（採用した判断・plan からの逸脱）\n"
                    "- Open Issues（未解決事項）\n\n"
                    "完了後: Critic に追加 transfer context が必要な場合だけ handoff.md を更新してください。ファイルが無ければ framework/templates/handoff.md から作成してください。"
                ),
                handoff_hint="Critic に追加 transfer context が必要な場合だけ handoff.md（Builder → Critic）を更新すること",
                decision_reason="plan.md filled; build.md not filled",
            )

        # --- REVIEW ---
        if not self._is_filled("review.md"):
            return _info(
                phase=Phase.REVIEW_NEEDED,
                evidence=["build.md 記入済み", "review.md が未記入または存在しない"],
                next_role="Critic",
                files_to_read=["build.md", "plan.md", *(["handoff.md"] if self._exists("handoff.md") else []), "goal.md", "review_review.md"],
                file_to_write="review.md",
                instruction_template=(
                    "あなたは Critic です。build.md を評価して review.md を作成してください。\n\n"
                    "含めるべき内容:\n"
                    "- Summary（総評・採用推奨/却下推奨）\n"
                    "- Risks（Critical / Major / Minor 分類）\n"
                    "- Success Criteria Check（goal.md の成功基準との照合）\n"
                    "review_review.md がある場合は、その再レビュー指示も反映してください。\n\n"
                    "完了後: Judge に追加 transfer context が必要な場合だけ handoff.md を更新してください。ファイルが無ければ framework/templates/handoff.md から作成してください。"
                ),
                handoff_hint="Judge に追加 transfer context が必要な場合だけ handoff.md（Critic → Judge）を更新すること",
                decision_reason="build.md filled; review.md not filled",
            )

        # --- IMPROVE_PLAN_OPTIONAL (v0.2) ---
        # review.md 記入済み後に improve-plan.md が存在するが未記入の場合 → v0.2 フロー
        # v0.2: Goal → Plan → Build → Review → [Improve Plan] → Improve → Verify → Result
        # v0.1: improve-plan.md を使わない場合はここをスキップして IMPROVE_NEEDED へ進む
        if self._exists("improve-plan.md") and not self._is_filled("improve-plan.md"):
            return _info(
                phase=Phase.IMPROVE_PLAN_OPTIONAL,
                evidence=["review.md 記入済み", "improve-plan.md が存在するが未記入"],
                next_role="Judge (Human)",
                files_to_read=["review.md", *(["handoff.md"] if self._exists("handoff.md") else []), "build.md", "improve_review.md"],
                file_to_write="improve-plan.md",
                instruction_template=(
                    "あなたは Judge です。improve-plan.md を作成してください（v0.2 フェーズ）。\n\n"
                    "含めるべき内容:\n"
                    "- Improvement Scope（何を改善するか・スコープの明示）\n"
                    "- Non-scope（今回対応しない項目）\n"
                    "- Done Criteria（構造的・測定可能な完了条件）\n"
                    "- Executor Instructions（実行者への具体的な指示）\n\n"
                    "完了後: Builder または指定 executor に improve-plan.md を渡してください。"
                ),
                decision_reason="review.md filled; improve-plan.md exists but not filled",
            )

        # --- IMPROVE (Judge) ---
        if not self._is_filled("improve.md"):
            return _info(
                phase=Phase.IMPROVE_NEEDED,
                evidence=["review.md 記入済み", "improve.md が未記入または存在しない"],
                next_role="Judge (Human)",
                files_to_read=["review.md", *(["handoff.md"] if self._exists("handoff.md") else []), "build.md", "improve_review.md"],
                file_to_write="improve.md",
                instruction_template=(
                    "あなたは Judge です。review.md を確認して improve.md を記入してください。\n\n"
                    "含めるべき内容:\n"
                    "- Decision（採用 / 修正後採用 / 却下）\n"
                    "- Rationale（判断の根拠）\n"
                    "- Next Iteration Scope（次 run または次ループのスコープ）\n"
                    "improve_review.md がある場合は、その修正要求を反映してください。\n\n"
                    "採用 → result.md へ\n"
                    "修正後採用 → improve-plan.md を作成して再ループへ"
                ),
                decision_reason="review.md filled; improve.md not filled",
            )

        # --- VERIFY_OPTIONAL (v0.2) ---
        # verify.md が存在するが未記入、かつ result.md がまだ未完
        if self._exists("verify.md") and not self._is_filled("verify.md"):
            if not self._is_filled("result.md"):
                return _info(
                    phase=Phase.VERIFY_OPTIONAL,
                    evidence=["improve.md 記入済み", "verify.md が存在するが未記入"],
                    next_role="Judge (Human)",
                    files_to_read=["improve-plan.md", "build.md", *(["handoff.md"] if self._exists("handoff.md") else [])],
                    file_to_write="verify.md",
                    instruction_template=(
                        "あなたは Verifier です。verify.md を記入してください（v0.2 フェーズ）。\n\n"
                        "含めるべき内容:\n"
                        "- Done Criteria Check（improve-plan.md の完了条件ごとに Pass/Fail）\n"
                        "- Overall Verdict（全条件クリアなら合格・次フェーズへ）\n\n"
                        "注意: これは新たなレビューではなく、完了条件の照合のみを行ってください。\n"
                        "合格後: result.md を記入してください。"
                    ),
                    decision_reason="improve.md filled; verify.md exists but not filled",
                )

        # --- RESULT ---
        if not self._is_filled("result.md"):
            return _info(
                phase=Phase.RESULT_NEEDED,
                evidence=["improve.md 記入済み", "result.md が未記入または存在しない"],
                next_role="Human",
                files_to_read=["improve.md", "build.md", "goal.md"],
                file_to_write="result.md",
                instruction_template=(
                    "run を締めてください。result.md を記入してください。\n\n"
                    "含めるべき内容:\n"
                    "- Outcome（何を達成したか）\n"
                    "- Success Criteria（goal.md の成功基準の達成状況）\n"
                    "- Generalization（他の run に転用できる知見）\n"
                    "- Reusable Prompt（あれば）\n"
                    "- Framework Feedback（フレームワーク自体への気づき）\n\n"
                    "完了後: `apsf transcript <run-name>` で transcript.md を生成してください。"
                ),
                decision_reason="improve.md filled; result.md not filled",
            )

        # --- TRANSCRIPT ---
        if not self._is_filled("transcript.md"):
            return _info(
                phase=Phase.TRANSCRIPT_RECOMMENDED,
                evidence=["result.md 記入済み", "transcript.md が未生成または空"],
                next_role="Human (optional)",
                files_to_read=["result.md", "goal.md", "build.md", "review.md"],
                file_to_write="transcript.md",
                instruction_template=(
                    "run は完了しています。transcript.md の生成を推奨します（特に初回 run）。\n\n"
                    "生成方法:\n"
                    "  apsf transcript <run-name>\n\n"
                    "transcript は二次成果物です。一次記録（goal.md〜result.md）の可読化のための\n"
                    "再構成文書であり、逐語ログでも会話の再現でもありません。"
                ),
                decision_reason="result.md filled; transcript.md not generated",
            )

        # --- COMPLETE ---
        return _info(
            phase=Phase.COMPLETE,
            evidence=["All primary files filled", "transcript.md generated"],
            next_role="(none)",
            files_to_read=[],
            file_to_write="(none)",
            instruction_template="This run is complete.",
            decision_reason="All required files are filled including transcript.md",
        )
