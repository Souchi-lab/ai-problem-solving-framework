# Result

---

## Unit C1 完了

`framework/legacy/` を repo 上に実体化し、
legacy と読むべき framework 文書群を着地させた。

---

## 実施内容

### 1. `framework/legacy/` の新設

次の構造で `framework/legacy/` を作成した。

```
framework/legacy/
├── README.md
├── execution-model.md
├── overview.md
├── workflow/
│   ├── v0.1.md
│   └── v0.2.md
├── agents/
│   ├── builder.md
│   ├── critic.md
│   ├── judge.md
│   ├── junior-builder.md
│   ├── planner.md
│   ├── critics/
│   └── planners/
├── templates/
│   └── (全テンプレート)
└── skills/
    └── planning-patterns.md
```

### 2. 直下文書の landing

- `framework/execution-model.md` → `framework/legacy/execution-model.md`
- `framework/overview.md` → `framework/legacy/overview.md`

### 3. 種別別文書群の landing

- `framework/workflow/` → `framework/legacy/workflow/`
- `framework/agents/` → `framework/legacy/agents/`
- `framework/templates/` → `framework/legacy/templates/`
- `framework/skills/` → `framework/legacy/skills/`

### 4. 旧位置誘導の設置

次の旧位置に誘導スタブを残した。

- `framework/execution-model.md`（冒頭スタブ）
- `framework/overview.md`（冒頭スタブ）
- `framework/workflow/README.md`（新設スタブ）
- `framework/agents/README.md`（新設スタブ）
- `framework/templates/README.md`（新設スタブ）
- `framework/skills/README.md`（新設スタブ）

---

## 除外確認

- `framework/planning-patterns.md`（root 直下）: 今回対象外 ✓
- `framework/core/` 側: 変更なし ✓
- Python 実装移行: 対象外 ✓

---

## Verification チェック

1. `framework/legacy/` が存在する ✓
2. `execution-model.md` と `overview.md` の landing が読める ✓
3. 文書群が legacy 側に整理されている ✓
4. root 直下の `planning-patterns.md` を巻き込んでいない ✓

---

## C1 → 次フェーズの状態

- `framework/core/` landing: Unit A で完了済み
- `framework/legacy/` landing: Unit C1 で完了（この run）
- `src/apsf/core/` Python contracts: Unit B で完了済み（run-021）
- `src/apsf/legacy/` skeleton: Unit C2 で完了済み（run-024）
- Python 実装移行計画（Unit C3）: 次の planning run へ

文書 legacy の着地が完了したことで、
C3 planning では「文書 legacy はすでに着地済み」として
Python 実装側の移行スコープに集中できる状態になった。
