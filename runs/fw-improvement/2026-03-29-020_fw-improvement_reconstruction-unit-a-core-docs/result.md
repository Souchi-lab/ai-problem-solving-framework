# Result

---

## Status

Completed

---

## 実装差分サマリー

| 変更 | 内容 |
|---|---|
| `framework/core/` 新設 | `core` の最小着地点として新設 |
| `framework/core/README.md` 新設 | `core` の役割・入れるもの・入れないものを 8 行で記述 |
| `framework/core/operating-model.md` 新設 | 正本を `core/` に配置。`../templates/` への相対リンクを修正 |
| `framework/core/responsibility-matrix.md` 新設 | 正本を `core/` に配置。内容変更なし |
| `framework/operating-model.md` 更新 | 旧位置に導線スタブを追加（正本へのリンク + 旧位置維持の注記） |
| `framework/responsibility-matrix.md` 更新 | 旧位置に導線スタブを追加（正本へのリンク + 旧位置維持の注記） |

---

## Verification

| 観点 | 確認結果 |
|---|---|
| ファイル配置 | `framework/core/` に 2 文書が存在する ✅ |
| README / 案内接続 | `framework/core/README.md` から `core` の役割と文書が辿れる ✅ |
| 旧位置導線 | 旧位置に `> 正本: framework/core/...` スタブを追加。急な意味断絶なし ✅ |
| 変更範囲 | `framework/core/`（新設）+ 旧位置 2 ファイル（スタブ追加）のみ。Unit A の範囲に閉じている ✅ |
| 保留資産 | `execution-model.md`・`planning-patterns.md`・`overview.md` は未変更 ✅ |
| src/apsf/ 変更 | なし ✅ |

---

## `core` の最小着地として妥当か

妥当。

- `operating-model.md` と `responsibility-matrix.md` は redesign plan.md の Rule 1「安定した契約・責務境界」に該当する
- 両文書とも「現行 CLI フローへの依存」「template ボディへの依存」がなく、core 禁止事項に抵触しない
- `framework/core/README.md` で「入れるもの / 入れないもの」を明示したことで、次の文書追加判断の基準が生まれた

---

## 旧位置導線が残っているか

残っている。

旧位置（`framework/operating-model.md`・`framework/responsibility-matrix.md`）に以下のスタブを追加した:

```
> この文書は framework/core/ に移動しました。
> 正本: framework/core/operating-model.md
> この旧位置のファイルは導線維持のために残しています。
```

既存の runs/ や他の framework 文書からの参照が急に切れることを防いでいる。

---

## Unit A の範囲に閉じているか

閉じている。

変更ファイル: `framework/core/`（3 ファイル新設）+ `framework/operating-model.md`（スタブ追加）+ `framework/responsibility-matrix.md`（スタブ追加）。

`execution-model.md`・`src/apsf/`・`legacy`・compare material に変更なし。

---

## Unit B へ自然につながるか

つながる。

`framework/core/` が実体として存在し、「core = 安定契約」の意味が文書レベルで repo に着地した。次の Unit B run が `src/apsf/core/` を立ち上げるとき、文書側 `core` が先行して存在している状態になっている。

---

## Success Criteria 照合

| # | 基準 | 結果 |
|---|---|---|
| 1 | `framework/core/` が新設されている | ✅ |
| 2 | `operating-model.md` と `responsibility-matrix.md` が `framework/core/` に収まっている | ✅ |
| 3 | `framework/` 側から新しい `core` 位置が辿れる | ✅（旧位置スタブ + `framework/core/README.md`） |
| 4 | `legacy` 文書群の読みやすさが悪化していない | ✅（`legacy` には未変更・旧位置に導線スタブ） |
| 5 | 保留資産が巻き込まれていない | ✅ |
| 6 | 変更が Unit A の範囲に閉じている | ✅ |
| 7 | 次の Unit B 実装 run に自然につなげられる | ✅ |

---

## Next Trigger

**Unit B 実装 run（Codex）**

- `src/apsf/core/` を新設する
- `src/apsf/domain/models.py`、`providers/base.py`、`agents/base.py`、`executors/base.py` を移行する
- import 影響を列挙・修正する
- `pytest tests/` を通す

**保留継続**:

- `framework/execution-model.md` の精読と core / legacy 判定（Unit B 前後に単独タスクとして実施）
