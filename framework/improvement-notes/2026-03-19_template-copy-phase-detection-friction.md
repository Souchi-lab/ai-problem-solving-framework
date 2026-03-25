# FW Improvement Note

Date: 2026-03-19
Theme: template copy file と phase detection / wrapper success 判定の摩擦
Scope: `apsf start-run` / phase detector / `write-phase` / wrapper

---

## Observation

`apsf start-run` は `runs/_template/` から複数の run ファイルを先にコピーする。
その結果、`improve.md` や `result.md` のような将来フェーズ用ファイルも、run 作成直後から
テンプレ本文を持った状態で存在する。

この前提のまま phase detection や `apsf write-phase` が「内容あり」を強く解釈すると、
テンプレだけのファイルを実成果物として誤認しやすい。

さらに wrapper (`scripts/apsf-claude-act.ps1`) 側でも、以前は
「phase が進んだ = target file も保存された」と見なしていたため、
template copy 由来の誤判定や別ファイルへの書き込みを成功扱いし得た。

---

## Symptoms

- Human が `improve.md` をまだ書いていないのに、CLI 側では `"already filled"` に見えることがある
- phase detector が template-only file を根拠に次フェーズへ進めてしまう恐れがある
- wrapper が phase advancement だけを見て `build.md saved` のように表示し、target file 未更新を見逃し得た

---

## Root Cause

共通の根は 1 つで、template scaffolding と実際の run 成果物の区別が弱いこと。

ただし問題は 2 層に分かれる。

1. Core layer
`phase_detector.py` / `write-phase` が template-only file を実データ扱いしてしまう

2. Wrapper layer
`apsf-claude-act.ps1` が phase 遷移を target file 保存の証拠として使ってしまう

つまり同じ根の派生だが、完全に同一バグではない。

---

## Current Mitigation

- `apsf write-phase` 側では template-only / empty input をより明示的に扱う方向が必要
- Human-owned phase は `[Stop]` で止める
- wrapper 側では target file の existence / hash change を確認してから success 扱いにする

2026-03-19 時点で wrapper には後者の防御を追加済み。

---

## Improvement Directions

1. Template copy reduction
- `apsf start-run` は `goal.md` など即時に必要な最小ファイルだけ作る
- 将来フェーズ用ファイルは phase 到達時に生成する

2. Template-aware phase detection
- phase detector は「ファイルがあるか」ではなく「template-only かどうか」を見る
- `write-phase` は `already filled` の理由を `real content` / `template scaffolding only` に分ける

3. Wrapper hardening
- wrapper は success 判定で target file の変更有無を確認する
- `phase advanced but target file unchanged` を明示的な warning / stop にする

4. P-TYPE-driven file set
- `2026-03-19_run021-observer-notes.md` の observation 1 と合わせて、
  P-TYPE ごとに必要最小ファイルセットを定義する

---

## References

- [`2026-03-19_run021-observer-notes.md`](C:\Users\PC_User\PRJ\ai-problem-solving-framework\framework\improvement-notes\2026-03-19_run021-observer-notes.md)
- [`phase_detector.py`](C:\Users\PC_User\PRJ\ai-problem-solving-framework\src\apsf\orchestration\phase_detector.py)
- [`main.py`](C:\Users\PC_User\PRJ\ai-problem-solving-framework\src\apsf\cli\main.py)
- [`apsf-claude-act.ps1`](C:\Users\PC_User\PRJ\ai-problem-solving-framework\scripts\apsf-claude-act.ps1)
