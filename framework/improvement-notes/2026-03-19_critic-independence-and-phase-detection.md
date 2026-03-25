# FW Improvement Note

Date: 2026-03-19
Theme: Critic 独立性の定義曖昧さ と apsf next の role 割り当て未検証問題
Scope: operating model / Critic role / CLI phase detection

---

## 観察した事象

run-022 の REVIEW_NEEDED フェーズで `apsf-claude-act.ps1` を実行したところ、`execution-assignment.md` で `Critic = human / ChatGPT` と指定されているにもかかわらず、スクリプトが停止せず `claude -p`（Claude Sonnet）で `review.md` を自動生成した。

生成された review.md の `Reviewer: Claude Code` 表記から、Builder と同一モデルが Critic を担当したことが判明した。

---

## 問題 1: `apsf next` が execution-assignment.md の role 割り当てを読んでいない

**現状:**
`apsf next` は phase ファイルの存在・充填状態からフェーズを判定するが、`execution-assignment.md` の role 割り当て（`human / cli`）を参照していない。そのため REVIEW_NEEDED フェーズが `human` 担当であっても Human stop がかからず、スクリプトが自動実行に進んでしまう。

**改善候補:**
- `apsf next` が `execution-assignment.md` を読み、現フェーズの担当 role が `human` なら `[Stop] Human-owned phase` を出力する
- `apsf-claude-act.ps1` が `execution-assignment.md` の role 列を確認し、`human` 担当フェーズでは自動実行を停止する

---

## 問題 2: 「同モデル別セッション」は Critic の独立性要件を満たすか

**フレームワークの要件（operating-model.md）:**
> 異なる学習データ・アーキテクチャのモデルを組み合わせることで、見落としを補完し合うレビューになる。
> Builder = Anthropic 系 / Critic = OpenAI 系（または人間）

**今回の実態:**
- Builder = Claude Sonnet 4.6（この会話セッション）
- Critic = Claude Sonnet 4.6（`claude -p` 別セッション）

**論点:**
「別セッション」であることの意義:
- build.md を書いた文脈（会話履歴）を持たない → 独立した推論として動く ✅
- 新規セッションのため直接的な context bias はない ✅

「同モデル」であることの限界:
- 同一の重み・学習データ・アーキテクチャ = 体系的に同じ盲点を持つ可能性がある
- GPT-4o / Codex が指摘できる「Claude が気づきにくい観点」は検出されない
- フレームワークが求める「補完関係」は別セッションでは実現されない

**実用的な判断基準（案）:**
- Minor のみの指摘で終わった場合は「同モデル別セッション」でも proceed 可
- Major 以上が出なかった場合に「見落としがないか」を疑う必要がある
- 重要 run（アーキテクチャに影響する変更など）は必ず別モデル（GPT-4o / 人間）を Critic にする

**改善候補:**
- `execution-assignment.md` の Critic 行に `same-model-ok: true/false` フラグを追加し、`false` の場合は `apsf next` が警告を出す
- `operating-model.md` に「同モデル別セッションは Critic として条件付き許容」の基準を追記する（run の重要度・影響範囲による）

---

## 関連

- run-021 でも同様の Critic 独立性侵害が発生（Builder が review.md を自己作成）
- `framework/improvement-notes/2026-03-19_run021-observer-notes.md` 観察 3 と連続する問題
- `framework/cli-orchestrator.md`（phase detection 設計）
- `src/apsf/orchestration/phase_detector.py`（実装）
- `scripts/apsf-claude-act.ps1`（wrapper）
