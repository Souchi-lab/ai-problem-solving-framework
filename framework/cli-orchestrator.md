# CLI Orchestrator — 設計メモ

> **何か**: `apsf` CLI の Human-in-the-loop 支援コマンド群の責務・設計方針の記録。
> **いつ参照するか**: CLI コマンドの動作を確認するとき / 追加・変更の設計判断時。

---

## 全体責務

```
Human → apsf start-run → [run ディレクトリ作成]
Human → [goal.md を書く]
Human → apsf next      → [次ロールへの指示を表示]
  └→ AI / Human が指示を受け取り、該当ファイルを記入
  └→ apsf next を再実行して次フェーズへ進む
Human → apsf transcript → [transcript.md を自動生成]
```

`apsf` は Human の意思決定を代行しない。
何を書くかは Human と各 role が決める。
`apsf` は「今どこにいるか」と「何をすべきか」を整理して提示するだけである。

---

## コマンド一覧と責務

### `apsf start-run <name>`

**責務**: 新しい run ディレクトリを作成し、Human が goal.md を書き始められる状態にする。

- `runs/_template/` からファイルを一式コピーする
- 日付プレフィックスが省略されていれば今日の日付を自動付与する
- 作成したファイルの一覧を表示する
- goal.md を書くよう次アクションを案内する

**しないこと**:
- goal.md の本文を生成しない
- execution-assignment.md を自動で埋めない
- 「賢い」ことをしすぎず、骨格作成のみに集中する

**オプション**:
- `--dry-run`: 実際には作成せず、作成予定ファイルをプレビュー
- `--force` / `-f`: 既存ディレクトリを上書き

---

### `apsf next <run-name>`

**責務**: run の現在フェーズを推定し、次ロールにそのまま渡せる指示を表示する。

- `PhaseDetector` でファイル存在・充填状態からフェーズを推定する
- `NextInstructionBuilder` でフェーズ別の `short_instruction` + `detailed_instruction` を生成する
- 出力はあくまで「提案」であり、Human の判断を上書きしない

**重要: `next` は提案型である**

`apsf next` の出力は推定に基づく。以下の場合は誤検知が起きる可能性がある:
- ファイルに 4 行未満しか書いていない（充填済みと判定されない）
- テンプレートのコメント行だけ残っている
- v0.2 フローの optional ファイル（improve-plan.md / verify.md）が中途半端に存在する

迷ったら直接ファイルを確認すること。`apsf next` はあくまで出発点の提案である。

**オプション**:
- `--debug`: 判定根拠（existing / filled / unfilled / decision_reason）を追加表示

---

### `apsf write-phase <run-name>`

**責務**: 現在フェーズに対応する md を受け取り、正しいファイルへ保存する。

- `PhaseDetector` でフェーズを判定する
- `NextInstructionBuilder` で instruction を取得する
- 入力コンテンツを対象 md に保存する
- 保存後、`apsf next` を案内する

**`next` との責務分離**:

| | `apsf next` | `apsf write-phase` |
|---|---|---|
| 責務 | 案内 | 保存 |
| 出力 | instruction の表示 | ファイルへの書き込み |
| stdin 入力 | なし | あり |

**オプション**:
- `--print-prompt`: instruction だけ表示して終了（保存しない）。`next` の instruction を貼り付け用途に使う場合に便利。
- `--stdin`: 標準入力からコンテンツを受け取る（対話プロンプトなし）。パイプやリダイレクトで使用。
- `--dry-run`: 保存先を確認するだけ（実際には保存しない）
- `--force` / `-f`: 既存の meaningful content を上書き

**安全性**:
- 対象ファイルに meaningful content が既にある場合、デフォルトでは上書きしない（`--force` 必要）
- 空入力・空白のみ・テンプレート骨格のみは保存しない
- `transcript.md` は対象外（`apsf transcript` コマンドを使うこと）

**しないこと**:
- Goal の内容を自動生成しない
- Judge の判断を代行しない
- 複数フェーズを一気に進めない
- executor に直接接続しない（将来の `apsf act` の役割）

