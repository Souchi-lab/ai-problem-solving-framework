# Execution Model — CLI / Human 前提の実行設計

## なぜ execution 抽象が必要か

「どの AI モデルを使うか」と「どうやって実行するか」は別の問題である。

同じ Builder role でも:
- Claude Code CLI から実行する
- 人間が手でコードを書く
- 将来、Anthropic API を直接呼ぶ

これらは**同じ role、異なる execution**であり、分離して扱う必要がある。

このフレームワークは `execution type` を抽象化することで、
**役割の設計をそのままに、実行手段だけを差し替えられる**構造にする。

---

## execution type の定義

| type | 説明 | v0.1 での扱い |
|---|---|---|
| `cli` | CLI ツール（Claude Code, Gemini CLI 等）を subprocess で呼ぶ | **主要対象** |
| `human` | 人間が手動で実行する | **主要対象** |
| `future-api` | REST/SDK API を直接呼ぶ | **今後の拡張** |

v0.1 では `cli` と `human` を中心に設計する。

---

## cli / human / future-api の違い

### cli executor
```
apsf run-step build  →  [ subprocess ]  →  claude "以下の plan.md を読んで..."
                                                ↓
                                         build.md が生成される
```

- ローカルの CLI ツールを subprocess で呼び出す
- API キー課金なしに、インストール済みの CLI ツールを活用できる
- dry-run が容易（コマンドを表示するだけ）
- 対話型CLI の完全自動化は v0.2 以降

### human executor
```
apsf run-step plan  →  [ 手動実行指示を表示 ]  →  人間が実行・記録
                                                     ↓
                                              plan.md を書く
```

- 実際の処理は人間が行う
- フレームワークは「何をすべきか」の指示と確認を担う
- Planner / Judge など判断が重要な役割に最適
- どのファイルを読んで、何を書けばよいかを明示する

### future-api executor（v0.2+）
```
apsf run-step build  →  [ API call ]  →  response.content → build.md
```

- `src/apsf/providers/` に実装される予定
- v0.1 では stub として placeholder を置く
- API executor を足しても、agent 側のコードは変わらない

---

## v0.1 で CLI / Human を選んだ理由

1. **API キー課金を避けられる**
   - Claude Code, Gemini CLI などのツールはローカルに既に入っている
   - 課金設定を整える前でもフレームワーク自体を検証できる

2. **フレームワークの本質を先に検証できる**
   - 「正しい handoff ができているか」「Goal が曖昧でないか」
   - これらの問題は API の有無に関係ない

3. **人間の介入が品質を安定させる**
   - Planner / Judge は人間が入ることで品質が高くなる
   - v0.1 段階では human executor が最も信頼できる

4. **後方互換で API 対応できる**
   - executor を差し替えるだけで、agent / orchestration / pipeline は変わらない
   - 先に良い骨格を作ってから API を足す方が品質が上がる

---

## workspaces を分ける意味

各 role が作業するディレクトリ（workspace）を分ける。

```
workspaces/
  planner/      ← Planner がここで作業する
  builder/      ← Builder がここで作業する
  critic/       ← Critic がここで作業する
  judge/        ← Judge がここで作業する
```

**目的:**
- CLI ツールの作業ディレクトリを role ごとに分離する
- 成果物の出力先を明確にする
- role をまたいだ context の混入を防ぐ

**重要:** workspaces に**実データ・成果物を長期保管しない**。
成果物の最終形は `runs/<run-name>/` に Markdown として記録する。
workspaces はあくまで作業空間であり、run のログは runs/ が持つ。

---

## role と executor の分離

```
BuilderAgent  uses  CLIExecutor(command="claude")
CriticAgent   uses  HumanExecutor()
PlannerAgent  uses  HumanExecutor()   # Planner は人間推奨
JudgeAgent    uses  HumanExecutor()   # Judge は人間必須（v0.1）
```

role の設計は変えずに、executor だけを差し替えられる。

悪い例: `ClaudeBuilder` — role と executor が密結合
良い例: `BuilderAgent(executor=CLIExecutor("claude"))` — 独立

---

## execution-assignment.md の位置づけ

`model-assignment.md` が「どのモデルを使うか」を定義するのに対し、
`execution-assignment.md` は「どうやって実行するか」を定義する。

v0.1 では execution-assignment.md の方が実質的に重要。
API が使えない状況では、実行手段（CLI か手動か）を最初に決めることが run の成否を左右する。

---

## 将来 API executor を足すときの考え方

1. `src/apsf/executors/api_executor.py` に実装を追加する
2. `src/apsf/providers/` 配下の各 provider を呼び出す
3. `execution-assignment.md` で role の execution を `future-api` に変更する
4. `assignment_service.py` が `api_executor` を生成するよう拡張する
5. **agent のコードは変えなくてよい**

これが executor 抽象の価値。
実行手段の変更が agent に波及しない。
