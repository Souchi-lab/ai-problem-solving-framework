# RuntimeTransport Interface — 最小設計書

---

## Metadata

| 項目 | 内容 |
|---|---|
| Status | Draft |
| Type | Design Note |
| Scope | Experimental / runtime abstraction |
| Intended use | GUI 化または wrapper 複雑化が進んだときの transport 切り出し参照 |
| 作成日 | 2026-03-28 |
| 関連設計判断 | smux 評価 RUN（Hold 判定）から派生 |

この文書は確定仕様ではない。
APSF の runtime 抽象化に関する将来設計メモとして、
`experimental/redesign` に保持する。

---

## Problem

現在の APSF は transport 層を持っていない。
agent 間のコンテキスト受け渡し操作が複数の層に散在している。

```
ActService.execute()
  → target_path.write_text(content)           # write 相当
  → PhaseDetector.detect() がファイル存在から推定  # advance は暗黙
  → _read_context_files() でファイル読み込み     # read 相当
```

この構造のまま GUI 化・pane IPC 化が進むと:

- ActService を transport ごとに分岐改修する必要が生じる
- 「どこが transport か」が読み手に見えない
- テスト時に「ファイルが存在するかどうか」という副作用に依存し続ける

RuntimeTransport interface を定義しておくことで、
transport の実装を差し替えても ActService の呼び出し側が変わらない構造を用意する。

---

## Interface

```python
# 想定配置: src/apsf/transport/base.py

from abc import ABC, abstractmethod
from ..orchestration.phase_detector import Phase


class RuntimeTransport(ABC):
    """
    phase 間のコンテキスト受け渡しを担う抽象層。
    実装を差し替えることで Markdown / GUI event / pane IPC を透過的に扱う。
    """

    @abstractmethod
    def write(self, phase: Phase, content: str) -> None:
        """このphaseの成果物を保存する。
        例: BUILD_NEEDED → build.md に書く / Viewer DB に格納 / pane に type する"""
        ...

    @abstractmethod
    def read(self, phase: Phase) -> str:
        """このphaseの成果物を取得する。未存在・未入力なら空文字列を返す。"""
        ...

    @abstractmethod
    def advance(self, phase: Phase) -> None:
        """このphaseの完了を通知する。
        Markdown 実装では no-op。GUI 実装ではイベント発火。pane 実装では Enter 送信。"""
        ...
```

**メソッド数: 3。これ以上は増やさない（現時点）。**

---

## Transport Variants

### MarkdownTransport（現状 / 今すぐ実装できる）

現在 ActService・PhaseDetector に暗黙で存在する操作を 1 クラスに集約したもの。

| メソッド | 動作 |
|---|---|
| `write(phase, content)` | `phase → filename` を解決して `path.write_text(content)` |
| `read(phase)` | 対応 .md ファイルが存在すれば `read_text()`、なければ `""` |
| `advance(phase)` | **no-op**。PhaseDetector がファイル存在から次 phase を推定するため明示的通知は不要 |

`phase → filename` のマッピングは現在 PhaseDetector の `_KNOWN_FILES` に暗黙で存在する。
MarkdownTransport はそれを明示化するだけ。既存動作は変わらない。

コンストラクタ: `MarkdownTransport(run_dir: Path)`

---

### GUIEventTransport（将来）

`advance` が初めて有意義になる実装。GUI では「書いた」と「次へ進む承認」は別操作。

| メソッド | 動作 |
|---|---|
| `write(phase, content)` | Viewer DB に `(run_id, phase, content)` を upsert |
| `read(phase)` | Viewer DB から `phase` に対応する content を取得 |
| `advance(phase)` | GUI に `phase_complete` イベントを発火。人間が「次へ」を押すまでブロック |

`gui-operation-north-star.md` に記載した「ポチポチ運用」の run type / required checks / next trigger が、
この `advance` のイベントとして自然に実装できる。

---

### PaneTransport（参考モデル / smux 型）

smux（tmux-bridge）の思想を参考にした実装例。smux への依存前提ではない。
subprocess で `tmux-bridge` を呼ぶか、同等の pane 操作を独自実装することになる。

