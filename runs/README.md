# runs/

## 目的

`runs/` は **問題解決の実行ログ**を蓄積するディレクトリである。

1 つの `run` = 1 つの problem solving cycle。
ループを回すたびに記録を残し、振り返り・再現・改善・Generalization に活用する。

---

## 1 run = 1 problem solving cycle

```
YYYY-MM-DD_case-key_topic/
  execution-assignment.md  ← run 開始前（実行手段の定義）
  model-assignment.md      ← run 開始前（role 割当の定義）
  goal.md
  plan.md
  handoff.md               ← role 間の受け渡し文書（step ごとに更新）
  build.md
  review.md
  improve.md
  result.md                ← これを書いて初めて「完了」
  transcript.md            ← result.md 完了後に生成（optional / strongly recommended）
```

### 読む順番

- **全体を素早く把握したい場合**: `transcript.md` を最初に読む（会話形式で全体の流れが分かる）
- **詳細・正確な情報が必要な場合**: 各 .md ファイルを直接読む
- **事実確認・再現には必ず元ファイルを参照すること**（transcript.md は二次成果物）

---

## 命名規則

taxonomy サブディレクトリ内（新規 run の標準）:

```
runs/fw-improvement/YYYY-MM-DD-NNN_case-key_topic/
runs/work/YYYY-MM-DD-NNN_case-key_topic/
```

例:
- `runs/fw-improvement/2026-03-19-017_apsf_plan-readiness-template-update/`
- `runs/work/2026-03-19-005_sochi-blocks_publish-pipeline/`

legacy（top-level、既存 run のみ）:

```
runs/YYYY-MM-DD_case-key_topic/
```

- 日付は `goal.md` を書いた日
- `case-key` は `cases/` のフォルダ名と合わせる
- `topic` は英小文字 + kebab-case
- `NNN` は taxonomy サブディレクトリ内での通し番号（3 桁ゼロパディング）
- **1 run に大きすぎる課題を詰め込まない**。スコープが広すぎたら run を分割する

---

## run taxonomy

run は **taxonomy（種別）** で 2 系統に分類される。

| Taxonomy | 対象 |
|---|---|
| `fw-improvement` | framework 自体の仕様・CLI・template・repository・agent policy・運用ルール・改善 retrospective を対象とする run |
| `work` | SoChi BLOCKS などの実案件、検証・コンテンツ・配信・実装など、成果物や案件を前進させる run |

### taxonomy と topology は別軸

taxonomy は「run の種別」、parent/child topology は「run 同士の関係」を表す。両者は独立した軸であり、混同しない。

```
fw-improvement          work
  parent run              parent run
    child run               child run
```

### filesystem 反映状況（2026-03-19 実装済み）

taxonomy に対応した物理ディレクトリ `runs/fw-improvement/` / `runs/work/` を実装済み。

- **新規 run** は taxonomy に従い対応するサブディレクトリに作成する
- **既存 top-level run** は legacy として当面許容する（一括移行は行わない）
- `RunRepository` / CLI の taxonomy-aware 対応は別途 run で判断する

#### legacy top-level run の扱い

`runs/` 直下に残った既存 run は legacy として参照のみ。新規 run は `runs/fw-improvement/` または `runs/work/` 配下に作成すること。

---

## parent/child topology

通常の run は `runs/` 直下に並ぶが、ある run が別の run の探索ラウンドとして生まれる場合（**parent/child run**）は、child run を親 run ディレクトリ直下に置く。

### 標準構造

```
runs/
  work/
    2026-03-18-016_sochi-blocks_x-post-experiment/   ← parent run
      goal.md
      plan.md
      build.md
      ...
      016c1_sochi-blocks_x-thread-content/            ← child run
        goal.md
        plan.md
        build.md
        ...
      016c2_sochi-blocks_x-experiment-exec/           ← child run
        ...
```

### child run の命名ルール

- parent run 名を繰り返さず、child 番号 + topic を中心に短く持たせてよい
- 例: `016c1_sochi-blocks_x-thread-content`（親の `2026-03-18-016` を省略）
- `children/` のような中間ディレクトリは挟まない

### legacy 方針

既存の top-level child run（`runs/` 直下に並んだ child run）は **legacy として当面許容する**。
新規の parent/child run からは上記の標準 topology を採用すること。

### run discovery / RunRepository への注記

現在の `RunRepository` と CLI は `runs/` 直下の run を前提にしている。
child run を含む再帰的な discovery や、parent 指定による child run 作成は別 run で設計・実装予定。

---

## 各ファイルの説明

