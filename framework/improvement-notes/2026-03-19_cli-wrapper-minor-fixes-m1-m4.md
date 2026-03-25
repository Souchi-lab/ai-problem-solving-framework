# CLI / Wrapper Minor Fixes: M-1 to M-4

Date: 2026-03-19
Type: fw-improvement memo
Status: Applied

---

## Summary

CLI と wrapper に残っていた軽微な運用ノイズ 4 件を修正した。

- M-1: `already_filled` 時の `[Info]` を stdout ではなく stderr に出す
- M-2: `apsf-claude-act.ps1` の `generate-setup` だけ stderr 抑制を解除する
- M-3: `generate-setup` 完了後の next 表示を `apsf act` から `apsf next` に修正する
- M-4: `-UntilPlan -DryRun` の Step 1 表示を現在 phase に応じて動的化する

---

## Why This Matters

どれも大きな設計不整合ではないが、CLI を pipe で使う時の見通しとデバッグ性に直接効く。

- stdout/stderr の役割が曖昧だと、pipe 利用時に機械処理しにくくなる
- wrapper が stderr を捨てると、失敗理由が見えず調査コストが上がる
- next action 表示が実際の推奨コマンドとズレると利用者を迷わせる
- DryRun 表示が実動作とズレると wrapper への信頼が落ちる

---

## Applied Changes

### M-1: already_filled message to stderr

File:
- `src/apsf/cli/main.py`

Change:
- `result.mode == "already_filled"` の `[Info]` と `Use: ... --force` を stderr 出力へ変更

Effect:
- stdout を prompt / machine-readable output から汚しにくくした

### M-2: keep generate-setup stderr visible in wrapper

File:
- `scripts/apsf-claude-act.ps1`

Change:
- `generate-setup` 呼び出しだけ `2>$null` を解除

Effect:
- setup 失敗時に原因が wrapper 利用者へ見えるようになった

### M-3: next action text corrected

File:
- `src/apsf/cli/main.py`

Change:
- `generate-setup` 成功後の `[Next]` を `apsf act <run>` から `apsf next <run>` に修正
- あわせて stderr 出力へ変更

Effect:
- 実際の推奨導線と表示が一致した

### M-4: dynamic dry-run display in -UntilPlan

File:
- `scripts/apsf-claude-act.ps1`

Change:
- `-UntilPlan -DryRun` の Step 1 表示を固定文言ではなく現在 phase ベースで切り替えるように修正

Effect:
- `execution-assignment.md` が既に埋まっている場合、DryRun でも `(skipped)` と表示される

---

## Lesson

minor fix でも、CLI / wrapper では以下を外すと体験が悪化しやすい。

- informational guard message は stderr に寄せる
- pipe の source になる stdout はなるべくクリーンに保つ
- wrapper の dry-run 表示は実動作と一致させる
- debug に必要な stderr を安易に捨てない

---

## Related Files

- `src/apsf/cli/main.py`
- `scripts/apsf-claude-act.ps1`
