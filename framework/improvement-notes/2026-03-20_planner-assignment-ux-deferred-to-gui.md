# Improvement Note: Planner 未設定時の案内 → GUI 実装まで保留

Date: 2026-03-20

---

## 背景

PLAN_NEEDED 到達時に execution-assignment.md の Planner 行が未設定でも、
`apsf next` はフェーズと次ロールを表示するだけで「Planner を追加してください」とは案内しない。

## 検討した改善

- `apsf next` が Planner 未設定を検知して設定を促す案内を出す（P-01）
- execution-assignment.md テンプレートに「TBD OK」注釈を追加する（P-05）

## 判断: 保留（GUI 実装時に対応）

CLI ユーザーにとって execution-assignment.md を直接編集するハードルは許容範囲。
GUI 実装時にプランナー選択 UI（ドロップダウン → 保存 → 自動起動）として実装する方が
自然かつリッチに解決できるため、CLI 側の対応は不要。

## GUI 実装時にやること

- PLAN_NEEDED 画面に「Planner が未設定」バナーを表示
- [+ プランナーを追加] ボタンで Claude / ChatGPT / Gemini / 人間 を選択
- 保存後に `apsf act` を自動起動

## 自動探索（フォールバック）について

「適切なプランナーが不在の場合に別のプランナーを自動探索する仕組み」も検討したが不要と判断。
run は PLAN_NEEDED で止まり人間に戻ってくる運用で十分。
