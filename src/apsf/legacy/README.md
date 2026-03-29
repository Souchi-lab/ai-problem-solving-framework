# src/apsf/legacy

このパッケージは現行 APSF の実装形状を保持します。

---

## 役割

- `src/apsf/core/` が安定契約（ABC / domain model）を定義する
- `src/apsf/legacy/` はそれらの契約を使って現在動いている実装を保持する
- 削除候補ではなく、現行 CLI / orchestration / storage が動く readable な写しとして維持する

---

## 現在の内容（skeleton）

| ディレクトリ | 役割 | 状態 |
|---|---|---|
| `cli/` | 現行 CLI エントリポイントとコマンド群 | 受け皿のみ（実装は移行待ち） |
| `orchestration/` | 現行フェーズオーケストレーション・act service | 受け皿のみ（実装は移行待ち） |
| `storage/` | 現行 Markdown / run リポジトリ | 受け皿のみ（実装は移行待ち） |

実装本体の移行は Unit C3 以降の専用 run で行います。

---

## 含まないもの

- `src/apsf/viewer/` — 独立サポート層として現位置維持
- `src/apsf/core/` — 安定契約層（別ディレクトリ）
- `providers/`・`agents/`・`config/`・`prompts/` — Unit C3 planning run で追加予定
