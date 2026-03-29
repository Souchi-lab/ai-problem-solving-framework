# Goal

Run: 2026-03-29-019_fw-improvement_reconstruction-implementation-planning
Date: 2026-03-29

---

## Goal Readiness Check

- `run-018` で資産分類表、directory mapping、compare material、implementation-planning acceptance criteria が完成済み
- `run-018` の主分類結果と迷い資産 3 点が明示されている
- 次段は design-only ではなく、実装計画を Codex 向けに具体化する段階である
- ただし、この run 自体はまだファイル移動や import 変更を実行しない

Decision: Proceed

---

## Objective

`run-018` の分類結果を前提に、
APSF 再構築の最初の安全な移行単位と実装順序を定義する。

今回の run の目的は、
`core / legacy / experimental / viewer`
の思想をもう一度議論することではなく、
Codex が次の implementation run で安全に着手できるように、

- どこから移すか
- 何をまだ移さないか
- 変更単位をどう切るか
- import / path / CLI 影響をどう抑えるか
- 何をもって 1 移行単位の完了とみなすか

を実装計画として定義することである。

---

## Scope

この run が出力するものは次の 4 点に限定する。

1. **Initial migration unit proposal**
   - 最初に着手すべき移行単位
   - 対象は `run-018` で `core` に分類された明確資産を優先する
   - 迷い資産 3 点は初手から外す

2. **Implementation order**
   - 複数の移行単位がある場合の順序
   - 依存関係、import 影響、検証容易性を基準に並べる

3. **Risk-controlled change boundaries**
   - 各移行単位で触ってよい範囲
   - 触らない範囲
   - `viewer`、迷い資産、legacy 読解資産を巻き込まない条件

4. **Verification and completion criteria**
   - 各移行単位で必要な検証
   - 完了判定
   - 次単位へ進んでよい条件

---

## Constraints on Planning

### 実行しないこと

- 実ファイルの移動
- import / path の変更
- CLI entrypoint の変更
- `viewer` の位置づけ変更
- 迷い資産 3 点の最終決着

### 初手で触らないもの

- `framework/planning-patterns.md`
- `src/apsf/orchestration/pipeline.py`
- `src/apsf/storage/*` の contract 抽出を伴う変更
- `src/apsf/viewer/*`
- `framework/experimental/redesign/` 配下の experimental 資産

### planning 原則

- 最初の移行単位は小さく、検証しやすく、巻き込みが少ないこと
- `core` の明確資産から始める
- `legacy` は readable な現行運用として維持する
- 1 run で全部動かそうとしない

---

## Non-Goals

- `core / legacy / experimental` の再定義
- `run-018` の分類結果の再審議
- compare material の増補
- 実装実行そのもの
- legacy retirement の決定

---

## Success Criteria

1. 最初の移行単位が 1〜3 単位に絞られている
2. 各単位に対象ファイル群と非対象範囲がある
3. 順序づけに理由が 1 段落で説明されている
4. 迷い資産 3 点を初手から外す理由が明記されている
5. 検証方法が `pytest`、readability、import 影響などの観点で定義されている
6. Codex がそのまま implementation run に移れる粒度になっている
7. 出力全体が implementation-planning に留まり、実装指示書そのものに崩れていない

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-28-018_fw-improvement_reconstruction-asset-classification/result.md`
- `framework/experimental/redesign/plan.md`
- `framework/experimental/redesign/result.md`

特に `run-018` の次を尊重すること。

- `core` の明確資産
- `legacy` は現行運用として readable に保つ
- `viewer` は現位置維持
- 迷い資産 3 点は保留
- implementation-planning acceptance criteria 7 項目

---

## Desired Landing

この run の着地は、
`次に Codex が実際にどの単位から移行し始めれば安全か`
が明確になった状態である。

理想形は、

- 最初の移行単位
- 次の移行単位
- 各単位のリスク境界
- 検証方法
- 保留資産の扱い

がそのまま次 run の `plan.md` または `build.md` の土台として使えることである。
