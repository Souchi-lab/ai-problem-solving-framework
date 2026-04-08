# APSF Agent OS v1 実装タスク分解ドラフト

## 1. 目的

本ドキュメントは、`APSF Agent OS v1 Migration Adoption Memo` で合意した移行方針を、実装可能なタスク単位に分解するためのドラフトである。

この段階で固定したいのは、方針そのものではなく、

- 誰が
- どのファイルを
- どの順で
- どこまで触るか

である。

v1 の目的は、APSF を一気に完成させることではない。  
まずは **write-safety-first / artifact-first / minimal-state** の原則で、壊れにくい実行基盤へ移行する。

---

## 2. 実装方針の前提

今回の実装は、以下を前提とする。

- v1 は **state-first ではなく write-safety-first**
- raw write を残したまま canonical metadata を増やさない
- `phase_detector` は最終的に advisory に落とす
- Claude-Codex 正式委譲は、contract が揃うまで本格導入しない
- v1 では parallel execution をやらない
- ただし **single-writer lock は v1 必須**

---

## 3. 実装ステップ一覧

1. Step 1 write path unification
2. Step 2 ownership policy + enums
3. Step 3 minimal run_state
4. Step 4 handoff canonicalization
5. Step 5 artifact manifest
6. Step 6 minimal gates
7. Step 7 `phase_detector` advisory 化

---

## 4. Step 1: write path unification

### 目的

全 canonical artifact 書き込みを、1つの repository 経由に寄せる。  
以後、raw `write_text()` 直書きを原則禁止する。

### 主担当

- Builder 実装担当
- Critic は raw write 残存チェック担当

### 対象ファイル候補

- `src/apsf/legacy/orchestration/act_service.py`
- `src/apsf/legacy/cli/main.py`
- `src/apsf/legacy/storage/markdown_repository.py`
- `src/apsf/legacy/orchestration/transcript_generator.py`
- `src/apsf/legacy/orchestration/handoff_service.py`
- 必要に応じて新設:
  - `src/apsf/core/storage/artifact_repository.py`

### このステップでやること

- canonical artifact 書き込み口を `ArtifactRepository` に集約する
- safe write を導入する
  - temp file write
  - atomic rename
  - checksum hook
  - single-writer lock
- 既存 raw write を repository 呼び出しへ置換する
- `write-phase` 相当の保存処理を repository 経由に寄せる

### このステップでまだやらないこと

- manifest の本格運用
- gate 判定
- 複雑な ownership 判定
- phase canonicalization

### 完了条件

- canonical artifact を保存する経路が repository 経由に統一されている
- `write_text()` 直書きが canonical path に残っていない
- lock 付き safe write が最低1本の共通実装になっている

### テスト

同時書き込みテストは Step 1 完了条件の検証に必要なため、Step 1 と並走して作成する。

### レビュー観点

- raw write の取りこぼしがないか
- temp rename と lock の責務が分散していないか
- transcript / handoff 系の例外 path が残っていないか

---

## 5. Step 2: ownership policy + enums

### 目的

artifact の ownership を、実装前提として明文化する。  
この段階では「完全な metadata 運用」より先に、**ルールを固定する**。

### 主担当

- Planner / Design 担当
- Builder は enum / policy 実装
- Critic は cross-role overwrite の抜け確認

### 対象ファイル候補

- `src/apsf/core/domain/models.py`
- `src/apsf/legacy/cli/role_rules.py`
- `src/apsf/core/domain/ownership.py`（新設候補）
- `src/apsf/core/domain/enums.py`（新設候補）

### 先に固定する enum

- `RunStatus`
- `ArtifactStatus`
- `HandoffStatus`
- `GateType`

### 先に固定する ownership contract

- `owner_role`
- `writer_agent`
- `finalizer_role`
- `allowed_writers`
- `requires_handoff_from`
- `requires_approval_from`

### このステップでやること

- cross-role overwrite 禁止をデフォルトにする
- `--force` を縮小する
- override は human-only + reason mandatory に寄せる
- artifact ごとの canonical writer role を定義する
- finalizer role を定義する

### 補足

Schema defaults はこの段階で固定する。  
それらは **Step 5 で manifest が入った時点で enforced ownership rules になる**。

### このステップでまだやらないこと

- manifest による永続記録
- handoff acceptance の厳格運用
- state transition との完全統合

### 完了条件

- どの artifact をどの role が書けるかが enum / policy として固定されている
- `--force` による cross-role override が弱くなっている
- ownership 契約がコード上の参照点を持っている

### レビュー観点

- policy だけ定義して enforcement が空文化していないか
- human override の理由記録が抜けていないか
- `role_rules` 側との二重管理が起きていないか

