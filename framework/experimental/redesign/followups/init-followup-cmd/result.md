# Result

---

## Status

Completed

---

## 1. 実装差分サマリー

### 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `src/apsf/cli/main.py` | `init-followup` コマンド追加 + 4テンプレート定数 |

### 変更量

- テンプレート定数: 4つ（約160行）
- コマンド本体: 約30行
- docstring 更新: 1行

既存コマンドへの変更ゼロ。settings.py・外部ファイルへの変更なし。

---

## 2. 動作確認結果

| ケース | 結果 |
|---|---|
| `apsf init-followup <new-slug>` | 4ファイル生成 ✓ |
| 重複 slug（--force なし） | エラーメッセージ + exit 1 ✓ |
| `apsf init-followup <slug> --force` | 上書き生成 ✓ |
| クリーンアップ後に既存コマンドに影響なし | 確認 ✓ |

---

## 3. 採用判断

**採用** — このまま常用に入る。

---

## 4. 心理コスト評価（4観点）

| 観点 | 変化 |
|---|---|
| 開始までの迷い | 消えた。`apsf init-followup <slug>` を打てば始まる |
| 手作業量 | goal.md のヘッダ組み・セクション名の打ち込みがゼロになった |
| 命名迷い | Follow-up Context の5フィールドが最初から出るので「何を書くか」が明確 |
| 初期構造の再発明量 | 実績から抽出した骨格がそのまま出る。再発明なし |

総評: **コスト低減は明確**。
「書き始める前の準備」が完全になくなり、最初の1行から中身を書ける状態になった。

---

## 5. 形式評価（4点セットの CLI 拡張タスクへの適合度）

### 機能したもの

- **goal の Non-Goals**: `settings.py` / 外部ファイル / GUI を明示的に除外したことで、
  実装中に「ここまでやるか」の判断がゼロになった。
- **plan の Scope Policy**: `main.py` 1ファイル完結を事前に決めたことで迷いなし。
- **review skip の判断**: 実装規模・閉じ具合から正しかった。build → result で十分見えた。

### 機能しなかったもの（なし）

今回は全フェーズが plan 通りに動いた。
CLI 拡張タスクのような「スコープが明確で副作用が小さい実装」は
4点セット（review skip）との相性が良い。

---

## 6. Closing

### Stable Baseline

- `apsf init-followup <slug>` が常用コマンドとして利用可能
- テンプレートはコード内定数で十分（外部ファイル化は不要）
- CLI 拡張タスクには 4点セット（review skip）が適合する

### Open Conditional

- followups/ の場所が変わる場合は settings.py に `followups_dir` を追加する
- テンプレートが肥大化・多様化した場合は外部ファイル化を検討する
- slug バリデーション（使用可能文字の制限）は利用頻度次第で追加を判断する

### Next Trigger

- `apsf init-followup` を実際の follow-up で使い始めて、
  テンプレートの粒度に問題が出たら改訂する
- 次の着地候補: GUI の前段として `apsf list-followups` や `apsf status` の検討
