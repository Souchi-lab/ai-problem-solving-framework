# framework/legacy

このディレクトリは「現行 APSF が動作するために必要な現行運用形状」を保持します。

---

## 役割

- `framework/core/` が安定契約（role 境界・artifact 定義）を定義する
- `framework/legacy/` はその実装形状、つまり現在の workflow・agent・template・execution 設計を保持する
- 削除候補ではなく、現行 APSF が readable な状態を維持するための写しとして扱う

---

## 現在の内容

| パス | 役割 |
|---|---|
| `execution-model.md` | CLI / Human 前提の実行設計（v0.1 運用形状） |
| `overview.md` | 旧 framework 全体案内（extraction source） |
| `workflow/` | v0.1 / v0.2 ワークフロー定義 |
| `agents/` | role 別 agent 文書（planners/ / critics/ 含む） |
| `templates/` | 各フェーズのテンプレートボディ |
| `skills/` | CLI / skill 向けの運用ガイダンス |

---

## 含まないもの

- `framework/core/` — 安定契約層（別ディレクトリ）
- `framework/experimental/` — 再設計ドラフト（現位置維持）
- `framework/improvement-notes/` — docs 層（現位置維持）
- `framework/planning-patterns.md` — 保留資産（未確定）
