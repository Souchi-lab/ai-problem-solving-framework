# Goal

---

## Goal Statement

`apsf init-followup <slug>` コマンドを CLI に追加し、
`framework/experimental/redesign/followups/<slug>/` に
4ファイルのスケルトン（goal / plan / review / result）を生成できるようにする。

目的は全文自動生成ではなく、
骨格だけを即座に出して「手で構造を組む」摩擦を取り除くことである。

今回も目的は二層になっている。

- 表層: `apsf init-followup` コマンドの実装
- 裏層: 「CLI 拡張を伴う小実装 follow-up」に4点セットが機能するかの形式検証

---

## Background

これまでの follow-up（twitter-tag-improvement / video-intro-assembly）では、
goal / plan / review / result を毎回手で作成してきた。

構造は毎回ほぼ同じで：
- Follow-up Context（parent series / previous result / new trigger / scope limit）
- narrow question 用の見出し群
- result の closing block（Stable Baseline / Open Conditional / Next Trigger）

これを手で組むたびに「どこまで書くか」の判断コストが発生し、
follow-up を始める心理的摩擦になっていた。

CLI コマンドで骨格だけ出せれば、
この摩擦を「コマンド1本 + 中身を書く」だけに圧縮できる。

また、これは north star の「GUI 中心のポチポチ運用」への
CLI 前段としての最小着地でもある。

---

## Success Criteria

次の条件を満たす状態になること。

1. `apsf init-followup <slug>` で4ファイルが `followups/<slug>/` に生成される
2. 生成内容は全文自動生成ではなく骨格テンプレ（セクション見出し + プレースホルダー）
3. Follow-up Context・narrow question 見出し・closing block が最初から含まれている
4. 既存の CLI コマンド（init-run 等）と同じパターンで追加されている
5. `--force` フラグで既存ディレクトリを上書きできる
6. 使ってみて「心理コストが下がった」かどうかを result で判断できる観点が定義されている
   （判定観点の例: 開始までの迷い / 手作業量 / 命名迷い / 初期構造の再発明量）

---

## Expected Outputs

- `src/apsf/cli/main.py` への `init-followup` コマンド追加
- 4ファイルのテンプレート文字列（コード内定義 or テンプレファイル）
- `apsf init-followup <slug>` の動作確認（手動テスト）
- 形式評価（CLI 拡張タスクに4点セットは適切だったか）

---

## Non-Goals

- テンプレートの自動カスタマイズ（goal の中身を AI が書く）
- `runs/` 配下への適用（対象は `followups/` のみ）
- 既存の `init-run` コマンドの変更
- テンプレートファイルの外部化（v1 はコード内定義で十分）
- GUI 実装

---

## Constraints

- 変更対象は `src/apsf/cli/main.py` のみ（または最小の追加ファイル）
- テンプレートは骨格のみ（プレースホルダー付き見出し構造）
- 既存コマンドのパターン（typer.Argument / typer.Option）に従う
- `followups/` ディレクトリが存在しない場合は作成する

---

## Notes For Planner

Planner は次を明確化すること。

- テンプレート文字列をコード内に埋め込むか、別ファイルに分けるか
- 4ファイルそれぞれのスケルトン構造（どのセクションを含めるか）
- `--force` の動作（ファイルごと上書き or ディレクトリごと）
- 既存の `init-run` との実装パターン上の差分

特に、
「骨格テンプレ」の粒度判断が重要である。
多すぎると「テンプレを消す」手間が生まれ、
少なすぎると「構造を考える」コストが残る。
今回の実験台（twitter-tag / video-intro の実績）を参考に適切な粒度を決めること。
