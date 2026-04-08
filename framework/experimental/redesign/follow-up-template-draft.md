# Follow-up Template Draft

---

## Purpose

この草案は、
新しい大型系列を増やさずに、
既存系列に対する small follow-up を
狭く、差分中心に運用するための
テンプレ変更案である。

今回の SoChi BLOCKS 試走から確認できたことは次のとおりである。

- follow-up は narrow question に固定すると成立しやすい
- 親文脈を再発明しない方が冗長化を抑えやすい
- `review` と `result` で drift を止めやすい
- `goal / plan / review / result` の骨格は維持しつつ、
  冒頭と末尾に軽い follow-up 専用欄を足すだけで十分である

---

## Draft Change Summary

今回の草案で足したいのは大きく2つである。

1. `goal / plan / review / result` の前段に入る
   `Follow-up Classification Gate`
2. `result` の末尾に入る
   `Stable Baseline / Open Conditional / Next Trigger`

この2つにより、
follow-up が新系列化することと、
result が broad redesign 許可書として読まれることを防ぎやすくする。

---

## 1. Follow-up Classification Gate

### Intent

この gate は、
その文書が
「新しい大型系列」
なのか、
「既存文脈に対する局所 follow-up」
なのかを最初に固定するためのものである。

follow-up でない場合は、
この gate を使わず、
通常系列の書き方へ戻るべきである。

### Recommended Fields

- Parent series:
  親系列名
- Previous result:
  直前の判断または既存前提
- New trigger:
  今回 follow-up を切る直接原因
- Scope limit:
  今回 narrow に扱う問い
- Non-goals:
  今回扱わない拡張領域

### Why It Helps

この block があると、
次の drift を防ぎやすい。

- 親文脈の再説明による冗長化
- broad redesign への拡張
- follow-up と新系列の混同

### Example Shape

```md
## Follow-up Context

- Parent series:
  SoChi BLOCKS 初回体験改善
- Previous result:
  初回導線は first playable moment を優先して評価すべきである
- New trigger:
  遊び方ページ先読みに hidden dependency がある可能性
- Scope limit:
  first-question entry のみ
- Non-goals:
  full onboarding redesign / implementation
```

---

## 2. Result Closing Block

### Intent

follow-up の `result.md` は、
Accept / Reject だけで閉じると
次の運用基準が残りにくい。

そこで末尾に、
次の3欄を軽く固定する。

- Stable Baseline
- Open Conditional
- Next Trigger

### Recommended Fields

#### Stable Baseline

今回の follow-up で
以後の前提として固定してよいものを書く。

例:

- 主題は first-question entry である
- 説明の存在と説明依存は分けて扱う

#### Open Conditional

まだ確定していないが、
後続で再判定しうる条件付き論点を書く。

例:

- `clarity` が説明量議論へ滑るかどうか
- `playable transition` が onboarding redesign へ膨らむかどうか

#### Next Trigger

どんな evidence が出たら
次の follow-up を切るかを書く。

例:

- first-question friction の具体例が観察された
- prior reading なしで始められない evidence が出た
- compare が optional / required explanation の差を要する状態になった

---

## Proposed Template Delta

### Goal

`goal.md` の本文前に
`Follow-up Context` を追加する。

狙い:

- 親文脈を再発明しない
- 今回の narrow question を固定する
- 非対象を早めに切る

### Plan

`plan.md` の冒頭にも
同じ `Follow-up Context` を置いてよい。

狙い:

- plan が broad redesign 設計へ流れるのを防ぐ
- 「今回は何の差分か」を毎回見えるようにする

### Review

`review.md` では
次の gate を優先する。

- small follow-up discipline
- narrow question の維持
- broader redesign drift の有無

### Result

既存の
`Safe Interpretation`
と
`Recommended Next Step`
の後ろに、
次を足す案が有効である。

```md
## Stable Baseline

- 今回以後の固定前提

## Open Conditional

- まだ再判定余地があるもの

## Next Trigger

- 次の follow-up を切る条件
```

---

## What This Draft Changes

この草案は、
`goal / plan / review / result`
の骨格自体を作り直すものではない。

変えるのは、

- follow-up であることの明示
- 狭い問いの固定
- result 後の運用接続

の3点だけである。

---

## What This Draft Does Not Change

この草案は次を変えない。

- 通常の大型 redesign 系列の書き方
- compare 系列の構造
- row execution や mapping 系列の判断基準
- implementation run の扱い

---

## Initial Recommendation

まずは公式テンプレートを直接置き換えず、
follow-up 用の軽量 variant として試すのがよい。

具体的には、

- `goal.md`
- `plan.md`
- `review.md`
- `result.md`

の運用メモとしてこの差分を適用し、
2〜3件の follow-up で再利用できるかを見る。

その後に、
正式テンプレートへ吸収するかどうかを決めるのが安全である。

---

## Reusable Takeaway

Follow-up をうまく回すには、
新しい骨格を増やすより、
既存骨格の前後に
「親文脈との接続」
と
「次の follow-up が発火する条件」
を小さく足す方が効く。
