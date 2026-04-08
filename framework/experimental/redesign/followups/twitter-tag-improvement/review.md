# Review

---

## Review Scope

この review は `goal.md` と `plan.md` を対象とする。

目的は、result に入る前に次の3点をゲートとして確認することである。

1. 二層目的（タグ改善 + 形式検証）が崩れていないか
2. SNS 戦略全体に広がっていないか
3. 形式評価4観点が result で本当に答えられるか

実装・投稿・SNS 効果の評価はこの review の対象外である。

---

## Review Standard

次の基準で評価する。

1. 二層目的が goal から plan まで一貫して保たれている
2. scope がタグ構成に限定されており、戦略全体に広がっていない
3. 形式評価の4観点（作業量 / 判断量 / 文書量 / 効果の見えやすさ）が
   result で答えられる状態になっている
4. 形式変更の結論が result 前に出ていない
5. 「効果の予測」と「実運用後の確認」が分けて扱われる設計になっている

---

## Primary Review Questions

### 1. 二層目的は崩れていないか

goal と plan の両方で、
「タグ改善」と「形式検証」が並列に扱われているかを確認する。

確認事項:

- goal の Goal Statement で二層が明示されている
- plan の Execution Intent で二層が整理されている
- Deliverables に両方の出力が含まれている
- Planned Output Shape が result で両方に答える構成になっている

Failure mode:

タグ改善だけが進み、形式検証が result で抜け落ちる。

---

### 2. SNS 戦略全体に広がっていないか

scope がタグ構成に限定されているかを確認する。

確認事項:

- goal の Non-Goals に SNS 戦略全体が除外されている
- plan の Scope Policy に含めないものが明示されている
- Working Definitions がタグ種別の定義に留まっている
- 投稿頻度・コンテンツ方針が含まれていない

Failure mode:

plan の中で SNS 運用全般の改善に話が広がっている。

---

### 3. 形式評価4観点が result で答えられるか

4観点（作業量 / 判断量 / 文書量 / 効果の見えやすさ）が
result で実際に評価できる状態になっているかを確認する。

確認事項:

- goal の Notes For Planner に4観点が定義されている
- plan の Problem Structure に4観点が明示されている
- plan の Deliverables に形式評価が含まれている
- 「過剰」の定義が Working Definitions にある
- result で「重い / ちょうどよい / 足りない」を答えるための
  判断材料が plan 内に揃っている

Failure mode:

result に入ったとき、形式評価の基準が定義されておらず、
「なんとなく重かった」という感想止まりになる。

---

### 4. 効果の扱いが適切か

投稿前に効果を断定する設計になっていないかを確認する。

確認事項:

- plan の Assumptions に「予測と確認を分ける」が明示されている
- result の Planned Output Shape が「案」の段階で止まっている
- 効果断定が result の完了条件に入っていない

Failure mode:

result で「このタグにしたら効果が出た」と
未実施の効果を断定する構成になっている。

---

## Severity Model

### Critical

設計の目的自体を壊す欠陥。

例:

- 二層目的の片方が plan から消えている
- SNS 戦略全体が scope に入っている
- 形式変更の結論が plan 段階で出ている

### Major

result での判断を歪める欠陥。

例:

- 形式評価4観点が result で答えられない設計になっている
- 「過剰」の定義がなく、評価基準が曖昧なまま
- 効果の予測と確認が混在している

### Minor

明確さや運用しやすさを下げるが、構造を壊さない欠陥。

例:

- タグ分類の境界がやや曖昧
- result の構成案が抽象的すぎる

---

## Acceptance Conditions

次をすべて満たせば result に進んでよい。

- Critical issue がない
- 二層目的が goal から plan まで一貫している
- scope がタグ構成に限定されている
- 形式評価4観点が result で答えられる
- 形式変更の結論が result 前に出ていない
- 効果の予測と実運用後の確認が分けて設計されている

---

## Current Review Position

現在の評価:

- Accept

Rationale:

- goal と plan の二層目的は一貫している
- Non-Goals と Scope Policy により SNS 戦略全体への拡大は抑制されている
- 形式評価4観点は goal と plan の両方に定義されており、result で答えられる
- 「過剰」の定義が Working Definitions にある
- 効果の予測・確認の分離が plan の Assumptions に明示されている
- Critical / Major issue は見当たらない

---

## Safe Next Step

result に進む。

result では次を記録する。

1. タグ改善案（固定 / カテゴリ / 到達）
2. 投稿タイプ別組み合わせルール
3. 形式評価（4観点）
4. 軽量 variant 検討への示唆
