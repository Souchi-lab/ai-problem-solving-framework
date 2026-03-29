"""
NextInstructionBuilder -- フェーズごとの次ロール向け実行指示を生成する

PhaseDetector が返す PhaseInfo をもとに、
次ロールにそのまま渡せる短文・詳細指示を構造化して返す。

使用例:
    from apsf.legacy.orchestration.phase_detector import PhaseDetector
    from apsf.legacy.orchestration.next_instruction_builder import NextInstructionBuilder

    info = PhaseDetector(run_dir).detect()
    instruction = NextInstructionBuilder().build(info, run_name="2026-03-17_my-run")
    print(instruction.short_instruction)
    print(instruction.detailed_instruction)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .phase_detector import Phase, PhaseInfo


@dataclass
class NextInstruction:
    """フェーズごとの次ロール向け実行指示。"""
    phase: Phase
    next_role: str
    target_file: str
    short_instruction: str    # 1 行表示用の簡潔な指示
    detailed_instruction: str  # 次ロールにそのまま渡せる詳細指示


class NextInstructionBuilder:
    """
    PhaseInfo から NextInstruction を生成する。

    各フェーズに対応するメソッド（_phase_name）が実行指示を担当する。
    CLI 表示ロジックとは独立しており、テスト可能。
    """

    def build(self, info: PhaseInfo, run_name: str = "") -> NextInstruction:
        """PhaseInfo から NextInstruction を構築して返す。"""
        _dispatch: dict[Phase, Callable[[PhaseInfo, str], NextInstruction]] = {
            Phase.SETUP_NEEDED:           self._setup,
            Phase.GOAL_NEEDED:            self._goal,
            Phase.PLAN_NEEDED:            self._plan,
            Phase.IMPROVE_PLAN_OPTIONAL:  self._improve_plan,
            Phase.BUILD_NEEDED:           self._build,
            Phase.REVIEW_NEEDED:          self._review,
            Phase.IMPROVE_NEEDED:         self._judge,
            Phase.VERIFY_OPTIONAL:        self._verify,
            Phase.RESULT_NEEDED:          self._result,
            Phase.TRANSCRIPT_RECOMMENDED: self._transcript,
            Phase.COMPLETE:               self._complete,
        }
        fn = _dispatch.get(info.phase, self._fallback)
        instruction = fn(info, run_name)
        if (
            info.phase == Phase.IMPROVE_NEEDED
            and "framework/templates/handoff.md" not in instruction.detailed_instruction
        ):
            instruction.detailed_instruction += (
                "\n\nOptional handoff path:\n"
                "If the next role needs additional transfer context, create or update handoff.md "
                "from framework/templates/handoff.md.\n"
            )
        return instruction

    # ------------------------------------------------------------------
    # Per-phase builders
    # ------------------------------------------------------------------

    def _setup(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Fill execution-assignment.md before starting the run.",
            detailed_instruction=(
                "# Setup: execution-assignment.md\n\n"
                "Run は開始できません。以下の 2 ファイルを記入してください。\n\n"
                "## 1. execution-assignment.md\n"
                "各 role の実行手段を定義します。\n"
                "テンプレート: framework/templates/execution-assignment.md\n\n"
                "記入項目:\n"
                "- Planner の executor（cli / human）と使用ツール\n"
                "- JuniorBuilder の executor と使用ツール（省略可）\n"
                "- Builder の executor と使用ツール\n"
                "- Critic の executor と使用ツール\n"
                "- Judge は human 固定\n\n"
                "## 2. model-assignment.md\n"
                "各 role に使用するモデルが run outcome に効くかを先に判断してください。\n"
                "mandatory / recommended の run だけ framework/templates/model-assignment.md から作成して記録し、optional なら省略して構いません。\n\n"
                "完了後: `apsf next " + (run_name or "<run-name>") + "` を再実行してください。"
            ),
        )

    def _goal(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Write goal.md: what to solve and how to measure success.",
            detailed_instruction=(
                "# Goal: goal.md\n\n"
                "テンプレート: framework/templates/goal.md\n\n"
                "## 必須セクション\n\n"
                "**Goal Statement**\n"
                "1 文で「何をゴールとするか」を書いてください。\n"
                "例: 「SNS 投稿用テンプレートを 5 カテゴリ × 3 パターン生成する」\n\n"
                "**Background**\n"
                "なぜ今この問題を解くのか。1〜3 文で。\n\n"
                "**Success Criteria**\n"
                "検証可能な完了条件を箇条書きで列挙してください。\n"
                "NG: 「読みやすい」「適切な品質」（主観的）\n"
                "OK: 「全 15 本が 150 文字以内」「{{変数}} が明示されている」（構造的）\n\n"
                "**Notes for Planner**（任意）\n"
                "Planner に伝えておきたい制約・前提・懸念点があれば。\n\n"
                "完了後: `apsf next " + (run_name or "<run-name>") + "` を実行してください。"
            ),
        )

    def _plan(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Planner: read goal.md and any plan_review.md, then write plan.md.",
            detailed_instruction=(
                "# Plan: plan.md\n\n"
                "あなたは Planner です。\n\n"
                "## 読むファイル\n"
                "- goal.md -- Goal Statement / Background / Success Criteria\n"
                "- execution-assignment.md -- 各 role の実行手段\n"
                "- plan_review.md -- 再プラン依頼がある場合のレビュー指摘\n\n"
                "## 書くファイル\n"
                "plan.md（テンプレート: framework/templates/plan.md）\n\n"
                "## 記入項目\n"
                "1. **Problem Structure**: 問題を構成要素に分解してください\n"
                "2. **Selected Approach**: 採用するアプローチと選択理由\n"
                "3. **Build Instructions**: Builder が迷わない粒度の具体的な指示\n"
                "4. **Quality Criteria**: Critic が評価に使う軸\n\n"
                "## しないこと\n"
                "- 成果物の生成（それは Builder の責務）\n"
                "- goal.md の成功基準を変更すること\n"
                "- plan_review.md がある場合に、その指摘を無視すること\n\n"
                "## 完了後\n"
                "Builder に追加 transfer context が必要な場合だけ handoff.md を更新してください。\n"
                "ファイルが無ければ framework/templates/handoff.md から作成してください。\n"
                "書く場合は「何が決まったか」「何が未決か」「Builder が最初に確認すべきこと」を簡潔に記録。"
            ),
        )

    def _improve_plan(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        handoff_line = (
            "- handoff.md -- 存在する場合だけ読む追加 transfer context\n"
            if "handoff.md" in info.files_to_read
            else ""
        )
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Judge: define improvement scope and done criteria in improve-plan.md (v0.2).",
            detailed_instruction=(
                "# Improve Plan: improve-plan.md (v0.2 フェーズ)\n\n"
                "あなたは Judge です。\n\n"
                "## 読むファイル\n"
                "- review.md -- Critic の指摘（Critical / Major / Minor）\n"
                + handoff_line +
                "- build.md -- 現状の成果物\n\n"
                "## 書くファイル\n"
                "improve-plan.md（テンプレート: framework/templates/improve-plan.md）\n\n"
                "## 記入項目\n"
                "1. **Improvement Scope**: 今回改善する範囲を明示する\n"
                "2. **Non-scope**: 今回は対応しない項目（スコープ外を明示）\n"
                "3. **Done Criteria**: 構造的・測定可能な完了条件\n"
                "   例: 「全テンプレートの CTA が 30 文字以内」「感嘆符が含まれない」\n"
                "4. **Executor Instructions**: 実行者への具体的な手順書\n\n"
                "## 設計のポイント\n"
                "- Done Criteria は「良いか悪いか」ではなく「あるかないか」で判定できる形に\n"
                "- 実行者が他のファイルを調べ直さなくて済むよう、必要情報を Improve Plan に埋め込む\n\n"
                "## 完了後\n"
                "Builder または指定 executor に improve-plan.md を渡してください。"
            ),
        )

    def _build(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        handoff_line = (
            "- handoff.md -- 存在する場合だけ読む追加 transfer context\n"
            if "handoff.md" in info.files_to_read
            else ""
        )
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Builder: read plan.md, optional handoff.md, and any build_review.md, then write build.md.",
            detailed_instruction=(
                "# Build: build.md\n\n"
                "あなたは Builder です。\n\n"
                "## 読むファイル\n"
                "- plan.md -- Problem Structure / Selected Approach / Build Instructions\n"
                + handoff_line +
                "- build_review.md -- 再build 時の修正依頼がある場合だけ読む補助文書\n"
                "- execution-assignment.md -- あなたの executor / tool 設定\n\n"
                "## 書くファイル\n"
                "build.md（テンプレート: framework/templates/build.md）\n\n"
                "## 記入項目\n"
                "1. **What was built**: 成果物の一覧（ファイルパス・内容サマリー）\n"
                "2. **Decisions made**: 採用した判断、plan からの逸脱とその理由\n"
                "3. **Open Issues**: 未解決事項（Critic に判断を委ねるものを明記）\n\n"
                "## しないこと\n"
                "- 問題の再定義・plan の変更\n"
                "- build_review.md の指摘を無視した再build\n"
                "- 実コードや durable artifact を build.md に埋め込むこと\n"
                "- Critic の評価を先取りした自己評価\n\n"
                "## 完了後\n"
                "Critic に追加 transfer context が必要な場合だけ handoff.md を更新してください。\n"
                "ファイルが無ければ framework/templates/handoff.md から作成してください。\n"
                "書く場合は「何が完成したか」「何を重点評価してほしいか」「未決事項」を記載。"
            ),
        )

    def _review(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        handoff_line = (
            "- handoff.md -- 存在する場合だけ読む追加 transfer context（重点評価箇所・未決事項）\n"
            if "handoff.md" in info.files_to_read
            else ""
        )
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Critic: evaluate build.md and any review_review.md, then classify findings as Critical/Major/Minor.",
            detailed_instruction=(
                "# Review: review.md\n\n"
                "あなたは Critic です。\n\n"
                "## 読むファイル\n"
                "- build.md -- 評価対象の成果物\n"
                "- plan.md -- 意図・設計方針（逸脱判定の基準）\n"
                "- goal.md -- 成功基準（照合先）\n"
                + handoff_line +
                "- review_review.md -- 再レビュー時だけ読む補助文書\n\n"
                "## 書くファイル\n"
                "review.md（テンプレート: framework/templates/review.md）\n\n"
                "## 記入項目\n"
                "1. **Summary**: 採用推奨 / 修正後採用 / 却下 の総評（1〜2 文）\n"
                "2. **Risks**: 各指摘を以下の 3 段階で分類\n"
                "   - Critical: 採用不可の欠陥（これがあれば却下）\n"
                "   - Major: 修正が必要だが修正後採用可\n"
                "   - Minor: あったほうがよい改善（次 run でも可）\n"
                "3. **Success Criteria Check**: goal.md の成功基準を 1 件ずつ照合\n\n"
                "## 判断の閾値\n"
                "- Critical / Major がゼロなら採用推奨\n"
                "- Critical があれば必ず却下推奨\n"
                "- review_review.md がある場合は、その Requested Revisions を無視しない\n"
                "- ただし review_review.md は補助文書であり、review.md を置き換えない\n\n"
                "## 完了後\n"
                "Judge に追加 transfer context が必要な場合だけ handoff.md を更新してください。\n"
                "ファイルが無ければ framework/templates/handoff.md から作成してください。\n"
                "採用推奨 / 修正後採用推奨 / 却下推奨 と理由を明記。"
            ),
        )

    def _judge(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        handoff_line = (
            "- handoff.md -- 存在する場合だけ読む追加 transfer context\n"
            if "handoff.md" in info.files_to_read
            else ""
        )
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Judge: read review.md and decide adopt/revise/reject in improve.md.",
            detailed_instruction=(
                "# Judge Decision: improve.md\n\n"
                "あなたは Judge です。\n\n"
                "## 読むファイル\n"
                "- review.md -- Critic の評価・指摘（Critical / Major / Minor）\n"
                + handoff_line +
                "- build.md -- 実際の成果物（必要に応じて確認）\n"
                "- improve_review.md -- 再improve 用の修正メモ（存在する場合のみ）\n\n"
                "## 書くファイル\n"
                "improve.md（テンプレート: framework/templates/improve.md）\n\n"
                "## 記入項目\n"
                "1. **Decision**: 採用 / 修正後採用 / 却下\n"
                "2. **Rationale**: 判断の根拠（Critical/Major の件数と対応方針）\n"
                "3. **Next Iteration Scope**: 次 run または次ループで対応するスコープ\n\n"
                "## 判断の目安\n"
                "- Critical なし + Major なし → 採用\n"
                "- Critical なし + Major あり → 修正後採用（次 run で対応）\n"
                "- Critical あり → 却下（再 Build）\n\n"
                "improve_review.md がある場合は、その Requested Revisions を反映して improve.md を更新すること。\n"
                "ただし improve_review.md は補助メモであり、canonical artifact は improve.md のままです。\n\n"
                "## 完了後\n"
                "採用 → result.md を記入して run を締める\n"
                "修正後採用 → improve-plan.md を作成して再ループへ（v0.2）"
            ),
        )

    def _verify(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        handoff_line = (
            "- handoff.md -- 存在する場合だけ読む追加 transfer context\n\n"
            if "handoff.md" in info.files_to_read
            else "\n"
        )
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Verify: check done criteria pass/fail against build result (v0.2).",
            detailed_instruction=(
                "# Verify: verify.md (v0.2 フェーズ)\n\n"
                "あなたは Verifier です。\n\n"
                "## 読むファイル\n"
                "- improve-plan.md -- Done Criteria（照合先）\n"
                "- build.md -- 検証対象の成果物\n"
                + handoff_line +
                "## 書くファイル\n"
                "verify.md（テンプレート: framework/templates/verify.md）\n\n"
                "## 記入項目\n"
                "improve-plan.md の Done Criteria を 1 件ずつ照合してください。\n"
                "各条件に対して Pass / Fail と根拠を記録してください。\n\n"
                "## 重要な制約\n"
                "- これは新たなレビューではありません\n"
                "- improve-plan.md の Done Criteria に書かれた条件の照合のみを行ってください\n"
                "- 範囲外の改善点は記録しない（次 run のスコープへ）\n\n"
                "## 完了後\n"
                "全条件 Pass → result.md を記入して run を締める\n"
                "Fail あり → Judge に報告して再 Improve へ"
            ),
        )

    def _result(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Write result.md to close this run and capture learnings.",
            detailed_instruction=(
                "# Result: result.md\n\n"
                "run を締めてください。\n\n"
                "テンプレート: framework/templates/result.md\n\n"
                "## 記入項目\n"
                "1. **Outcome**: 何を達成したか（1〜2 文）\n"
                "2. **Success Criteria**: goal.md の成功基準を 1 件ずつ 達成/未達/部分 で記録\n"
                "3. **Generalization**: 他の run に転用できる知見・パターン\n"
                "   例: 「目的カテゴリを先に分類すると生成物の網羅性が上がる」\n"
                "4. **Reusable Prompt**: 再利用できるプロンプトがあれば\n"
                "5. **Framework Feedback**: APSF 自体への改善提案・気づき\n\n"
                "## 完了後\n"
                "`apsf transcript " + (run_name or "<run-name>") + "` で transcript.md を生成してください。\n"
                "runs/README.md のテーブルに今回の run を追記してください。"
            ),
        )

    def _transcript(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        cmd = "apsf transcript " + (run_name or "<run-name>")
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Run is complete. Generate transcript.md (recommended).",
            detailed_instruction=(
                "# Run Complete: transcript.md の生成を推奨します\n\n"
                "run はすべての一次記録ファイルが揃っています。\n\n"
                "## transcript.md とは\n"
                "一次記録（goal.md〜result.md）を役割別の発言形式で再構成した可読化文書。\n"
                "逐語ログでも会話の再現でもありません。正確な情報は一次記録を参照してください。\n\n"
                "## 生成方法\n"
                f"  {cmd}\n\n"
                "## 生成後の推奨アクション\n"
                "- runs/README.md のテーブルに transcript 生成済みを記録する\n"
                "- result.md の Generalization を framework/overview.md のパターンに反映する\n"
                "- 必要なら framework/pattern-application-checklist.md を更新する"
            ),
        )

    def _complete(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction="Run complete.",
            detailed_instruction=(
                "# Run Complete\n\n"
                "この run はすべて完了しています。\n\n"
                "## 次の候補アクション（任意）\n"
                "- result.md の Generalization を framework/overview.md のパターンに反映する\n"
                "- runs/README.md のテーブルに今回の run を追記する\n"
                "- 次の run を開始する: `apsf start-run <case-key>_<topic>`\n"
                "- framework/pattern-application-checklist.md を確認して次 run の設計に活かす"
            ),
        )

    def _fallback(self, info: PhaseInfo, run_name: str) -> NextInstruction:
        """未知のフェーズへのフォールバック。"""
        return NextInstruction(
            phase=info.phase,
            next_role=info.next_role,
            target_file=info.file_to_write,
            short_instruction=f"Phase: {info.phase.value}",
            detailed_instruction=info.instruction_template,
        )
