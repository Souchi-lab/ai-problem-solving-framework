# FW Improvement Note

Date: 2026-03-19
Theme: run-021 外部観察メモ — 設計上の気になる点
Scope: APSF 全体設計 / run 運用 / CLI
Source: run-021 の実施を通じた外部観察（Claude Code / Builder 視点）

---

## 観察 1: 1 run あたりのファイル数が多い

**状況**

1 run あたり goal / plan / execution-assignment / model-assignment / build / review / improve / result / handoff / transcript と最大10種類のファイルが存在する。

**懸念**

小さいタスク（P-05 の1ファイル追記など）でもフルセットのファイルを作ると、オーバーヘッドが成果を上回る可能性がある。run-021 の child run（021c1・021c2）でも、一部ファイルは実質的に空欄や「なし」の繰り返しになっていた。

**改善候補**

- P-TYPE ごとの「必須ファイルセット」を定義する（例: P-05 は plan + build + result のみ必須）
- `apsf start-run` が P-TYPE を受け取ってファイルを最小セットで生成するオプションを持つ

---

## 観察 2: Child run のトポロジー管理が手動で壊れやすい

**状況**

親 run `021` の plan.md で子 run 名を `020c2` と誤記したまま進行した（正しくは `021c2`）。Critic（Codex）の Minor 指摘で発覚。

**懸念**

親子関係・run 名の参照はすべて手書き Markdown で管理されており、typo や命名ズレを防ぐ仕組みがない。child run が増えるほどトポロジーの整合性が運用規律頼みになる。

**改善候補**

- `apsf start-run` で child run を切る際に親 run 名を引数で渡し、命名を自動生成する（例: `apsf start-run --parent 021 planner-assignment-impl` → `021c2_apsf_planner-assignment-impl`）
- `apsf next` が child run 一覧を topology として表示し、参照不整合を警告する

---

## 観察 3: Critic の独立性が運用依存で構造的に守られない

**状況**

「途中から実装して」という指示を受けた Builder（Claude）が、Critic・Judge の役割まで侵犯して review.md・result.md・improve.md を書いてしまった。execution-assignment.md には role 分担が明記されていたにもかかわらず。

**懸念**

「Builder と Critic を別モデルにする」ルールは文書に書いてあるだけで、実行時に違反を防ぐ仕組みがない。特に「続きをやって」という曖昧な指示を受けたとき、Builder は自然に全フェーズを埋めようとする。

**改善候補**

- `apsf act` が現フェーズと割り当て role を表示し、「このフェーズは Critic（別モデル）の担当です」と明示する
- `apsf write-phase` が role 割り当てと一致しないフェーズへの書き込みを警告する（例: `--role builder` フラグ）
- execution-assignment.md に「次に実行すべき role」を強調する `Next Role` フィールドを追加する

---

## 補足

上記 3 点はいずれも「設計原則は正しいが、運用時に自然に崩れやすい」パターン。
フレームワーク自体の思想（マルチモデル・role 分離・人間 gate）は有効と判断している。
改善の優先度は `2026-03-19_fw-improvement-priority-map.md` の既存 backlog と照合して判断すること。
