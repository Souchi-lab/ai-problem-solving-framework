# Plan

---

## Follow-up Context

- Parent series:
  SoChi BLOCKS 初回体験改善
- Previous result:
  初回導線は first playable moment を優先して評価すべきである
- New trigger:
  easy 問題が「簡単そうに見える」だけで、
  本当に初見向け easy として機能しているかは未確認である
- Scope limit:
  easy 問題の first-look suitability のみ
- Non-goals:
  full difficulty rebalance / 全問題の再分類 / implementation

---

## Run Metadata

- Run Name:
  sochi-easy-first-look
- Series:
  SoChi BLOCKS 初回体験改善
- Run Type:
  Small follow-up
- Primary Question:
  easy 問題は、初見ユーザー向けの最初の1問として本当に機能しているか

---

## Goal Readiness Check

| Item | Status | Notes |
|---|---|---|
| Goal statement is clear | Yes | 主題は `easy label` ではなく `初見向け easy として成立しているか` に固定されている |
| Scope is narrow enough | Yes | easy 問題の first-look suitability のみに限定されている |
| Success criteria are actionable | Yes | first-look 観点への分解と non-goals の維持が確認可能 |
| Follow-up context is usable | Yes | previous result と new trigger の接続が自然 |
| Risk of scope drift exists | Yes | difficulty taxonomy / onboarding redesign / rebalance へ広がりやすいので gate が必要 |

Readiness verdict:

- Proceed

この run は成立している。  
ただし execution 中に論点が `difficulty 全般` や `onboarding 全面改善` へ広がらないよう、
最初に evaluation frame を固定する必要がある。

---

## Problem Framing

今回見るのは、
「easy と名付けられているか」ではない。

見るべき問いは次である。

> この easy 問題は、
> 初見ユーザーが SoChi BLOCKS に最初に触れる1問として、
> entry-friendly に機能するか。

ここでいう `entry-friendly` は、
後半で上達しやすいかではなく、
first look の時点で前に進めるかを意味する。

したがって、
difficulty の一般論ではなく、
初見接触時の usability を扱う。

今回は representative な easy 問題の first-look suitability を扱い、
easy 群全体の再分類には進まない。

---

## Decision Frame

最初に次の区別を固定する。

### 1. Easy label

- difficulty taxonomy 上で easy と整理されていること
- 相対難易度として他問題より軽い可能性を示す

### 2. First-time usability

- 初見ユーザーが説明なし、または最小説明で前進できること
- 最初の一手が見えること
- 早期に「できそう」「分かったかも」を持てること

この run で主に扱うのは `2` である。  
`1` は補助情報に留め、評価の主語にしない。

---

## Core Evaluation Axes

この run では easy 問題の first-look suitability を、
少なくとも次の観点に分解して扱う。

### A. Discoverability

初見で「何を見ればよいか」「何を目標にすればよいか」が分かるか。

見る点:

- 問題の見た目だけで注目点が拾えるか
- 盤面 / ピース / 空きの関係が把握しやすいか
- 何から考え始めるべきかの足がかりがあるか

### B. First Move Clarity

説明なしでも最初の一手候補が立つか。

見る点:

- 初手候補が自然に思い浮かぶか
- 「どこから触ればよいか不明」の停止が起きないか
- 候補が多すぎて固まらないか

この軸では、
初手候補そのものが立つかを主に見る。

### C. Early Success Expectation

最初の数手で「進んでいる感」が得られるか。

見る点:

- 早い段階で部分的成功や手応えがあるか
- 試した結果が理解につながるか
- 失敗しても学習可能で、理不尽感が強くないか

この軸では、
初手の後に継続意欲を支える進展感があるかを主に見る。

### D. Rules Ambiguity Pressure

難しいのではなく、ルールや見方が曖昧なために止まっていないか。

見る点:

- puzzle difficulty ではなく解釈負荷で詰まっていないか
- 初見で前提ルールの理解不足が主要因になっていないか
- `easy-looking but confusing` になっていないか

---

## Working Hypothesis

今回の仮説は次の形で置く。

- easy 問題の中には、
  relative difficulty は低くても、
  first-look では entry-friendly とは限らないものがある
- 初見体験で問題になるのは、
  解けるかどうかだけでなく、
  最初に触った瞬間に前へ進める構造かどうかである
- したがって、
  easy 評価は
  `難易度が低い`
  と
  `初見導入に向いている`
  を分けて扱う必要がある

---

## Execution Plan

### Step 1. Evaluation Gate を固定する

この run の開始時に、次の gate を明示する。

- 問いは「初見向け easy として成立するか」
- easy label の妥当性それ自体は主題ではない
- full rebalance / taxonomy redesign / onboarding redesign には進まない

この gate を外れた論点は補足に退避する。

### Step 2. First-look 観点だけで観察する

easy 問題を見る際は、
完成難度や熟達後の面白さではなく、
first look のみで観察する。

具体的には、

- 最初に何が見えるか
- 最初の一手が立つか
- 早期成功の予感があるか
- confusion の原因が難しさか曖昧さか

を確認する。

### Step 3. `Easy-looking but confusing` を識別する

必要なら compare 的に、次の差だけを切る。

- easy-looking but confusing
- actually entry-friendly

ただし compare は補助であり、
本 run の中心は分類表づくりではなく、
first-look suitability の framing である。

compare は confusion source の切り分け補助に限り、
分類表づくり自体を目的にしない。

### Step 4. Minimal Output にまとめる

最終的には、
後続 review / result に渡せるよう、
次だけを残す。

- 初見向け easy を判定する最小観点
- easy label と first-time usability の区別
- 今回扱うこと / 扱わないこと
- 次段で見るべき narrow questions

---

## Boundaries and Non-Expansion Rules

以下に話が広がったら scope drift とみなす。

- SoChi BLOCKS 全問題の難易度再評価
- easy / normal / hard の taxonomy 再設計
- onboarding 全体の再設計
- UI / copy / tutorial 実装改善の具体案
- 問題差し替えや full rebalance の決定

これらは今回の output には入れず、
必要なら future follow-up 候補として別置きする。

---

## Deliverables

この plan run の成果物は次の最小セットとする。

1. easy 問題の first-look suitability という問いの固定
2. `easy label` と `初見向け easy` の区別
3. evaluation axes
   - discoverability
   - first move clarity
   - early success expectation
   - rules ambiguity pressure
4. scope boundary と non-goals の再確認
5. 後続 run に渡せる narrow handoff

---

## Review Focus

後続 review では特に次を確認してもらう。

- 主語が最後まで `初見向け easy` に保たれているか
- difficulty 一般論に流れていないか
- 観点が first playable moment 系列と接続しているか
- compare を使いすぎて分類作業へ寄っていないか
- broad redesign を呼び込む書き方になっていないか

---

## Expected Landing

今回の着地は、
「この easy 問題は難度分類上 easy か」ではなく、

- 初見導入として成立しうる評価軸は何か
- easy label とは別に first-time usability をどう見るか
- 次段で何を narrow に確認すべきか

を定義した状態である。

結論を大きくしすぎず、
SoChi BLOCKS 初回体験改善系列の
small follow-up として閉じる。