**`apsf act` との関係**:

`write-phase` は "台車" である。将来の `apsf act`（executor への自動投入）の前段に位置するが、
今は「Human または外部 AI が生成したコンテンツを正しいファイルに着地させる」に責務を限定する。

```
現在: Human → [AI に投げる] → [返答をコピー] → apsf write-phase [stdin] → saved
将来: Human →                                    apsf act → executor 自動投入 → saved
```

`write-phase` の保存ロジックは将来の `act` コマンドから再利用できる形に保つ。

---

### `apsf transcript <run-name>`

**責務**: run ディレクトリ内の一次記録ファイルを所定順に連結し、`transcript.md` を自動生成する。

- `TranscriptGenerator` が `TRANSCRIPT_SOURCE_ORDER` に従って処理する
- 存在しないファイルはスキップ（v0.2 の optional ファイルも同様）
- `transcript.md` 自身は入力対象としない（再帰読み込みの防止）

**transcript は正式フェーズではない**:

```
Goal → Plan → Build → Review → Improve → Result
                                              ↓ (optional)
                                          [Transcript]
```

`transcript.md` は二次成果物である。一次記録（goal.md〜result.md）の可読化ツールであり、
逐語ログでも会話の再現でもない。正確な情報は一次記録を参照すること。

---

## Human と CLI の責務分離

| 責務 | Human | CLI |
|---|---|---|
| 何を解くかを決める | **Human** | CLI は問わない |
| run を開始する | `apsf start-run` を呼ぶ | ディレクトリ作成・ファイルコピー |
| goal.md を書く | **Human** が書く | CLI は生成しない |
| 各ロールの指示を受け取る | `apsf next` で確認 | フェーズ推定・指示文生成 |
| build.md / review.md などを書く | **各ロール** が書く | CLI は内容を生成しない |
| 採用・却下を判断する | **Human (Judge)** | CLI は判断しない |
| transcript を生成する | `apsf transcript` を呼ぶ | ファイル連結・整形 |

---

## フェーズ判定のルール（PhaseDetector）

判定基準: ファイルの存在 + 充填状態（`_is_filled`）

```
充填済み = コメント行・見出し行・区切り行を除いて 4 行以上ある
```

フェーズ判定順序（waterfall）:
```
SETUP_NEEDED          ← execution-assignment.md が未充填
GOAL_NEEDED           ← goal.md が未充填
PLAN_NEEDED           ← plan.md が未充填
IMPROVE_PLAN_OPTIONAL ← improve-plan.md が存在・未充填（v0.2）
BUILD_NEEDED          ← build.md が未充填
REVIEW_NEEDED         ← review.md が未充填
IMPROVE_NEEDED        ← improve.md が未充填
VERIFY_OPTIONAL       ← verify.md が存在・未充填（v0.2）
RESULT_NEEDED         ← result.md が未充填
TRANSCRIPT_RECOMMENDED← transcript.md が未充填
COMPLETE              ← 全ファイル充填済み
```

IMPROVE_PLAN_OPTIONAL / VERIFY_OPTIONAL はファイルが存在する場合のみ発動する。
v0.1 フロー（これらのファイルを使わない）では検出されない。

---

## 実装ファイル

| ファイル | 責務 |
|---|---|
| `src/apsf/cli/main.py` | CLI コマンド定義・表示ロジック |
| `src/apsf/orchestration/phase_detector.py` | フェーズ推定ロジック |
| `src/apsf/orchestration/next_instruction_builder.py` | フェーズ別指示文生成 |
| `src/apsf/orchestration/transcript_generator.py` | transcript.md 生成ロジック |
| `src/apsf/storage/run_repository.py` | run ディレクトリの作成・管理 |

CLI 表示ロジックと instruction 生成ロジックは分離されている。
`NextInstructionBuilder` は CLI に依存せず、単独でテスト可能。

---

*このファイルは設計の説明文書です。コードと乖離が生じたらコードを優先してください。*
