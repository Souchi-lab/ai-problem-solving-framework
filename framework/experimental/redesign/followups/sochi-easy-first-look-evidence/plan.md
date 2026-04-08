# Plan

---

## Run Metadata

- Run Name:
  sochi-easy-first-look-evidence
- Series:
  SoChi BLOCKS 初回体験改善
- Run Type:
  Small follow-up evidence run
- Primary Question:
  既存の4軸は、representative な easy 問題 1 件に対して
  `初見向け easy`
  を見る concrete observation frame として十分に機能するか

---

## Goal Readiness Check

| Item | Status | Notes |
|---|---|---|
| Goal statement is clear | Yes | 主題は「4軸の追加」ではなく「4軸の適用による evidence 取得」に固定されている |
| Scope is narrow enough | Yes | representative な easy 問題 1 件に限定されている |
| Success criteria are actionable | Yes | 軸ごとの観察結果または保留点を残せる形が明示されている |
| Follow-up continuity is strong | Yes | 前段で定義した baseline を実問題へ当てる自然な接続になっている |
| Risk of scope drift exists | Yes | 問題評価から taxonomy 議論や改善案に広がりやすいので gate が必要 |

Readiness verdict:

- Proceed

この run は成立している。  
ただし execution 中に
`4軸の再設計`
`easy 群全体の横断評価`
`改善案の設計`
へ広がらないよう、
evidence run としての boundary を最初に固定する必要がある。

---

## Problem Framing

今回やることは、
新しい評価軸を作ることではない。

また、
この representative easy 問題が
difficulty taxonomy 上で本当に easy か
を再判定することでもない。

今回の問いは次である。

> 既に定義済みの4軸を
> representative な easy 問題 1 件に当てたとき、
> 初見向け easy としての friction / entry point / ambiguity を
> concrete に観察できるか

したがって、
今回の主語は
`puzzle の再設計`
ではなく
`評価枠の適用`
である。

---

## Fixed Baseline

今回使う baseline は前段で定義済みの次の4軸に限定する。

- discoverability
- first move clarity
- early success expectation
- rules ambiguity pressure

この run では、
これらの軸を変更しない。
増やさない。
統合しない。

必要なのは、
各軸が実問題に対して
観察可能な distinction を生むかどうかを見ることである。

---

## Evaluation Gate

run 開始時に次を gate として固定する。

- 対象は representative な easy 問題 1 件のみ
- 今回は 4軸の適用可能性を見る
- 新しい軸の追加や taxonomy の再議論には進まない
- 改善案が浮かんでも implementation や redesign 決定には進まない
- compare を使う場合も confusion source の切り分け補助に限る

この gate を外れる論点は、
すべて補足または future follow-up 候補へ退避する。

---

## Observation Unit

今回の最小観察単位は、
`各軸ごとに、この問題に対して初見ユーザーがどう止まる / 進めるか`
である。

各軸で最低限残すものは次の3つ。

1. **Observation**
   - その軸で実際に見えたこと
2. **Interpretation**
   - それが初見向け easy として何を示すか
3. **Ambiguity / Open Question**
   - まだ断定しきれない点

Observation は見えた事実を記し、
Interpretation はそれが初見向け easy として何を示すかを記す。

これにより、
result で
「見えたこと」と
「まだ保留のこと」
を分けて閉じやすくする。

---

## Axis-by-Axis Working Use

### 1. Discoverability

見ること:

- 初見でどこに注目すべきか拾えるか
- 盤面 / 空き / ピースの関係が把握しやすいか
- 問題の入口が見えるか

残す形:

- 注目点が自然に立つか
- 入口が見えない場合、それは情報不足か構造由来か

### 2. First Move Clarity

見ること:

- 初手候補が自然に立つか
- 最初の一手を置く場所の見当がつくか
- 候補過多または候補欠如で停止しないか

残す形:

- 初手の見えやすさ
- 止まる場合、その原因が多すぎる候補か全く見えないことか

### 3. Early Success Expectation

見ること:

- 初手のあとに進展感があるか
- 数手以内で
  `できそう`
  `分かったかも`
  が立つか
- 継続意欲を支える手応えがあるか

残す形:

- 初手後の手応えの有無
- progress feeling が弱い場合、その弱さがどこから来るか