---

## 6. Step 3: minimal run_state

### 目的

phase truth を file heuristic から切り離し、最小 canonical state を持つ。

### 主担当

- Builder 実装担当
- Critic は state / file divergence 観点でレビュー

### 対象ファイル候補

- `src/apsf/core/domain/models.py`
- `src/apsf/core/state/run_state.py`（新設候補）
- `src/apsf/legacy/orchestration/act_service.py`
- `src/apsf/legacy/orchestration/pipeline.py`
- `src/apsf/legacy/orchestration/phase_detector.py`

### 最小項目

- `run_id`
- `current_phase`
- `phase_status`
- `current_owner`
- `retry_count`
- `last_error`
- `active_handoff_id`

### このステップでやること

- `run_state.json` を導入する
- 保存と読み取りを repository / state service 経由にする
- phase 判定の正本を `run_state.json` に寄せる
- `phase_detector` はまだ残すが、canonical ではなく補助扱いに近づける

### このステップでまだやらないこと

- artifact 単位の細粒度 state
- cross-run ledger
- GUI 連携

### 完了条件

- `run_state.json` が run の canonical phase truth になっている
- `act_service` などが phase を heuristic ではなく state から参照している
- rerun 時に `phase_status` と `retry_count` を扱える

### レビュー観点

- state と実ファイルの乖離ポイントが残っていないか
- run_state が artifact truth を過剰に重複していないか
- current_owner と ownership policy の責務がぶつかっていないか

---

## 7. Step 4: handoff canonicalization

### 目的

handoff を自由文メモから、機械可読な委譲情報へ格上げする。

### 主担当

- Builder 実装担当
- Critic は stale handoff / acceptance 抜け確認

### 対象ファイル候補

- `src/apsf/legacy/orchestration/handoff_service.py`
- `src/apsf/core/domain/handoff.py`（新設候補）
- `src/apsf/core/storage/handoff_repository.py`（新設候補）

### 最小項目

- `handoff_id`
- `from_role`
- `to_role`
- `artifact_scope`
- `status`
- `accepted_by_next_role`
- `supersedes`
- `created_at`
- `accepted_at`
- `proceed_without_handoff_reason`

### このステップでやること

- `handoff.json` を正本にする
- `handoff.md` は render / view 扱いにする
- downstream role 実行前に handoff 状態を確認できるようにする
- stale handoff を supersede できるようにする

### このステップでまだやらないこと

- 高度な handoff routing
- 複数 handoff の並列制御
- queue 的な受け渡し

### 完了条件

- handoff 正本が `handoff.json` に移っている
- next role が machine-readable に判断できる
- handoff acceptance の有無が追跡できる

### レビュー観点

- acceptance が実質 optional のままになっていないか
- supersedes の扱いが曖昧で stale handoff が残らないか
- human が handoff なしで進めた場合の理由が残るか

---

## 8. Step 5: artifact manifest

### 目的

artifact を「ただのファイル」ではなく、状態を持つ管理対象にする。

### 主担当

- Builder 実装担当
- Critic は stale manifest / ownership drift / checksum drift 確認

### 対象ファイル候補

- `src/apsf/core/storage/artifact_repository.py`
- `src/apsf/core/domain/artifact.py`
- `src/apsf/legacy/storage/markdown_repository.py`
- `src/apsf/legacy/orchestration/act_service.py`

### 最小項目

- `artifact_name`
- `artifact_type`
- `owner_role`
- `written_by`
- `status`
- `checksum`
- `updated_at`
- `finalized_at`
- `finalized_by`
- `revision`
- `source_handoff_id`

### このステップでやること

- `artifact_manifest.json` を導入する
- canonical write のたびに manifest を自動更新する
- artifact status を持つ
- ownership policy と接続する
- `result.md exists == complete` のような判定を廃止方向に寄せる

### 重要ルール

**manifest 導入と全 canonical write path 更新を同一 PR に入れる。**

### このステップでまだやらないこと

- 高度な差分可視化
- cross-run artifact 分析
- publish manifest までの一般化

### 完了条件

- artifact 正本が manifest で追える
- すべての canonical write が manifest を更新する
- ownership / finalization / revision が追跡できる

### レビュー観点

- raw write の生き残りで manifest が stale にならないか
- `finalized_at` だけあって `finalized_by` が抜けていないか
- `source_handoff_id` が空文化していないか

---

## 9. Step 6: minimal gates

### 目的

`plan.md` の文章ルールを脱し、停止条件を機械評価可能にする。

### 主担当

- Planner / Design 担当
- Builder 実装担当
- Critic は false pass / false block 観点

### 対象ファイル候補