| ファイル | 書く人 | タイミング | 種別 |
|---|---|---|---|
| `execution-assignment.md` | 人間 | 最初（run 開始前） | 一次記録 |
| `model-assignment.md` | 人間 | 最初（run 開始前） | 一次記録 |
| `goal.md` | 人間 | run 開始時 | 一次記録 |
| `plan.md` | Planner | goal.md 完了後 | 一次記録 |
| `handoff.md` | 各 role | role 交代のたびに更新 | 一次記録 |
| `build.md` | Builder | plan.md 完了後 | 一次記録 |
| `review.md` | Critic | build.md 完了後 | 一次記録 |
| `improve.md` | 人間（Judge） | review.md 確認後 | 一次記録 |
| `result.md` | 人間 | ループ完了時 | 一次記録 |
| `transcript.md` | 人間（or AI 補助） | result.md 完了後 | **二次成果物** |

**一次記録**: 正式な事実・判断の根拠。厳密確認には必ず参照する。
**二次成果物**: 一次記録を役割別の発言形式で再構成した可読化文書。逐語ログでも会話の再現でもない。読みやすさ・共有性のための補助ファイル。正確な情報が必要な場合は一次記録を参照すること。

---

## framework/templates/ と runs/_template/ の違い

| パス | 役割 |
|---|---|
| `framework/templates/` | **設計資産の原本**（仕様書）。直接書き込まない。 |
| `runs/_template/` | **run 開始時にコピーする運用ひな型**（用紙）。 |

「用紙（run）に書いた経験をもとに仕様書（templates）を改訂する」という循環が理想。

---

## model-assignment.md と handoff.md の使い方

### model-assignment.md

- run 開始時に**最初に**作成する
- どの role に何のモデルを使うかを決める
- コスト意識・品質戦略をここで考える

### handoff.md

- role が変わるたびに更新する
- 「何が決まっているか」「何が未決か」「次の role がすること」を明記する
- モデルを分けるほど、この文書の品質が問題解決の品質に直結する

---

## iteration の考え方

1 つの run で複数回ループを回す場合：

### 方法 A: ファイルを更新する（シンプル・推奨）
- git の変更履歴が iteration の記録になる

### 方法 B: iteration 番号を付ける（詳細記録）
```
plan_v1.md / build_v1.md / review_v1.md
plan_v2.md / build_v2.md / ...
result.md
```

v0.1 では方法 A を推奨。

---

## transcript.md の生成方法

### transcript.md とは

一次記録（goal.md 〜 result.md）を「役割別の発言形式で再構成した可読化文書」。
**会話ログの保存ではなく、可読化のための再構成文書**である。

- transcript を最初に読んで全体像を掴む → 詳細は元ファイルで確認する、という使い方が自然
- 逐語ログではない。元ファイルにない発言・判断を補完・創作しない
- handoff の内容は要約で書く（引用ブロックより要約の方が安全）

### 手動生成

```
1. runs/_template/transcript.md をコピーして使う
2. 各セクションを一次記録ファイルを参照しながら記述する
3. 事実ベースで書く。元ファイルにないことを追加しない
4. handoff は引用ではなく要約で書く
```

### CLI 補助

```bash
apsf generate-transcript <run-name>
# 参照すべきファイルの一覧と各セクションの記入ガイドを表示する
```

---

## 現在の runs

個別 run の詳細は各フォルダの `result.md` を参照。棚卸し一覧は `legacy-run-inventory.md` を参照。

### fw-improvement/

framework 自体の仕様・CLI・template・運用ルール改善 run。
`runs/fw-improvement/` 配下に配置（2026-03-19〜）。

主なシリーズ:
- `2026-03-17_apsf-dogfood_*`: CLI dogfood 検証（8 run）
- `2026-03-19-002〜013`: run repository / taxonomy filesystem 設計・実装
- `2026-03-19-014〜015`: legacy run 棚卸し・移行
- `2026-03-19-016〜017`: plan readiness gate 設計・実装
- `2026-03-19-018`: planning patterns 設計

### work/

SoChi BLOCKS などの実案件 run。
`runs/work/` 配下に配置（2026-03-19〜）。

| run | テーマ | 状態 |
|---|---|---|
| 2026-03-19-001_sochi-blocks_shared-puzzle-mode-impl | shared puzzle モード実装 | - |
| 2026-03-19-005_sochi-blocks_publish-pipeline | 投稿パイプライン検証 | 完了 |

### legacy（top-level）

`runs/` 直下の既存 run。新規追加なし。詳細は `legacy-run-inventory.md` 参照。

| run | テーマ | 状態 |
|---|---|---|
| 2026-03-15_sochi-blocks_sns-post-template | SNS 投稿テンプレート作成 | 完了 |
| 2026-03-16_sochi-blocks_sns-post-template-v2 | SNS テンプレ改善 + APSF v0.2 試験 | 完了 |
| 2026-03-18-001〜018 | sochi-blocks / apsf 各種（18 run） | 詳細は inventory 参照 |
