# APSF Planning Patterns

APSF で `plan.md` を書くときの primary pattern を整理するための参照資料。
pattern は planner の思考補助であり、厳密な分類器ではない。まず 1 つの primary pattern を選び、必要な場合だけ secondary pattern を補助的に使う。

---

## How To Use

1. 今回の run の主目的を 1 文で言い切る。
2. `P-01` から `P-08` の中から primary pattern を 1 つ選ぶ。
3. 必要な場合のみ secondary pattern を 1 つ補助的に併記する。
4. 選んだ pattern を使って `Problem Structure`、`Execution Plan`、`Implementation Readiness` を具体化する。

> **実行手順が必要な場合**: `framework/skills/planning-patterns.md` を参照する。このファイルは概念定義であり、スキルファイルが「plan.md を書くときの適用手順」を担う。

---

## Readiness Connection

run-016 で導入した `Implementation Readiness` は pattern と切り離して使うものではない。pattern ごとに build 前に確定しているべき論点が少し違う。

- `P-01 Feature Implementation`
  API / data shape、変更対象ファイル、テスト観点を build 前に固定する。
- `P-02 Bug Fix`
  再現条件、期待挙動、局所修正範囲、回帰確認点を build 前に固定する。
- `P-03 Refactoring`
  挙動維持の境界、対象モジュール、非目的を先に固定する。
- `P-04 Migration`
  移行単位、legacy fallback、cross-reference 更新範囲を先に固定する。
- `P-05 Document / Template Update`
  反映対象、非対象、既存文章との整合点を先に固定する。
- `P-06 Design-only`
  実装に持ち込まないこと、決めるべき設計論点、handoff 先を先に固定する。
- `P-07 Retrospective / Analysis`
  評価対象、比較軸、記録粒度を先に固定する。
- `P-08 Research / Discovery`
  探索母集団、評価軸、shortlist 条件を先に固定する。

特に `P-01` と `P-04` は run-016 の checklist と結びつきが強い。`変更対象ファイルの列挙` と `検証観点の事前明示` が曖昧なまま build に入らない。

---

## P-01 Feature Implementation

- Purpose: 新機能や新能力を実装する。
- Typical Input: 仕様、既存設計、対象コード、制約条件。
- Typical Output: 実装、テスト、必要な文書更新。
- Recognition Signals:
  - 新しい API、command、workflow、artifact が増える。
  - 既存挙動の維持よりも新規能力の追加が主目的。
- Problem Structure Shape:
  - 仕様確定
  - 変更対象の分解
  - 実装順序の確定
  - 検証観点の定義
- Execution Plan Shape:
  - API / data shape 確定
  - 変更ファイル列挙
  - 実装
  - テスト
  - 文書更新
- Readiness Implications:
  - API / data shape を build 前に固定する。
  - 影響ファイルとテスト観点を列挙する。
- APSF-specific Notes:
  - CLI 拡張や repository API 追加はこの型に当たりやすい。
- Non-Examples / Boundary:
  - 既存不具合の局所修正が主目的なら `P-02`。
  - 実装せず設計だけなら `P-06`。

### Example

- **Run**: `runs/fw-improvement/2026-03-19-007_apsf_run-repository-child-run-impl`
- **概要**: `RunRepository` に child run 対応 API 7 メソッドを新規実装し、テストを追加した。
- **この P-TYPE である理由**: run-006 の設計を受けて存在しなかった API を追加する run。「壊れた挙動を直す」でも「構造を整理する」でもなく、新しい能力を追加することが主目的。Execution Plan は仕様確定 → 実装 → テストの典型 P-01 構造。

## P-02 Bug Fix

- Purpose: 期待挙動との差分を局所的に修正する。
- Typical Input: 再現条件、期待挙動、実際挙動、関連コード。
- Typical Output: バグ修正、回帰テスト、原因説明。
- Recognition Signals:
  - 再現ケースがある。
  - 「何が壊れているか」が中心論点。
- Problem Structure Shape:
  - 再現
  - 原因局所化
  - 修正
  - 回帰確認
- Execution Plan Shape:
  - 再現条件整理
  - 原因候補確認
  - 修正
  - 回帰テスト
- Readiness Implications:
  - expected / actual を build 前に言語化する。
  - 修正対象を局所化する。
- APSF-specific Notes:
  - `P-01` から分ける理由は readiness の中心が「新仕様」ではなく「再現と回帰」だから。
- Non-Examples / Boundary:
  - 新能力追加が主目的なら `P-01`。
  - 構造改善が主目的なら `P-03`。

### Example

- **Run**: `runs/fw-improvement/2026-03-19-008_apsf_run-name-pattern-fix`
- **概要**: `_RUN_NAME_PATTERN` 正規表現が連番付き run 名（`YYYY-MM-DD-NNN_...`）を reject する不具合を修正した。
- **この P-TYPE である理由**: 再現条件が明確（run-007 実装中に顕在化）、修正対象が局所的（正規表現 1 行）、回帰確認が主軸。新機能追加ではなく期待動作との差分解消が目的であり、P-01 との境界は「既存挙動の修正か新能力の追加か」で判断できる。