### 4. Rules Ambiguity Pressure

見ること:

- 難しいのではなく、
  見方や前提ルールの曖昧さで止まっていないか
- puzzle difficulty とは別の confusion が主因になっていないか

残す形:

- friction の主因が difficulty か ambiguity か
- `easy-looking but confusing`
  の兆候があるか

---

## Evidence Capture Format

この run では、
最終的に次の形で evidence を残せれば十分とする。

### Problem Under Observation

- representative easy 問題 1 件

### Observations by Axis

- Discoverability:
  - observation
  - interpretation
  - ambiguity/open question
- First Move Clarity:
  - observation
  - interpretation
  - ambiguity/open question
- Early Success Expectation:
  - observation
  - interpretation
  - ambiguity/open question
- Rules Ambiguity Pressure:
  - observation
  - interpretation
  - ambiguity/open question

### Provisional Synthesis

- この問題は
  `初見向け easy`
  としてどこが機能しているか
- どこに friction があるか
- 4軸は十分に切り分けに機能したか

---

## Execution Plan

### Step 1. Representative problem を固定する

対象問題を1件だけ固定する。

ここでは
`representative easy 問題`
として扱うが、
その代表性自体を大きく論じない。

必要なのは、
この問題を evidence carrier として使うことである。

今回の representative 性は、
厳密な代表性証明ではなく、
4軸適用の evidence carrier としての実用的選定に留める。

### Step 2. First-look sequence を仮置きする

その問題に対して、
初見ユーザーが最初に触れたときの sequence を仮置きする。

例:

- 最初に何が目に入るか
- どこから考え始めそうか
- どこで止まりそうか
- 何が progress feeling を生むか

ここでは詳細な UX script にはしない。
first-look observation に必要な最小線だけを置く。

### Step 3. 4軸で観察を分解する

問題全体の印象ではなく、
4軸ごとに observation を分解する。

重要なのは、
1つの感想を繰り返すのではなく、
軸ごとに distinct な見え方があるかを確認することである。

### Step 4. Ambiguity を明示的に残す

判定しきれない点は、
無理に結論化しない。

むしろ

- evidence が足りない
- 軸の適用はできるが断定はまだ弱い
- friction source が複合的

といった形で残す。

これにより、
result が過剰断定にならずに済む。

### Step 5. Narrow synthesis で閉じる

最後は、

- この問題に対して4軸は使えたか
- 初見向け easy として見えた friction は何か
- 次に必要なのは追加 evidence か、別問題適用か

を narrow にまとめる。

改善案設計や taxonomy 再設計には進まない。
この synthesis は対象 1 件に限定し、
easy 群全体への一般化は行わない。

---

## Boundaries and Non-Expansion Rules

以下には進まない。

- easy 群全体の横断評価
- difficulty taxonomy の見直し
- 問題全体の rebalance
- UI / tutorial / copy 改善案の具体設計
- puzzle 差し替え判断
- 新しい評価軸の増設
- broad onboarding redesign

また、
compare を使う場合も、
次の範囲を超えない。

- `easy-looking but confusing`
  と
  `actually entry-friendly`
  の切り分け補助

---

## Deliverables

この plan run の成果物は次の最小セットとする。

1. representative easy 問題 1 件への適用方針
2. 軸ごとの最小観察単位
3. evidence の記録形式
4. ambiguity を含めた narrow synthesis の形
5. broad redesign に広がらない boundary

---

## Review Focus

後続 review では特に次を確認してもらう。

- 主語が
  `4軸を実問題に適用して evidence を得る`
  に固定されているか
- 対象が本当に 1 件に留まっているか
- 4軸の再設計や増設に流れていないか
- 観察結果の残し方が result に繋がるか
- compare が補助に留まっているか
- 改善案への早すぎるジャンプを抑えられているか

---

## Expected Landing

今回の着地は、
代表問題 1 件について

- 4軸が concrete observation frame として使えたか
- 各軸で何が見えたか
- どこに ambiguity が残るか

を narrow に残した状態である。

結論を一般化しすぎず、
`sochi-easy-first-look`
で定義した baseline を
実データへ一度着地させる
small follow-up evidence run として閉じる。
