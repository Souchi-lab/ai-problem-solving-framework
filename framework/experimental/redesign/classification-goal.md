# Goal

---

## Goal Statement

APSF 再構築の concrete example classification pass として、
代表的な既存 asset を実repoから選び、
それぞれを新構造候補に対して
`outcome category` つきで分類する。

今回の目的は repo 全体の完全分類ではなく、
mapping package で定義した配置ルールが
現実の asset に対してどこまで無理なく機能するかを検証し、
後続の `docs/compare` と implementation-planning acceptance criteria に繋がる
判断材料を作ることである。

---

## Background

前段の mapping package により、
repo-specific mapping の考え方は定義された。

その中で次の点が確定している。

- 配置判断は current path ではなく responsibility で行う
- outcome category は
  `Immediate Placement`
  `Legacy-For-Now`
  `Extraction Candidate`
  `Hold / Review Later`
  の4つを使う
- `shared` は最小共有に限定する
- compare material は `docs/compare` 側へ送る
- viewer は支援層であり、
  durable Markdown の canonical authority ではない

ただし現時点では、
これらのルールが concrete example に当たったときに
どこで素直に機能し、どこで caution や hold が必要になるかは
まだ十分に見えていない。

そのため今回は、
代表例ベースの concrete classification pass を行う。

---

## Success Criteria

今回の goal は、次の条件を満たす分類成果物を作れる状態になること。

1. 代表的な既存 asset 群について、
   新構造候補への分類判断が記録されている
2. 各 asset について、
   少なくとも次の5項目が揃っている
   `asset / proposed destination / outcome category / one-line rationale / caution`
3. outcome category の使い分けが健全であり、
   無理な `Immediate Placement` で押し切っていない
4. `storage/*` `orchestration/*` `planning-patterns` `overview.md`
   のような hotspot が慎重に扱われている
5. `shared` に入れないべきものが、
   concrete example ベースでも確認できる
6. compare material に回すべき判断が識別できる
7. 同一テーマの run を旧構造と新候補構造で対照できる粒度が壊れていない
8. この run が design-oriented に留まり、
   実際の移行作業に化けていない

---

## Expected Outputs

この run で目指す出力は次である。

- concrete example classification table
- hotspot asset に関する caution 一覧
- hold list の更新
- extraction-candidate list の更新
- compare material 候補の抽出
- compare material に送る理由の記録

分類表の各行は、少なくとも次を持つこと。

- asset
- proposed destination
- outcome category
- one-line rationale
- caution

なお、本 run は representative example を対象とし、
repo 全件分類は必須成果物としない。

---

## Non-Goals

今回の run では次はやらない。

- 全repoの完全分類
- 実ファイル移動
- import path の変更
- CLI の切替
- viewer 実装改修
- compare 文書の完成
- migration 開始判断
- `experimental` の canonical 化

---

## Constraints

- 設計runとして扱い、移行runにしない
- mapping package のルールを逸脱しない
- outcome category を無理に圧縮しない
- `Hold / Review Later` を正当な結果として許容する
- `shared` を便利箱にしない
- viewer と durable Markdown の責務を混同しない
- compare 不能を ad hoc メモ増殖でごまかさない

---

## Classification Principle

各 example は、
現在の場所ではなく主責務によって分類する。

その際、最終配置だけを見るのではなく、
その判断が現時点でどれだけ確実かを
outcome category で明示する。

したがって今回の run では、
「どこに置くか」と同じくらい
「なぜその確度なのか」を残すことが重要である。

---

## Explicit Caution

この run の分類結果は、
設計上の concrete evidence であって、
移行許可ではない。

どれだけ配置判断が明瞭でも、
そのまま実装着手やファイル移動の根拠にはしない。

また、複数の例で ad hoc 例外が必要になる場合は、
個別例外を積み増すのではなく、
mapping rule 側を見直すべきである。

---

## Notes For Planner

Planner は次を明確化すること。

- どの representative asset を今回の対象にするか
- 各 asset の proposed destination
- 各 asset の outcome category
- one-line rationale
- caution
- hold に回すべき例
- compare material に送るべき例

特に次は hotspot として慎重に扱うこと。

- `framework/overview.md`
- `framework/planning-patterns.md`
- `src/apsf/storage/run_repository.py`
- `src/apsf/storage/markdown_repository.py`
- `src/apsf/orchestration/phase_detector.py`
- `src/apsf/orchestration/next_instruction_builder.py`
- `src/apsf/viewer/api.py`
