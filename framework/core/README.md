# framework/core

このディレクトリは APSF の安定した契約・責務境界定義を置く場所です。

ここに入る文書の条件:
- 実装形状・CLI フロー・template 構造が変わっても意味を保つ
- role 境界・artifact の意味・durable record の定義など、再設計をまたいで安定する責務を記述している
- 現行運用の手順説明ではない

---

## 現在の内容

| ファイル | 役割 |
|---|---|
| `operating-model.md` | role / provider / model の分離原則・artifact trigger policy |
| `responsibility-matrix.md` | phase / role / artifact の canonical 境界定義 |

---

## 入れないもの

- 現行 workflow のフェーズ手順（→ `framework/legacy/workflow/`）
- template ボディ（→ `framework/legacy/templates/` または `framework/templates/`）
- CLI 実装前提の手順（→ `framework/legacy/`）
- 再設計ドラフト（→ `framework/experimental/`）