## P-03 Refactoring

- Purpose: 外部挙動を保ちながら内部構造を改善する。
- Typical Input: 技術的負債、重複、複雑な実装、保守負荷。
- Typical Output: より単純な構造、保持された挙動、必要なテスト調整。
- Recognition Signals:
  - 目標が保守性改善で、ユーザー価値の新規追加ではない。
  - 外部仕様は変えない前提が強い。
- Problem Structure Shape:
  - 改善対象の特定
  - 挙動維持境界の定義
  - 段階分解
- Execution Plan Shape:
  - 既存責務確認
  - 分解方針確定
  - リファクタ
  - 回帰確認
- Readiness Implications:
  - 非目的を先に書く。
  - 外部仕様不変更の確認点を先に書く。
- APSF-specific Notes:
  - 既存 framework 資産の整理 run で使いやすい。
- Non-Examples / Boundary:
  - 実際に保存先や topology を変えるなら `P-04` 寄り。

### Example

- **Run**: `runs/fw-improvement/2026-03-19-013_apsf_cli-taxonomy-aware`
- **概要**: CLI 8 コマンドの直パス解決（`settings.runs_dir / run_name`）を `RunRepository` 経由の fallback 解決に置き換えた。
- **この P-TYPE である理由**: CLI の外部挙動（コマンドの動作）を変えず、内部の path 解決ロジックを整理した。P-01 との境界: `--taxonomy` オプション追加という P-01 要素も含むが、この run の primary goal は「直パス除去」という構造改善であり P-03 が主型。

## P-04 Migration

- Purpose: データ、配置、命名、運用単位を新標準へ移行する。
- Typical Input: 旧構造、新構造、移行対象一覧、互換条件。
- Typical Output: 移行済み資産、fallback 方針、更新済み参照。
- Recognition Signals:
  - 既存資産を新構造へ動かす。
  - legacy と新方式の併存整理が必要。
- Problem Structure Shape:
  - 標準構造確定
  - lookup / fallback 方針
  - 移行単位分割
  - 参照更新
- Execution Plan Shape:
  - 方式確定
  - 実装
  - 限定移行
  - cross-reference 更新
  - 回帰確認
- Readiness Implications:
  - 移行単位、legacy policy、fallback 順序を build 前に固定する。
  - 参照更新範囲を事前に列挙する。
- APSF-specific Notes:
  - taxonomy filesystem や parent/child topology の物理移行はこの型。
- Non-Examples / Boundary:
  - 新標準の設計だけなら `P-06`。

### Example

- **Run**: `runs/fw-improvement/2026-03-19-015_apsf_legacy-run-migration`
- **概要**: `runs/` 直下の legacy run 11 本を `runs/fw-improvement/` / `runs/work/` へ物理移行し、cross-reference を更新した。
- **この P-TYPE である理由**: ファイルの配置（topology）を旧方式から新方式へ移す run。P-03 との境界: P-03 は「挙動維持の構造整理」だが、P-04 は資産の配置先・保存先そのものを変える移行が主目的。inventory → target mapping → move/update → regression check の典型構造。

## P-05 Document / Template Update

- Purpose: README、template、policy 文書を更新する。
- Typical Input: 既存文書、反映すべき設計、変更境界。
- Typical Output: 更新済み文書、記述整合、利用者向け説明。
- Recognition Signals:
  - 主成果物が文書。
  - 実装コード変更が主目的ではない。
- Problem Structure Shape:
  - 反映対象の整理
  - 挿入位置判断
  - 文言統合
- Execution Plan Shape:
  - 反映範囲確定
  - 文章更新
  - SC 照合
  - handoff
- Readiness Implications:
  - 変更対象文書と非対象文書を build 前に固定する。
  - 追記か置換かを明記する。
- APSF-specific Notes:
  - `framework/templates/*.md` と `runs/_template/*.md` の更新 run に多い。
- Non-Examples / Boundary:
  - 文書で終わらず実装設計が中心なら `P-06`。

### Example

- **Run**: `runs/fw-improvement/2026-03-19-017_apsf_plan-readiness-template-update`
- **概要**: run-016 で設計した readiness gate を `framework/templates/plan.md` など 4 ファイルへ追記した。
- **この P-TYPE である理由**: 確定済みの設計（run-016 の build.md）を template 文書に反映することが主目的。P-06 との境界: 「何を書くか」は run-016 で決定済みであり、この run は「書く」だけ。コード変更なし・文書更新のみ。

## P-06 Design-only

- Purpose: 実装前に設計方針を固める。
- Typical Input: 要求、制約、候補案、影響範囲。
- Typical Output: 採用方針、代替案比較、次 run への handoff。
- Recognition Signals:
  - 今回はコード変更しない。
  - build の成果物が設計文書。
