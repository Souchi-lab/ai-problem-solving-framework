# Review

<!-- このファイルは framework/templates/review.md のひな型を使用している -->
<!-- Critic が build.md + 成果物 + goal.md をもとに作成する -->
<!-- プロンプト: framework/agents/critic.md を参照 -->

---

## Summary of review

---

## Plan Readiness Review

<!-- plan.md の Implementation Readiness セクションを Critic が検証する -->
<!-- build.md の内容と照合し、plan 時点の readiness 申告が妥当だったかを評価する -->

| 観点 | plan 時点の申告 | build 後の実態 | 判定 |
|---|---|---|---|
| API / data shape 確定 | ✅ / ❌ | （build で設計変更があったか） | ○ / △ / × |
| 変更対象の列挙 | ✅ / ❌ | （漏れ・追加があったか） | ○ / △ / × |
| 依存順の明確さ | ✅ / ❌ | （build 中に分岐が増えたか） | ○ / △ / × |
| 互換保持点 | ✅ / ❌ | （互換判断を build 中にしたか） | ○ / △ / × |
| 検証観点の具体化 | ✅ / ❌ | （想定外の確認作業があったか） | ○ / △ / × |

**総合判定**:
- ○ plan の readiness は適切だった
- △ 一部 plan の精度が足りなかった（次回の改善点として記録）
- × plan が不十分だった（Improve で plan を再設計することを推奨）

> △ / × の場合、review の総合判定は原則 Improve 行きとする。Accept にする場合は理由を明記すること。

---

## Risks

### Critical
- なし

### Major
- なし

### Minor
- なし

---

## Weak Points

-

---

## Suggested Improvements

- [ ] [High]
- [ ] [Mid]
- [ ] [Low]

---

## Notes
