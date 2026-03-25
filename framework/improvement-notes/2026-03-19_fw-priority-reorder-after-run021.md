# FW Improvement Note

Date: 2026-03-19
Theme: run-021 観察を反映した FW 改善優先順の再整理
Scope: APSF framework improvement backlog

---

## One-Line Summary

run-021 を踏まえると、最優先は単なる phase 境界整理ではなく、
**phase / role / artifact の責務境界を一体で締め、Critic 独立性を運用依存ではなく構造で守ること** である。

---

## Why Reorder Was Needed

既存の `2026-03-19_fw-improvement-priority-map.md` は妥当な全体像を持っているが、
run-021 では次の運用上の露出があった。

- Builder が review / improve / result まで埋めてしまい、Critic / Judge 境界が崩れた
- child run 名の typo が親 run の手書き参照で混入した
- 小さい run でもファイルセットが多く、自己点検と正式 review の区別が曖昧になりやすかった

このため、priority は「理論上の整理しやすさ」だけでなく、
**実運用で自然に壊れやすい箇所を先に締める順** に調整した方がよい。

---

## Revised Priority Order

### 1. Phase / Role / Artifact Boundary Clarification

**Why first**

- 既存 priority map の P0 を維持しつつ、対象を phase だけでなく role / artifact まで広げる
- `review / self-check / improve / result` の責務が曖昧だと、今後の template / CLI 改善もぶれる
- Builder, Critic, Judge の境界を 1 文で固定できないと、run ごとの運用規律頼みになる

**Suggested run**

- `apsf_phase-role-artifact-boundary-clarification`

**Expected deliverable**

- phase責務表
- role責務表
- artifact責務表
- `review / self-check / improve / result` の正規定義

### 2. Critic Independence Execution Guard

**Why second**

- run-021 で最も実害があったのはここ
- 「Builder と Critic を別モデルにする」は思想として正しいが、実行時ガードがない
- CLI / write-phase / execution-assignment のどこで防ぐかを早めに決めるべき

**Source**

- `2026-03-19_run021-observer-notes.md` 観察 3

**Suggested run**

- `apsf_critic-independence-execution-guard`

**Expected deliverable**

- role割当と phase書き込みの整合ルール
- `apsf act` / `apsf write-phase` の警告設計
- execution-assignment.md の補強案

### 3. CLI / Framework Alignment Audit

**Why third**

- 2 を実装しても、README / workflow / CLI 実装の導線がズレていると再び崩れる
- 実装ガードを入れる前に現状差分を可視化しておく価値が高い

**Suggested run**

- `apsf_cli-framework-alignment-audit`

### 4. Build Auto-Progression Policy

**Why fourth**

- Builder の責務境界と直接つながる
- `plan -> build` をどの条件で自動進行してよいかは、phase責務整理の直後に決めるべき
- 実験系 run 需要も既にある

**Source**

- `2026-03-19_build-auto-progression-policy.md`

**Suggested run**

- `apsf_build-auto-progression-policy`

### 5. Implementation Readiness as Explicit Gate

**Why fifth**

- build 自動進行ポリシーを入れるなら、「進んでよい条件」の明文化が必要
- readiness を plan / review の受理条件へ格上げすると、設計 run と実装 run の切り分けが安定する

**Source**

- `2026-03-19_implementation-readiness-signals.md`

**Suggested run**

- `apsf_readiness-gate-operationalization`

### 6. Template Dedup and Minimal File Set

**Why sixth**

- artifact責務を決めた後でないと、安全に削れない
- run-021 で露出した「小さい run に対するファイル数過多」を扱うにはここが本丸

**Source**

- `2026-03-19_fw-improvement-priority-map.md`
- `2026-03-19_run021-observer-notes.md` 観察 1

**Suggested run**

- `apsf_template-dedup-and-minimal-file-sets`

### 7. Parent / Child Run Topology and Child Creation Flow

**Why seventh**

- 必要性は高いが、直ちに全 run の責務境界を壊す類ではない
- 先に role / artifact / CLI 側の正規ルールを固めた方が、topology 変更の影響範囲を判断しやすい

**Source**

- `2026-03-19_parent-child-run-directory-topology.md`
- `2026-03-19_run021-observer-notes.md` 観察 2

**Suggested run**

- `apsf_parent-child-topology-and-creation-flow`

### 8. Experimental Run Patterns / Naming Rulebook

**Why later**

- 有用だが、基礎境界と運用ガードが固まった後の方が設計しやすい
- naming は parent/child topology と artifact責務の影響を受ける

---

## De-Prioritized / Already Applied

### CLI / Wrapper Minor Fixes

`2026-03-19_cli-wrapper-minor-fixes-m1-m4.md` は `Status: Applied` のため、
優先順位対象からは外す。

---

## Recommended Next Run

最初に切るなら:

**`apsf_phase-role-artifact-boundary-clarification`**

理由:

- run-021 で露出した問題の大半がここにぶら下がっている
- Critic 独立性、self-check と review の分離、result の責務まで一気通貫で整理できる
- 以降の CLI / template / auto-progression 改善の前提になる

次点:

**`apsf_critic-independence-execution-guard`**

---

## Related Notes

- `2026-03-19_fw-improvement-priority-map.md`
- `2026-03-19_run021-observer-notes.md`
- `2026-03-19_build-auto-progression-policy.md`
- `2026-03-19_implementation-readiness-signals.md`
- `2026-03-19_parent-child-run-directory-topology.md`
