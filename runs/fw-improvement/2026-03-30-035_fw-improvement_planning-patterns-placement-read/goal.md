# Goal

Run: 2026-03-30-035_fw-improvement_planning-patterns-placement-read
Date: 2026-03-30

---

## Goal Readiness Check

- `framework/planning-patterns.md` は reconstruction 系列を通じて最後の保留文書として残っている
- `run-033` で reconstruction 全体 handoff は完了しており、残件はこの 1 本だけに絞られている
- `framework/core/` と `framework/legacy/` はすでに着地済みであり、文書 placement の受け皿は存在する
- 今回は design-only read run であり、ファイル移動や書き換えは行わない

Decision: Proceed

---

## Objective

`framework/planning-patterns.md` を精読し、
この文書が現在の再構築方針において
`framework/core/` に置くべき資産か、
`framework/legacy/` に置くべき資産か、
あるいは引き続き `hold` とするべきかを、
根拠つきで narrow に判定する。

今回の run は、
reconstruction 系列の最後の保留文書について
placement ambiguity を解消することを目的とする。

---

## Scope

この run で扱うのは次だけである。

1. `framework/planning-patterns.md` の精読
2. `core / legacy / hold` のいずれが妥当かの判定
3. 判定理由の要約
4. 最終 handoff への短い接続

---

## Constraints

### 含めるもの

- `framework/planning-patterns.md` の本文読解
- 既存 reconstruction 判断との整合確認
- placement 判定のための短い比較

### 含めないもの

- 実ファイル移動
- 文書書き換え
- viewer の再配置
- 新しい大きな設計議論

### 判断上の制約

- 「抽象度が高いから core」と短絡しない
- durable guidance と current operational advice の混在があるなら正直に扱う
- 即断できないなら hold を選んでよい

---

## Success Criteria

1. `planning-patterns.md` の placement が `core / legacy / hold` のいずれかで明示される
2. 判定理由が structural reading に基づいている
3. 既存の reconstruction 判断と矛盾しない
4. reconstruction の最後の保留論点を 1 点解消したと言える
5. 実装計画や追加分類 run に逸脱していない

---

## Verification

- `planning-patterns.md` の読解結果が要約されている
- 判定が `core / legacy / hold` のどれかに閉じている
- 判定理由が最終 handoff に接続できる

---

## Non-Goals

- `planning-patterns.md` の実移動
- `planning-patterns.md` の書き換え
- 新しい redesign 文書の追加

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-29-033_fw-improvement_reconstruction-final-handoff/result.md`
- `framework/planning-patterns.md`
- `framework/core/`
- `framework/legacy/`

特に次を守ること。

- これは最後の保留文書である
- 今回は判定だけで閉じる
- reconstruction 系列を再び広げない

---

## Desired Landing

この run の着地は、
`framework/planning-patterns.md` の placement ambiguity が解消され、
reconstruction 後の保留論点が実質ゼロになる状態である。

結果は、
「planning-patterns.md をどう読むべきか」
を短く固定する handoff で十分であり、
新しい大きな論点を増やさない。