- Problem Structure Shape:
  - 論点分解
  - 案比較
  - 採用方針
  - handoff
- Execution Plan Shape:
  - 選択肢比較
  - 採用理由整理
  - 影響点列挙
  - 実装 run へ handoff
- Readiness Implications:
  - build で新しい設計論点を増やさない。
  - 実装 run に必要な決定事項を明示する。
- APSF-specific Notes:
  - run-006 や taxonomy 設計系の run が典型。
- Non-Examples / Boundary:
  - 実装や移行まで行うなら `P-01` または `P-04`。

### Example

- **Run**: `runs/fw-improvement/2026-03-19-016_apsf_plan-readiness-gate`
- **概要**: build に進む前の readiness チェックリスト（5 項目・4/5 閾値）と review.md への確認項目を設計した。
- **この P-TYPE である理由**: コード・文書の変更なし。成果物は設計方針と run-017 への handoff のみ。P-05 との境界: 「何を template に入れるか」を決める run（P-06）と「入れる」run（P-05）は別であり、この run は前者。

## P-07 Retrospective / Analysis

- Purpose: 実施済み run や実験結果を分析し、評価や改善点を整理する。
- Typical Input: build / review / result、ログ、比較対象。
- Typical Output: 判定、改善点、次 action。
- Recognition Signals:
  - すでに終わった作業の評価が中心。
  - inventory / run-audit / 棚卸しが主成果物。
- Problem Structure Shape:
  - 対象棚卸し
  - 比較軸定義
  - 判定
  - 改善提案
- Execution Plan Shape:
  - 対象収集
  - 評価
  - 判定
  - handoff
- Readiness Implications:
  - 評価軸、比較対象、粒度を build 前に明示する。
- APSF-specific Notes:
  - retrospective run、legacy run inventory、run-audit はこの型に含める。
- Non-Examples / Boundary:
  - 未知領域の候補探索が主なら `P-08`。

### Example

- **Run**: `runs/fw-improvement/2026-03-19-014_apsf_legacy-run-inventory`
- **概要**: `runs/` 直下の legacy run 33 本を一覧化し、fw-improvement / work への分類と移行優先度案を作成した。
- **この P-TYPE である理由**: 既存資産の棚卸し・分類・優先度付けが主成果物。P-06 との境界: 設計方針を決めるのではなく、過去の run を観察して事実整理と優先度案を作ることが目的。P-08 との境界: 外部から新知識を収集するのではなく、既存の APSF 資産を振り返る内向きの分析。

## P-08 Research / Discovery

- Purpose: 未整理の選択肢群を探索し、候補を絞り、仮説を形成する。
- Typical Input: 外部候補、参考事例、比較軸、探索対象。
- Typical Output: shortlist、除外理由、仮説、次段階への handoff。
- Recognition Signals:
  - まだ解き方を狭めていない。
  - 候補探索と input narrowing 自体が成果物になる。
- Problem Structure Shape:
  - 母集団定義
  - 候補収集
  - 評価軸設定
  - shortlist
  - handoff
- Execution Plan Shape:
  - 候補収集
  - 評価
  - 統合 / 除外判断
  - shortlist
  - 次段階へ handoff
- Readiness Implications:
  - 探索母集団、評価軸、shortlist 条件を build 前に固定する。
- APSF-specific Notes:
  - APSF 固有の新設型。初版定義は暫定であり、実例追加に応じて見直す。
  - 有効なのは、独立した input narrowing / hypothesis shaping を成果物として持つ場合のみ。
- Non-Examples / Boundary:
  - 単なる retrospective や inventory なら `P-07`。
  - 設計方針を決める段階に入っているなら `P-06`。

### Example

- **Run**: `runs/fw-improvement/2026-03-19-018_apsf_planning-patterns-design/018c1_apsf_collect-and-shortlist`
- **概要**: web 由来 9 類型と APSF 固有 3 類型を評価軸で比較し、APSF 向け 8 型に shortlist した。
- **この P-TYPE である理由**: 候補収集と shortlist（input narrowing）そのものが独立した成果物。P-07 との境界: 過去の APSF run を振り返るのではなく、外部から新しい知識を収集して絞り込む探索が主目的。P-08 実例が現時点で 1 件のみのため、この定義は暫定的。実例追加に応じて更新する。

---

## Skill Usage Principle

skill は実行能力そのものではなく、手順と判断基準を共有するための資産として扱う。

- pattern 定義は `skill` の利用可能性を前提にしない。
- skill が必要な場合は user-triggered usage を原則にする。
- agent が暗黙に skill を自動起動する前提では書かない。

---

## Notes

- first version は examples の網羅よりも pattern 境界の安定化を優先する。
- `SKILL.md` への skillization は follow-up run で扱う。