| メソッド | 動作 |
|---|---|
| `write(phase, content)` | `tmux-bridge type` で次 agent pane に content を送信 |
| `read(phase)` | `tmux-bridge read` で前 agent pane の stdout を取得 |
| `advance(phase)` | `tmux-bridge keys Enter` で次 pane の agent を起動 |

**現時点では採用しない。** Windows 非対応・GUI North Star と逆行するため。
「agent 間 IPC に明示的な transport 抽象が必要」という smux の示唆を設計メモとして保持するための参考実装として記載する。

---

## Design Decisions

### なぜ 3 メソッドか

`write` / `read` / `advance` はそれぞれ「保存」「取得」「進行通知」という独立した責務を持つ。

- これ以下では transport の基本契約を表現できない
- これ以上（error handling / retry / streaming）は orchestration 層の責務であり interface に含めない

### なぜ write と advance を分けるか

現在の Markdown 実装では write が暗黙的に advance を兼ねている
（ファイルが存在すれば PhaseDetector が次 phase と判定する）。

しかし GUI では「保存した」と「次へ進む承認」は別アクション。
分離することで両方の実装に対応できる。
Markdown 実装では `advance` が no-op になるだけであり、分離のコストは低い。

### なぜ Phase を引数の型にするか

`str` や汎用 key にすると APSF の vocabulary が薄まり、呼び出し側でキャスト地獄が生まれる。
`Phase` は既に APSF の中核語彙（phase_detector.py）であり、interface もそれに従う。
将来 Phase の構造が変わるなら interface ごと変えればよい。

### なぜ run_context を引数にしないか

どの run について操作するかはコンストラクタで注入する（例: `MarkdownTransport(run_dir=Path(...))`）。
メソッド引数に run_context を持ち込むと呼び出し側の責務が増え、interface の用途が曖昧になる。

---

## Extension Room

将来拡張の候補。今すぐ設計に含める必要はない。

| 拡張 | 方法 | 着手条件 |
|---|---|---|
| 非同期対応 | `AsyncRuntimeTransport(ABC)` を並列定義 | phase 間で待機ブロックが問題になったとき |
| 複数 transport の合成 | `CompositeTransport(primary, mirror)` | Markdown + Viewer DB を同時書きしたいとき |
| `write` の戻り値 | `-> Path` で呼び出し側がパスを知れるように | MarkdownTransport の path を外部から参照したいとき |

現時点でこれらを先取りする必要はない。

---

## Scope Boundary

RuntimeTransport が担うのは **phase の成果物 I/O と進行通知のみ**。
以下は引き続き別レイヤーの責務であり、この interface に含めない。

| 責務 | 担当レイヤー |
|---|---|
| Phase の現状推定 | PhaseDetector |
| Run ディレクトリ管理 | RunRepository |
| プロンプト構築 | renderer.py |
| LLM 呼び出し | Provider / ActService |
| Human vs Auto 判定 | HUMAN_OWNED_PHASES（phase_detector.py）|

---

## Current Decision / Trigger Conditions

**現時点の判断: Hold**

MarkdownTransport の切り出し実装は未着手。
現在の `ActService + PhaseDetector + write_text` の構造は機能しており、
今すぐ rip-out するコストをかける必然性はない。

**着手条件（以下のいずれかが顕在化したとき）:**

1. **GUI 設計の開始**
   `gui-operation-north-star.md` に記載した「ポチポチ運用」の具体実装に着手するとき。
   GUIEventTransport を追加するタイミングで MarkdownTransport の切り出しも同時に行う。

2. **wrapper 複雑化**
   `apsf-claude-act.ps1` の分岐・再試行ロジックが transport 差異の吸収のために肥大化したとき。

3. **phase 間同期・並列実行の必要性顕在化**
   複数 agent が同時実行し、phase の complete 通知をイベントで受ける必要が生じたとき。

---

## 次 RUN 候補名（着手時）

```
YYYY-MM-DD_apsf-design_markdown-transport-extraction
```

この RUN では:
- `MarkdownTransport` を `src/apsf/transport/markdown.py` に切り出す
- `ActService` の write_text 呼び出しを `transport.write()` に差し替える
- 既存テストが変わらず通ることを確認する
- `GUIEventTransport` の stub を用意する（実装は GUI RUN に委譲）