- `src/apsf/core/gates/`（新設候補）
- `src/apsf/legacy/orchestration/pipeline.py`
- `src/apsf/legacy/orchestration/phase_detector.py`
- `src/apsf/core/domain/gates.py`

### 最小 gate

- `completeness`
- `schema_valid`
- `consistency`
- `human_approved`

### このステップでやること

- structural gate を実装する
- artifact 保存時または phase 進行時に gate を評価する
- block 時は `run_state` に反映する
- Claude-Codex 委譲時の最低停止条件を持つ

### このステップでまだやらないこと

- semantic quality gate
- model quality scoring
- auto-approval

### 完了条件

- incomplete artifact が final に進めない
- schema invalid write を止められる
- human approval が必要な箇所で止まれる

### レビュー観点

- gate 判定責務が repository / state / pipeline に散っていないか
- consistency gate が artifact / state / handoff のどれを参照するか明確か
- false positive で運用を詰まらせないか

---

## 10. Step 7: `phase_detector` advisory 化

### 目的

heuristic routing を source of truth から降ろし、互換補助診断レイヤにする。

### 主担当

- Builder 実装担当
- Critic は backward compatibility 確認

### 対象ファイル候補

- `src/apsf/legacy/orchestration/phase_detector.py`
- `src/apsf/legacy/storage/run_repository.py`
- `src/apsf/legacy/orchestration/act_service.py`

### このステップでやること

- canonical 判定を `run_state.json` + `artifact_manifest.json` に置く
- `phase_detector` は advisory signal 扱いに下げる
- UI / diagnosis 用の補助出力として残す
- 旧判定ロジック依存を段階的に外す

### 移行条件

**Step 7 は Step 3 と同じ release、または直後の PR で行う。別 sprint にしない。**

### このステップでまだやらないこと

- detector 高度化
- router 全面自動化
- viewer 完全統合

### 完了条件

- phase の正本判定が heuristic に依存していない
- `phase_detector` を消さなくても、消しても canonical flow が壊れない
- legacy 互換の役割が明確になっている

### レビュー観点

- 旧 completion semantics が残っていないか
- `run_repository` と state 判定の分裂が再発していないか
- advisory と canonical の境界が曖昧でないか

---

## 11. 横断タスク

### A. テスト整備

各 step で最低限必要。

- 同時書き込み
- partial write 後 rerun
- stale handoff
- cross-role overwrite
- manifest stale 検知
- run_state / artifact / handoff の整合性

### B. legacy → core 移行方針

- 新しい型 / schema / repository は原則 `core/` に置く
- `legacy/` は段階的に `core/` を参照する
- 新機能を legacy に直置きしない

### C. Claude-Codex contract 下準備

正式委譲前に少なくとも以下を固定する。

#### input contract

- `run_id`
- `phase`
- `target_artifact`
- `read_set`
- `write_set`
- `owner_role`
- `allowed_writer_identity`
- `active_handoff_id`
- `expected_output_schema`
- `forbidden_artifacts`

#### output contract

- `artifact_name`
- `artifact_content`
- `artifact_status`
- `execution_status`
- `warnings`
- `requires_handoff_update`
- `requires_human_approval`
- `decision_log`

#### abort / interruption contract

- `aborted`
- `partial_output_present`
- `safe_to_retry`
- `cleanup_required`

---

## 12. v1 の境界

### v1 に入れる

- safe write
- single-writer lock
- ownership policy
- minimal run state
- structured handoff
- artifact manifest
- structural gates
- advisory detector 化

### v1 に入れない

- advanced parallel execution
- queue / worker pool
- semantic quality gate
- model-specific gate
- auto-approval
- full viewer integration
- cross-run ledger
- advanced router automation

---

## 13. 最終メッセージ

この分解の目的は、APSF を一気に完成させることではない。  
まずは **「推測のシステム」から「保存と状態が正しいシステム」へ移す** ことが目的である。

そのための合言葉は変わらない。

> **正本を増やす前に、保存を正す**

---

## 14. Progress Snapshot

### Completed

- Step 1: write path unification
  - canonical write を `ArtifactRepository` 経由へ一本化
  - safe write と single-writer lock を導入
- Step 2: ownership policy + enums
  - `ownership.py` を canonical source に固定
  - `role_rules.py` を adapter 化
  - ownership hook を `ArtifactRepository` に接続
- Step 3: minimal run_state
  - `RunState` / `RunStateRepository` を導入
  - `ActService` を state-first routing に変更
  - `phase_detector` は non-canonical 明記まで完了

### Next

- Step 7: `phase_detector` advisory 化
  - Step 3 と同 release または直後 PR で実施
- Step 4: handoff canonicalization
- Step 5: artifact manifest
- Step 6: minimal gates
